"""CLI entry point for hook-gym."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from rich.console import Console

from .loader import load_cases, load_hooks, match_hooks_for_case
from .reporter import print_report, write_report_md
from .runner import run_case


CASES_DIR = Path(__file__).parent.parent / "cases"


def cmd_run(args: argparse.Namespace) -> int:
    console = Console()

    settings_path = Path(args.hooks).expanduser()
    if not settings_path.exists():
        console.print(f"[red]settings.json not found: {settings_path}[/red]")
        return 1

    cases_dir = Path(args.cases).expanduser() if args.cases else CASES_DIR
    if not cases_dir.exists():
        console.print(f"[red]cases directory not found: {cases_dir}[/red]")
        return 1

    hooks = load_hooks(settings_path)
    cases = load_cases(cases_dir)

    if not hooks:
        console.print("[yellow]No hooks found in settings.json[/yellow]")
        return 1

    if not cases:
        console.print("[yellow]No test cases found[/yellow]")
        return 1

    if args.tag:
        cases = [c for c in cases if any(t in c.tags for t in args.tag)]

    console.print(f"[dim]Loaded {len(hooks)} hooks, {len(cases)} cases[/dim]")
    console.print()

    results = []
    for case in cases:
        matched = match_hooks_for_case(hooks, case)
        result = run_case(matched, case)
        results.append(result)

    print_report(results, console)

    if args.report:
        report_path = Path(args.report)
        write_report_md(results, report_path)
        console.print(f"[dim]Report written to {report_path}[/dim]")

    failed = sum(1 for r in results if not r.passed)
    return 1 if failed else 0


def cmd_list(args: argparse.Namespace) -> int:
    console = Console()

    settings_path = Path(args.hooks).expanduser()
    if settings_path.exists():
        hooks = load_hooks(settings_path)
        console.print(f"[bold]Hooks[/bold] ({len(hooks)}):")
        for h in hooks:
            console.print(f"  {h.event_type:20s} | {h.matcher:15s} | {h.name}")
        console.print()

    cases_dir = Path(args.cases).expanduser() if args.cases else CASES_DIR
    if cases_dir.exists():
        cases = load_cases(cases_dir)
        console.print(f"[bold]Cases[/bold] ({len(cases)}):")
        for c in cases:
            tags = f" [{', '.join(c.tags)}]" if c.tags else ""
            console.print(f"  {c.name:40s} | expect={c.expect:7s} | {c.hook_event}{tags}")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="hook-gym",
        description="Test harness for Claude Code hooks",
    )
    parser.add_argument(
        "--hooks",
        default="~/.claude/settings.json",
        help="Path to Claude Code settings.json",
    )
    parser.add_argument(
        "--cases",
        default=None,
        help="Path to cases directory (default: built-in cases/)",
    )

    sub = parser.add_subparsers(dest="command")

    run_p = sub.add_parser("run", help="Run all test cases against hooks")
    run_p.add_argument("--tag", action="append", help="Filter cases by tag")
    run_p.add_argument("--report", help="Write markdown report to file")

    sub.add_parser("list", help="List loaded hooks and cases")

    args = parser.parse_args()

    if args.command is None:
        args.command = "run"
        args.tag = None
        args.report = None

    if args.command == "run":
        sys.exit(cmd_run(args))
    elif args.command == "list":
        sys.exit(cmd_list(args))


if __name__ == "__main__":
    main()
