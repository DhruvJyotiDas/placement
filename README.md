# Placement Portal Application (PPA) — Version 2

**Name:** Dhruv Jyoti Das
**Roll Number:** 23f2001463
**Status:** Diploma

A full-stack campus recruitment portal with three roles — **Admin (Institute)**,
**Company**, and **Student** — built on Flask (API), Vue 3 (UI), SQLite, Redis, and
Celery. Companies register and post placement drives after admin approval, students
browse and apply to drives they're eligible for, and the whole pipeline — approvals,
shortlisting, notifications, and reporting — is backed by real background jobs and a
caching layer, not just a CRUD demo.

---

## Tech Stack — What's Used, and For What

| Purpose | Technology | Where / Why |
|---|---|---|
| **Backend API framework** | Flask 3 | `backend/app.py` — app factory pattern; all JSON endpoints |
| **Backend auth** | Flask-JWT-Extended | Issues/validates JWTs; `backend/security.py` wraps every protected route with a role check |
| **Backend ORM / database** | Flask-SQLAlchemy + SQLite | `backend/models/models.py`; the `.db` file is **created programmatically** via `db.create_all()`, never by hand |
| **Backend caching** | Flask-Caching + Redis | `backend/extensions.py`; caches admin stats and the open-drives list, with explicit expiry and invalidation |
| **Background job queue** | Celery + Redis (as broker & result backend) | `backend/celery_worker.py`, `backend/tasks/jobs.py` — daily reminders, monthly reports, async CSV export |
| **Email delivery** | Python stdlib `smtplib` → MailHog | `backend/tasks/mailer.py` — sends real SMTP mail to a local catcher, so nothing needs a live mail account to demo |
| **Cross-origin support** | Flask-CORS | Lets the Vite dev server (port 5173) call the Flask API (port 5000) as if same-origin |
| **Frontend framework** | Vue 3 (Composition API, `<script setup>`, Single File Components) | `frontend/src/components/*.vue` |
| **Frontend build tool** | Vite | `frontend/vite.config.js` — dev server + `/api` proxy to Flask, production bundler |
| **Frontend routing** | Vue Router 4 | `frontend/src/router/index.js` — role-based navigation guards |
| **Frontend styling** | Bootstrap 5 (only CSS framework used, per project constraints) | Imported once in `main.js`; light custom polish in `styles.css` sits on top of it, not instead of it |
| **State / API layer** | Plain reactive JS module (no Vuex/Pinia needed at this scale) | `frontend/src/api.js` — JWT storage, fetch wrapper, toast notifications, formatting helpers |

---

## Project Structure

```
placement_portal_23f2001463/
├── README.md
├── api.yaml                     API endpoint reference (all routes, methods, descriptions)
├── requirements.txt              Backend Python dependencies
├── background.jpg                Background image used on the Login/Register pages
│
├── frontend/                     Vue 3 + Vite single-page application
│   ├── index.html                HTML entry point, mounts #app
│   ├── package.json              Frontend dependencies (vue, vue-router, bootstrap, vite)
│   ├── vite.config.js            Dev server config; proxies /api/* to Flask on :5000
│   ├── public/
│   │   └── background.jpg        Static asset served as-is (used by the auth pages)
│   └── src/
│       ├── main.js               App bootstrap: mounts Vue, imports Bootstrap + router
│       ├── App.vue                Root shell — navbar, role-aware nav links, toast container
│       ├── api.js                 fetch() wrapper (attaches JWT), auth state, toast helper,
│       │                          date/status formatting, avatar-color helpers
│       ├── styles.css             Small CSS layer on top of Bootstrap (backgrounds, cards,
│       │                          navbar gradient, glassmorphic auth page styling)
│       ├── router/
│       │   └── index.js           All routes + role-based route guard (redirects users to
│       │                          their own dashboard if they hit the wrong role's page)
│       └── components/
│           ├── LoginForm.vue          Login page — email/password form, JWT storage on success
│           ├── RegisterForm.vue       Self-registration for Students and Companies (role toggle)
│           ├── AdminDashboard.vue     Admin home — stats cards, pending company/drive approvals,
│           │                          registered companies/students lists, blacklist controls,
│           │                          all-applications table, global search
│           ├── CompanyDashboard.vue   Company home — profile summary, upcoming/closed drives,
│           │                          "create drive" and "mark as complete" actions
│           ├── CreateDrive.vue        Form for a company to post a new placement drive
│           │                          (eligibility criteria, salary, deadline, location)
│           ├── DriveApplications.vue  List of all applicants for one specific drive
│           ├── ApplicationReview.vue  Single-applicant detail view — company sets
│           │                          shortlisted / waiting / selected / rejected + remarks
│           ├── StudentDashboard.vue   Student home — browse approved drives with eligibility
│           │                          filtering/search, apply, trigger async CSV export
│           ├── StudentProfile.vue     Edit profile (branch, CGPA, year) + resume upload
│           ├── DriveDetail.vue        Full detail of one drive from the student's side,
│           │                          with an eligibility check and an Apply button
│           ├── CompanyDetail.vue      A company's public profile + its currently open drives
│           └── ApplicationHistory.vue Student's complete placement history across all drives
│
└── backend/                      Flask REST API
    ├── app.py                    App factory: wires up db/jwt/cache/celery, registers
    │                             blueprints, creates tables, seeds the one admin account
    ├── config.py                 All configuration in one place (DB URI, JWT secret, Redis
    │                             URLs, SMTP host/port, admin credentials, business constants)
    ├── extensions.py             Shared singletons (db, jwt, cache, celery) — avoids
    │                             circular imports between app.py / models / routes
    ├── security.py                role_required() RBAC decorator + current_company() /
    │                             current_student() lookup helpers
    ├── celery_worker.py          Entry point used by `celery worker` / `celery beat`
    │
    ├── models/
    │   └── models.py             SQLAlchemy models: User, CompanyProfile, StudentProfile,
    │                             PlacementDrive, Application — with relationships,
    │                             to_dict() serializers, and eligibility-check logic
    │
    ├── routes/                   One Flask Blueprint per role
    │   ├── auth.py                POST /register, POST /login
    │   ├── admin.py               Dashboard stats, company/student/drive search,
    │   │                          approve/reject/blacklist actions, all-applications view
    │   ├── company.py             Profile, drive CRUD, applicant list, shortlist/update
    │   │                          status, résumé viewing
    │   └── student.py             Profile, résumé upload, drive browsing + eligibility,
    │                              apply, application history, async CSV export
    │
    ├── tasks/
    │   ├── jobs.py                 The 3 Celery jobs: daily_reminder, monthly_report,
    │   │                          export_applications_csv
    │   └── mailer.py               Thin SMTP helper (send_email, with optional
    │                              attachments) used by every job and by the
    │                              "new applicant" notification on apply
    │
    ├── uploads/                   Uploaded student résumés (created at runtime)
    └── exports/                   Generated CSV exports + monthly HTML reports (runtime)
```

