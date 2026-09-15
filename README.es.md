# RoutePlanner — Español

![Página principal](docs/home.png)

**RoutePlanner** es una aplicación web integral para gestionar ubicaciones geográficas y calcular rutas óptimas. Usa **Dijkstra** (`NetworkX`) con distancia Haversine, mapas interactivos (`Leaflet.js`) y reportes PDF profesionales (`fpdf2` + `html2canvas`).

> **Despliegue 2026 — Imagen Única Docker:** `SQLite` por defecto (sin dependencias externas, persistido con volumen). **MySQL/PostgreSQL** opcional vía `DATABASE_URL` (drivers `pymysql` + `psycopg2-binary` incluidos). `gunicorn` en **`8003`**.

---

## Contenido
- [Características](#características)
- [Stack Tecnológico](#stack-tecnológico)
- [Inicio Rápido (Imagen Única)](#inicio-rápido-imagen-única)
- [Base de Datos Externa (MySQL/PostgreSQL)](#base-de-datos-externa-mysqlpostgresql)
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
- **BD:** **SQLite por defecto** (`sqlite:///routeplanner.db` → `instance/routeplanner.db`, volumen `sqlite_data`). **MySQL/PostgreSQL opcional** vía `DATABASE_URL` — drivers `pymysql` + `psycopg2-binary` **incluidos en la imagen**, sin rebuild. Solo define `DATABASE_URL` como `mysql+pymysql://...` o `postgresql+psycopg2://...`.
- **Frontend:** Bootstrap 5 / AdminLTE, Leaflet.js, Jinja2
- **Grafo:** NetworkX, matplotlib
- **PDF:** fpdf2, html2canvas
- **Servidor:** gunicorn (prod) / Flask dev (local)
- **Tooling:** `uv`, Docker, docker-compose

---

## Inicio Rápido (Imagen Única)

### Requisitos
- Docker >= 20.10 y Docker Compose v2 (`docker compose version`)
- Git
- (Opcional) `uv` para dev local sin Docker

### 1. Clonar
```bash
git clone <url-del-repo> RoutePlanner
cd RoutePlanner
```

### 2. Configurar env (opcional para SQLite)
```bash
cp .env.example .env
# Para SQLite deja DATABASE_URL vacío (default).
# Para BD externa, define DATABASE_URL en .env (ver siguiente sección).
# Mínimo en prod: SECRET_KEY, ENCRYPTION_KEY.
```

### 3. Ejecutar — SQLite (sin BD externa)
```bash
# Opción A: docker run — más simple, solo imagen
docker build -t route-planner .
docker run -d -p 8003:8003 --name route-planner -v routeplanner_data:/app/instance route-planner

# Opción B: docker compose — un solo servicio + volumen
docker compose up --build -d
docker compose logs -f web  # espera "RoutePlanner READY" + "DEMO READY"
```
- **App:** http://localhost:8003
- **Archivo BD:** volumen `sqlite_data` → `/app/instance/routeplanner.db` (persistido)

### 4. Parar / Resetear
```bash
docker compose down        # mantiene datos (volumen sqlite_data)
docker compose down -v     # borra también la BD (inicio limpio)
# para docker run:
docker rm -f route-planner
docker volume rm routeplanner_data
```

---

## Base de Datos Externa (MySQL/PostgreSQL)

Drivers ya **incluidos en la imagen** (`pyproject.toml:15-16` `pymysql`, `psycopg2-binary`). El contenedor detecta `DATABASE_URL` y espera la BD antes de migrar.

```bash
# MySQL externo (RDS, mysql local, o contenedor aparte)
DATABASE_URL=mysql+pymysql://route_user:route_password@host:3306/routeplanner docker compose up -d
# PostgreSQL externo
DATABASE_URL=postgresql+psycopg2://route_user:route_password@host:5432/routeplanner docker compose up -d

# Vía .env (persistente)
# edita .env: DATABASE_URL=mysql+pymysql://...
docker compose up -d --build

# Directo con docker run y BD externa
docker run -d -p 8003:8003 \
  -e DATABASE_URL=mysql+pymysql://user:pass@host:3306/routeplanner \
  -e SECRET_KEY=tu-secreto \
  route-planner

# Verificar BD externa en uso:
curl http://localhost:8003/health | python3 -m json.tool  # db: ok
docker logs route-planner | grep "Waiting for MySQL"
```

> **Fallback:** Si `DATABASE_URL` vacío/no definido, `config.py:15` usa `sqlite:///routeplanner.db` automáticamente.

---

## Variables de Entorno

| Variable | Default (Dockerfile / .env.example) | Descripción |
|---|---|---|
| `HOST` | `0.0.0.0` | bind Flask/gunicorn |
| `PORT` | `8003` | **Expuesto** `8003:8003` |
| `DATABASE_URL` | *(vacío)* → `sqlite:///routeplanner.db` | URI SQLAlchemy. **SQLite default**. Usa `mysql+pymysql://...` o `postgresql+psycopg2://...` para BD externa (drivers incluidos) |
| `SECRET_KEY` | `dev-secret-key-change-in-production` | Sesión Flask. **Cambiar en prod** |
| `ENCRYPTION_KEY` | `0A1glB0r_8tPpo8k9eeWZW3TXvkvCPpw1ZgBmsV5D6s=` | Fernet 44 chars. Debe ser Fernet válido |
| `CONFIG_ACCESS_KEY` | `admin` | Clave para `/configuration` si no eres admin |
| `ADMIN_USERNAME` | `admin` | Login demo admin |
| `ADMIN_EMAIL` | `admin@routeplanner.local` | Email demo |
| `ADMIN_PASSWORD` | `Admin123!` | **Cambiar tras primer login** o por env |
| `ADMIN_FORCE_RESET` | `false` | Si `true`, resetea password admin en cada arranque |

> `config.py` ahora tiene defaults seguros.

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
  # opción B: docker run
  docker run -d -p 8003:8003 -e ADMIN_USERNAME=miadmin -e ADMIN_PASSWORD='S3guro!' route-planner
  # opción C: por UI tras login -> /users/update & /users/change-password
  # opción D: forzar reset en próximo boot
  ADMIN_FORCE_RESET=true docker compose up -d
  ```
- **Crear usuarios normales:** página `Sign Up` (`/users/signup`) → rol `user` por defecto.

**¿Cómo sé si el demo está corriendo?**
- **Durante el deploy:** `entrypoint.sh` imprime banner antes de gunicorn:
  ```
  >> Seeding admin...
    created admin: admin
    ✅ DEMO READY: 'admin' / 'Admin123!' -> http://localhost:8003/users/signin
  ========================================
    RoutePlanner READY
    App:   http://localhost:8003
  ========================================
  ```
- **Después del deploy:**
  ```bash
  docker compose logs web | grep -A2 "DEMO READY"
  curl -s http://localhost:8003/health/demo | python3 -m json.tool
  curl -s http://localhost:8003/health | python3 -m json.tool
  docker compose exec web python seed.py  # re-seed manual
  ```

**Sin Docker** (fallback SQLite) también tienes admin:
```bash
uv sync
# asegúrate que DATABASE_URL esté vacío para usar SQLite
uv run python seed.py
uv run python app.py           # http://localhost:8003
```

---

## Cómo Funciona el Despliegue (entrypoint)

`entrypoint.sh` (definido como `ENTRYPOINT` en `Dockerfile`) minimalista (~80 líneas):

1. **Espera BD (condicional):** Si `DATABASE_URL` contiene `mysql` → bucle `pymysql` 30×2s; si `postgres` → `psycopg2`; si no **salta** (SQLite instantáneo).
2. **Migraciones:** `flask db upgrade` (Alembic). Avisa pero continúa si faltan.
3. **Asegura tablas:** `python -c "db.create_all()"` tras importar todos los modelos.
4. **Stamp:** `flask db stamp head`.
5. **Seed:** creación admin idempotente (`ADMIN_FORCE_RESET` opcional).
6. **Arranque:** `gunicorn --bind 0.0.0.0:8003 --workers 2 --threads 4 app:app`.

`Dockerfile`:
- `python:3.13-slim` + `curl` + `uv sync --frozen`, `mkdir -p /app/instance`, `EXPOSE 8003`, `HEALTHCHECK curl`.

`docker-compose.yml` (un solo servicio):
- `web: build: ., ports: 8003:8003, volumes: sqlite_data:/app/instance, env_file: .env`

---

## Verificación

```bash
docker compose ps
docker compose logs web  # debe terminar en "DEMO READY" + "RoutePlanner READY" + "Starting gunicorn"
curl -f http://localhost:8003/health && echo "APP OK"
curl -s http://localhost:8003/health/demo | python3 -m json.tool
# test login
curl -c jar -b jar -L http://localhost:8003/users/signin -d "username=admin&password=Admin123!"
```

Log esperado `entrypoint.sh`:
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

## Despliegue en Producción

```bash
cp .env.example .env
# edita .env: SECRET_KEY, ENCRYPTION_KEY (genera: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"), ADMIN_PASSWORD
docker compose -f docker-compose.prod.yml up --build -d
docker compose -f docker-compose.prod.yml logs -f web
```

Notas:
- `docker-compose.prod.yml` misma imagen única, `restart: always`, volumen `sqlite_data`.
- Para usar imagen prebuilt: descomenta `image: jorgearguello/route-planner:1.0` y comenta `build: .`.
- Para BD externa en prod, define `DATABASE_URL=mysql+pymysql://...` o `postgresql+psycopg2://...` en `.env` o secretos del orquestador.
- Detrás de proxy inverso (nginx/traefik) redirige a `8003`, activa TLS.
- Cambia `ADMIN_PASSWORD` inmediatamente tras primer login.

---

## Solución de Problemas

| Síntoma | Causa / Solución |
|---|---|
| `RuntimeError: Either 'SQLALCHEMY_DATABASE_URI'...` | Código viejo sin fallback. Arreglado en `config.py`. |
| `ValueError: ENCRYPTION_KEY must be set` / Fernet inválido | Viejo `dev_encryption_key` no es Fernet válido. Ahora default funciona o genera uno real. |
| `table users already exists` en `flask db upgrade` | BD creada vía `create_all` sin stamp. EntryPoint hace `db.create_all()` + `stamp head`. Ignorable. |
| BD externa MySQL/Postgres no lista / connection refused | `entrypoint.sh` espera 60s solo si `DATABASE_URL` coincide. Revisa `docker logs web`, que `DATABASE_URL` sea alcanzable (para host local usa `host.docker.internal`). |
| Login `admin` falla / `demo_ready:false` | `curl http://localhost:8003/health/demo` muestra `hint`. Prueba `ADMIN_FORCE_RESET=true docker compose up -d` o `docker compose exec web python seed.py`. |
| Puerto `8003` ocupado | Cambia `ports: "8003:8003"` y `PORT` juntos, o `lsof -i :8003` / `docker ps`. |
| Cambiar de SQLite a MySQL/Postgres después | Solo define `DATABASE_URL` y recrea: `DATABASE_URL=... docker compose up -d --force-recreate`. SQLite viejo queda en volumen `sqlite_data` (backup: `docker run --rm -v route-planner_sqlite_data:/data -v $(pwd):/backup ubuntu tar czf /backup/sqlite.tgz /data`). |

---

## Ejecución Local Manual (sin Docker)

```bash
# requiere Python 3.13 + uv
uv sync
cp .env.example .env  # o dejar DATABASE_URL vacío -> fallback SQLite
uv run python seed.py
uv run python app.py          # http://localhost:8003 (o gunicorn)
# o con BD externa local:
DATABASE_URL=mysql+pymysql://user:pass@127.0.0.1:3306/routeplanner uv run python app.py
DATABASE_URL=postgresql+psycopg2://user:pass@127.0.0.1:5432/routeplanner uv run python app.py
```

Fallback `config.py` → no necesitas `DATABASE_URL` local; se crea `instance/routeplanner.db` (ignorado).

---

## Estructura del Proyecto
```
RoutePlanner/
├── app.py                 # Flask app, init_db, register_routes, run
├── config.py              # Config con defaults + override DATABASE_URL
├── entrypoint.sh          # wait condicional, migrate, create_all, seed, gunicorn
├── seed.py                # script seed standalone
├── Dockerfile             # imagen única: python:3.13-slim, uv, 8003, HEALTHCHECK
├── docker-compose.yml     # un solo servicio + volumen sqlite_data
├── docker-compose.prod.yml# prod: misma imagen, restart: always
├── .env.example           # plantilla (DATABASE_URL vacío = SQLite)
├── pyproject.toml / uv.lock  # incluye pymysql + psycopg2-binary
├── models/                # User, Location, API_Storage, RouteHistory, db/migrate
├── controllers/           # lógica negocio
├── routers/               # Blueprint endpoints
├── utils/                 # auth, encryption
├── templates/ / static/   # Jinja2 + AdminLTE + Leaflet
├── migrations/            # versiones Alembic
└── test/                  # scripts verify_*
```

Ver `DEVELOPMENT.md` para guía profunda.

---

**Mantenido por Jorge Arguello — RoutePlanner 2026**
