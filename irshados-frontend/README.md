# IrshadOS Frontend

The IrshadOS frontend is a React (Vite + TypeScript) admin and POS shell derived from the ECME template. It provides the user experience for IrshadOS tenants across retail/wholesale and restaurant workflows, including product management, inventory, purchasing, sales, POS, and add-on restaurant modules.

## Table of Contents
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
- [Available Scripts](#available-scripts)
- [Project Structure](#project-structure)
- [Architecture Notes](#architecture-notes)
- [Integration Points](#integration-points)
- [Next Steps](#next-steps)

## Tech Stack
- React 18 + TypeScript
- Vite build tool
- Tailwind CSS
- React Router, TanStack Query, React Hook Form, Zod (to be wired in as modules land)
- Axios for API communication

## Getting Started

```bash
# Install dependencies
npm install

# Configure environment
cp .env.example .env  # create one if it does not exist yet
# Update VITE_API_BASE_URL and other keys when backend endpoints are ready

# Run the app
npm run dev
```

Visit the Vite dev server URL (usually `http://127.0.0.1:5173`) to load the IrshadOS admin shell.

## Available Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start the development server. |
| `npm run build` | Create a production bundle in `dist/`. |
| `npm run preview` | Preview the production build locally. |
| `npm run lint` | Run ESLint with zero allowed warnings. |
| `npm run lint:fix` | Apply ESLint autofixes. |
| `npm run format` | Check formatting with Prettier. |
| `npm run format:fix` | Format the repository with Prettier. |
| `npm run typecheck` | Run the TypeScript compiler in strict mode (`noEmit`). |
| `npm run test` | Compile TypeScript tests and execute them with the Node.js test runner. |
| `npm run test:watch` | Re-run the Node.js test suite on changes. |

Run `npm run prepare` once per clone to wire the `.husky` pre-commit hook (implemented as a Git `core.hooksPath` override). The hook executes linting, tests, and type-checking before every commit.

## Project Structure

```
irshados-frontend/
├─ src/
│  ├─ @types/            # Shared TypeScript definitions
│  ├─ assets/            # Local images/icons before moving to /assets repo folder
│  ├─ auth/              # Authentication flows (login, invite acceptance)
│  ├─ components/        # Reusable UI components
│  ├─ configs/           # Theme/layout/runtime configuration
│  ├─ constants/         # Application constants and enums
│  ├─ locales/           # i18n resources (English/Urdu planned)
│  ├─ mock/              # Temporary mock data during scaffolding
│  ├─ services/          # API clients (Axios) and domain services
│  ├─ store/             # Zustand stores for session, layout, POS state
│  ├─ utils/             # Helper utilities and hooks
│  └─ views/             # Route-level screens and dashboards
├─ public/               # Static assets served as-is
├─ index.html
├─ package.json
├─ tailwind.config.cjs
├─ tsconfig*.json        # TypeScript configuration files
└─ README.md (this file)
```

## Architecture Notes
- Derived from the ECME admin template to accelerate development. Remove unused demo code as new IrshadOS modules replace them.
- Use route-based code splitting for large verticals (POS, Reports, Restaurant pack).
- Maintain tenant branding/theme overrides and module toggles via configuration coming from the backend `tenant` settings.
- Plan for offline support (IndexedDB) for POS flows and WebSocket channels for KOT/KDS updates.

## Leather Storefront Demo
- Public routes (`/`, `/collections`, `/product/:slug`, `/journal`, `/about`, `/contact`) now render the Passion Atelier experience that mirrors the Upwork requirement for a leather accessories web store.
- Catalog/testimonial/metrics content live in [`src/data/leatherProducts.ts`](src/data/leatherProducts.ts). Update this file to add products, journal entries, or hero stats without digging through JSX.
- Shared layout code sits in [`src/views/storefront`](src/views/storefront), including a reusable shell with merchandising header, footer, and cart summary fed by the new Zustand store in [`src/store/cartStore.ts`](src/store/cartStore.ts).
- The storefront is unauthenticated so stakeholders can explore the demo instantly, while `/home` remains the authenticated dashboard for ERP/POS work.
- To showcase the admin, sign in at `/sign-in` with `admin-01@ecme.com` / `123Qwe` and organization slug `atelier-demo`. The side menu exposes Products, Orders, and Customers demos sourced from [`src/data/adminStore.ts`](src/data/adminStore.ts).

## Authentication Screens

The auth area now implements the multi-tenant flows backed by the Django API:

- **Sign Up (`/sign-up`)** – Users can choose between creating a new organization or joining an existing slug. The UI collects:
  - `organizationMode`: `'new'` or `'existing'`
  - Organization details (name/domain) when creating a workspace.
  - Organization slug when joining an existing tenant.
  - Desired role (`owner`, `admin`, `member`). Creating a tenant auto-locks to `owner`.
- **Sign In (`/sign-in`)** – Requires email, password, and the organization slug so consultants can hop between tenants that share the same email address.
- Successful responses persist the returned organization roster inside the auth store (`useSessionUser`) for upcoming role-based menu gating.

## Integration Points
- **API base URL**: configured via `VITE_API_BASE_URL` to talk to the Django backend.
- **Auth**: access tokens are issued by `/api/sign-in` and `/api/sign-up`. Include the organization slug in sign-in payloads and propagate the returned `activeOrganization` data when rendering menus.
- **RBAC**: client-side route guards and component level checks will map to backend role/permission responses.
- **Assets**: Shared imagery, logos, and icons are kept in the repository-level `assets/` folder. Import or copy them into `src/assets/` as needed.

## Next Steps
1. Extend the authenticated shell to respect the active organization and `authority` flags returned during sign-in.
2. Implement core CRUD flows (products, warehouses, suppliers, customers) using TanStack Query + React Hook Form.
3. Build POS workspace with offline cache, payment integrations, and receipt printing.
4. Layer in restaurant pack modules (menu, modifiers, KOT, KDS) with WebSocket updates.
5. Harden UI quality gates: ESLint, TypeScript strict mode, Prettier, Husky pre-commit, Node.js component smoke tests, and Playwright E2E scenarios.

Keep this README updated as modules evolve and demo components are replaced with production-ready flows.
