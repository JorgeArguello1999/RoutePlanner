# RoutePlanner

![Home Page](docs/home.png)

**RoutePlanner** — Manage locations and calculate optimal routes with **Dijkstra** + Haversine, interactive **Leaflet** maps and **PDF** reports.

> **ES** — Gestiona ubicaciones y calcula rutas óptimas con **Dijkstra** + Haversine, mapas **Leaflet** y reportes **PDF**. **Despliegue Docker listo: MySQL 8.0 + gunicorn en `8003`**.

---

## 🌐 Language / Idioma

| [🇬🇧 English — Full Guide](README.en.md) | [🇪🇸 Español — Guía Completa](README.es.md) | [🛠️ Development / Desarrollo](DEVELOPMENT.md) |
|---|---|---|
| Complete deployment, demo user, env vars, troubleshooting | Despliegue completo, usuario demo, variables, solución de problemas | Architecture, migrations, contributing (bilingual) |

This `README.md` is a **bilingual hub** — brief quick-start in both languages below. See links above for full guides.

---

<a id="english-quick"></a>
## 🇬🇧 English — Quick Deploy

### Stack
Python 3.13 / Flask 3 / SQLAlchemy / Flask-Migrate / MySQL 8.0 (`pymysql`) + SQLite fallback / NetworkX / Leaflet / fpdf2 / gunicorn / uv / Docker

### 1-Minute Deploy
```bash
git clone <repo> RoutePlanner && cd RoutePlanner
cp .env.example .env   # edit secrets if needed
docker compose up --build -d
docker compose logs -f web  # wait for "Seeding default admin user..." + "Using gunicorn"
open http://localhost:8003
# MySQL: localhost:3306  route_user/route_password  DB routeplanner
```

### Production
```bash
cp .env.example .env  # set SECRET_KEY, ENCRYPTION_KEY (Fernet), ADMIN_PASSWORD, MYSQL_PASSWORD
docker compose -f docker-compose.prod.yml up --build -d
```

### Demo Admin (auto-created, idempotent via `entrypoint.sh` + `seed.py`)
- **URL:** http://localhost:8003 → `Sign In`
- **User:** `admin` / **Pass:** `Admin123!` / **Email:** `admin@routeplanner.local` / **Role:** `ADMIN` (all permissions)
- **What admin can do:** manage users/roles, delete locations in bulk, reset passwords, access `/configuration` without extra key, view histories.
- **Change it:**
  ```bash
  ADMIN_USERNAME=myadmin ADMIN_PASSWORD='S3cure!' docker compose up --build
  # or after login: /users/update, /users/change-password, or /configuration
  # force reset on next boot: ADMIN_FORCE_RESET=true docker compose up -d
  ```
- **Normal users:** `Sign Up` at `/users/signup` (role `user`, admin promotes in `/configuration`).
- **Without Docker:** `uv sync && uv run python seed.py && uv run python app.py` → same admin on SQLite `instance/routeplanner.db`.

### Env Highlights
| Var | Default | Note |
|---|---|---|
| `PORT` | `8003` | `8003:8003` exposed |
| `DATABASE_URL` | `mysql+pymysql://route_user:route_password@db:3306/routeplanner` | fallback `sqlite:///routeplanner.db` fixes `RuntimeError: Either 'SQLALCHEMY_DATABASE_URI'...` |
| `ENCRYPTION_KEY` | `0A1glB0r_8tPpo8k9eeWZW3TXvkvCPpw1ZgBmsV5D6s=` | valid Fernet 44-char (old `dev_encryption_key` was invalid) |
| `SECRET_KEY` | `dev-secret-key...` | change in prod |
| `ADMIN_*` | `admin/Admin123!` | demo |

### Verify
```bash
docker compose ps
curl -f http://localhost:8003/ && echo OK
docker compose logs web | tail -20
```

### Key Fixes in This Deployment
- `config.py:8-14` safe defaults → no crash without `.env`
- `entrypoint.sh:82-112` wait MySQL (`pymysql`), `flask db upgrade` → `db.create_all()` (covers missing `locations`/`route_history` migrations) → `flask db stamp head` → seed admin → `gunicorn`
- `Dockerfile:32-50` `EXPOSE 8003`, `HEALTHCHECK`, `ENTRYPOINT`
- `docker-compose.yml` / `docker-compose.prod.yml` → `mysql:8.0` with `healthcheck: mysqladmin ping`, `8003:8003`

See **[README.en.md](README.en.md)** for full English guide (features, verification, production, troubleshooting, manual local run).

![Dashboard and Map](docs/dashboard.png)
![Graph Visualization](docs/routes.png)
| User Management | Trip History |
| :---: | :---: |
| ![User Management](docs/manageusers.png) | ![Trip History](docs/TripHistory.png) |
![User Configuration](docs/userconfig.png)

---

<a id="espanol-quick"></a>
## 🇪🇸 Español — Despliegue Rápido

