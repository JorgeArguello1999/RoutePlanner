# RoutePlanner — English

![Home Page](docs/home.png)

Manage locations and calculate optimal routes with **Dijkstra** (NetworkX + Haversine), **Leaflet** maps and **PDF** reports.

> **Single Docker image.** SQLite by default (no external DB). MySQL/PostgreSQL optional via `DATABASE_URL`. Demo auto-created and **visible on the site**.

---

> [!IMPORTANT]
> **Demo — you will see it on the website**
> - **Home page** banner: *“Try the demo — admin / Admin123! → Sign in as admin”*
> - **Login page** (`/users/signin`): blue box *“Demo: admin / Admin123! [fill]”*
> - **Direct:** http://localhost:8003/users/signin — **admin / Admin123!**

---

## Quick Start — 1 command

**Prerequisites:** Docker, Docker Compose v2, Git

```bash
git clone <repo> RoutePlanner && cd RoutePlanner
docker compose up --build -d
```

Open http://localhost:8003 — click **Sign in as admin** or go to **Sign In** and press **[fill]**.

```bash
docker compose logs -f web  # wait for "DEMO READY: admin / Admin123!"
```

**Without compose:**
```bash
docker build -t route-planner .
docker run -d -p 8003:8003 --name route-planner -v routeplanner_data:/app/instance route-planner
# http://localhost:8003
```

**Stop:**
```bash
docker compose down        # keep DB
docker compose down -v     # wipe DB
docker rm -f route-planner; docker volume rm routeplanner_data  # for docker run
```

---

## Demo account

| | Value |
|---|---|
| URL | `/users/signin` |
| User | `admin` |
| Password | `Admin123!` |
| Email | `admin@routeplanner.local` |
| Role | `ADMIN` |

Capabilities: manage users/roles, delete locations, reset passwords, view all history. Normal users register at `/users/signup` (admin promotes them).

**Change demo:**
```bash
ADMIN_USERNAME=myadmin ADMIN_PASSWORD='S3cure!' docker compose up --build -d
ADMIN_FORCE_RESET=true docker compose up -d   # reset password to .env value
# or inside app: /users/update, /users/change-password, /configuration
```

---

## Features

- **Leaflet** interactive map — markers, popups
- **Routing:** Start / End / optional Mid → Dijkstra on graph where edges = Haversine km
- **PDF export** `/graphs/export_pdf` — map capture + schematic graph + distance/ETA

![Dashboard](docs/dashboard.png)
![Graph](docs/routes.png)
| Users | History |
|---|---|
| ![Users](docs/manageusers.png) | ![History](docs/TripHistory.png) |

---

## Stack

- Backend: Python 3.13, Flask 3, Flask-SQLAlchemy, Flask-Migrate
- DB: **SQLite default** (`instance/routeplanner.db`, volume `sqlite_data`). MySQL/Postgres optional — drivers `pymysql` + `psycopg2-binary` included
- Frontend: Bootstrap 5 / AdminLTE, Leaflet, Jinja2
- Graph: NetworkX, matplotlib — PDF: fpdf2 — Server: gunicorn — Tooling: `uv`, Docker

---

## External DB (optional)

No rebuild needed — drivers are in the image.

```bash
# MySQL
DATABASE_URL=mysql+pymysql://user:pass@host:3306/routeplanner docker compose up -d
# Postgres
DATABASE_URL=postgresql+psycopg2://user:pass@host:5432/routeplanner docker compose up -d
# via .env: edit DATABASE_URL then docker compose up -d
# docker run:
docker run -d -p 8003:8003 -e DATABASE_URL=mysql+pymysql://user:pass@host:3306/routeplanner route-planner
```

Leave `DATABASE_URL` empty for SQLite (`config.py:16` fallback).

---

## Environment variables

| Var | Default | Note |
|---|---|---|
| `PORT` | `8003` | `8003:8003` |
| `DATABASE_URL` | *(empty)* → `sqlite:///routeplanner.db` | Set to `mysql+pymysql://...` or `postgresql+psycopg2://...` |
| `SECRET_KEY` | `dev-secret-key...` | Change in prod |
| `ENCRYPTION_KEY` | `0A1glB0r_8tPpo8k9eeWZW3TXvkvCPpw1ZgBmsV5D6s=` | Fernet 44-char |
| `ADMIN_USERNAME` / `ADMIN_PASSWORD` | `admin` / `Admin123!` | Demo — also shown on site |

---

## How it works

`entrypoint.sh` (~80 lines): `mkdir -p instance` → wait **only if** `DATABASE_URL` is MySQL/Postgres (else instant) → `flask db upgrade` → `db.create_all()` → `stamp head` → seed admin → `gunicorn --bind 0.0.0.0:8003`.

`Dockerfile`: `python:3.13-slim` + `curl` + `uv sync`, `EXPOSE 8003`, `HEALTHCHECK curl /health`.

`docker-compose.yml`: single service `web`, `sqlite_data:/app/instance`.

---

## Verify

```bash
curl http://localhost:8003/health | python3 -m json.tool          # demo_ready:true
curl http://localhost:8003/health/demo | python3 -m json.tool
docker compose logs web | grep "DEMO READY"
# login test
curl -c c -b c -L http://localhost:8003/users/signin -d "username=admin&password=Admin123!" | grep -qi dashboard && echo OK
```

---

## Production

```bash
cp .env.example .env  # set SECRET_KEY, ENCRYPTION_KEY, ADMIN_PASSWORD
docker compose -f docker-compose.prod.yml up --build -d   # restart: always
```

For external DB in prod set `DATABASE_URL` in `.env` or secrets. Behind nginx/traefik → forward `8003`, enable TLS.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `admin` login fails | `curl /health/demo` → `hint`. Try `ADMIN_FORCE_RESET=true docker compose up -d` or `docker compose exec web python seed.py` |
| External DB connection refused | Check `DATABASE_URL` reachable from container (`host.docker.internal` for host DB), `docker logs web` |
| Port `8003` in use | `lsof -i :8003` or change `ports: "8003:8003"` + `PORT` |
| Switch SQLite → MySQL/PG later | Set `DATABASE_URL` and `docker compose up -d --force-recreate` |

---

## Local run without Docker

```bash
uv sync
uv run python seed.py
uv run python app.py   # http://localhost:8003
# external DB locally:
DATABASE_URL=mysql+pymysql://user:pass@127.0.0.1:3306/routeplanner uv run python app.py
```

---

## Project structure

```
├── app.py / config.py / entrypoint.sh / seed.py
├── Dockerfile (single image)
├── docker-compose.yml (single service)
├── docker-compose.prod.yml
├── models/ controllers/ routers/ utils/
├── templates/ static/ (banner + login demo box)
├── migrations/
└── test/
```

See `DEVELOPMENT.md` for dev deep dive.

**Maintained by Jorge Arguello — 2026**
