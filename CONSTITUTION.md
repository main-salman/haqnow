# 📜 HaqNow Project Constitution

**The governing document for the HaqNow platform** — mission, values, principles, guardrails, and ethics that guide every decision.

> *This is a living document. Amendments require explicit team consensus and must be recorded in the changelog below.*

---

## 🌍 Article I — Mission & Purpose

### Section 1.1 — Mission Statement
HaqNow ("Haq" = truth/right in Arabic) exists to **expose corruption through technology, transparency, and global collaboration** while protecting the identity and safety of those who contribute.

### Section 1.2 — Core Purpose
1. Provide a **privacy-first platform** for anonymous corruption document exposure
2. Enable **global accessibility** through 60+ language support
3. Use **ethical AI** to make corruption documents discoverable and searchable
4. Maintain **complete anonymity** for all users — uploaders, viewers, and searchers

### Section 1.3 — Target Users
- Whistleblowers exposing corruption evidence
- Journalists investigating corruption
- Citizens seeking transparency in government and institutions
- Researchers studying corruption patterns globally

---

## ⚖️ Article II — Core Values

### 2.1 — Truth (Haq)
Every feature, design decision, and architectural choice must serve the goal of making truth accessible. We do not censor, filter, or suppress legitimate corruption evidence.

### 2.2 — Privacy Above All
User privacy is **non-negotiable**. We will sacrifice features, performance, and convenience before compromising user anonymity. No system is 100% guaranteed, but we strive for the strongest possible protections.

### 2.3 — Global Accessibility
The platform must be usable by anyone, anywhere, in any language. We actively support 60+ languages with automatic translation to English for global reach.

### 2.4 — Ethical Technology
We commit to using ethical, privacy-respecting technology. Our AI stack (Thaura.AI, local embeddings) is chosen for ethical alignment, not just performance.

### 2.5 — Open Source Transparency
The codebase is open source (MIT License) to enable security auditing and build trust with users who risk their safety to expose corruption.

---

## 🏛️ Article III — Development Principles

### 3.1 — Privacy-First Architecture
```
Every new feature MUST pass the Privacy Test:
  1. Does it log IP addresses?                    → REJECT
  2. Does it track or identify users?             → REJECT
  3. Does it send data to untrusted externals?    → REJECT
  4. Does it store identifying metadata?          → REJECT
  5. Does it require user accounts for access?    → REJECT (for public features)
```

### 3.2 — Single Deployment Method
All deployments go through `scripts/deploy.sh`. No exceptions. No manual server edits. No ad-hoc kubectl commands for deployment.

```bash
# The ONLY way to deploy
./scripts/deploy.sh --env=dev patch    # Development
./scripts/deploy.sh --env=prod patch   # Production
```

### 3.3 — Secrets Management
- All secrets live in `.env` (root level, gitignored)
- Never hardcode credentials in source code
- `deploy.sh` syncs `.env` to Kubernetes secrets automatically
- Never edit `.env` on the server directly

### 3.4 — Zero-Tolerance for Hardcoded Secrets
- Any PR or commit containing hardcoded API keys, database credentials, or private tokens will be REJECTED and the secret considered compromised.
- Use `os.getenv()` with NO hardcoded fallback for all sensitive configurations.
- Use pre-commit hooks or GitGuardian-like scanning to catch leaks before they are pushed.

### 3.5 — Test Before Deploy
Every change must be tested locally before deployment:
```bash
./scripts/run-local.sh    # Start local environment
# Test changes...
./scripts/deploy.sh       # Deploy only after verification
```

### 3.6 — Documentation-Driven Development
- Read existing docs before writing code
- Update documentation when making architectural changes
- Every new service/feature should be reflected in relevant docs
- The `documentation/` folder is the canonical reference

### 3.7 — Extend Before Creating
Before creating a new service, component, or module:
1. Check if an existing service can be extended
2. Check if the pattern exists elsewhere in the codebase
3. Follow established conventions (file naming, structure, error handling)
4. Only create new when extending would violate separation of concerns

---

## 🔒 Article IV — Security Mandates

