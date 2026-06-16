# Test-Driven Development (TDD) — Opt-In

**Extension**: Test-Driven Development

## Opt-In Prompt

The following question is automatically included in the Requirements Analysis clarifying questions when this extension is loaded:

```markdown
## Question: Test-Driven Development Extension
Should Test-Driven Development (TDD) rules be enforced for this project?

A) Yes — enforce all TDD rules as blocking constraints (recommended for backend services, APIs, data processing pipelines, and business logic)
B) Partial — enforce core TDD rules (TDD-01, TDD-02, TDD-03, TDD-05) but treat others as advisory
C) No — do not enforce TDD rules

[Answer]:
```

## When User Selects A (Yes)

Load the full TDD rules from `test-driven-development.md` in this directory. All rules are blocking.

## When User Selects B (Partial)

Load the full TDD rules from `test-driven-development.md` in this directory. Only rules TDD-01, TDD-02, TDD-03, and TDD-05 are blocking; others are advisory.

## When User Selects C (No)

Do not load the full TDD rules file. TDD extension is disabled.
