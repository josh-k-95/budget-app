# Budget App Plan

Last updated: 2026-11-27

## Vision

A budgeting app for casual users: simple by default, grows with you. Advanced features are optional
modules, each with a tutorial and a toggle. Self-hosted before 1.0.0; at 1.0.0, public web +
Android (Play Store) release.

## Principles

- Only the next version is a firm plan. Later versions are direction and get re-planned after each release.
- Scope is frozen per version. New ideas go in `IDEAS.md`.
- Never block recording a transaction. Show problems; don't refuse records.
- From beta (0.6.0) on, testers' data must survive every update.
- Launch cost: $25 one-time (Play developer account). No recurring costs. No paid domain.

## Versioning

- Semantic Versioning (`MAJOR.MINOR.PATCH`). `0.x` = pre-release; `1.0.0` = public release.
  0.10.0 follows 0.9.0.
- Each release: git tag (`v0.1.0`), Docker image tag (`0.1.0` + `latest`), `CHANGELOG.md` entry.
- Patches (`0.1.1`) are bug fixes only.
- After 1.0.0 the mobile app has its own version line.

## Stages

| Stage | Versions | Who uses it |
|---|---|---|
| Alpha | 0.1–0.5 | Me. Breaking changes allowed. |
| Beta | 0.6–0.9 | Web testers on my server, then Play closed test. Data must survive updates. |
| Release candidate | 0.10 | Fixes and release work only. |
| GA | 1.0.0 | Public. |

## Stack

| Layer | Choice | Why |
|---|---|---|
| Frontend | React, TypeScript, Vite, Tailwind, React Router | Standard; React skills carry to React Native; TS catches errors and shares types |
| Shared logic | `packages/core` (pure TypeScript) | One implementation for web, offline, Android |
| Backend | FastAPI, Uvicorn, SQLAlchemy, Pydantic, Alembic | Fast to build; auto API docs; safe migrations |
| Database | PostgreSQL | Multi-user, no SQLite migration later |
| Auth | Own: `pwdlib` (Argon2), DB sessions, httpOnly Secure cookies | FastAPI-Users is in maintenance mode; DB sessions are revocable |
| Deploy | Docker Compose: app container (serves API + frontend) + Postgres | One port, works behind any proxy |
| HTTPS | Required. Tailscale profile included; any proxy works | |
| Quality | pytest, Vitest, Ruff, ESLint, Prettier, GitHub Actions | |
| Mobile (0.9.0) | React Native (Android) | Shares TS and core logic |
| Docs | GitHub repo + GitHub Pages (docs and privacy policy only) | Free |

Known weak point: two languages (Python server, TypeScript elsewhere). Revisit by 0.9.0 whether the
sync server should move to TypeScript.

## Architecture rules

- Data belongs to budgets (with members), not directly to users. Every table has `budget_id`;
  access is checked through membership. Enables shared household budgets.
- Transactions have `account_id`. Default "Main" account created at signup.
- UUID primary keys; client may supply IDs; creates are idempotent.
- `created_at`, `updated_at`, `deleted_at` on every table; soft deletes.
- Money stored as integer cents. Single currency, locale formatting.
- Calculations live in `packages/core`; server stores, validates, authorizes.
- Per-user settings table with feature flags.
- Every schema change is a data-preserving Alembic migration.
- App on one port; trusts proxy headers; `PUBLIC_URL`; `/api/health`.
- Login refused over plain HTTP unless localhost or `ALLOW_INSECURE_HTTP=true`.

## Roadmap

### NOW

#### 0.1.0 — Foundation (alpha, est. 3–4 weeks, target early Jan 2027)
- **Goal:** I can log in to my own server and record every transaction.
- **Features:**
  - Register, login, logout; multiple users; login rate limiting; `ALLOW_SIGNUP`; password reset via server CLI.
  - Transactions: amount, type (income/expense), category, descriptor, date, note (optional). Add/edit/delete; list by month.
  - Categories: user-created, separate income/expense.
  - Mobile-friendly UI (375px–1280px). Optional minimal installable PWA.
  - Groundwork: budgets + members, default "Main" account, UUIDs, soft deletes, settings/feature flags.