### Stack
Python 3.13 / Flask 3 / SQLAlchemy / Flask-Migrate / MySQL 8.0 (`pymysql`) + fallback SQLite / NetworkX / Leaflet / fpdf2 / gunicorn / uv / Docker

### Despliegue en 1 minuto
```bash
git clone <repo> RoutePlanner && cd RoutePlanner
cp .env.example .env   # edita secretos si quieres
docker compose up --build -d
docker compose logs -f web  # espera "Seeding default admin user..." + "Using gunicorn"
open http://localhost:8003
# MySQL: localhost:3306  route_user/route_password  BD routeplanner
```

### Producción
```bash
cp .env.example .env  # define SECRET_KEY, ENCRYPTION_KEY (Fernet), ADMIN_PASSWORD, MYSQL_PASSWORD
docker compose -f docker-compose.prod.yml up --build -d
```

### Usuario Demo Admin (auto-creado, idempotente vía `entrypoint.sh` + `seed.py`)
- **URL:** http://localhost:8003 → `Sign In`
- **Usuario:** `admin` / **Contraseña:** `Admin123!` / **Email:** `admin@routeplanner.local` / **Rol:** `ADMIN` (todos los permisos)
- **Qué puede hacer admin:** gestionar usuarios/roles, borrar ubicaciones en lote, resetear contraseñas, acceder a `/configuration` sin clave extra, ver historiales.
- **Cambiarlo:**
  ```bash
  ADMIN_USERNAME=miadmin ADMIN_PASSWORD='S3guro!' docker compose up --build
  # o tras login: /users/update, /users/change-password, o /configuration
  # forzar reset en próximo arranque: ADMIN_FORCE_RESET=true docker compose up -d
  ```
- **Usuarios normales:** `Sign Up` en `/users/signup` (rol `user`, el admin los promueve en `/configuration`).
- **Sin Docker:** `uv sync && uv run python seed.py && uv run python app.py` → mismo admin en SQLite `instance/routeplanner.db`.

### Variables Clave
| Var | Default | Nota |
|---|---|---|
| `PORT` | `8003` | expuesto `8003:8003` |
| `DATABASE_URL` | `mysql+pymysql://route_user:route_password@db:3306/routeplanner` | fallback `sqlite:///routeplanner.db` arregla `RuntimeError` |
| `ENCRYPTION_KEY` | `0A1glB0r_8tPpo8k9eeWZW3TXvkvCPpw1ZgBmsV5D6s=` | Fernet válido 44 chars (antes `dev_encryption_key` inválido) |
| `SECRET_KEY` | `dev-secret-key...` | cambiar en prod |
| `ADMIN_*` | `admin/Admin123!` | demo |

### Verificar
```bash
docker compose ps
curl -f http://localhost:8003/ && echo OK
docker compose logs web | tail -20
```

### Fixes Clave de Este Despliegue
- `config.py:8-14` defaults seguros → no falla sin `.env`
- `entrypoint.sh:82-112` espera MySQL, `flask db upgrade` → `db.create_all()` (cubre migraciones faltantes `locations`/`route_history`) → `flask db stamp head` → seed admin → `gunicorn`
- `Dockerfile:32-50` `EXPOSE 8003`, `HEALTHCHECK`, `ENTRYPOINT`
- `docker-compose.yml` / `docker-compose.prod.yml` → `mysql:8.0` con `healthcheck`, `8003:8003`

Ver **[README.es.md](README.es.md)** para guía completa en español (características, verificación, producción, troubleshooting, ejecución manual).

---

## 📚 More Docs / Más Documentación

- **User guides:** [README.en.md](README.en.md) (EN) | [README.es.md](README.es.md) (ES)
- **Developer guide (bilingual):** [DEVELOPMENT.md](DEVELOPMENT.md) — architecture, `entrypoint.sh`, migrations, `seed.py`, demo user deep-dive, contributing
- **Technical report:** [docs/technical_report.md](docs/technical_report.md) — MVC, MySQL, NetworkX/Dijkstra, AdminLTE/Leaflet, PDF export
- **Env template:** [.env.example](.env.example) — copy to `.env` and edit
- **Compose files:** [docker-compose.yml](docker-compose.yml) (dev) | [docker-compose.prod.yml](docker-compose.prod.yml) (prod) — both `8003:8003` + MySQL 8.0

### Project Structure / Estructura
```
RoutePlanner/
├── app.py / config.py / entrypoint.sh / seed.py
├── Dockerfile (8003, HEALTHCHECK, gunicorn) 
├── docker-compose.yml / docker-compose.prod.yml (MySQL 8.0)
├── .env.example
├── models/ (User, Location, API_Storage, RouteHistory)
├── controllers/ / routers/ (Blueprints) / utils/ (auth, encryption)
├── templates/ / static/ (Jinja2, AdminLTE, Leaflet)
├── migrations/ (Alembic)
└── test/ (verify_*.py)
```

---

**Maintained by Jorge Arguello — RoutePlanner 2026**  
Issues? https://github.com/anomalyco/opencode (using Muse Spark)
