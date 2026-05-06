# 🎨 Frontend Architecture Specification

**React + TypeScript frontend architecture for the HaqNow platform.**

---

## 🏗️ Technology Stack

| Technology | Version | Purpose |
|-----------|---------|---------|
| React | 18.x | UI framework |
| TypeScript | 5.x | Type safety |
| Vite | 5.x | Build tool and dev server |
| Tailwind CSS | 3.x | Utility-first CSS |
| shadcn/ui | Latest | Component library |
| react-i18next | Latest | Internationalization |
| React Router | 6.x | Client-side routing |

---

## 📁 Directory Structure

```
frontend/src/
├── main.tsx                    # App entry point
├── router.tsx                  # Root router configuration
├── user-routes.tsx             # All page route definitions
├── AppWrapper.tsx              # App-level providers and wrappers
├── index.css                   # Global styles (Tailwind imports)
├── constants.ts                # App-wide constants
├── vite-env.d.ts              # Vite type declarations
│
├── components/                 # Reusable UI components
│   ├── ui/                    # shadcn/ui base components
│   ├── RAGQuestionAnswering.tsx   # AI Q&A interface
│   └── ...                    # Feature-specific components
│
├── pages/                     # Page-level components
│   └── ...                    # One file per route/page
│
├── i18n/                      # Internationalization
│   ├── config.ts              # i18n configuration
│   └── locales/               # Translation JSON files
│       ├── en.json            # English
│       ├── ar.json            # Arabic
│       ├── fr.json            # French
│       ├── de.json            # German
│       ├── ru.json            # Russian
│       ├── pl.json            # Polish
│       └── tr.json            # Turkish
│
├── lib/                       # Utility libraries
├── utils/                     # Helper functions
├── constants/                 # Feature-specific constants
├── brain/                     # AI/data logic (client-side)
├── extensions/                # Plugin/extension system
├── polyfills/                 # Browser polyfills
├── internal-components/       # Internal/system components
└── prod-components/           # Production-only components
```

---

## 🗺️ Page Routing

**Router**: `frontend/src/user-routes.tsx`

### Public Pages
| Route | Page | Description |
|-------|------|-------------|
| `/` | Home | Landing page with mission, stats, featured docs |
| `/search-page` | Search | Document search + AI Q&A tabs |
| `/document/{id}` | Document View | Full document details, download, comments |
| `/upload-page` | Upload | Anonymous document upload form |
| `/about-page` | About | Platform mission and information |

### Admin Pages
| Route | Page | Description |
|-------|------|-------------|
| `/admin-login-page` | Admin Login | OTP-based passwordless login |
| `/admin-management-page` | Admin Dashboard | Document management, approvals |
| `/admin-analytics-page` | Analytics | Upload trends, stats, RAG metrics |

---

## 🧩 Key Components

### AI Q&A Interface
**File**: `frontend/src/components/RAGQuestionAnswering.tsx`
- Natural language question input
- AI-generated answers with confidence scores
- Source document attribution with clickable links
- User feedback system (thumbs up/down)
- Loading states and error handling

### Search Interface
- Dual tab layout: "Document Search" | "AI Q&A"
- Full-text keyword search with filters
- Country, language, and date filtering
- Paginated results with document previews

### Document Viewer
- Document metadata display
- Multi-language content (original + English translation)
- Download options (original, translation, extracted text)
- Anonymous commenting system
- View count tracking

### Upload Form
- Drag-and-drop file upload
- Country selection (180+ countries)
- Tag input with suggestions
- Language auto-detection
- Progress feedback and confirmation

### Admin Dashboard
- Document approval queue
- Translation management interface
- API key management
- Analytics charts (upload trends, country distribution)
- Site announcement banner editor

---

## 🌐 Internationalization (i18n)

### Supported Languages

| Language | Code | Direction |
|----------|------|-----------|
| English | `en` | LTR |
| Arabic | `ar` | RTL |
| French | `fr` | LTR |
| German | `de` | LTR |
| Russian | `ru` | LTR |
| Polish | `pl` | LTR |
| Turkish | `tr` | LTR |

### Usage Pattern
```typescript
import { useTranslation } from "react-i18next";

function MyComponent() {
  const { t } = useTranslation();
  return <h1>{t("page.title")}</h1>;
}
```

### Rules
- **All user-facing text** must use `t()` translation function
- **New i18n keys** must be added to all 7 language files
- **RTL support** required (Arabic uses right-to-left layout)
- **Admin translations** editable via admin dashboard

---

## 🎨 Design System

### shadcn/ui Components
Config: `frontend/components.json`

Commonly used:
- `Button`, `Input`, `Textarea` — forms
- `Card`, `Dialog`, `Sheet` — containers
- `Tabs`, `Select`, `Switch` — navigation/controls
- `Table`, `Badge`, `Avatar` — data display
- `Toast`, `Alert` — feedback
- `Skeleton` — loading states

### Tailwind Configuration
Config: `frontend/tailwind.config.js`

### Color Theme
- Follows shadcn/ui theming system
- Dark mode support via CSS variables
- Consistent with platform branding

---

## ⚡ Build & Development

### Local Development
```bash
cd frontend
npm install          # Install dependencies
npm run dev          # Start dev server → http://localhost:5173
```

### Production Build
```bash
cd frontend
npm run build        # Output → frontend/dist/
```
Build is handled automatically by `scripts/deploy.sh`.

### Vite Configuration
**File**: `frontend/vite.config.ts`
- API proxy to backend (`/api` → `http://localhost:8000`)
- Path aliases (`@/` → `src/`)
- Optimized production builds

---

## 📊 Analytics Integration

### Umami Tracking
**File**: `frontend/index.html` (tracking script)
- Privacy-focused, no-cookie tracking
- Disabled in development environment
- Website ID configured via `UMAMI_WEBSITE_ID` env var

---

## 📏 Frontend Conventions

1. **Functional components only** — no class components
2. **TypeScript strict mode** — all props typed
3. **shadcn/ui first** — use library components before custom ones
4. **i18n always** — no hardcoded user-facing strings
5. **Responsive design** — mobile-first with Tailwind breakpoints
6. **Accessibility** — proper ARIA labels, keyboard navigation
7. **Error boundaries** — graceful error handling in all pages
8. **Loading states** — skeleton/spinner for all async operations
