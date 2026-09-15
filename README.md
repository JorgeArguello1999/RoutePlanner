# RoutePlanner

![Home Page](docs/home.png)

**RoutePlanner** — Manage locations and calculate optimal routes with **Dijkstra** + Haversine, interactive **Leaflet** maps and **PDF** reports.

> **ES** — Gestiona ubicaciones y calcula rutas óptimas con **Dijkstra** + Haversine, mapas **Leaflet** y reportes **PDF**. **Single Docker image: SQLite default + MySQL/PostgreSQL optional via `DATABASE_URL`.**

---

## 🌐 Language / Idioma

| [🇬🇧 English — Full Guide](README.en.md) | [🇪🇸 Español — Guía Completa](README.es.md) | [🛠️ Development / Desarrollo](DEVELOPMENT.md) |
|---|---|---|
| Complete deployment, env vars, external DB | Despliegue completo, variables, BD externa | Architecture, migrations, contributing |

This `README.md` is a **bilingual hub** — brief quick-start below. See links above for full guides.

---

<a id="english-quick"></a>
## 🇬🇧 English — Quick Deploy (Single Image)

### Stack
Python 3.13 / Flask 3 / SQLAlchemy / Flask-Migrate / **SQLite default** (MySQL/PostgreSQL optional via `DATABASE_URL`, drivers `pymysql` + `psycopg2-binary` included) / NetworkX / Leaflet / fpdf2 / gunicorn / uv / Docker

### 1-Minute Deploy — SQLite (no external DB needed)
```bash
git clone <repo> RoutePlanner && cd RoutePlanner
# Option A: docker run (single image, simplest)
docker build -t route-planner .
docker run -d -p 8003:8003 --name route-planner -v routeplanner_data:/app/instance route-planner
# Option B: docker compose (single service)
docker compose up --build -d
docker compose logs -f web  # wait for "Seeding admin..." + "RoutePlanner READY"
open http://localhost:8003
```

### External Database (optional)
Drivers are **included** — just set `DATABASE_URL`:
```bash
# MySQL external
DATABASE_URL=mysql+pymysql://user:pass@host:3306/routeplanner docker compose up -d
# PostgreSQL external
DATABASE_URL=postgresql+psycopg2://user:pass@host:5432/routeplanner docker compose up -d
# Or via .env: edit DATABASE_URL in .env then docker compose up -d
# Docker run example with MySQL:
docker run -d -p 8003:8003 -e DATABASE_URL=mysql+pymysql://user:pass@host:3306/routeplanner route-planner
```
If `DATABASE_URL` is empty (default), `config.py:12` uses `sqlite:///routeplanner.db` (`instance/routeplanner.db` persisted via `sqlite_data` volume).

### Production
```bash
cp .env.example .env  # set SECRET_KEY, ENCRYPTION_KEY (Fernet), ADMIN_PASSWORD
docker compose -f docker-compose.prod.yml up --build -d  # same single image, restart: always
```

### Demo Admin (auto-created, idempotent)
- **URL:** http://localhost:8003 → `Sign In`
- **User:** `admin` / **Pass:** `Admin123!` / **Email:** `admin@routeplanner.local` / **Role:** `ADMIN`
- **Change it:** `ADMIN_USERNAME=myadmin ADMIN_PASSWORD='S3cure!' docker compose up --build` or via UI `/users/update` or `ADMIN_FORCE_RESET=true docker compose up -d`

### Verify
```bash
docker compose ps
curl -f http://localhost:8003/health && echo "APP OK"
curl -s http://localhost:8003/health/demo | python3 -m json.tool  # demo_ready:true/false + hint
docker compose logs web | grep -A2 "DEMO READY"
```

### Key Design — Single Image
- `Dockerfile:1-35` — `python:3.13-slim` + `curl` + `uv sync --frozen`, `EXPOSE 8003`, `HEALTHCHECK curl /health`, `ENTRYPOINT entrypoint.sh` (no `default-mysql-client` needed).
- `entrypoint.sh` — `mkdir -p instance`, wait only if `DATABASE_URL` is MySQL/Postgres (otherwise SQLite instant), `flask db upgrade` → `db.create_all()` → `stamp head` → seed admin → `gunicorn`.
- `docker-compose.yml` — single service `web`, volume `sqlite_data:/app/instance`, `env_file: .env`.