### 4.1 — Non-Negotiable Security Requirements

| Mandate | Enforcement |
|---------|-------------|
| No IP logging anywhere | All logs, databases, and services must exclude IP addresses |
| Anonymous uploads | No user identification required for document submission |
| Metadata stripping | All uploaded documents have identifying metadata removed |
| HTTPS everywhere | All communications encrypted via TLS |
| Security headers | Full complement on both nginx and FastAPI responses |
| Virus scanning | All uploads scanned via VirusTotal before acceptance |
| Rate limiting | Anonymous time-bucket system (no IP-based tracking) |
| OTP authentication | Admin access via passwordless OTP only |
| JWT sessions | Short-lived tokens with proper validation |

### 4.2 — Incident Response Protocol
1. **Identify** — Detect the security issue (monitoring, user report, scan)
2. **Contain** — Isolate affected components (pod restart, service disable)
3. **Assess** — Determine scope and impact
4. **Remediate** — Fix the vulnerability
5. **Deploy** — Push fix via `deploy.sh`
6. **Document** — Record in `documentation/penetration-testing.md`
7. **Review** — Conduct post-incident review

### 4.3 — Regular Security Practices
- Monthly Nuclei security scans
- Quarterly dependency audits
- Security header validation after every deployment
- Penetration testing documentation maintained

---

## 🤖 Article V — AI Ethics Charter

### 5.1 — Ethical AI Commitment
HaqNow exclusively uses AI technologies that respect user privacy and align with ethical principles.

### 5.2 — Approved AI Stack

| Component | Technology | Why |
|-----------|-----------|-----|
| LLM | Thaura.AI | Privacy-first, ethical LLM provider |
| Embeddings | sentence-transformers | Local, open source, no data leaves our servers |
| Vector DB | pgvector (PostgreSQL) | Self-hosted, full data control |

### 5.3 — AI Boundaries
- ✅ **DO**: Use AI to help users discover corruption evidence
- ✅ **DO**: Generate embeddings locally (no external API for embeddings)
- ✅ **DO**: Provide confidence scores with AI answers
- ✅ **DO**: Attribute sources for every AI-generated response
- ❌ **DON'T**: Send raw document content to unauthorized external services
- ❌ **DON'T**: Store user queries with identifying information
- ❌ **DON'T**: Use AI for surveillance, profiling, or user tracking
- ❌ **DON'T**: Train models on user data without explicit consent

### 5.4 — AI Model Change Policy
Any change to the AI stack (new LLM provider, embedding model, etc.) requires:
1. Privacy impact assessment
2. Ethical alignment review
3. Performance benchmarking
4. Team consensus
5. Documentation update

---

## 🏗️ Article VI — Architecture Guardrails

### 6.1 — Technology Decisions

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Cloud | Exoscale (Swiss) | Swiss privacy laws, GDPR compliance |
| Orchestration | Kubernetes (SKS) | Container isolation, rolling deploys |
| CDN/DDoS | Deflect.ca | Non-profit, aligned with press freedom |
| Analytics | Umami (self-hosted) | No cookies, GDPR compliant, privacy-first |
| LLM | Thaura.AI | Ethical, privacy-respecting AI |

### 6.2 — Database Separation
- **MySQL**: Application data (documents, users, translations, config)
- **PostgreSQL**: AI/vector operations (embeddings, chunks, query logs)
- Reason: Separation of concerns, optimal tooling for each workload

### 6.3 — Dual Environment Strategy
- **Development** (`main` branch → `haqnow.click` → `haqnow-dev` namespace)
- **Production** (`prod` branch → `haqnow.com` → `haqnow` namespace)
- All changes flow dev → prod, never the reverse

### 6.4 — Statelessness
Backend pods must be stateless. All persistent state lives in:
- MySQL database (application data)
- PostgreSQL database (AI/vector data)
- S3 object storage (documents)
- Kubernetes secrets (configuration)

