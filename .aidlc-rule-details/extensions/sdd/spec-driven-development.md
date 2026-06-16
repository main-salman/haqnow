# Spec-Driven Development (SDD) Rules

## Overview

These Spec-Driven Development (SDD) rules are cross-cutting constraints that apply across applicable AI-DLC phases. They ensure that all implementation decisions trace back to formal specifications, architectural documents, and requirements artifacts, maintaining alignment between what is specified and what is built.

Spec-Driven Development treats specifications as the single source of truth for system behavior. Every feature, API endpoint, data model, and workflow MUST be traceable to a specification before implementation begins. Deviations from specs require explicit approval and spec updates.

**Enforcement**: At each applicable stage, the model MUST verify compliance with these rules before presenting the stage completion message to the user.

### Blocking SDD Finding Behavior

A **blocking SDD finding** means:
1. The finding MUST be listed in the stage completion message under a "SDD Findings" section with the SDD rule ID and description
2. The stage MUST NOT present the "Continue to Next Stage" option until all blocking findings are resolved
3. The model MUST present only the "Request Changes" option with a clear explanation of what needs to change
4. The finding MUST be logged in `aidlc-docs/audit.md` with the SDD rule ID, description, and stage context

If an SDD rule is not applicable to the current project or unit (e.g., SDD-05 when no infrastructure specs exist), mark it as **N/A** in the compliance summary — this is not a blocking finding.

### Default Enforcement

All rules in this document are **blocking** by default. If any rule's verification criteria are not met, it is a blocking SDD finding — follow the blocking finding behavior defined above.

### Partial Enforcement Mode

If the user selected **Partial** enforcement during opt-in, only rules SDD-01, SDD-02, SDD-04, and SDD-06 are enforced. All other rules are treated as advisory (non-blocking). Log the enforcement mode in `aidlc-docs/aidlc-state.md` under `## Extension Configuration`.

### Verification Criteria Format

Verification items in this document are plain bullet points describing compliance checks. Each item should be evaluated as compliant or non-compliant during review.

---

## Rule SDD-01: Spec-First Requirement

**Rule**: Every new feature, endpoint, data model change, or workflow modification MUST have a corresponding specification BEFORE implementation begins. The specification MUST exist in one of the following:

| Spec Location | Format | Example |
|---|---|---|
| `specs/` directory | `SPEC-NNN-<name>.md` | `SPEC-005-admin-workflow.md` |
| `documentation/ARCHITECTURE.md` | Architecture section | Infrastructure topology changes |
| `CONSTITUTION.md` | Governance section | Privacy/security policy changes |
| `AGENTS.md` | Agent behavior section | AI agent workflow changes |
| API contract files | OpenAPI/Swagger/Pydantic | Endpoint schema definitions |

If no specification exists for a requested feature, the AI agent MUST:
1. **Halt implementation** and notify the user
2. **Draft a specification** following the existing spec format (see `specs/` directory for examples)
3. **Present the spec for approval** before proceeding with implementation
4. **Create the spec file** in the `specs/` directory with the next available SPEC number

**Verification**:
- Every implementation change maps to a specification document
- New features have a corresponding `SPEC-NNN-*.md` file
- Specification exists before code is written
- Implementation matches the spec (not the other way around)

---

## Rule SDD-02: Specification Format Standard

**Rule**: All specifications MUST follow a consistent format to ensure clarity and traceability:

```markdown
# SPEC-NNN: <Feature Name>

> **Status**: Draft | Active | Deprecated
> **Last Updated**: YYYY-MM-DD
> **Owner**: <Team/Individual>
> **Traces To**: <Parent spec or requirement>

## Overview
Brief description of what this specification covers.

## Requirements
### Functional Requirements
- FR-1: <Requirement with measurable acceptance criteria>
- FR-2: ...

### Non-Functional Requirements
- NFR-1: <Performance, security, privacy requirement>
- NFR-2: ...

## Data Model
Schema definitions, field descriptions, constraints.

## API Contract
Endpoints, request/response schemas, status codes.

## State Machine / Workflow
State transitions, lifecycle stages.

## Invariants
Properties that must ALWAYS hold true.

## Dependencies
Other specs, services, or components this depends on.

## Acceptance Criteria
Concrete, testable criteria for considering this spec satisfied.
```

