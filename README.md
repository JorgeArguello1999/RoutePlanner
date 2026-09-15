# RoutePlanner

![Home Page](docs/home.png)

Manage locations and calculate optimal routes with **Dijkstra + Haversine**, **Leaflet** maps and **PDF** reports.

> **Single Docker image** — SQLite by default (no external DB). MySQL/PostgreSQL optional via `DATABASE_URL`. Demo auto-created.

---

> [!IMPORTANT]
> **Demo account — visible on the website and ready to use**
> - **URL:** http://localhost:8003 → **Sign In**
> - **User:** `admin` — **Password:** `Admin123!`
> - Auto-created on first run. No registration needed. Change via `ADMIN_PASSWORD` env.
> - You will also see this banner **on the home page and on the login page** (`Sign in as admin →`).

---

## 🌐 Language

| [🇬🇧 English](README.en.md) | [🇪🇸 Español](README.es.md) | [🛠️ Dev Guide](DEVELOPMENT.md) |
|---|---|---|
| Full guide | Guía completa | Architecture & contributing |

---

## 🚀 Deploy — 1 command

**Requires:** Docker + Docker Compose v2

```bash
git clone <repo> RoutePlanner && cd RoutePlanner
docker compose up --build -d
# or without compose:
# docker build -t route-planner . && docker run -d -p 8003:8003 -v routeplanner_data:/app/instance route-planner
```

Open **http://localhost:8003** → you will see:

- Home banner: **“Try the demo — admin / Admin123! → Sign in as admin”**
- Login page: blue box **“Demo: admin / Admin123! [fill]”** — click *fill* to auto-fill

**Sign in → Dashboard** to create locations, plan routes, export PDF.

```bash
docker compose logs -f web   # wait for "DEMO READY: admin / Admin123!"
docker compose ps            # → healthy on 8003
```

**Stop:**
```bash
docker compose down        # keep data
docker compose down -v     # wipe DB (fresh)
```

---

## 🔑 Demo credentials (also on site)

| Field | Value |
|---|---|
| URL | http://localhost:8003/users/signin |
| User | `admin` |
| Password | `Admin123!` |
| Email | `admin@routeplanner.local` |
| Role | `ADMIN` (manage users, locations, history) |

Normal users: `Sign Up` at `/users/signup` (role `user`, admin promotes in `/configuration`).

Change demo:
```bash
ADMIN_USERNAME=myadmin ADMIN_PASSWORD='S3cure!' docker compose up --build -d
# or inside app: /users/update, /users/change-password
# force reset: ADMIN_FORCE_RESET=true docker compose up -d
```

---

## 🗃️ Need MySQL/PostgreSQL?

Drivers `pymysql` + `psycopg2-binary` are **already in the image**. Just set `DATABASE_URL`:

```bash
DATABASE_URL=mysql+pymysql://user:pass@host:3306/routeplanner docker compose up -d
DATABASE_URL=postgresql+psycopg2://user:pass@host:5432/routeplanner docker compose up -d
```

Leave `DATABASE_URL` empty (default) to use SQLite (`instance/routeplanner.db` via `sqlite_data` volume).

<details>
<summary>More details</summary>

- `config.py:16` fallback → `sqlite:///routeplanner.db` if `DATABASE_URL` empty
- `entrypoint.sh` waits only if `DATABASE_URL` is MySQL/Postgres, otherwise instant
- For `docker run`: `-e DATABASE_URL=mysql+pymysql://...`

</details>

---

## ✅ Verify

```bash
curl http://localhost:8003/health | python3 -m json.tool   # demo_ready:true
curl http://localhost:8003/health/demo | python3 -m json.tool
docker compose logs web | grep "DEMO READY"
```

---

## 🧩 Stack & Structure

**Python 3.13 / Flask 3 / SQLAlchemy / NetworkX (Dijkstra) / Leaflet / fpdf2 / gunicorn / uv / Docker**

```
RoutePlanner/
├── Dockerfile              # single image, SQLite default
├── docker-compose.yml      # single service → sqlite_data:/app/instance
├── docker-compose.prod.yml # same image, restart: always
├── entrypoint.sh           # ~80 lines: migrate → seed → gunicorn
├── app.py / config.py / seed.py
├── models/  controllers/  routers/  utils/
├── templates/  static/     # home banner + signin demo box
└── migrations/
```

![Dashboard](docs/dashboard.png)
![Graph](docs/routes.png)
| Users | History |
|---|---|
| ![Users](docs/manageusers.png) | ![History](docs/TripHistory.png) |

---

**Maintained by Jorge Arguello — 2026** • See `README.en.md` / `README.es.md` for full guides • `DEVELOPMENT.md` for dev setup