![Dashboard and Map](docs/dashboard.png)
![Graph Visualization](docs/routes.png)
| User Management | Trip History |
| :---: | :---: |
| ![User Management](docs/manageusers.png) | ![Trip History](docs/TripHistory.png) |
![User Configuration](docs/userconfig.png)

---

<a id="espanol-quick"></a>
## 🇪🇸 Español — Despliegue Rápido (Imagen Única)

### Stack
Python 3.13 / Flask 3 / SQLAlchemy / Flask-Migrate / **SQLite por defecto** (MySQL/PostgreSQL opcional vía `DATABASE_URL`, drivers incluidos) / NetworkX / Leaflet / fpdf2 / gunicorn / uv / Docker

### Despliegue en 1 minuto — SQLite (sin BD externa)
```bash
git clone <repo> RoutePlanner && cd RoutePlanner
# Opción A: docker run (imagen única, más simple)
docker build -t route-planner .
docker run -d -p 8003:8003 --name route-planner -v routeplanner_data:/app/instance route-planner
# Opción B: docker compose (un solo servicio)
docker compose up --build -d
docker compose logs -f web  # espera "Seeding admin..." + "RoutePlanner READY"
open http://localhost:8003
```

### Base de Datos Externa (opcional)
Drivers **incluidos** — solo define `DATABASE_URL`:
```bash
# MySQL externo
DATABASE_URL=mysql+pymysql://user:pass@host:3306/routeplanner docker compose up -d
# PostgreSQL externo
DATABASE_URL=postgresql+psycopg2://user:pass@host:5432/routeplanner docker compose up -d
# vía .env: edita DATABASE_URL en .env luego docker compose up -d
```
Si `DATABASE_URL` vacío (default), `config.py:12` usa `sqlite:///routeplanner.db` (`instance/routeplanner.db` persistido con volumen `sqlite_data`).

### Producción
```bash
cp .env.example .env  # define SECRET_KEY, ENCRYPTION_KEY (Fernet), ADMIN_PASSWORD
docker compose -f docker-compose.prod.yml up --build -d  # misma imagen única, restart: always
```

### Usuario Demo Admin
- **URL:** http://localhost:8003 → `Sign In`
- **Usuario:** `admin` / **Contraseña:** `Admin123!` / **Email:** `admin@routeplanner.local` / **Rol:** `ADMIN`
- **Cambiarlo:** `ADMIN_USERNAME=miadmin ADMIN_PASSWORD='S3guro!' docker compose up --build` o `ADMIN_FORCE_RESET=true docker compose up -d`

### Verificar
```bash
docker compose ps
curl -f http://localhost:8003/health && echo "APP OK"
curl -s http://localhost:8003/health/demo | python3 -m json.tool
docker compose logs web | grep -A2 "DEMO READY"
```

### Diseño — Imagen Única
- `Dockerfile:1-35` — `python:3.13-slim` + `uv`, `EXPOSE 8003`, `HEALTHCHECK`, sin `default-mysql-client`.
- `entrypoint.sh` — espera condicional solo si `DATABASE_URL` es MySQL/Postgres, si no SQLite instantáneo.
- `docker-compose.yml` — un solo servicio `web`.

Ver **[README.es.md](README.es.md)** para guía completa.

---

## 📚 More Docs / Más Documentación

- **User guides:** [README.en.md](README.en.md) (EN) | [README.es.md](README.es.md) (ES)
- **Developer guide:** [DEVELOPMENT.md](DEVELOPMENT.md)
- **Technical report:** [docs/technical_report.md](docs/technical_report.md)
- **Env template:** [.env.example](.env.example)
- **Compose files:** [docker-compose.yml](docker-compose.yml) (dev, single service) | [docker-compose.prod.yml](docker-compose.prod.yml) (prod)

### Project Structure / Estructura
```
RoutePlanner/
├── app.py / config.py / entrypoint.sh / seed.py
├── Dockerfile (single image, SQLite default, drivers for MySQL/PG)
├── docker-compose.yml (single service + sqlite_data volume)
├── docker-compose.prod.yml (prod, same image, restart: always)
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
