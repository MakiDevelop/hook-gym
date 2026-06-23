"""Execute hooks against test cases and collect results."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from enum import Enum

from .loader import Case, Hook


class Outcome(Enum):
    BLOCKED = "blocked"
    ALLOWED = "allowed"
    ERROR = "error"
    NO_HOOK = "no_hook"


@dataclass
class CaseResult:
    case: Case
    outcome: Outcome
    passed: bool
    hook_name: str = ""
    hook_output: str = ""
    exit_code: int = 0
    error_msg: str = ""


def run_hook(hook: Hook, event_json: dict) -> tuple[int, str]:
    """Run a single hook script with event JSON on stdin."""
    try:
        proc = subprocess.run(
            hook.command,
            shell=True,
            input=json.dumps(event_json),
            capture_output=True,
            text=True,
            timeout=hook.timeout + 2,
        )
        return proc.returncode, proc.stdout.strip()
    except subprocess.TimeoutExpired:
        return -1, "TIMEOUT"
    except Exception as e:
        return -1, str(e)


def parse_hook_output(stdout: str) -> Outcome:
    """Determine if hook blocked the action."""
    if not stdout:
        return Outcome.ALLOWED
    try:
        data = json.loads(stdout)
        hso = data.get("hookSpecificOutput", {})
        decision = hso.get("permissionDecision", "")
        if decision == "deny":
            return Outcome.BLOCKED
        if decision == "block":
            return Outcome.BLOCKED
    except (json.JSONDecodeError, AttributeError):
        pass
    if "DANGER GUARD" in stdout or "deny" in stdout.lower():
        return Outcome.BLOCKED
    return Outcome.ALLOWED


def run_case(hooks: list[Hook], case: Case) -> CaseResult:
    """Run all matching hooks for a case. Any block = blocked."""
    if not hooks:
        passed = case.expect == "allowed"
        return CaseResult(
            case=case,
            outcome=Outcome.NO_HOOK,
            passed=passed,
            error_msg="no matching hook found",
        )

    for hook in hooks:
        exit_code, stdout = run_hook(hook, case.event_json)

        if exit_code == -1:
            return CaseResult(
                case=case,
                outcome=Outcome.ERROR,
                passed=False,
                hook_name=hook.name,
                exit_code=exit_code,
                hook_output=stdout,
                error_msg=stdout,
            )

        if exit_code == 2:
            outcome = Outcome.BLOCKED
        else:
            outcome = parse_hook_output(stdout)

        if outcome == Outcome.BLOCKED:
            passed = case.expect == "blocked"
            return CaseResult(
                case=case,
                outcome=outcome,
                passed=passed,
                hook_name=hook.name,
                exit_code=exit_code,
                hook_output=stdout,
            )

    passed = case.expect == "allowed"
    return CaseResult(
        case=case,
        outcome=Outcome.ALLOWED,
        passed=passed,
        hook_name=hooks[-1].name,
        exit_code=0,
        hook_output="",
    )
