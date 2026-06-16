# Test-Driven Development (TDD) Rules

## Overview

These Test-Driven Development (TDD) rules are cross-cutting constraints that apply across applicable AI-DLC phases. They enforce the Red-Green-Refactor cycle to ensure that code is written to satisfy well-defined tests, improving quality, reducing regressions, and maintaining a living specification of expected behavior.

TDD mandates that tests are written BEFORE implementation code. The cycle is:
1. **RED** — Write a failing test that defines expected behavior
2. **GREEN** — Write the minimum implementation code to make the test pass
3. **REFACTOR** — Clean up code while keeping tests green

**Enforcement**: At each applicable stage, the model MUST verify compliance with these rules before presenting the stage completion message to the user.

### Blocking TDD Finding Behavior

A **blocking TDD finding** means:
1. The finding MUST be listed in the stage completion message under a "TDD Findings" section with the TDD rule ID and description
2. The stage MUST NOT present the "Continue to Next Stage" option until all blocking findings are resolved
3. The model MUST present only the "Request Changes" option with a clear explanation of what needs to change
4. The finding MUST be logged in `aidlc-docs/audit.md` with the TDD rule ID, description, and stage context

If a TDD rule is not applicable to the current project or unit (e.g., TDD-06 when no API endpoints exist), mark it as **N/A** in the compliance summary — this is not a blocking finding.

### Default Enforcement

All rules in this document are **blocking** by default. If any rule's verification criteria are not met, it is a blocking TDD finding — follow the blocking finding behavior defined above.

### Partial Enforcement Mode

If the user selected **Partial** enforcement during opt-in, only rules TDD-01, TDD-02, TDD-03, and TDD-05 are enforced. All other rules are treated as advisory (non-blocking). Log the enforcement mode in `aidlc-docs/aidlc-state.md` under `## Extension Configuration`.

### Verification Criteria Format

Verification items in this document are plain bullet points describing compliance checks. Each item should be evaluated as compliant or non-compliant during review.

---

## Rule TDD-01: Test-First Development Cycle

**Rule**: Every new function, method, endpoint, or component MUST be developed using the Red-Green-Refactor cycle. This means:

1. **Write failing test(s)** that define the expected behavior before writing implementation code
2. **Verify the test fails** (RED phase) — confirming the test actually tests something
3. **Write minimum implementation** to make the test pass (GREEN phase)
4. **Refactor** while keeping all tests passing (REFACTOR phase)

The test MUST be committed or presented before or alongside the implementation code, never after.

**Applies to AI-DLC Phases**:
- **Construction > Code Generation**: All new code units must follow TDD cycle
- **Construction > Build and Test**: Verify TDD compliance in test results

**Verification**:
- Every new function/method has at least one corresponding test
- Tests are written/presented before or alongside implementation code
- Test files follow project naming conventions (e.g., `test_*.py`, `*.test.ts`)
- No implementation code exists without a corresponding test

---

## Rule TDD-02: Test Coverage Requirements

**Rule**: All code units produced during the Construction phase MUST meet minimum test coverage thresholds:

| Coverage Type | Minimum Threshold | Description |
|---|---|---|
| Line coverage | 80% | Lines of code executed by tests |
| Branch coverage | 70% | Decision branches (if/else, switch) exercised |
| Function coverage | 90% | Functions/methods called by tests |
| Critical path coverage | 100% | Error handling, security checks, data validation |

**Critical paths** include:
- Authentication and authorization logic
- Input validation and sanitization
- Error handling and exception management
- Data persistence operations (CRUD)
- External service integrations (API calls, message queues)
- Privacy-sensitive operations (per HaqNow CONSTITUTION.md Article IV)

**Verification**:
- Coverage reports are generated and attached to build artifacts
- Coverage thresholds are met for all new code
- Critical paths have explicit test cases covering success and failure scenarios
- Coverage gaps are documented with justification if below threshold

---

## Rule TDD-03: Test Categories and Structure

**Rule**: Tests MUST be organized into the following categories, with each category serving a distinct purpose:

| Category | Scope | Speed | Dependencies | When to Write |
|---|---|---|---|---|
| **Unit Tests** | Single function/class | < 100ms each | None (mocked) | Every code change |
| **Integration Tests** | Component interactions | < 5s each | Limited (test DB, test API) | Feature completion |
| **API/Contract Tests** | Endpoint behavior | < 2s each | Test server | Every endpoint change |
| **End-to-End Tests** | User workflows | < 30s each | Full stack | Critical path changes |

### Directory Structure Convention:
```
backend/
  tests/
    unit/           # Fast, isolated unit tests
    integration/    # Component interaction tests
    api/            # API endpoint contract tests
    e2e/            # End-to-end workflow tests
    conftest.py     # Shared fixtures and test configuration
    
frontend/
  src/
    __tests__/      # Component tests co-located or centralized
    e2e/            # End-to-end browser tests
```

**Verification**:
- Tests are organized by category in appropriate directories
- Unit tests have no external dependencies (all mocked/stubbed)
- Integration tests use test doubles for external services
- Each test file clearly indicates its category via location or naming

---

## Rule TDD-04: Test Naming and Documentation

