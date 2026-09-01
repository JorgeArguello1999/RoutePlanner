# RoutePlanner — Español

![Página principal](docs/home.png)

**RoutePlanner** es una aplicación web integral para gestionar ubicaciones geográficas y calcular rutas óptimas. Usa **Dijkstra** (`NetworkX`) con distancia Haversine, mapas interactivos (`Leaflet.js`) y reportes PDF profesionales (`fpdf2` + `html2canvas`).

> **Despliegue 2026:** Docker + `MySQL 8.0`, migraciones y seeding automáticos, `gunicorn` en **`8003`** interno y externo.

---

## Contenido
- [Características](#características)
- [Stack Tecnológico](#stack-tecnológico)
- [Inicio Rápido (Docker)](#inicio-rápido-docker)
- [Variables de Entorno](#variables-de-entorno)
- [Usuario Demo / Admin por Defecto](#usuario-demo--admin-por-defecto)
- [Cómo Funciona el Despliegue (entrypoint)](#cómo-funciona-el-despliegue-entrypoint)
- [Verificación](#verificación)
- [Despliegue en Producción](#despliegue-en-producción)
- [Solución de Problemas](#solución-de-problemas)
- [Ejecución Local Manual (sin Docker)](#ejecución-local-manual-sin-docker)
- [Estructura del Proyecto](#estructura-del-proyecto)

---

## Características

### 🗺️ Mapas Interactivos y Ruteo
- **Leaflet:** mapa interactivo, marcadores, popups.
- **Planificación:** selecciona Origen / Destino / Intermedio opcional.
- **Dijkstra** sobre grafo dinámico (nodos = `Location` guardadas, aristas = km Haversine).

![Dashboard y mapa](docs/dashboard.png)

### 📊 Reportes Avanzados
- **Exportar PDF** (`/graphs/export_pdf`): captura del mapa (`html2canvas`), grafo esquemático (`NetworkX`+`matplotlib`), métricas (distancia, ETA a 60 km/h), coordenadas.
![Visualización de grafo](docs/routes.png)

### 🔒 Gestión de Usuarios y Ubicaciones
- **Auth segura:** hash `werkzeug.security`, sesión, `UserRole` (`admin`/`moderator`/`user`).
- **CRUD Ubicaciones:** `GET/POST /locations/`, `PUT/DELETE /locations/<id>` (requiere login).
- **Historial:** persistencia `RouteHistory`.
| Gestión de usuarios | Historial de viajes |
| :---: | :---: |
| ![User Management](docs/manageusers.png) | ![Trip History](docs/TripHistory.png) |
![Configuración de usuario](docs/userconfig.png)

---

## Stack Tecnológico
- **Backend:** Python 3.13, Flask 3, Flask-SQLAlchemy, Flask-Migrate (Alembic)
- **BD:** MySQL 8.0 (`pymysql`) en Docker; fallback SQLite (`sqlite:///routeplanner.db`) para dev local sin Docker. Postgres sigue soportado (`psycopg2-binary`) si cambias `DATABASE_URL`.
- **Frontend:** Bootstrap 5 / AdminLTE, Leaflet.js, Jinja2
- **Grafo:** NetworkX, matplotlib
- **PDF:** fpdf2, html2canvas
- **Servidor:** gunicorn 26 (prod) / Flask dev (local)
- **Tooling:** `uv`, Docker, docker-compose

---

## Inicio Rápido (Docker)

### Requisitos
- Docker >= 20.10 y Docker Compose v2 (`docker compose version`)
- Git
- (Opcional) `uv` para dev local sin Docker

### 1. Clonar
```bash
git clone <url-del-repo> RoutePlanner
cd RoutePlanner
```

### 2. Configurar env
```bash
cp .env.example .env
# edita .env para cambiar secretos (recomendado en prod)
# mínimo: SECRET_KEY, ENCRYPTION_KEY, ADMIN_PASSWORD
```

### 3. Ejecutar (desarrollo)
```bash
docker compose up --build
# o en segundo plano:
docker compose up --build -d
docker compose logs -f web
docker compose logs -f db
```
- **App:** http://localhost:8003
- **MySQL:** localhost:3306 (`route_user` / `route_password` → BD `routeplanner`)

### 4. Parar / Resetear
```bash
docker compose down        # mantiene datos (volumen mysql_data)
docker compose down -v     # borra también la BD (inicio limpio)
```

---

## Variables de Entorno

| Variable | Default (Dockerfile / compose) | Descripción |
|---|---|---|
| `HOST` | `0.0.0.0` | bind Flask/gunicorn |
| `PORT` | `8003` | **Expuesto** `8003:8003` (cambia ambos lados si necesitas otro puerto) |
| `DATABASE_URL` | `mysql+pymysql://route_user:route_password@db:3306/routeplanner` | URI SQLAlchemy. Fallback `sqlite:///routeplanner.db` si vacío (arregla `RuntimeError: Either 'SQLALCHEMY_DATABASE_URI'...`) |
| `SECRET_KEY` | `dev-secret-key-change-in-production` | Sesión Flask. **Cambiar en prod** |
| `ENCRYPTION_KEY` | `0A1glB0r_8tPpo8k9eeWZW3TXvkvCPpw1ZgBmsV5D6s=` | Fernet 44 chars. Debe ser Fernet válido (antes `dev_encryption_key` inválido) |
| `CONFIG_ACCESS_KEY` | `admin` | Clave para `/configuration` si no eres admin |
| `ADMIN_USERNAME` | `admin` | Login demo admin |
| `ADMIN_EMAIL` | `admin@routeplanner.local` | Email demo |
| `ADMIN_PASSWORD` | `Admin123!` | **Cambiar tras primer login** o por env |
| `ADMIN_FORCE_RESET` | `false` | Si `true`, resetea password admin en cada arranque |
| `MYSQL_ROOT_PASSWORD` | `rootpassword` | root MySQL |
| `MYSQL_DATABASE` | `routeplanner` |  |
| `MYSQL_USER` | `route_user` | Debe coincidir con `DATABASE_URL` |
| `MYSQL_PASSWORD` | `route_password` | Debe coincidir con `DATABASE_URL` |

> `config.py` ahora tiene defaults seguros, `uv run app.py` sin `.env` ya no falla.

---

## Usuario Demo / Admin por Defecto

El contenedor **crea automáticamente** un admin en cada arranque (`entrypoint.sh` + `seed.py`, idempotente):

- **URL:** http://localhost:8003
- **Ir a:** `Sign In` → usuario `admin` / contraseña `Admin123!`
- **Permisos (UserRole.ADMIN):** gestionar todos los usuarios, cambiar roles (`admin`/`moderator`/`user`), borrar `Location` en lote, resetear contraseñas, acceder a `/configuration` sin clave extra, ver todo el historial.
- **Cambiar credenciales:**
  ```bash
  # opción A: por env antes de arrancar
  ADMIN_USERNAME=miadmin ADMIN_EMAIL=yo@ejemplo.com ADMIN_PASSWORD='S3guro!' docker compose up --build
  # opción B: por UI tras login -> /users/update & /users/change-password
  # opción C: por /configuration (panel admin) -> Update Password
  # opción D: forzar reset en próximo boot
  ADMIN_FORCE_RESET=true docker compose up -d
  ```
- **Crear usuarios normales:** página `Sign Up` (`/users/signup`) → rol `user` por defecto. Un admin los puede promover en `/configuration`.

**¿Cómo sé si el demo está corriendo? (el deploy ahora avisa)**
- **Durante el deploy:** `entrypoint.sh` imprime verificación *antes* de arrancar gunicorn:
  ```
  >> Verifying demo user (AVISO deploy - ¿demo corriendo?)...
    ✅ DEMO USER READY: 'admin' / 'Admin123!' -> http://localhost:8003/users/signin
  ========================================
    RoutePlanner DEPLOY COMPLETE
    App:      http://localhost:8003
    Health:   http://localhost:8003/health
    Demo chk: curl http://localhost:8003/health/demo
    Login:    http://localhost:8003/users/signin
    Demo:     admin / Admin123!
  ========================================
  ```
  Si ves `❌ MISMATCH` o `❌ NOT FOUND`, sigue el hint (ej. `ADMIN_FORCE_RESET=true docker compose up -d`).

- **Después del deploy (runtime):**
  ```bash
  docker compose logs web | grep -A5 "DEMO USER"  # aviso del deploy
  curl -s http://localhost:8003/health/demo | python3 -m json.tool
  # {"demo_ready": true/false, "db": "ok", "hint": "Login en /users/signin..."}
  curl -s http://localhost:8003/health | python3 -m json.tool
  docker compose exec web python seed.py  # re-seed manual si falta demo
  ```

**Sin Docker** (fallback SQLite) también tienes admin:
```bash
uv sync
# asegúrate que DATABASE_URL esté vacío (o unset) para usar SQLite: deja .env DATABASE_URL en blanco
uv run python seed.py          # debe decir [seed] Created / already exists
DATABASE_URL= uv run python -c "from app import app; from models.users import User; with app.app_context(): u=User.query.filter_by(username='admin').first(); print(u.check_password('Admin123!'))" # -> True
uv run python app.py           # http://localhost:8003
# check demo: curl http://localhost:8003/health/demo | grep demo_ready
```

---

## Cómo Funciona el Despliegue (entrypoint)

`entrypoint.sh` (definido como `ENTRYPOINT` en `Dockerfile`) corrige bugs previos:

1. **Espera BD:** parsea `DATABASE_URL`, bucle `pymysql` 60×2s (o `psycopg2` para Postgres, o salta para SQLite).
2. **Migraciones:** `flask db upgrade` (Alembic). Si faltan migraciones (ej. `locations`/`route_history` aún no en `migrations/versions/`), avisa pero continúa.
3. **Asegura tablas:** `python -c "db.create_all()"` tras importar todos los modelos — garantiza tablas aunque migraciones incompletas (bug anterior).
4. **Stamp:** `flask db stamp head` para alinear `alembic_version`.
5. **Seed:** creación admin idempotente (busca por `username` luego `email`, promueve si hace falta).
6. **Arranque:** `gunicorn --bind 0.0.0.0:8003 --workers 2 --threads 4 app:app` (fallback `uv run python app.py`).

`Dockerfile` ahora:
- `EXPOSE 8003`, `ENV PORT=8003 HOST=0.0.0.0`, `HEALTHCHECK curl -f http://localhost:${PORT}/`
- `uv sync --frozen --no-cache --system` + `chmod +x entrypoint.sh`

`docker-compose.yml` (dev) y `docker-compose.prod.yml` (prod):
- `image: mysql:8.0` con `healthcheck: mysqladmin ping`, `volumes: mysql_data:/var/lib/mysql`, `ports: 3306:3306`
- `web: 8003:8003`, `depends_on: db: condition: service_healthy`

---

## Verificación (el deploy te avisa)

```bash
docker compose ps
docker compose logs web  # debe terminar en "DEMO USER READY" + "DEPLOY COMPLETE" + "Using gunicorn"
curl -f http://localhost:8003/health && echo "APP OK"
curl -s http://localhost:8003/health/demo | python3 -m json.tool  # demo_ready + hint
docker compose logs web | grep -E "DEMO USER|DEPLOY COMPLETE|HEALTH"
# test login
curl -c jar -b jar -L http://localhost:8003/users/signin -d "username=admin&password=Admin123!"
```

Log esperado `entrypoint.sh` (ahora con aviso demo):
```
=== RoutePlanner Entrypoint ===
>> Waiting for MySQL to be ready...
  MySQL at db:3306/routeplanner is ready!
>> Running migrations...
>> Ensuring all tables exist...
>> Seeding default admin user...
  Successfully created admin user: admin / admin@routeplanner.local
>> Verifying demo user (AVISO deploy - ¿demo corriendo?)...
  ✅ DEMO USER READY: 'admin' / 'Admin123!' -> http://localhost:8003/users/signin
========================================
  RoutePlanner DEPLOY COMPLETE
  App:      http://localhost:8003
  Health:   http://localhost:8003/health
  Demo:     admin / Admin123!
========================================
>> Starting application on 0.0.0.0:8003
  Using gunicorn
```
Si ves `❌ DEMO USER PASSWORD MISMATCH` → `ADMIN_FORCE_RESET=true docker compose up -d` y luego `curl /health/demo`.

---

## Despliegue en Producción

```bash
cp .env.example .env
# edita .env: SECRET_KEY, ENCRYPTION_KEY (genera: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"), ADMIN_PASSWORD, MYSQL_PASSWORD, etc.
docker compose -f docker-compose.prod.yml up --build -d
docker compose -f docker-compose.prod.yml logs -f web
```

Notas:
- `docker-compose.prod.yml` tiene `restart: always` y volumen separado `route-planner-prod_mysql_data`.
- Para usar imagen prebuilt: descomenta `image: jorgearguello/route-planner:1.0` y comenta `build: .`.
- Detrás de proxy inverso (nginx/traefik) redirige a `8003`, activa TLS.
- Cambia `ADMIN_PASSWORD` inmediatamente tras primer login.

---

## Solución de Problemas

| Síntoma | Causa / Solución |
|---|---|
| `RuntimeError: Either 'SQLALCHEMY_DATABASE_URI'...` | Código viejo sin fallback. Arreglado en `config.py`. Asegura `DATABASE_URL` o usa fallback SQLite. `docker compose` ya lo setea. |
| `ValueError: ENCRYPTION_KEY must be set` / Fernet inválido | Viejo `dev_encryption_key` no es Fernet 44 chars. Ahora default `0A1glB0r_8tPpo8k9eeWZW3TXvkvCPpw1ZgBmsV5D6s=` funciona, o genera uno real con `Fernet.generate_key()`. |
| `table users already exists` en `flask db upgrade` | BD creada vía `create_all` sin stamp Alembic. Arreglado: entrypoint hace `db.create_all()` + `flask db stamp head`. Ignorable. |
| MySQL no listo / `pymysql` connection refused | `entrypoint.sh` espera 120s. Revisa `docker compose logs db`, que `MYSQL_USER`/`MYSQL_PASSWORD` coincidan con `DATABASE_URL`. `docker compose down -v` para BD limpia si cambiaste credenciales. |
| Login `admin` falla / `demo_ready:false` | `curl http://localhost:8003/health/demo` muestra `hint`. `docker compose logs web \| grep DEMO` muestra `MISMATCH/NOT FOUND`. Prueba `ADMIN_FORCE_RESET=true docker compose up -d` o `docker compose exec web python seed.py` o `DATABASE_URL= uv run python seed.py` para SQLite local. Revisa `DATABASE_URL` en `.env` — para local sin Docker deja `DATABASE_URL=` vacío. |
| Puerto `8003` ocupado | Cambia `ports: "8003:8003"` y `PORT` juntos, o `lsof -i :8003` / `docker ps`. |

---

## Ejecución Local Manual (sin Docker)

```bash
# requiere Python 3.13 + uv
uv sync
cp .env.example .env  # o dejar vacío -> fallback SQLite
uv run python seed.py
uv run python app.py          # http://localhost:8003 (o gunicorn)
# o
uv run gunicorn --bind 127.0.0.1:8003 app:app
```

Fallback `config.py` → no necesitas `DATABASE_URL` local; se crea `instance/routeplanner.db` (ignorado por `.dockerignore`/`.gitignore`).

---

## Estructura del Proyecto
```
RoutePlanner/
├── app.py                 # Flask app, init_db, register_routes, run
├── config.py              # Config con defaults seguros
├── entrypoint.sh          # wait DB, migrate, create_all, seed admin, gunicorn
├── seed.py                # script seed standalone
├── Dockerfile             # python:3.13-slim, uv, 8003, HEALTHCHECK, ENTRYPOINT
├── docker-compose.yml     # dev: MySQL 8.0, 8003:8003, volumen mysql_data
├── docker-compose.prod.yml# prod: restart always, env prod
├── .env.example           # plantilla
├── pyproject.toml / uv.lock
├── models/                # User, Location, API_Storage, RouteHistory, db/migrate
├── controllers/           # lógica negocio
├── routers/               # Blueprint endpoints
├── utils/                 # auth, encryption
├── templates/ / static/   # Jinja2 + AdminLTE + Leaflet
├── migrations/            # versiones Alembic
└── test/                  # scripts verify_*
```

Ver `DEVELOPMENT.md` para guía profunda de desarrollador (arquitectura, migraciones, auth, algoritmo de grafo, contribución).

---

**Mantenido por Jorge Arguello — RoutePlanner 2026**
