# RoutePlanner — English

![Home Page](docs/home.png)

**RoutePlanner** is a comprehensive web application for managing geographical locations and calculating optimal routes. It uses **Dijkstra** (via `NetworkX`) with Haversine distance, interactive maps (`Leaflet.js`), and professional PDF reports (`fpdf2` + `html2canvas`).

> **Deployment 2026 — Single Docker Image:** `SQLite` by default (zero external dependencies, persisted via volume). **MySQL/PostgreSQL** supported optionally via `DATABASE_URL` (drivers `pymysql` + `psycopg2-binary` included). `gunicorn` on **`8003`**.

---

## Table of Contents
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Quick Start (Single Image)](#quick-start-single-image)
- [External Database (MySQL/PostgreSQL)](#external-database-mysqlpostgresql)
- [Environment Variables](#environment-variables)
- [Demo / Default Admin User](#demo--default-admin-user)
- [How Deployment Works (entrypoint)](#how-deployment-works-entrypoint)
- [Verification](#verification)
- [Production Deployment](#production-deployment)
- [Troubleshooting](#troubleshooting)
- [Manual Local Run (without Docker)](#manual-local-run-without-docker)
- [Project Structure](#project-structure)

---

## Features

### 🗺️ Interactive Maps & Routing
- **Leaflet** interactive map, markers, popups.
- **Route Planning:** select Start / End / optional Mid point.
- **Dijkstra** on a dynamically built graph (nodes = your saved `Location`s, edges = Haversine km).

![Dashboard and Map](docs/dashboard.png)

### 📊 Advanced Reporting
- **PDF Export** (`/graphs/export_pdf`): captured map (`html2canvas`), schematic graph (`NetworkX`+`matplotlib`), metrics (distance, ETA at 60 km/h), coordinates.
![Graph Visualization](docs/routes.png)

### 🔒 User & Location Management
- **Secure Auth:** `werkzeug.security` hashing, session, `UserRole` (`admin`/`moderator`/`user`).
- **CRUD Locations:** `GET/POST /locations/`, `PUT/DELETE /locations/<id>` (auth required).
- **Trip History:** `RouteHistory` persistence.
| User Management | Trip History |
| :---: | :---: |
| ![User Management](docs/manageusers.png) | ![Trip History](docs/TripHistory.png) |
![User Configuration](docs/userconfig.png)

---

## Tech Stack
- **Backend:** Python 3.13, Flask 3, Flask-SQLAlchemy, Flask-Migrate (Alembic)
- **DB:** **SQLite default** (`sqlite:///routeplanner.db` → `instance/routeplanner.db`, volume `sqlite_data`). **MySQL/PostgreSQL optional** via `DATABASE_URL` — drivers `pymysql` + `psycopg2-binary` are **included in the image**, no rebuild needed. Just set `DATABASE_URL` to `mysql+pymysql://...` or `postgresql+psycopg2://...`.
- **Frontend:** Bootstrap 5 / AdminLTE, Leaflet.js, Jinja2
- **Graph:** NetworkX, matplotlib
- **PDF:** fpdf2, html2canvas (client capture)
- **Server:** gunicorn (prod) / Flask dev server (local)
- **Tooling:** `uv`, Docker, docker-compose

---

## Quick Start (Single Image)

### Prerequisites
- Docker >= 20.10 & Docker Compose v2 (`docker compose version`)
- Git
- (Optional) `uv` for local dev without Docker

### 1. Clone
```bash
git clone <your-repo-url> RoutePlanner
cd RoutePlanner
```

### 2. Configure env (optional for SQLite)
```bash
cp .env.example .env
# For SQLite default you can leave DATABASE_URL empty.
# For external DB, set DATABASE_URL in .env (see next section).
# At minimum set SECRET_KEY, ENCRYPTION_KEY for prod.
```

### 3. Run — SQLite (no external DB)
```bash
# Option A: docker run — simplest, single image only
docker build -t route-planner .
docker run -d -p 8003:8003 --name route-planner -v routeplanner_data:/app/instance route-planner

# Option B: docker compose — single service + volume
docker compose up --build -d
docker compose logs -f web  # wait for "RoutePlanner READY" + "DEMO READY"
```
- **App:** http://localhost:8003
- **DB file:** `sqlite_data` volume → `/app/instance/routeplanner.db` (persisted)

### 4. Stop / Reset
```bash
docker compose down        # keep data (sqlite_data volume)
docker compose down -v     # also delete DB data (fresh start)
# for docker run:
docker rm -f route-planner
docker volume rm routeplanner_data  # to wipe DB
```

---

## External Database (MySQL/PostgreSQL)

Drivers are **already included in the image** (`pyproject.toml:15-16` `pymysql`, `psycopg2-binary`). The container detects `DATABASE_URL` and waits for the DB before migrating.

```bash
# MySQL external (e.g., managed RDS, local mysql, or separate container)
DATABASE_URL=mysql+pymysql://route_user:route_password@host:3306/routeplanner docker compose up -d
# PostgreSQL external
DATABASE_URL=postgresql+psycopg2://route_user:route_password@host:5432/routeplanner docker compose up -d

# Via .env (persistent)
# edit .env: DATABASE_URL=mysql+pymysql://...
docker compose up -d --build

# Direct docker run with external DB
docker run -d -p 8003:8003 \
  -e DATABASE_URL=mysql+pymysql://user:pass@host:3306/routeplanner \
  -e SECRET_KEY=your-secret \
  route-planner

# Verification that external DB is used:
curl http://localhost:8003/health | jq .db  # should be "ok"
docker logs route-planner | grep "Waiting for MySQL"
```

> **Fallback:** If `DATABASE_URL` is empty/unset, `config.py:15` uses `sqlite:///routeplanner.db` automatically — fixes `RuntimeError: Either 'SQLALCHEMY_DATABASE_URI'...`.

---

## Environment Variables

| Variable | Default (Dockerfile / .env.example) | Description |
|---|---|---|
| `HOST` | `0.0.0.0` | Flask/gunicorn bind |
| `PORT` | `8003` | **Exposed** `8003:8003` |
| `DATABASE_URL` | *(empty)* → `sqlite:///routeplanner.db` | SQLAlchemy URI. **SQLite default**. Set to `mysql+pymysql://...` or `postgresql+psycopg2://...` for external DB (drivers included) |
| `SECRET_KEY` | `dev-secret-key-change-in-production` | Flask session. **Change in prod** |
| `ENCRYPTION_KEY` | `0A1glB0r_8tPpo8k9eeWZW3TXvkvCPpw1ZgBmsV5D6s=` | Fernet 44-char. Must be valid Fernet |
| `CONFIG_ACCESS_KEY` | `admin` | Key for `/configuration` when not admin |
| `ADMIN_USERNAME` | `admin` | Demo admin login |
| `ADMIN_EMAIL` | `admin@routeplanner.local` | Demo admin email |
| `ADMIN_PASSWORD` | `Admin123!` | **Change after first login** or via env |
| `ADMIN_FORCE_RESET` | `false` | If `true`, resets admin password on every container start |

> `config.py` provides safe defaults so `uv run app.py` without `.env` no longer crashes.

---

## Demo / Default Admin User

The container **auto-creates** an admin on every start (`entrypoint.sh` + `seed.py`, idempotent):

- **URL:** http://localhost:8003
- **Go to:** `Sign In` → username `admin` / password `Admin123!`
- **Capabilities (UserRole.ADMIN):** manage all users, change any role (`admin`/`moderator`/`user`), delete any `Location` batch, reset passwords, access `/configuration` without extra key, view all histories.
- **To change credentials:**
  ```bash
  # option A: via env before start
  ADMIN_USERNAME=myadmin ADMIN_EMAIL=me@example.com ADMIN_PASSWORD='S3cure!' docker compose up --build
  # option B: docker run
  docker run -d -p 8003:8003 -e ADMIN_USERNAME=myadmin -e ADMIN_PASSWORD='S3cure!' route-planner
  # option C: via UI after login -> /users/update & /users/change-password
  # option D: force reset on next boot
  ADMIN_FORCE_RESET=true docker compose up -d
  ```
- **Create normal users:** `Sign Up` page (`/users/signup`) → role `user` by default. An admin can promote them in `/configuration`.

**How to know if demo is running?**
- **During deploy:** `entrypoint.sh` prints banner before gunicorn:
  ```
  >> Seeding admin...
    created admin: admin
  >> Quick demo check...
    ✅ DEMO READY: 'admin' / 'Admin123!' -> http://localhost:8003/users/signin
  ========================================
    RoutePlanner READY
    App:   http://localhost:8003
    Health: http://localhost:8003/health
  ========================================
  ```
- **After deploy:**
  ```bash
  docker compose logs web | grep -A2 "DEMO READY"
  curl -s http://localhost:8003/health/demo | python3 -m json.tool
  curl -s http://localhost:8003/health | python3 -m json.tool
  docker compose exec web python seed.py  # manual re-seed if demo missing
  ```

**Without Docker** (SQLite fallback) you still get the admin:
```bash
uv sync
# ensure DATABASE_URL is empty to use SQLite
uv run python seed.py
uv run python app.py           # http://localhost:8003
# check demo: curl http://localhost:8003/health/demo | jq .demo_ready
```

---

## How Deployment Works (entrypoint)

`entrypoint.sh` (set as `ENTRYPOINT` in `Dockerfile`) is minimal (~80 lines):

1. **Wait for DB (conditional):** If `DATABASE_URL` contains `mysql` → `pymysql` loop 30×2s; if `postgres` → `psycopg2` loop; otherwise **skip** (SQLite instant).
2. **Migrations:** `flask db upgrade` (Alembic). Warns but continues if missing.
3. **Ensure tables:** `python -c "db.create_all()"` after importing all models — guarantees tables even if migrations incomplete.
4. **Stamp:** `flask db stamp head` to align `alembic_version`.
5. **Seed:** idempotent admin creation (checks `username` then `email`, promotes if needed, `ADMIN_FORCE_RESET` optional).
6. **Start:** `gunicorn --bind 0.0.0.0:8003 --workers 2 --threads 4 app:app`.

`Dockerfile` now:
- `python:3.13-slim` + `curl` + `uv sync --frozen`, `mkdir -p /app/instance`, `EXPOSE 8003`, `HEALTHCHECK curl -f http://localhost:${PORT}/health`, `ENTRYPOINT ./entrypoint.sh` (no `default-mysql-client`).

`docker-compose.yml` (single service):
- `web: build: ., ports: 8003:8003, volumes: sqlite_data:/app/instance, env_file: .env, healthcheck: curl`

---

## Verification

```bash
docker compose ps
docker compose logs web  # should end with "DEMO READY" + "RoutePlanner READY" + "Starting gunicorn"
curl -f http://localhost:8003/health && echo "APP OK"
curl -s http://localhost:8003/health/demo | python3 -m json.tool  # check demo_ready + hint
# login test
curl -c cookies.txt -b cookies.txt -L http://localhost:8003/users/signin -d "username=admin&password=Admin123!"
```

Expected `entrypoint.sh` log:
```
=== RoutePlanner (single image) ===
DATABASE_URL=sqlite:///routeplanner.db (default)
>> Using SQLite (no external DB wait)
>> Running migrations...
>> Ensuring tables...
>> Seeding admin...
  created admin: admin
  ✅ DEMO READY: 'admin' / 'Admin123!' -> http://localhost:8003/users/signin
========================================
  RoutePlanner READY
  App:   http://localhost:8003
========================================
>> Starting gunicorn on 0.0.0.0:8003
```

---

## Production Deployment

```bash
cp .env.example .env
# edit .env: SECRET_KEY, ENCRYPTION_KEY (generate: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"), ADMIN_PASSWORD
docker compose -f docker-compose.prod.yml up --build -d
docker compose -f docker-compose.prod.yml logs -f web
```
Notes:
- `docker-compose.prod.yml` same single image, `restart: always`, volume `sqlite_data`.
- To use a prebuilt image: uncomment `image: jorgearguello/route-planner:1.0` and comment `build: .` in compose file.
- For external DB in prod, set `DATABASE_URL=mysql+pymysql://...` or `postgresql+psycopg2://...` in `.env` or orchestrator secrets.
- Behind a reverse proxy (nginx/traefik) forward to `8003`, enable TLS.
- Change `ADMIN_PASSWORD` immediately after first login.

---

## Troubleshooting

| Symptom | Cause / Fix |
|---|---|
| `RuntimeError: Either 'SQLALCHEMY_DATABASE_URI'...` | Old code without fallback. Fixed in `config.py`. Ensure `DATABASE_URL` is set or use default SQLite. |
| `ValueError: ENCRYPTION_KEY must be set` / Fernet invalid | Old `dev_encryption_key` not valid 44-char. Now default `0A1glB0r_8tPpo8k9eeWZW3TXvkvCPpw1ZgBmsV5D6s=` works, or set `Fernet.generate_key()`. |
| `table users already exists` on `flask db upgrade` | DB was created via `create_all` without Alembic stamp. Fixed: entrypoint does `db.create_all()` + `flask db stamp head`. Safe to ignore. |
| External MySQL/Postgres not ready / connection refused | `entrypoint.sh` waits 60s only if `DATABASE_URL` matches. Check `docker logs web`, ensure `DATABASE_URL` host/port reachable from container (for compose, use host.docker.internal if DB on host). |
| `admin` login fails / `demo_ready:false` | `curl http://localhost:8003/health/demo` shows `hint`. `docker logs web \| grep DEMO` shows status. Try `ADMIN_FORCE_RESET=true docker compose up -d` or `docker compose exec web python seed.py`. |
| Port already in use `8003` | Change `ports: "8003:8003"` and `PORT` together, or `lsof -i :8003` / `docker ps`. |
| Want to switch from SQLite to MySQL/Postgres later | Just set `DATABASE_URL` and recreate container: `DATABASE_URL=... docker compose up -d --force-recreate`. Data will be in new DB; old SQLite file remains in `sqlite_data` volume (backup: `docker run --rm -v route-planner_sqlite_data:/data -v $(pwd):/backup ubuntu tar czf /backup/sqlite.tgz /data`). |

---

## Manual Local Run (without Docker)

```bash
# requires Python 3.13 + uv
uv sync
cp .env.example .env  # or leave DATABASE_URL empty -> SQLite fallback
uv run python seed.py
uv run python app.py          # http://localhost:8003 (or gunicorn)
# or with external DB locally:
DATABASE_URL=mysql+pymysql://user:pass@127.0.0.1:3306/routeplanner uv run python app.py
# or Postgres:
DATABASE_URL=postgresql+psycopg2://user:pass@127.0.0.1:5432/routeplanner uv run python app.py
```

`config.py` fallback → no need to set `DATABASE_URL` locally; `instance/routeplanner.db` is created and ignored by `.dockerignore`/`.gitignore`.

---

## Project Structure
```
RoutePlanner/
├── app.py                 # Flask app, init_db, register_routes, run
├── config.py              # Config with safe defaults + DATABASE_URL override
├── entrypoint.sh          # conditional DB wait, migrate, create_all, seed, gunicorn (~80 lines)
├── seed.py                # standalone seed script
├── Dockerfile             # single image: python:3.13-slim, uv, 8003, HEALTHCHECK
├── docker-compose.yml     # single service + sqlite_data volume
├── docker-compose.prod.yml# prod: same image, restart: always
├── .env.example           # template (DATABASE_URL empty = SQLite)
├── pyproject.toml / uv.lock  # includes pymysql + psycopg2-binary for external DB
├── models/                # User, Location, API_Storage, RouteHistory, db/migrate
├── controllers/           # business logic (users, locations, graphs, etc.)
├── routers/               # Blueprint endpoints
├── utils/                 # auth, encryption
├── templates/ / static/   # Jinja2 + AdminLTE + Leaflet
├── migrations/            # Alembic versions
└── test/                  # verify_* scripts
```

See `DEVELOPMENT.md` for developer deep-dive.

---

**Maintained by Jorge Arguello — RoutePlanner 2026**
