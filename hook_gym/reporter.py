"""Generate pass/fail reports from test results."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from rich.console import Console
from .runner import CaseResult, Outcome


def print_report(results: list[CaseResult], console: Console | None = None) -> None:
    console = console or Console()

    by_hook: dict[str, list[CaseResult]] = defaultdict(list)
    for r in results:
        key = r.hook_name or r.case.hook_event
        by_hook[key].append(r)

    total_pass = sum(1 for r in results if r.passed)
    total = len(results)

    console.print()
    console.print("[bold]Hook Gym Results[/bold]")
    console.print(f"[dim]{'=' * 50}[/dim]")
    console.print()

    for hook_name, cases in sorted(by_hook.items()):
        passed = sum(1 for r in cases if r.passed)
        count = len(cases)

        if passed == count:
            icon = "[green]PASS[/green]"
        elif passed == 0:
            icon = "[red]FAIL[/red]"
        else:
            icon = "[yellow]PARTIAL[/yellow]"

        console.print(f"  {icon}  [bold]{hook_name}[/bold]: {passed}/{count} cases")

        for r in cases:
            if r.passed:
                console.print(f"       [green]OK[/green]  {r.case.name}")
            else:
                expect = r.case.expect
                got = r.outcome.value
                console.print(f"       [red]NG[/red]  {r.case.name} (expected={expect}, got={got})")
                if r.error_msg:
                    console.print(f"            [dim]{r.error_msg}[/dim]")
        console.print()

    pct = (total_pass / total * 100) if total else 0
    color = "green" if pct == 100 else "yellow" if pct >= 70 else "red"
    console.print(f"[{color} bold]Overall: {total_pass}/{total} passed ({pct:.0f}%)[/{color} bold]")
    console.print()


def write_report_md(results: list[CaseResult], output_path: Path) -> None:
    by_hook: dict[str, list[CaseResult]] = defaultdict(list)
    for r in results:
        key = r.hook_name or r.case.hook_event
        by_hook[key].append(r)

    total_pass = sum(1 for r in results if r.passed)
    total = len(results)
    pct = (total_pass / total * 100) if total else 0

    lines = [
        "# Hook Gym Report",
        "",
        f"**Overall: {total_pass}/{total} passed ({pct:.0f}%)**",
        "",
    ]

    for hook_name, cases in sorted(by_hook.items()):
        passed = sum(1 for r in cases if r.passed)
        count = len(cases)
        icon = "PASS" if passed == count else "FAIL" if passed == 0 else "PARTIAL"
        lines.append(f"## {icon} {hook_name} ({passed}/{count})")
        lines.append("")
        lines.append("| Case | Expect | Got | Status |")
        lines.append("|------|--------|-----|--------|")
        for r in cases:
            status = "OK" if r.passed else "NG"
            lines.append(f"| {r.case.name} | {r.case.expect} | {r.outcome.value} | {status} |")
        lines.append("")

    failures = [r for r in results if not r.passed]
    if failures:
        lines.append("## Failures Detail")
        lines.append("")
        for r in failures:
            lines.append(f"### {r.case.name}")
            lines.append(f"- **Description**: {r.case.description}")
            lines.append(f"- **Expected**: {r.case.expect}")
            lines.append(f"- **Got**: {r.outcome.value}")
            if r.hook_output:
                lines.append(f"- **Hook output**: `{r.hook_output[:200]}`")
            if r.error_msg:
                lines.append(f"- **Error**: {r.error_msg}")
            lines.append("")

    output_path.write_text("\n".join(lines))