**Verification**:
- All spec files follow the standard format
- Every spec has Status, Last Updated, and Owner fields
- Requirements are numbered and have acceptance criteria
- Invariants are explicitly stated and testable
- Dependencies are cross-referenced

---

## Rule SDD-03: Traceability Matrix

**Rule**: A traceability matrix MUST be maintained that maps:

```
Specification → Design Decision → Implementation → Test
```

The traceability matrix ensures that:
1. Every requirement in a spec has a corresponding implementation
2. Every implementation traces back to a spec requirement
3. Every test validates a specific spec requirement
4. No "orphan" implementations exist (code without a spec justification)

### Traceability File: `specs/TRACEABILITY.md`

```markdown
# Traceability Matrix

| Spec | Requirement | Implementation File | Test File | Status |
|------|-------------|--------------------|-----------| -------|
| SPEC-001 | FR-1: Upload validation | backend/app/apis/file_uploader.py | tests/api/test_upload.py | ✅ |
| SPEC-001 | FR-2: Virus scanning | backend/app/services/virus_scan.py | tests/unit/test_virus_scan.py | ✅ |
| SPEC-001 | INV-1: Job queue invariant | backend/worker.py | tests/integration/test_worker.py | ⚠️ |
```

**Verification**:
- Traceability matrix exists and is up to date
- Every spec requirement has at least one implementation entry
- Every implementation entry has at least one test entry
- Orphan implementations (no spec reference) are flagged

---

## Rule SDD-04: Spec-Implementation Drift Detection

**Rule**: Before any stage completion in the Construction phase, the model MUST check for drift between specifications and implementation:

### Drift Categories:

| Category | Severity | Description | Action |
|---|---|---|---|
| **Missing implementation** | Blocking | Spec requirement not implemented | Implement or update spec |
| **Extra implementation** | Warning | Code exists without spec backing | Create spec or remove code |
| **Behavior mismatch** | Blocking | Implementation differs from spec | Fix implementation or update spec |
| **Schema mismatch** | Blocking | Data model differs from spec | Reconcile and update both |
| **State machine violation** | Critical | State transitions violate spec | Fix immediately |

### Drift Detection Process:
1. Parse spec requirements and invariants
2. Analyze implementation code for spec compliance
3. Compare API contracts (endpoints, schemas, status codes)
4. Verify state machine transitions match spec
5. Report findings with severity classification

**Verification**:
- No blocking or critical drift exists at stage completion
- Warning-level drift is documented with planned resolution
- Spec files are updated when legitimate implementation changes diverge
- Drift check results are logged in `aidlc-docs/audit.md`

---

## Rule SDD-05: Infrastructure Spec Compliance

**Rule**: Infrastructure changes MUST comply with infrastructure specifications:

| Spec Source | Covers | Example Check |
|---|---|---|
| `SPEC-003-infrastructure.md` | K8s manifests, resource limits | Pod memory limits match spec |
| `documentation/ARCHITECTURE.md` | Service topology, networking | Service mesh matches architecture |
| `CONSTITUTION.md` Section 6 | Technology decisions, guardrails | Only approved technologies used |
| `k8s/manifests/` | Deployment configurations | Replica counts match requirements |

**HaqNow-Specific**:
- Kubernetes manifests must match `SPEC-003-infrastructure.md` resource allocations
- Network policies must match architecture topology
- Environment variables must be documented in `.env.example`
- All infrastructure must be provisioned via Terraform or K8s manifests (no manual setup)

**Verification**:
- Infrastructure changes trace to an infrastructure specification
- Resource limits match spec-defined thresholds
- Service topology matches architecture documentation
- No manual infrastructure changes (everything is code-defined)