### 6.5 — Translation & Content Governance
- The database is the **canonical source of truth** for all user-facing content and translations.
- Static translation files (`en.json`, etc.) serve only as **initial seeds** or **development fallbacks**.
- All content MUST be **editable in all supported languages** via the admin interface (`/admin-translations-page`).
- When adding new translation keys, developers MUST ensure they are **propagated to the database** in all supported languages to enable admin management.

---

## 📐 Article VII — Code Standards

### 7.1 — Backend (Python)
- **Framework**: FastAPI with async endpoints
- **ORM**: SQLAlchemy with type hints
- **Validation**: Pydantic models for all request/response schemas
- **Auth**: Depends() injection for JWT/OTP/API key validation
- **Error handling**: Proper HTTP status codes (400, 401, 403, 404, 500)
- **Naming**: snake_case for files and functions, PascalCase for classes

### 7.2 — Frontend (TypeScript)
- **Framework**: React 18 + TypeScript (strict mode)
- **Components**: Functional components with hooks
- **UI Library**: shadcn/ui + Tailwind CSS
- **i18n**: All user-facing text through `useTranslation()` hook
- **Naming**: PascalCase for components, camelCase for functions/variables

### 7.3 — Infrastructure
- **Kubernetes**: Declarative YAML manifests in `k8s/manifests/`
- **Docker**: Multi-stage builds, minimal base images
- **Terraform**: IaC for all Exoscale resources
- **Scripts**: Bash with error handling (`set -e`)

### 7.4 — Commit Messages
```
Format: <type>: <description>

Types:
  feat:     New feature
  fix:      Bug fix
  docs:     Documentation changes
  refactor: Code restructuring
  security: Security improvements
  deploy:   Deployment changes
  i18n:     Translation updates
```

### 7.5 — Documentation Standards
- Use emoji headers for visual scanning
- Include practical commands and examples
- Reference file paths relative to repo root
- Keep tables for structured data
- Update when architecture changes

---

## 🔄 Article VIII — Change Management

### 8.1 — Version Semantics
- **Patch** (x.x.1): Bug fixes, minor text changes, dependency updates
- **Minor** (x.1.0): New features, UI enhancements, new endpoints
- **Major** (1.0.0): Breaking changes, architecture shifts, data migrations

### 8.2 — Branch Strategy
```
Feature Development:
  feature/* branch → merge to main → deploy dev → test → merge to prod → deploy prod

Hotfix:
  main branch → fix → deploy dev → test → merge to prod → deploy prod
```

### 8.3 — Rollback Procedure
```bash
# 1. Revert to previous deployment
kubectl rollout undo deployment/backend-api -n haqnow

# 2. If database changes involved, restore from backup
./scripts/restore-from-backup.sh

# 3. Fix the issue on main branch
# 4. Re-deploy through normal pipeline
```

---

## 📊 Article IX — Quality Gates

### 9.1 — Pre-Deployment Gate
Before any deployment, verify:
- [ ] Code tested locally (`./scripts/run-local.sh`)
- [ ] No hardcoded secrets in diff
- [ ] No IP logging in new code
- [ ] Privacy test passed (Article 3.1)
- [ ] Relevant documentation updated

### 9.2 — Post-Deployment Gate
After every deployment, verify:
- [ ] Health check passes: `curl -s https://www.haqnow.com/api/health`
- [ ] RAG status OK: `curl -s https://www.haqnow.com/api/rag/status`
- [ ] Frontend loads correctly
- [ ] Security headers present: `curl -sI https://www.haqnow.com`

---

## 📝 Article X — Amendment Process

### 10.1 — How to Amend
1. Propose change with rationale
2. Discuss with team
3. Reach consensus
4. Update this document
5. Record in changelog below
6. Deploy updated constitution

### 10.2 — Amendment Changelog

| Date | Amendment | Rationale |
|------|-----------|-----------|
| 2026-04-30 | Initial constitution ratified | Establish governance for HaqNow project |
| 2026-05-06 | Added Translation & Content Governance (Section 6.5) | Ensure database is source of truth for all languages |

---

*This constitution governs all development, deployment, and operational decisions for the HaqNow platform. When in doubt, refer to the core values (Article II) and privacy-first principle (Article III, Section 3.1).*
