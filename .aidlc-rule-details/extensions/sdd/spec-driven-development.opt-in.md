# Spec-Driven Development (SDD) — Opt-In

**Extension**: Spec-Driven Development

## Opt-In Prompt

The following question is automatically included in the Requirements Analysis clarifying questions when this extension is loaded:

```markdown
## Question: Spec-Driven Development Extension
Should Spec-Driven Development (SDD) rules be enforced for this project?

A) Yes — enforce all SDD rules as blocking constraints (recommended for projects with formal specifications, API contracts, or architectural documentation)
B) Partial — enforce core SDD rules (SDD-01, SDD-02, SDD-04, SDD-06) but treat others as advisory
C) No — do not enforce SDD rules

[Answer]:
```

## When User Selects A (Yes)

Load the full SDD rules from `spec-driven-development.md` in this directory. All rules are blocking.

## When User Selects B (Partial)

Load the full SDD rules from `spec-driven-development.md` in this directory. Only rules SDD-01, SDD-02, SDD-04, and SDD-06 are blocking; others are advisory.

## When User Selects C (No)

Do not load the full SDD rules file. SDD extension is disabled.
