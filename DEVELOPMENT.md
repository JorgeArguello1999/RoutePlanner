# DEVELOPMENT GUIDE — RoutePlanner

> **Bilingual / Bilingüe:** [English](#english-developer-guide) | [Español](#guía-de-desarrollo-español)

---

<a id="english-developer-guide"></a>
# English — Developer Guide

## 1. Overview
RoutePlanner is an MVC Flask app: `models` (SQLAlchemy), `controllers` (business logic), `routers` (Blueprints), `templates`+`static` (Jinja2/AdminLTE/Leaflet), `utils` (auth/encryption). DB versioning via `Flask-Migrate` (Alembic).

## 2. Architecture

### App bootstrap
- `config.py:8-14` → `Config` with safe defaults (`SECRET_KEY`, `ENCRYPTION_KEY` Fernet-valid, `SQLALCHEMY_DATABASE_URI` fallback to `sqlite:///routeplanner.db`). Fixes `RuntimeError: Either 'SQLALCHEMY_DATABASE_URI'...` seen when running `uv run app.py` without `.env`.
- `app.py:14-20` → `Flask(__name__)`, `app.config.from_object(Config)`, `init_db(app)` (`models/__init__.py:7-18`), `register_routes(app)` (`routers/__init__.py:13-21`).
- `models/__init__.py:7-18` → `db = SQLAlchemy()`, `migrate = Migrate()`, `init_db()` imports models inside `app_context` so Alembic detects them. Previously `db.create_all()` was commented out; now entrypoint restores it as safety net.
- `app.py:31-38` → `if __name__ == "__main__"` runs optional `test.verify_locations.verify()` then `app.run(host, port, debug)` with bool-parsed `DEBUG` and default `PORT=8003`.

### Models
- `models/users.py:12-49` → `User` (`id`, `username` unique, `email` unique, `password_hash`, `role` Enum `ADMIN/USER/MODERATOR`, `is_active`, timestamps). `password` setter uses `generate_password_hash`, `check_password()` uses `check_password_hash`. `to_dict()` for API.
- `models/locations.py:4-38` → `Location` (`user_id` FK, `name`, `city`, `country`, `latitude/longitude`, timestamps) + `user` relationship.
- `models/api_storage.py:3-28` → `API_Storage` encrypted `api_key` via `utils/encryption.py:5-26` (`Fernet` with `Config.ENCRYPTION_KEY`).
- `models/routes.py:4-66` → `RouteHistory` snapshots start/mid/end (`id`+`lat/lon/name`), `distance_km`, `estimated_time_min`, `route_type`.
- Migrations: `migrations/versions/7ba6d6be0321_.py` (users) + `ecab7f4d0937_.py` (api_storage). `locations`/`route_history` historically missing → `entrypoint.sh:95-112` does `db.create_all()` + `flask db stamp head` to compensate. For new changes: `uv run flask db migrate -m "add_locations"` + `uv run flask db upgrade`.

### Routers & Controllers
- `routers/__init__.py:13-21` registers 7 blueprints: `home_page`, `users`, `dashboard_page`, `routes_page`, `locations`, `graphs`, `configuration`, `history_bp`.
- `routers/users.py:9-49` → `/users/signup|signin|signout|update|change-password` delegating to `controllers/users.py:24-221`. `update` and `change-password` support JSON (`is_json`) and HTML.
- `routers/locations.py:5-64` → REST `GET /locations/`, `POST /`, `PUT/DELETE /<id>` all `@login_required` (`utils/auth.py:4-12`), using `controllers/locations.py`.
- `routers/graphs.py:5-141` → `/graphs/locations.png` (png via `controllers/graphs.py:generate_location_graph` → NetworkX+matplotlib) and `/graphs/export_pdf` (GET/POST, calls `controllers/export.py:generate_route_pdf`).
- `routers/configuration.py` + `controllers/configuration.py:9-130` → admin panel: `CONFIG_ACCESS_KEY` or `role=admin` required (`utils/auth.py:14-28` `admin_or_key_required`), user role update, password reset, bulk delete.
- `controllers/dashboard.py:9-27`, `controllers/routes.py:3-4`, etc.

### Auth & Security
- `utils/auth.py:4-12` `login_required` checks `session['user_id']`; `admin_or_key_required` checks `session['role']=='admin'` or `session['config_access']==True`.
- `utils/encryption.py:5-10` requires valid Fernet key → now default `0A1glB0r_8tPpo8k9eeWZW3TXvkvCPpw1ZgBmsV5D6s=` prevents `ValueError`.
- `config.py` `SECRET_KEY` fallback prevents session failure.

### Graph Algorithm
- `controllers/graphs.py` builds `networkx.Graph` where nodes = user's `Location`s, edges weighted by `haversine(lat1,lon1,lat2,lon2)`. `dijkstra_path` finds shortest; `generate_location_graph` draws with `matplotlib` and highlights `[(u,v)]` or `[(u,mid),(mid,v)]`.

## 3. Local Dev without Docker

```bash
# Python 3.13, uv
uv sync                          # installs from pyproject.toml + uv.lock (now includes gunicorn)
cp .env.example .env             # optional; fallback SQLite works without it
uv run flask db upgrade          # may warn "table already exists" first time -> ok
uv run python -c "from app import app; from models import db; with app.app_context(): db.create_all(); print('ok')"
uv run python seed.py            # creates admin / Admin123!
uv run python app.py             # http://localhost:8003 (or 8003 default)
# alternative prod-like:
uv run gunicorn --bind 127.0.0.1:8003 --reload app:app
# verify endpoint:
curl http://127.0.0.1:8003/
# run verifications:
uv run python test/verify_locations.py
uv run python test/verify_users.py
```

**SQLite location:** `instance/routeplanner.db` (gitignored, dockerignored). Delete to reset: `rm -rf instance/ && uv run python seed.py`.

## 4. Docker Dev

```bash
docker compose up --build        # uses Dockerfile + entrypoint.sh
docker compose logs -f web db
docker compose exec web flask db current
docker compose exec web python -c "from app import app; from models.users import User; with app.app_context(): print([u.to_dict() for u in User.query.all()])"
docker compose down     # keep volume
docker compose down -v  # wipe DB
```

**Entrypoint steps** (`entrypoint.sh:1-186`):
1. Wait MySQL (`pymysql` parsing `DATABASE_URL`) — 60×2s.
2. `flask db upgrade` → `db.create_all()` import all models → `flask db stamp head`.
3. Seed admin idempotent (`ADMIN_USERNAME/_EMAIL/_PASSWORD`, `ADMIN_FORCE_RESET`).
4. Exec `gunicorn --bind 0.0.0.0:8003 --workers 2 --threads 4`.

**Dockerfile:** `python:3.13-slim`, `curl`+`default-mysql-client`, `uv sync --system`, `EXPOSE 8003`, `ENV PORT=8003`, `HEALTHCHECK curl`.

## 5. Migrations Workflow

```bash
# after editing models/*.py
uv run flask db migrate -m "describe change"
# review migrations/versions/<hash>_.py
uv run flask db upgrade
# downgrade if needed
uv run flask db downgrade
# if DB was manually created via create_all and alembic_version missing:
uv run flask db stamp head
uv run flask db current
```

**MySQL vs SQLite:** Alembic generates generic SQL; Enum `UserRole` works on both. Test with `DATABASE_URL=mysql+pymysql://route_user:route_password@localhost:3306/routeplanner uv run flask db upgrade` to ensure MySQL compatibility before commit.

## 6. Demo User for Developers

- **Default:** `admin` / `Admin123!` / `admin@routeplanner.local` / `role=ADMIN`
- **Env override:**
  ```bash
  ADMIN_USERNAME=dev ADMIN_EMAIL=dev@local ADMIN_PASSWORD='Dev123!' uv run python seed.py
  # or for Docker:
  ADMIN_USERNAME=dev ADMIN_PASSWORD='Dev123!' docker compose up --build
  ```
- **Force reset:** `ADMIN_FORCE_RESET=true` will overwrite password on boot (useful after sharing DB dump).
- **Idempotent:** running `seed.py` twice does not duplicate; second run prints `already exists` and ensures `role==ADMIN`.
- **Testing as demo:**
  ```bash
  curl -c jar -b jar -L http://localhost:8003/users/signin -d "username=admin&password=Admin123!"  # form
  # or JSON (if endpoint supports)
  curl -H "Content-Type: application/json" -d '{"username":"admin","password":"Admin123!"}' http://localhost:8003/users/signin
  curl -b jar http://localhost:8003/locations/ | jq
  curl -b jar http://localhost:8003/configuration/  # should succeed as admin
  ```
- **Programmatic:**
  ```python
  from app import app
  from models.users import User, UserRole
  with app.app_context():
      u = User.query.filter_by(username='admin').first()
      assert u.role == UserRole.ADMIN
      assert u.check_password('Admin123!')
  ```

## 7. Testing & Verification

- `test/verify_locations.py` — creates temp user+location, asserts `user.locations` relationship, cleans up. Run via `app.py` startup or `uv run python test/verify_locations.py`.
- `test/create_admin.py` — legacy admin creator; `seed.py` is preferred (env-aware).
- No formal pytest suite; manual `curl` + above verifications. Add tests under `test/` and run `uv run pytest` if you add `pytest` to `pyproject.toml`.

## 8. Production Checklist

- Generate secrets: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` for `ENCRYPTION_KEY`; `openssl rand -hex 32` for `SECRET_KEY`.
- Set `ADMIN_PASSWORD` strong, `CONFIG_ACCESS_KEY` strong, `MYSQL_PASSWORD` strong via `.env` or orchestrator secrets; `docker-compose.prod.yml` reads `${VAR:-default}`.
- `docker compose -f docker-compose.prod.yml up --build -d` → `restart: always`.
- Put behind TLS proxy, expose only `8003` (and maybe `3306` only internally; remove `ports: 3306:3306` if DB should not be public).
- Volume `mysql_data` persists; backup `docker run --rm -v route-planner-prod_mysql_data:/data -v $(pwd):/backup ubuntu tar czf /backup/mysql_backup.tgz /data`.
- Monitor `docker compose logs web` and `HEALTHCHECK` (`curl`).

## 9. Contributing

- Branch from `main`, `uv sync`, `uv run flask db upgrade && uv run python seed.py`.
- Code style: keep `models` pure SQLAlchemy, business logic in `controllers`, HTTP in `routers`. Use `TypedDict` for API shapes (see `controllers/users.py:18-21`).
- Secrets: never commit `.env`; use `.env.example` as template.
- Commits: `feat:`, `fix:`, `docs:` prefix; reference issue.
- Before PR: `docker compose config` passes, `uv run python app.py` boots without `DATABASE_URL`, demo login works, `flask db current` shows head.

## 10. Troubleshooting (Dev)

| Issue | Fix |
|---|---|
| `gunicorn: command not found` | `uv sync` (added to `pyproject.toml:18`) or `uv add gunicorn` |
| `pymysql` wait fails | Ensure `db` service healthy: `docker compose ps`, `docker compose logs db`. Credentials must match `DATABASE_URL`. |
| `instance/routeplanner.db` locked | Stop `app.py`/`gunicorn`, `rm instance/routeplanner.db`, `uv run python seed.py` |
| `sqlalchemy.exc.OperationalError table already exists` | Run `uv run flask db stamp head` once |

---

<a id="guía-de-desarrollo-español"></a>
# Español — Guía de Desarrollo

## 1. Visión General
MVC Flask: `models` (SQLAlchemy), `controllers` (lógica), `routers` (Blueprints), `templates`+`static` (Jinja2/AdminLTE/Leaflet), `utils` (auth/cifrado). Versionado BD con `Flask-Migrate` (Alembic).

## 2. Arquitectura

### Arranque App
- `config.py:8-14` → `Config` con defaults seguros (`SECRET_KEY`, `ENCRYPTION_KEY` Fernet válido, fallback SQLite). Arregla `RuntimeError` al hacer `uv run app.py` sin `.env`.
- `app.py:14-20` → `Flask`, `app.config.from_object(Config)`, `init_db(app)` (`models/__init__.py:7-18`), `register_routes(app)` (`routers/__init__.py:13-21`).
- `models/__init__.py:7-18` → `db = SQLAlchemy()`, `migrate = Migrate()`, `init_db()` importa modelos dentro de `app_context` para que Alembic los detecte. Antes `db.create_all()` estaba comentado; entrypoint lo restaura como red de seguridad.
- `app.py:31-38` → si `__main__` ejecuta `test.verify_locations.verify()` y `app.run(host,port,debug)` con `DEBUG` parseado y `PORT=8003` por defecto.

### Modelos
- `models/users.py:12-49` → `User` (`username` único, `email` único, `password_hash`, `role` Enum `ADMIN/USER/MODERATOR`). Setter `password` hace hash, `check_password()` verifica. `to_dict()`.
- `models/locations.py:4-38` → `Location` (`user_id` FK, `name`, `city`, `country`, `lat/lon`). Relación `user`.
- `models/api_storage.py:3-28` → `API_Storage` `api_key` cifrado vía `utils/encryption.py:5-26` (`Fernet`).
- `models/routes.py:4-66` → `RouteHistory` snapshots, `distance_km`, `estimated_time_min`.
- Migraciones: `7ba6d6be0321_.py` (users) + `ecab7f4d0937_.py` (api_storage). `locations`/`route_history` faltaban → `entrypoint.sh:95-112` hace `db.create_all()` + `stamp head`. Para cambios nuevos: `uv run flask db migrate -m "add_locations"` + `upgrade`.

### Routers y Controllers
- `routers/__init__.py:13-21` registra 7 blueprints.
- `routers/users.py:9-49` → `/users/signup|signin|signout|update|change-password` delega a `controllers/users.py:24-221` (soporta JSON y HTML).
- `routers/locations.py:5-64` → REST `GET/POST /locations/`, `PUT/DELETE /<id>` con `@login_required` (`utils/auth.py:4-12`).
- `routers/graphs.py:5-141` → `/graphs/locations.png` (NetworkX+matplotlib) y `/graphs/export_pdf`.
- `controllers/configuration.py:9-130` → panel admin, requiere `CONFIG_ACCESS_KEY` o `admin` (`utils/auth.py:14-28`), update rol, reset pass, borrado.

### Auth y Seguridad
- `utils/auth.py:4-12` `login_required` mira `session['user_id']`; `admin_or_key_required` mira `role==admin` o `config_access`.
- `utils/encryption.py:5-10` requiere Fernet válido → ahora default funciona.

### Algoritmo Grafo
- `controllers/graphs.py` construye `networkx.Graph` nodos = `Location`, aristas = Haversine km, `dijkstra_path`, dibuja con `matplotlib`.

## 3. Dev Local sin Docker

```bash
uv sync
cp .env.example .env  # opcional; funciona sin él (SQLite)
uv run flask db upgrade
uv run python -c "from app import app; from models import db; with app.app_context(): db.create_all()"
uv run python seed.py  # admin / Admin123!
uv run python app.py   # http://localhost:8003
# o
uv run gunicorn --bind 127.0.0.1:8003 --reload app:app
uv run python test/verify_locations.py
```

SQLite en `instance/routeplanner.db` (ignorado). Reset: `rm -rf instance/ && uv run python seed.py`.

## 4. Docker Dev

```bash
docker compose up --build
docker compose logs -f web db
docker compose exec web flask db current
docker compose down      # mantiene volumen
docker compose down -v   # borra BD
```

Pasos entrypoint (`entrypoint.sh:1-186`): espera MySQL, `flask db upgrade` → `db.create_all()` → `stamp head` → seed admin → `gunicorn`.

Dockerfile: `python:3.13-slim`, `curl`+`default-mysql-client`, `uv sync --system`, `EXPOSE 8003`.

## 5. Flujo Migraciones

```bash
# tras editar models/*.py
uv run flask db migrate -m "cambio"
uv run flask db upgrade
uv run flask db downgrade  # si hace falta
uv run flask db stamp head # si BD manual
```

Probar MySQL antes de commit: `DATABASE_URL=mysql+pymysql://... uv run flask db upgrade`.

## 6. Usuario Demo para Desarrolladores

- **Default:** `admin` / `Admin123!` / `admin@routeplanner.local` / `ADMIN`
- **Override env:**
  ```bash
  ADMIN_USERNAME=dev ADMIN_EMAIL=dev@local ADMIN_PASSWORD='Dev123!' uv run python seed.py
  ADMIN_USERNAME=dev ADMIN_PASSWORD='Dev123!' docker compose up --build
  ```
- **Force reset:** `ADMIN_FORCE_RESET=true`
- **Idempotente:** segunda ejecución no duplica.
- **Test:**
  ```bash
  curl -c jar -b jar -L http://localhost:8003/users/signin -d "username=admin&password=Admin123!"
  curl -b jar http://localhost:8003/locations/ | jq
  ```
- **Programático:** ver snippet Python arriba en sección inglesa.

## 7. Testing

- `test/verify_locations.py`, `test/create_admin.py` (legado; usar `seed.py`).
- Añadir `pytest` si necesitas suite formal.

## 8. Checklist Producción

- Genera secretos (`Fernet.generate_key()`, `openssl rand -hex 32`), set `ADMIN_PASSWORD`, `MYSQL_PASSWORD` en `.env`, `docker compose -f docker-compose.prod.yml up --build -d`, `restart: always`, proxy TLS, cambia `ADMIN_PASSWORD` tras login, backup volumen `mysql_data`.

## 9. Contribuir

- Branch desde `main`, `uv sync`, `flask db upgrade && python seed.py`. Lógica en `controllers`, HTTP en `routers`. No commitear `.env`. Prefijo `feat:`, `fix:`. Antes de PR: `docker compose config` ok, `uv run python app.py` sin `DATABASE_URL` arranca, login demo ok, `flask db current` en head.

## 10. Troubleshooting Dev

| Problema | Solución |
|---|---|
| `gunicorn: command not found` | `uv sync` |
| wait `pymysql` falla | `docker compose ps`/`logs db`, credenciales igual a `DATABASE_URL` |
| `instance/routeplanner.db` locked | parar app, `rm instance/routeplanner.db` |
| `table already exists` | `uv run flask db stamp head` |

---

*RoutePlanner 2026 — Jorge Arguello. Ver `README.en.md`/`README.es.md` para guía de usuario y despliegue, y `docs/technical_report.md` para reporte técnico.*
