---
name: review-loop
description: Multi-agent architect for self code review and implementation feedback loop. Use when implementing multi-step features with quality gates. Orchestrator delegates to subagents via `task` tool. Loop: Plan -> Implement -> Spec Review -> Code Quality Review -> Feedback -> Iterate -> Test.
---

# Review Loop — Multi-Agent Architect

Four agent roles. One feedback loop. Zero quality debt.

## Roles

| Role | Who | Responsibility |
|------|-----|----------------|
| **Orchestrator** | You (main agent) | Decompose work, delegate tasks, route feedback, update AGENTS.md + task.md |
| **Implementer** | `task` subagent (general) | Write code for one task at a time. Run self-review before reporting back. |
| **Reviewer** | `task` subagent (general) | Two-stage: (1) spec compliance, (2) code quality. Returns categorized issues. |
| **Tester** | `task` subagent (explore/general) | Run test commands, parse results, report pass/fail per test case. |

## The Loop

```
Orchestrator: Plan -> Decompose into tasks -> [FOR each task: Implement -> Review -> Feedback -> Fix -> Test] -> Merge -> Update memory
```

## Workflow Detail

### Phase 1: Plan & Decompose
1. Load project context from `.opencode/AGENTS.md`
2. Define tasks with clear acceptance criteria
3. Write plan to `docs/plans/<feature>-plan.md`
4. Update `docs/plans/task.md` tracker

### Phase 2: Implement (per task)
```
Orchestrator -> task(Implementer prompt) -> subagent implements -> returns report
```

**Implementer Prompt Template:**
```
You are the Implementer in a multi-agent architect system.

## Task: <number>: <title>

## Requirements
<paste task spec from plan>

## Constraints
- Follow existing code patterns in this project
- Read `.opencode/AGENTS.md` for project context
- Don't overbuild — implement exactly what's requested
- Write or update tests

## Before You Begin
Ask questions if anything is unclear.

## Self-Review (before reporting back)
1. Did I implement everything in the spec?
2. Did I avoid adding unrequested features?
3. Are there edge cases I missed?
4. Did I write/update tests?
5. Are names consistent with existing codebase conventions?

## Report Format
- What was implemented
- Files changed (with paths)
- Test results or verification evidence
- Self-review findings (if any)
- Any concerns or open questions
```

### Phase 3: Review (two-stage per task)
```
Orchestrator -> task(Spec Reviewer prompt) -> returns issues
              -> task(Code Quality Reviewer prompt) -> returns issues
```

**Spec Reviewer Prompt Template:**
```
You are the Spec Compliance Reviewer. The Implementer claims they built what was requested.
You must verify by reading the actual code, NOT by trusting the report.

## Requirements (from plan)
<paste task requirements>

## Implementer's Report
<paste implementer's report>

## Your Job
1. Read the actual code files
2. Compare implementation against requirements line by line
3. Check for: missing requirements, extra unrequested features, misunderstandings

## Output
- ✅ Spec compliant (with evidence from code inspection)
- ❌ Issues found (file:line references, what's wrong, what's expected)
```

**Code Quality Reviewer Prompt Template:**
```
You are the Code Quality Reviewer. Review implementation code for production readiness.

## What Was Implemented
<paste implementer's report>

## Review Checklist
- Clean separation of concerns?
- Error handling?
- Follows existing codebase patterns?
- Edge cases handled?
- Security considerations?
- Performance implications?
- Test quality (tests verify behavior, not mocks)?

## Output Format

### Strengths
[Specific things done well, with file:line]

### Issues
#### Critical (Must Fix)
[Bugs, security, data loss, broken functionality]
#### Important (Should Fix)
[Architecture problems, missing error handling, test gaps]
#### Minor (Nice to Have)
[Style, naming, optimization]

For each issue: file:line, what's wrong, why it matters, how to fix

### Assessment
**Ready to proceed?** [Yes/No/With fixes]
```

### Phase 4: Feedback & Fix
- Review issues collected → prioritize by severity
- Critical/Important issues → create fix task → loop back to Phase 2
- No Critical issues → proceed

### Phase 5: Test
```
Orchestrator -> task(Tester prompt) -> subagent runs tests -> returns results
```

**Tester Prompt Template:**
```
You are the Tester. Run the specified tests and report results.

## Test commands
<list of test commands>

## For each command, report:
- Command run
- Exit code
- Pass/fail counts
- Any error output or failures
- Overall verdict: ALL PASS / HAS FAILURES
```

### Phase 6: Merge & Memory
1. Update `.opencode/AGENTS.md` with decisions, context, file changes
2. Mark task complete in `docs/plans/task.md`
3. Proceed to next task

## Quality Gates
- **Gate 1 (per task)**: Spec review must pass (no missing/extra features)
- **Gate 2 (per task)**: Code quality review must have no Critical issues
- **Gate 3 (per feature)**: All tests pass
- **Gate 4 (per feature)**: Orchestrator reviews diff for consistency

## When to Use
- Multi-step features (3+ tasks) that need quality assurance
- Auth portal, payroll, pipeline — any complex feature
- Refactoring that touches many files

## When NOT to Use
- Single file change (just implement directly)
- Bug fix with clear root cause (use systematic-debugging)
- Exploration or research (use brainstorm first)

## Integration
- Project context: `.opencode/AGENTS.md`
- Task tracker: `docs/plans/task.md`
- Feature plans: `docs/plans/<feature>-plan.md`
- Test commands: `python -X utf8 src/test_*.py`