**Rule**: Every test MUST have a clear, descriptive name that communicates:
1. **What** is being tested (the unit/function)
2. **Under what conditions** (the scenario/input)
3. **What is expected** (the outcome)

### Naming Pattern:
```python
# Python: test_<what>_<condition>_<expected>
def test_upload_document_valid_pdf_returns_success():
def test_upload_document_oversized_file_returns_413():
def test_approve_document_unauthenticated_returns_401():

# Or Given-When-Then style:
def test_given_valid_pdf_when_upload_then_status_pending():
```

```typescript
// TypeScript: describe/it pattern
describe('DocumentUpload', () => {
  it('should return success for valid PDF files', () => {});
  it('should return 413 for files exceeding 100MB', () => {});
  it('should strip EXIF metadata before storage', () => {});
});
```

**Verification**:
- Test names follow the project's naming convention
- Test names describe the scenario without reading the test body
- No generic test names (e.g., `test_1`, `test_it_works`, `test_basic`)
- Each test has a single clear assertion focus (one logical assertion per test)

---

## Rule TDD-05: Regression Test Mandate

**Rule**: Every bug fix MUST include a regression test that:
1. **Reproduces** the original bug (test fails without the fix)
2. **Verifies** the fix resolves the issue (test passes with the fix)
3. **Is tagged** with the issue reference (e.g., `@pytest.mark.regression("BUG-123")`)

Bug fixes without regression tests are blocking findings.

**Verification**:
- Every bug fix commit includes at least one new test
- The regression test fails when the fix is reverted
- The regression test is clearly tagged/labeled as a regression test
- The regression test references the original issue or bug report

---

## Rule TDD-06: API Contract Testing

**Rule**: Every API endpoint MUST have contract tests that verify:

| Aspect | What to Test | Example |
|---|---|---|
| **Request validation** | Required fields, types, constraints | Missing `title` returns 422 |
| **Response schema** | Status codes, body structure, types | Success returns `{id, status, created_at}` |
| **Authentication** | Auth required/optional, role checks | Unauthenticated returns 401 |
| **Error responses** | Error format, appropriate status codes | Invalid ID returns 404 with message |
| **Edge cases** | Boundary values, empty inputs, special chars | Unicode filenames handled correctly |

**Specific to HaqNow**:
- Upload endpoints must test virus scanning integration (mocked)
- Document endpoints must test metadata stripping
- Admin endpoints must test JWT validation
- All endpoints must verify no IP address is logged

**Verification**:
- Every API endpoint has contract tests for success and error scenarios
- Request validation tests cover all required fields
- Response schema tests verify structure and types
- Authentication tests cover all auth scenarios (no auth, invalid, valid)
- Privacy-critical endpoints have explicit no-IP-logging assertions

---

## Rule TDD-07: Test Data Management

**Rule**: Tests MUST use controlled, repeatable test data following these principles:

1. **Fixtures over inline data** — Reusable test data defined in fixtures/factories
2. **Isolation** — Each test creates its own data; no shared mutable state
3. **Cleanup** — Test data is cleaned up after each test (database, file system)
4. **No production data** — Never use real user data or credentials in tests
5. **Deterministic** — Tests produce the same results on every run

### HaqNow-Specific:
- Test documents must be synthetic (not real corruption documents)
- Test embeddings can use fixed vectors for deterministic comparison
- Database tests must use transactions with rollback (not actual inserts)
- S3 operations in tests must use mocked/stubbed storage

**Verification**:
- Test fixtures or factories exist for common data patterns
- No tests rely on shared mutable state or execution order
- Database tests use transactions with rollback or in-memory databases
- No real credentials, tokens, or production data in test files

---

## Rule TDD-08: Continuous Integration Gate

**Rule**: The test suite MUST be executable in CI and serve as a deployment gate:

1. **All tests must pass** before code can be merged or deployed
2. **Test execution time** must be within acceptable limits (unit < 5min, integration < 15min)
3. **Flaky tests** (tests that intermittently fail) must be quarantined and fixed within one sprint
4. **New code** must not decrease overall test coverage

**Verification**:
- Test suite runs successfully in CI environment
- No test failures are acceptable for deployment
- Flaky tests are identified and tracked for resolution
- Coverage reports are generated and compared against thresholds

---

## HaqNow-Specific TDD Addendum

### Privacy-First Testing Rules

Given HaqNow's CONSTITUTION.md mandates (Article IV), the following additional TDD rules apply:

1. **TDD-P1: No IP Logging Test** — Every new endpoint MUST include a test asserting that no IP address appears in logs after the request
2. **TDD-P2: Metadata Stripping Test** — Any file processing code MUST include tests verifying all EXIF/metadata is removed
3. **TDD-P3: Anonymous Access Test** — Public-facing endpoints MUST be tested to confirm they work without user identification
4. **TDD-P4: Rate Limit Test** — Rate-limited endpoints MUST include tests for the rate limiting behavior using the anonymous time-bucket system

### Spec Alignment

Tests SHOULD reference the relevant specification from the `specs/` directory:
- `SPEC-001-document-lifecycle.md` — Document processing invariants
- `SPEC-002-ai-features.md` — AI/RAG behavior expectations
- `SPEC-003-infrastructure.md` — Infrastructure requirements
- `SPEC-004-upload-pipeline.md` — Upload pipeline behavior
