# RoutePlanner — Español

![Página principal](docs/home.png)

Gestiona ubicaciones y calcula rutas óptimas con **Dijkstra** (NetworkX + Haversine), mapas **Leaflet** y reportes **PDF**.

> **Imagen Docker única.** SQLite por defecto (sin BD externa). MySQL/PostgreSQL opcional vía `DATABASE_URL`. Demo auto-creada y **visible en la web**.

---

> [!IMPORTANT]
> **Demo — la verás al entrar al sitio**
> - **Home** banner: *“Try the demo — admin / Admin123! → Sign in as admin”*
> - **Login** (`/users/signin`): caja azul *“Demo: admin / Admin123! [fill]”*
> - **Directo:** http://localhost:8003/users/signin — **admin / Admin123!**

---

## Inicio rápido — 1 comando

**Requisitos:** Docker, Docker Compose v2, Git

```bash
git clone <repo> RoutePlanner && cd RoutePlanner
docker compose up --build -d
```

Abre http://localhost:8003 — haz clic en **Sign in as admin** o en **Sign In** pulsa **[fill]**.

```bash
docker compose logs -f web  # espera "DEMO READY: admin / Admin123!"
```

**Sin compose:**
```bash
docker build -t route-planner .
docker run -d -p 8003:8003 --name route-planner -v routeplanner_data:/app/instance route-planner
```

**Parar:**
```bash
docker compose down        # mantiene BD
docker compose down -v     # borra BD
```

---

## Cuenta demo

| | Valor |
|---|---|
| URL | `/users/signin` |
| Usuario | `admin` |
| Contraseña | `Admin123!` |
| Email | `admin@routeplanner.local` |
| Rol | `ADMIN` |

Permisos: gestionar usuarios/roles, borrar ubicaciones, resetear contraseñas, ver historial. Usuarios normales se registran en `/users/signup` (el admin los promueve).

**Cambiar demo:**
```bash
ADMIN_USERNAME=miadmin ADMIN_PASSWORD='S3guro!' docker compose up --build -d
ADMIN_FORCE_RESET=true docker compose up -d
# o dentro de la app: /users/update, /users/change-password
```

---

## Características

- **Leaflet** mapa interactivo — marcadores, popups
- **Ruteo:** Origen / Destino / Intermedio opcional → Dijkstra donde aristas = km Haversine
- **Exportar PDF** `/graphs/export_pdf` — captura mapa + grafo + distancia/ETA

![Dashboard](docs/dashboard.png)
![Graph](docs/routes.png)
| Usuarios | Historial |
|---|---|
| ![Users](docs/manageusers.png) | ![History](docs/TripHistory.png) |

---

## Stack

- Backend: Python 3.13, Flask 3, Flask-SQLAlchemy, Flask-Migrate
- BD: **SQLite por defecto** (`instance/routeplanner.db`, volumen `sqlite_data`). MySQL/Postgres opcional — drivers `pymysql` + `psycopg2-binary` incluidos
- Frontend: Bootstrap 5 / AdminLTE, Leaflet, Jinja2
- Grafo: NetworkX, matplotlib — PDF: fpdf2 — Server: gunicorn — Tooling: `uv`, Docker

---

## BD externa (opcional)

Sin rebuild — drivers ya están en la imagen.

```bash
# MySQL
DATABASE_URL=mysql+pymysql://user:pass@host:3306/routeplanner docker compose up -d
# Postgres
DATABASE_URL=postgresql+psycopg2://user:pass@host:5432/routeplanner docker compose up -d
# vía .env: edita DATABASE_URL luego docker compose up -d
# docker run:
docker run -d -p 8003:8003 -e DATABASE_URL=mysql+pymysql://user:pass@host:3306/routeplanner route-planner
```

Deja `DATABASE_URL` vacío para SQLite (`config.py:16` fallback).

---

## Variables de entorno

| Var | Default | Nota |
|---|---|---|
| `PORT` | `8003` | `8003:8003` |
| `DATABASE_URL` | *(vacío)* → `sqlite:///routeplanner.db` | `mysql+pymysql://...` o `postgresql+psycopg2://...` |
| `SECRET_KEY` | `dev-secret-key...` | Cambiar en prod |
| `ENCRYPTION_KEY` | `0A1glB0r_8tPpo8k9eeWZW3TXvkvCPpw1ZgBmsV5D6s=` | Fernet 44 chars |
| `ADMIN_USERNAME` / `ADMIN_PASSWORD` | `admin` / `Admin123!` | Demo — también visible en la web |

---

## Cómo funciona

`entrypoint.sh` (~80 líneas): `mkdir -p instance` → espera **solo si** `DATABASE_URL` es MySQL/Postgres (si no instantáneo) → `flask db upgrade` → `db.create_all()` → `stamp head` → seed admin → `gunicorn`.

`Dockerfile`: `python:3.13-slim` + `curl` + `uv sync`, `EXPOSE 8003`, `HEALTHCHECK`.

`docker-compose.yml`: un solo servicio `web`, `sqlite_data:/app/instance`.

---

## Verificar

```bash
curl http://localhost:8003/health | python3 -m json.tool
curl http://localhost:8003/health/demo | python3 -m json.tool
docker compose logs web | grep "DEMO READY"
```

---

## Producción

```bash
cp .env.example .env  # define SECRET_KEY, ENCRYPTION_KEY, ADMIN_PASSWORD
docker compose -f docker-compose.prod.yml up --build -d  # restart: always
```

Para BD externa en prod define `DATABASE_URL` en `.env` o secretos. Detrás de nginx/traefik → redirige `8003`, activa TLS.

---

## Solución de problemas

| Síntoma | Solución |
|---|---|
| Login `admin` falla | `curl /health/demo` → `hint`. Prueba `ADMIN_FORCE_RESET=true docker compose up -d` |
| BD externa connection refused | Revisa `DATABASE_URL` alcanzable (`host.docker.internal` para host), `docker logs web` |
| Puerto `8003` ocupado | `lsof -i :8003` o cambia `ports: "8003:8003"` + `PORT` |
| Cambiar SQLite → MySQL/PG | Define `DATABASE_URL` y `docker compose up -d --force-recreate` |

---

## Ejecución local sin Docker

```bash
uv sync
uv run python seed.py
uv run python app.py   # http://localhost:8003
```

---

## Estructura

```
├── app.py / config.py / entrypoint.sh / seed.py
├── Dockerfile (imagen única)
├── docker-compose.yml (un solo servicio)
├── docker-compose.prod.yml
├── models/ controllers/ routers/ utils/
├── templates/ static/ (banner + login demo box)
├── migrations/
└── test/
```

Ver `DEVELOPMENT.md` para guía dev.

**Mantenido por Jorge Arguello — 2026**