---

## Setup

```bash
pip install -r requirements.txt
cd frontend && npm install && cd ..
```

## Running (6 terminals)

**1 — Redis** (already installed on this machine)
```bash
redis-server
```

**2 — MailHog** (catches every email the app sends — installed system-wide)
```bash
mailhog
```
Read the mail at **http://localhost:8025**

**3 — Flask API** — creates the DB and seeds the admin on first run
```bash
cd backend
python app.py
```
API on **http://localhost:5000**

**4 — Celery worker** — `--pool=solo` is required on Windows
```bash
cd backend
celery -A celery_worker.celery worker --loglevel=info --pool=solo
```

**5 — Celery beat** (only needed to demo the *scheduled* jobs)
```bash
cd backend
celery -A celery_worker.celery beat --loglevel=info
```

**6 — Vue frontend**
```bash
cd frontend
npm run dev
```
Open **http://localhost:5173**

---

## Default Admin

The admin pre-exists and is created programmatically — there is no admin registration.

| Email | Password |
|---|---|
| `admin@ppa.com` | `admin123` |

---

## Application Flow

1. A **company** registers → status is `pending`.
2. The **admin** approves it. *A company cannot create a drive until it is approved.*
3. The company **creates a drive** → the drive is `pending`.
4. The admin **approves the drive** → only now is it visible to students.
5. A **student** registers, completes their profile, uploads a résumé.
6. The student sees approved drives, **filtered by eligibility** (branch, CGPA, year),
   and applies. Applying twice to the same drive is blocked. The company is emailed
   the moment a student applies.
7. The company reviews applicants and sets each to
   `shortlisted` / `waiting` / `selected` / `rejected`.
8. The student watches their status change and can export their full history as CSV
   (emailed to them with the file attached, plus an on-screen alert).

**Blacklisting.** If the admin blacklists a company, all of its `pending` and `approved`
drives are **cancelled** and its login is disabled. Blacklisting a student deactivates
their account.

---

## Batch Jobs

| Job | Type | Schedule | What it does |
|---|---|---|---|
| `tasks.daily_reminder` | scheduled | daily, 18:00 | Emails students about drives closing within 3 days that they are **eligible for** and have **not applied to**. |
| `tasks.monthly_report` | scheduled | 1st of month, 08:00 | Builds an HTML activity report (drives conducted, applications, students selected) and emails it to the admin. Also saved to `backend/exports/`. |
| `tasks.export_applications_csv` | user-triggered | on demand | Exports a student's placement history to CSV (roll number, name, email, branch, CGPA, company, drive, status, dates), then **emails it as an attachment** with a styled HTML summary, plus an on-screen toast alert. |

There is also a lightweight, synchronous notification (not a Celery job) that emails
the **company** the instant a student applies to one of its drives — see
`routes/student.py` → `apply()`.

Sending is **fail-soft**: if MailHog is not running, the email is printed to the console
instead of raising, so a demo never breaks on a dead SMTP port.

---

## Caching

Redis-backed, via Flask-Caching:

- `admin_stats` — the admin dashboard counts, 120s expiry
- `open_drives` — the approved-and-open drive list, 60s expiry

Both keys are **explicitly invalidated** on any write that would make them stale
(approval, rejection, blacklist, drive creation, application), so the cache never
serves a wrong number.

---

## API Reference

The full endpoint list — method, path, and description — lives in **[`api.yaml`](api.yaml)**.
