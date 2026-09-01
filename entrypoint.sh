#!/bin/sh
set -e

PORT=${PORT:-8003}
HOST=${HOST:-0.0.0.0}
FLASK_APP=${FLASK_APP:-app.py}

echo "=== RoutePlanner Entrypoint ==="
echo "HOST=$HOST PORT=$PORT"
echo "DATABASE_URL=${DATABASE_URL:-sqlite:///routeplanner.db (fallback)}"

# Ensure .venv exists (dev compose mounts host code over /app, hiding built venv)
# Anonymous volume /app/.venv in docker-compose.yml will be empty on first run
if [ ! -f "/app/.venv/bin/flask" ] || [ ! -f "/app/.venv/bin/gunicorn" ]; then
  echo ">> .venv not found or incomplete (dev volume mount?), running uv sync..."
  if uv sync --frozen --no-cache; then
    echo "  uv sync completed"
  else
    echo "  WARNING: uv sync failed, trying with --break-system-packages fallback"
    uv sync --frozen --no-cache || echo "  uv sync still failed, continuing (may fail later)"
  fi
fi
# Ensure PATH includes venv (also set via Dockerfile ENV)
export PATH="/app/.venv/bin:$PATH"
export VIRTUAL_ENV="/app/.venv"

# ---------------------------------------------------------
# 1. Wait for database (MySQL primary, PostgreSQL fallback)
# ---------------------------------------------------------
if echo "${DATABASE_URL}" | grep -qi "mysql"; then
  echo ">> Waiting for MySQL to be ready..."
  uv run python << 'PYEOF'
import os, time, sys
from urllib.parse import urlparse

url = os.getenv("DATABASE_URL", "")
# urlparse needs scheme without '+'
url_norm = url.replace("mysql+pymysql://", "mysql://", 1) if url.startswith("mysql+pymysql://") else url
from urllib.parse import urlparse
parsed = urlparse(url_norm)
host = parsed.hostname or "db"
port = parsed.port or 3306
user = parsed.username or os.getenv("MYSQL_USER", "user")
passwd = parsed.password or os.getenv("MYSQL_PASSWORD", "password")
database = parsed.path.lstrip("/") if parsed.path and len(parsed.path) > 1 else os.getenv("MYSQL_DATABASE", "routeplanner")

try:
    import pymysql
except ImportError:
    print("pymysql not installed, skipping MySQL wait (will retry via SQLAlchemy)")
    sys.exit(0)

max_retries = 60
for i in range(max_retries):
    try:
        conn = pymysql.connect(host=host, port=port, user=user, password=passwd, database=database, connect_timeout=2)
        conn.close()
        print(f"  MySQL at {host}:{port}/{database} is ready!")
        sys.exit(0)
    except Exception as e:
        print(f"  [{i+1}/{max_retries}] MySQL not ready: {e}")
        time.sleep(2)
print("MySQL did not become ready in time", file=sys.stderr)
sys.exit(1)
PYEOF
elif echo "${DATABASE_URL}" | grep -qi "postgres"; then
  echo ">> Waiting for PostgreSQL to be ready..."
  uv run python << 'PYEOF'
import os, time, sys
from urllib.parse import urlparse
url = os.getenv("DATABASE_URL","")
parsed = urlparse(url)
host = parsed.hostname or "db"
port = parsed.port or 5432
try:
    import psycopg2
except ImportError:
    print("psycopg2 not installed, skipping pg wait")
    sys.exit(0)
max_retries = 60
for i in range(max_retries):
    try:
        conn = psycopg2.connect(host=host, port=port, user=parsed.username, password=parsed.password, dbname=parsed.path.lstrip("/"))
        conn.close()
        print(f"  PostgreSQL at {host}:{port} ready")
        sys.exit(0)
    except Exception as e:
        print(f"  [{i+1}/{max_retries}] pg not ready: {e}")
        time.sleep(2)
print("Postgres not ready", file=sys.stderr)
sys.exit(1)
PYEOF
else
  echo ">> No MySQL/Postgres URL detected, skipping DB wait (likely SQLite)"