- **Other work:** CI, tests, Docker Compose, Tailscale profile, `.env.example`, README setup guide.
- **Exit criteria:** running on my homelab over HTTPS, used daily for 2 weeks, tests pass, no data bugs.

### NEXT

#### 0.2.0 — Budgets (alpha, 2–3 weeks)
- **Goal:** the app replaces a spreadsheet budget.
- Per-category monthly budget + overall monthly budget; visual warning when exceeded (never blocks).
- Dashboard: income, expenses, remaining this month; budget status; per-category spending vs budget.
- **Exit:** a full month of real budgeting in the app.

#### 0.3.0 — Recurring and bills (alpha, 1–2 weeks)
- **Goal:** monthly bills no longer need typing.
- Recurring transactions: same date monthly, or every X days; auto-created when due (catch-up on missed).
- Upcoming-bills list on dashboard; due-soon highlighting.
- **Exit:** a month of bills created correctly, no duplicates.

#### 0.4.0 — Accounts, savings, import (alpha, 2–3 weeks)
- **Goal:** I know what I can actually spend, and moving in from another tool is easy.
- Multiple accounts (checking, savings, cash, credit card); balances; transfers (not income/spending).
- Savings as an account type; monthly savings (percent or fixed) as a planned transfer.
- Usable amount.
- CSV import with saved column mappings per bank.
- Saved descriptor list per category.
- Savings built to be toggleable (for 0.6.0).
- **Exit:** a real bank CSV imports correctly; usable amount matches reality.

#### 0.5.0 — Planning mode (alpha, 3–4 weeks)
- **Goal:** I can see how a decision affects next month.
- Projection from recurring + category averages; what-if scenarios; purchase planning.
- **Decide before building:** averaging window, mean vs median, loans whose payments change.
- **Other work:** start recruiting web beta testers. Pick final app name (check Play Store, GitHub,
  trademarks); rename repo and Docker image before beta.
- **Exit:** last month's projection was close to reality.

### LATER (direction only)

#### 0.6.0 — Modules (beta starts, 3–4 weeks, ~mid Apr 2027)
- Tutorials page with toggles; behavior-based hints in context.
- Savings and planning mode become modules. Turning off hides data, never deletes.
- Web beta on my server, 3–10 testers, feedback channel.
- **Exit:** testers discover and enable modules without being told.

#### 0.7.0 — Offline (beta, 4–6 weeks)
- IndexedDB local copy, change queue, sync on reconnect, most-recent-edit wins.
- Calculations run on device from `packages/core`. Installable web app.
- **Exit:** offline edits sync across two devices with no loss or duplicates.

#### 0.8.0 — Envelopes, charts, sharing, search (beta, 3–5 weeks)
- Envelope budgeting module (carry-over, covering overspending).
- Charts: monthly trends, category breakdown, income vs spending.
- Shared household budgets: invite a member; both edit the same budget.
- Search across transactions.
- **Other work:** build a list of 15–20 Android testers.

#### 0.9.0 — Android (beta, 6–8 weeks)
- React Native Android app: local data, optional sync to self-hosted server, QR pairing.
- Bill notifications on the phone.
- **Other work:** Play developer account ($25); closed test with 12+ testers for 14 continuous days.
- **Exit:** closed test runs with no serious bugs.

#### 0.10.0 — Release candidate (3–4 weeks)
- Encrypted backup/restore, data export, Caddy profile.
- Security review, accessibility check, privacy policy, Play data safety form, self-hosting docs + troubleshooting.
- Apply for Play production access. Fixes only.
- **Exit:** production access approved; no open serious bugs.

#### 1.0.0 — Public release (~late Aug 2027; range Jun–Oct)
- Web app + Play Store app. Stable API.

