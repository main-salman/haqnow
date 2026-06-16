# 🔄 AI-DLC Workflow Integration

> **Status**: Active
> **Last Updated**: 2026-06-16
> **Framework**: [awslabs/aidlc-workflows](https://github.com/awslabs/aidlc-workflows)

## Overview

HaqNow integrates the **AI-Driven Life Cycle (AI-DLC)** adaptive workflow steering rules to guide AI-assisted development. AI-DLC is an intelligent software development workflow that adapts to project needs, maintains quality standards, and keeps the developer in control.

## What is AI-DLC?

AI-DLC provides a three-phase adaptive workflow:

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  INCEPTION   │────►│ CONSTRUCTION  │────►│  OPERATIONS  │
│              │     │               │     │              │
│ • Workspace  │     │ • Functional  │     │ • Deploy     │
│   Detection  │     │   Design      │     │ • Monitor    │
│ • Reverse    │     │ • Code Gen    │     │ • Maintain   │
│   Engineering│     │ • Build/Test  │     │              │
│ • Reqs       │     │ • NFR Design  │     │              │
│ • User Story │     │ • Infra       │     │              │
│ • Workflow   │     │               │     │              │
│ • App Design │     │               │     │              │
│ • Units Gen  │     │               │     │              │
└─────────────┘     └──────────────┘     └─────────────┘
```

### Key Principles
- **Adaptive**: The workflow adapts to the work, not the other way around
- **Phase-gated**: Each phase has mandatory checkpoints and user approval
- **Extension-driven**: Pluggable extensions add domain-specific constraints
- **Auditable**: All decisions logged in `aidlc-docs/audit.md`

## Project Configuration

### File Structure

```
fadih/
├── .cursor/rules/
│   └── ai-dlc-workflow.mdc          # Core AIDLC workflow (Cursor format)
├── .aidlc-rule-details/             # Detailed rule files
│   ├── common/                      # Cross-cutting rules
│   │   ├── process-overview.md
│   │   ├── session-continuity.md
│   │   ├── content-validation.md
│   │   ├── question-format-guide.md
│   │   ├── welcome-message.md
│   │   ├── ascii-diagram-standards.md
│   │   ├── depth-levels.md
│   │   ├── error-handling.md
│   │   ├── overconfidence-prevention.md
│   │   ├── terminology.md
│   │   └── workflow-changes.md
│   ├── inception/                   # Inception phase rules
│   │   ├── workspace-detection.md
│   │   ├── reverse-engineering.md
│   │   ├── requirements-analysis.md
│   │   ├── user-stories.md
│   │   ├── workflow-planning.md
│   │   ├── application-design.md
│   │   └── units-generation.md
│   ├── construction/                # Construction phase rules
│   │   ├── functional-design.md
│   │   ├── code-generation.md
│   │   ├── build-and-test.md
│   │   ├── infrastructure-design.md
│   │   ├── nfr-design.md
│   │   └── nfr-requirements.md
│   ├── operations/                  # Operations phase rules
│   │   └── operations.md
│   └── extensions/                  # Pluggable extensions
│       ├── testing/
│       │   ├── tdd/                 # 🆕 Test-Driven Development
│       │   │   ├── test-driven-development.opt-in.md
│       │   │   └── test-driven-development.md
│       │   └── property-based/      # Property-Based Testing
│       │       ├── property-based-testing.opt-in.md
│       │       └── property-based-testing.md
│       ├── sdd/                     # 🆕 Spec-Driven Development
│       │   ├── spec-driven-development.opt-in.md
│       │   └── spec-driven-development.md
│       ├── security/
│       │   └── baseline/
│       │       ├── security-baseline.opt-in.md
│       │       └── security-baseline.md
│       └── resiliency/
│           └── baseline/
│               ├── resiliency-baseline.opt-in.md
│               └── resiliency-baseline.md
├── specs/                           # Project specifications (SDD)
│   ├── SPEC-001-document-lifecycle.md
│   ├── SPEC-002-ai-features.md
│   ├── SPEC-003-infrastructure.md
│   ├── SPEC-004-upload-pipeline.md
│   └── TRACEABILITY.md             # 🆕 Spec-to-implementation matrix
└── aidlc-docs/                      # AIDLC runtime artifacts
    └── (created during workflow execution)
```

## Custom Extensions

### 🧪 Test-Driven Development (TDD) Extension

**Path**: `.aidlc-rule-details/extensions/testing/tdd/`

Enforces the Red-Green-Refactor cycle across all AI-DLC Construction phases:

| Rule | Description | Enforcement |
|------|-------------|-------------|
| TDD-01 | Test-First Development Cycle | Always blocking |
| TDD-02 | Test Coverage Requirements (80% line, 70% branch) | Always blocking |
| TDD-03 | Test Categories and Structure | Always blocking |
| TDD-04 | Test Naming and Documentation | Partial: advisory |
| TDD-05 | Regression Test Mandate | Always blocking |
| TDD-06 | API Contract Testing | Partial: advisory |
| TDD-07 | Test Data Management | Partial: advisory |
| TDD-08 | Continuous Integration Gate | Partial: advisory |

**HaqNow-Specific TDD Rules**:
- `TDD-P1`: No IP Logging Test — verify no IP in logs after requests
- `TDD-P2`: Metadata Stripping Test — verify EXIF removal
- `TDD-P3`: Anonymous Access Test — verify public endpoints work without auth
- `TDD-P4`: Rate Limit Test — verify anonymous rate limiting

### 📋 Spec-Driven Development (SDD) Extension

**Path**: `.aidlc-rule-details/extensions/sdd/`

Ensures all implementation traces back to formal specifications:

| Rule | Description | Enforcement |
|------|-------------|-------------|
| SDD-01 | Spec-First Requirement | Always blocking |
| SDD-02 | Specification Format Standard | Always blocking |
| SDD-03 | Traceability Matrix | Partial: advisory |
| SDD-04 | Spec-Implementation Drift Detection | Always blocking |
| SDD-05 | Infrastructure Spec Compliance | Partial: advisory |
| SDD-06 | Spec Review Gate | Always blocking |
| SDD-07 | Spec Versioning and Changelog | Partial: advisory |
| SDD-08 | Living Specification Maintenance | Partial: advisory |

## How to Use

### For New Features

1. **Inception**: AI-DLC automatically detects brownfield workspace and loads existing specs
2. **Requirements**: Answer opt-in prompts for TDD, SDD, and other extensions
3. **Construction**: Extensions enforce rules at each stage gate
4. **Operations**: Deploy via `scripts/deploy.sh` per project rules

### For Bug Fixes

1. Write a failing test reproducing the bug (TDD-05)
2. Verify the fix makes the test pass
3. Update specs if the bug reveals a spec gap (SDD-04)
4. Update traceability matrix (SDD-03)

### Creating New Specs

```bash
# Copy the spec template
cp specs/SPEC-001-document-lifecycle.md specs/SPEC-005-new-feature.md
# Edit the new spec following SDD-02 format standard
# Get approval before implementing (SDD-06)
```

## Compatibility

The AIDLC workflow rules are compatible with:
- ✅ Cursor IDE (via `.cursor/rules/ai-dlc-workflow.mdc`)
- ✅ Any AI coding assistant that reads `.aidlc-rule-details/`
- ✅ Amazon Q Developer (can add `.amazonq/rules/` mapping)
- ✅ Claude Code (can add `.claude/` mapping)
- ✅ GitHub Copilot (reads AGENTS.md)

## Version

- **AI-DLC Rules Version**: Based on awslabs/aidlc-workflows latest (June 2026)
- **Custom Extensions**: TDD v1.0, SDD v1.0