fi

# ---------------------------------------------------------
# 2. Run migrations (flask db upgrade)
# ---------------------------------------------------------
echo ">> Running migrations (flask db upgrade)..."
if uv run flask db upgrade; then
  echo "  Migrations applied successfully"
else
  echo "  WARNING: flask db upgrade failed, continuing (maybe no migrations needed)"
fi

# ---------------------------------------------------------
# 3. Ensure all tables exist (covers missing migrations for locations/route_history)
# ---------------------------------------------------------
echo ">> Ensuring all tables exist (db.create_all)..."
uv run python << 'PYEOF'
from app import app
from models import db
with app.app_context():
    # import models to register metadata before create_all
    from models.users import User
    from models.api_storage import API_Storage
    from models.locations import Location
    from models.routes import RouteHistory
    db.create_all()
    print("  db.create_all() completed - tables ensured")
PYEOF

# Try to stamp alembic to head so future `flask db upgrade` no longer fails on existing tables
echo ">> Ensuring alembic version is stamped..."
uv run flask db stamp head 2>&1 | head -n 20 || echo "  stamp head skipped (already stamped or not needed)"
uv run flask db current 2>&1 | head -n 20 || true

# ---------------------------------------------------------
# 4. Seed default admin user (idempotent, con todos los permisos)
# ---------------------------------------------------------
echo ">> Seeding default admin user..."
uv run python << 'PYEOF'
import os
from app import app
from models import db
from models.users import User, UserRole

admin_user = os.getenv("ADMIN_USERNAME", "admin")
admin_email = os.getenv("ADMIN_EMAIL", "admin@routeplanner.local")
admin_pass = os.getenv("ADMIN_PASSWORD", "Admin123!")
# For compatibility also check CONFIG_ACCESS_KEY as fallback? No, that's config page key.

with app.app_context():
    existing = User.query.filter_by(username=admin_user).first()
    if existing:
        print(f"  Admin user already exists: {existing.username} ({existing.role.value})")
        # Ensure role is ADMIN and active
        if existing.role != UserRole.ADMIN:
            existing.role = UserRole.ADMIN
            db.session.commit()
            print(f"  Updated role to ADMIN for {existing.username}")
        # Optionally update password if ADMIN_PASSWORD was changed and user asks? Keep existing to avoid surprises.
        # But if env ADMIN_FORCE_RESET=true, reset password
        if os.getenv("ADMIN_FORCE_RESET", "false").lower() == "true":
            existing.password = admin_pass
            db.session.commit()
            print(f"  Password reset for {existing.username} (ADMIN_FORCE_RESET=true)")
    else:
        # Check by email as well to avoid duplicate email error
        by_email = User.query.filter_by(email=admin_email).first()
        if by_email:
            print(f"  User with email {admin_email} already exists: {by_email.username}, promoting to ADMIN if needed")
            by_email.role = UserRole.ADMIN
            # Update password only if forcing
            if os.getenv("ADMIN_FORCE_RESET", "false").lower() == "true":
                by_email.password = admin_pass
            db.session.commit()
        else:
            try:
                new_admin = User(username=admin_user, email=admin_email, password=admin_pass, role=UserRole.ADMIN)
                new_admin.is_active = True
                db.session.add(new_admin)
                db.session.commit()
                print(f"  Successfully created admin user: {admin_user} / {admin_email} with role ADMIN")
                print(f"  Password: {admin_pass}  (change via ADMIN_PASSWORD env or UI)")
            except Exception as e:
                db.session.rollback()
                print(f"  Failed to create admin user: {e}")
            # Also create a secondary dev user if requested
    # Summary
    total = User.query.count()
    admins = User.query.filter_by(role=UserRole.ADMIN).count()
    print(f"  Total users: {total}, admins: {admins}")

PYEOF

echo ">> Database initialization complete"

# ---------------------------------------------------------
# 4b. Verify demo user can actually login (AVISO deploy)
# ---------------------------------------------------------
echo ">> Verifying demo user (AVISO deploy - ¿demo corriendo?)..."
uv run python << 'PYEOF'
import os
from app import app
from models.users import User

