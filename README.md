# Hook Gym

Test harness for Claude Code hooks. Batch-run violation cases against your guardrails and get a pass/fail report.

## Install

```bash
pip install -e .
```

## Usage

```bash
# Run all cases against your hooks
hook-gym run

# List loaded hooks and cases
hook-gym list

# Filter by tag
hook-gym run --tag destructive

# Generate markdown report
hook-gym run --report report.md
```

## Writing Cases

Cases are YAML files in `cases/`. Each file contains a list of test scenarios:

```yaml
cases:
  - name: git-force-push
    description: "git push --force should be blocked"
    hook_event: PreToolUse
    hook_matcher: Bash
    event_json:
      tool_name: Bash
      tool_input:
        command: "git push origin main --force"
    expect: blocked
    tags: [destructive, git]
```