---

## Rule SDD-06: Spec Review Gate

**Rule**: Specifications MUST be reviewed and approved before implementation proceeds:

### Review Criteria:
1. **Completeness** — All sections of the spec format are filled
2. **Clarity** — Requirements are unambiguous and testable
3. **Consistency** — No contradictions with existing specs
4. **Privacy compliance** — Spec passes HaqNow Privacy Test (CONSTITUTION.md Article III, Section 3.1)
5. **Security review** — Spec reviewed for security implications
6. **Feasibility** — Implementation is technically feasible within constraints

### Approval Flow:
```
Spec Draft → Self-Review → Peer Review → Approval → Implementation
```

For AI-DLC:
- The model presents the spec to the user during Inception Phase
- User must explicitly approve the spec before Construction begins
- Any spec changes during Construction require re-approval

**Verification**:
- Every spec has an explicit approval record (in audit.md or spec file)
- Spec changes during Construction trigger re-approval
- No implementation proceeds on a "Draft" status spec

---

## Rule SDD-07: Spec Versioning and Changelog

**Rule**: Specifications MUST be versioned and maintain a changelog:

1. **Version number** in the spec header (semantic: major.minor)
2. **Changelog section** at the bottom of each spec file
3. **Breaking changes** (major version bump) require downstream impact analysis
4. **Non-breaking additions** (minor version bump) require notification to implementers

### Changelog Format:
```markdown
## Changelog

| Version | Date | Change | Impact |
|---------|------|--------|--------|
| 1.0 | 2026-06-04 | Initial specification | N/A |
| 1.1 | 2026-06-10 | Added rate limiting to upload | Backend change required |
| 2.0 | 2026-06-15 | Changed auth model | Breaking: all API clients |
```

**Verification**:
- Every spec has a version number
- Every spec has a changelog section
- Breaking changes are flagged with impact analysis
- Downstream specs and implementations are updated for breaking changes

---

## Rule SDD-08: Living Specification Maintenance

**Rule**: Specifications are living documents that MUST be kept in sync with the codebase:

1. **Post-implementation sync** — After Construction phase, verify specs match what was built
2. **Deprecation marking** — Specs for removed features are marked as `Deprecated`
3. **Periodic review** — Specs should be reviewed quarterly for accuracy
4. **Cross-reference integrity** — All spec cross-references must resolve to existing specs

**Verification**:
- No active specs describe features that no longer exist
- No deprecated specs are referenced by active specs
- Spec cross-references are valid (no broken links)
- Recent implementation changes are reflected in specs

---

## HaqNow-Specific SDD Addendum

### Existing Specifications

The following specifications are already established in the `specs/` directory and MUST be treated as the source of truth:

| Spec | Covers | Critical Invariants |
|------|--------|-------------------|
| `SPEC-001-document-lifecycle.md` | Upload → Processing → Live pipeline | Job queue invariants, state transitions |
| `SPEC-002-ai-features.md` | RAG, embeddings, AI Q&A | Embedding dimensions, chunk sizes |
| `SPEC-003-infrastructure.md` | K8s, DBaaS, S3, networking | Resource limits, namespace separation |
| `SPEC-004-upload-pipeline.md` | File validation, virus scanning, metadata stripping | Size limits, supported formats |

### Governance Documents as Specs

The following project governance documents have spec-level authority:

- **CONSTITUTION.md** — Privacy mandates (Article IV), AI ethics (Article V), architecture guardrails (Article VI)
- **AGENTS.md** — Agent behavior rules, escalation matrix
- **CURSOR_CONTEXT.md** — Deployment rules, environment configuration

### Privacy Spec Compliance

Every new specification MUST include a "Privacy Compliance" section that addresses:
1. Does this feature process any user-identifiable data? → Document mitigation
2. Does this feature introduce new logging? → Verify no IP/PII logging
3. Does this feature interact with external services? → Verify data minimization
4. Does this feature change authentication/authorization? → Security review required