admin_user = os.getenv("ADMIN_USERNAME", "admin")
admin_pass = os.getenv("ADMIN_PASSWORD", "Admin123!")
port = os.getenv("PORT", "8003")

with app.app_context():
    try:
        u = User.query.filter_by(username=admin_user).first()
        if not u:
            print("  ❌ DEMO USER NOT FOUND")
            print(f"     Buscado: '{admin_user}' no existe en DB.")
            print("     Causa: seeding falló o volumen DB corrupto.")
            print("     Solución: docker compose logs web | grep -i seed  -> revisa error")
            print("              docker compose down -v && docker compose up --build  (resetea DB limpia)")
            print(f"              o: docker compose exec web python seed.py")
        elif not u.is_active:
            print(f"  ❌ DEMO USER INACTIVO: '{u.username}' (is_active=False)")
            print("     Solución: activa el usuario en /configuration o DB: is_active=1")
        elif not u.check_password(admin_pass):
            print(f"  ❌ DEMO USER PASSWORD MISMATCH para '{admin_user}'")
            print(f"     El usuario existe (role={u.role.value}, email={u.email}) pero el password en DB NO coincide con ADMIN_PASSWORD='{admin_pass}'")
            print("     Causa: ya existía con otro password (no se sobrescribe por seguridad).")
            print("     Soluciones:")
            print("       1) Loguéate con el password antiguo si lo recuerdas,")
            print("       2) ADMIN_FORCE_RESET=true docker compose up -d   -> resetea password al del .env")
            print("       3) docker compose exec web python -c \"from app import app; from models import db; from models.users import User; import os; u=User.query.filter_by(username=os.getenv('ADMIN_USERNAME','admin')).first(); u.password=os.getenv('ADMIN_PASSWORD','Admin123!'); db.session.commit(); print('reset ok')\"")
        else:
            print(f"  ✅ DEMO USER READY: '{admin_user}' / '{admin_pass}'")
            print(f"     Rol: {u.role.value} | Email: {u.email} | ID: {u.id}")
            print(f"     Login: http://localhost:{port}/users/signin")
            print(f"     Health: curl http://localhost:{port}/health/demo | jq")
        # Resumen para health endpoint
        total = User.query.count()
        print(f"  [demo-check] total_users={total} demo_ready={bool(u and u.is_active and u.check_password(admin_pass))}")
    except Exception as e:
        print(f"  ❌ DEMO CHECK ERROR: {e}")
        import traceback; traceback.print_exc()
        print("     Hint: ¿DB conectada? ¿tablas creadas? Revisa: flask db current && db.create_all() logs arriba")

PYEOF

# Banner final MUY visible para el deploy
echo ""
echo "========================================"
echo "  RoutePlanner DEPLOY COMPLETE"
echo "  App:      http://localhost:${PORT}"
echo "  Health:   http://localhost:${PORT}/health"
echo "  Demo chk: curl http://localhost:${PORT}/health/demo"
echo "  Login:    http://localhost:${PORT}/users/signin"
echo "  Demo:     ${ADMIN_USERNAME:-admin} / ${ADMIN_PASSWORD:-Admin123!}"
echo "========================================"
echo ""
echo "  Si el demo NO funciona, revisa:"
echo "    docker compose logs web | grep -A2 -i demo"
echo "    curl http://localhost:${PORT}/health/demo | python3 -m json.tool"
echo "    docker compose exec web python seed.py"
echo ""

# ---------------------------------------------------------
# 5. Start application
# ---------------------------------------------------------
echo ">> Starting application on $HOST:$PORT"
# Use gunicorn in production if available, otherwise Flask dev server
if command -v gunicorn >/dev/null 2>&1; then
  echo "  Using gunicorn"
  exec gunicorn --bind "$HOST:$PORT" --workers 2 --threads 4 --timeout 120 --access-logfile - --error-logfile - app:app
else
  echo "  gunicorn not found, using 'uv run python app.py'"
  exec uv run python app.py
fi
