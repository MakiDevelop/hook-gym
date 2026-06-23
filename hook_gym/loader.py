"""Load hooks from settings.json and cases from YAML files."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class Hook:
    event_type: str
    matcher: str
    command: str
    timeout: int = 5

    @property
    def name(self) -> str:
        script = Path(self.command.split()[-1])
        return script.stem


@dataclass
class Case:
    name: str
    description: str
    hook_event: str
    hook_matcher: str
    event_json: dict
    expect: str  # "blocked" or "allowed"
    tags: list[str] = field(default_factory=list)
    source_file: str = ""


def load_hooks(settings_path: Path) -> list[Hook]:
    data = json.loads(settings_path.read_text())
    raw_hooks = data.get("hooks", {})
    result = []
    for event_type, groups in raw_hooks.items():
        for group in groups:
            matcher = group.get("matcher", "")
            for h in group.get("hooks", []):
                if h.get("type") == "command" and h.get("command"):
                    result.append(Hook(
                        event_type=event_type,
                        matcher=matcher,
                        command=h["command"],
                        timeout=h.get("timeout", 5),
                    ))
    return result


def load_cases(cases_dir: Path) -> list[Case]:
    result = []
    for f in sorted(cases_dir.glob("*.yaml")):
        raw = yaml.safe_load(f.read_text())
        for c in raw.get("cases", []):
            result.append(Case(
                name=c["name"],
                description=c.get("description", ""),
                hook_event=c["hook_event"],
                hook_matcher=c.get("hook_matcher", ""),
                event_json=c["event_json"],
                expect=c.get("expect", "blocked"),
                tags=c.get("tags", []),
                source_file=f.name,
            ))
    return result


def match_hooks_for_case(hooks: list[Hook], case: Case) -> list[Hook]:
    """Find hooks that should fire for a given case."""
    matched = []
    for h in hooks:
        if h.event_type != case.hook_event:
            continue
        if h.matcher:
            tool_name = case.event_json.get("tool_name", "")
            file_path = case.event_json.get("file_path", "")
            matchers = h.matcher.split("|")
            if not any(m in tool_name or m in file_path for m in matchers):
                if not any(file_path.endswith(m.replace("*", "")) for m in matchers if "*" in m):
                    continue
        matched.append(h)
    return matched