### After 1.0.0
Split transactions, auto-categorization rules, bank sync ("bring your own provider" module, e.g. SimpleFIN), iOS, net worth, debt planner, multi-currency.

## Timeline

Assumes ~10–15 hours/week. Only dates through 0.2.0 are worth planning around; re-estimate after each release.
Biggest uncertainty: 0.7.0 (offline) and 0.9.0 (Android). Block out exam periods.

| Phase | Est. | Approx. end |
|---|---|---|
| Discovery (try competitor apps) | 2 wks | mid Dec 2026 |
| 0.1.0 | 3–4 wks | early Jan 2027 |
| 0.2.0 | 2–3 wks | late Jan |
| 0.3.0 | 1–2 wks | early Feb |
| 0.4.0 | 2–3 wks | late Feb |
| 0.5.0 | 3–4 wks | mid Mar |
| 0.6.0 | 3–4 wks | mid Apr |
| 0.7.0 | 4–6 wks | mid May |
| 0.8.0 | 3–5 wks | mid Jun |
| 0.9.0 | 6–8 wks | early Aug |
| 0.10.0 | 3–4 wks | late Aug |

## Deployment and HTTPS

- App runs on one port; never terminates TLS.
- Compose profiles: `tailscale` (0.1.0), `caddy` (0.10.0), or none (bring your own proxy).
- Officially supported: Tailscale, Caddy. Other proxies/tunnels: community-supported.
- Docs: one page per supported setup + troubleshooting (Tailscale key expiry, CGNAT, DNS).
- At-rest protection: recommend full-disk encryption; encrypted backups at 0.10.0.

## Beta testing

- Web beta (0.6.0+): friends, classmates, r/selfhosted, budgeting communities. Accounts on my server.
- Android (0.9.0): Play closed test via Google Group; 12+ testers opted in 14 continuous days; aim for 15–20.

## Git workflow

- `main`: released code only. `dev`: next version. `feature/<name>`: one feature, off `dev`.
- Feature → PR into `dev` → CI green → review → merge → delete branch.
- Release: update `CHANGELOG.md` + version → PR `dev` → `main` → tag `vX.Y.Z` → CI builds image.
- Hotfix: branch off `main` → PR into `main` → tag patch → merge `main` back into `dev`.

## Decisions log

| Decision | Choice |
|---|---|
| Version scheme | SemVer, 0.x pre-release |
| Transaction text field | "descriptor" |
| Version order | Budget-first (Option 1) |
| Login | In 0.1.0, multi-user |
| Database | PostgreSQL from 0.1.0 |
| Auth library | Own implementation (FastAPI-Users in maintenance mode) |
| Frontend language | TypeScript |
| HTTPS | Required; app is proxy-agnostic |
| Default access path | Tailscale Serve; Caddy optional |
| Mobile-friendly UI | From 0.1.0 |
| Modules + tutorials | 0.6.0, before beta; differentiator |
| Multiple accounts | Groundwork 0.1.0, feature 0.4.0; savings = account type |
| Shared household budgets | Groundwork 0.1.0, feature 0.8.0 |
| Bill reminders | 0.3.0 in-app; 0.9.0 phone notifications |
| Search | 0.8.0 |
| Split transactions, auto-categorization | After 1.0.0 |
| App name | Working name "budget-app"; name read from `APP_NAME` config; final name by 0.5.0; Android package ID permanent at 0.9.0. "Money Badger" rejected (taken by existing budgeting apps). |

## Dropped

GitHub Pages hosting for the app, custom encryption over HTTP, end-to-end encryption,
FastAPI-Users, Nginx by default, hosted service (SaaS), paid domain, SQLite.

## Open (decide later)

- Envelope vs category-limit as default model (~0.8.0).
- Planning mode details: averaging window, mean vs median, variable/amortizing payments (before 0.5.0).
- Sync server language: stay Python or move to TypeScript (by 0.9.0).
- Long-term direction for casual users: local-first app with optional self-hosted sync (implied by 0.7.0/0.9.0); confirm after 0.5.0.
