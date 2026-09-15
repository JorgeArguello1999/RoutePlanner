#!/bin/sh
set -e

PORT=${PORT:-8003}
HOST=${HOST:-0.0.0.0}
export PATH="/app/.venv/bin:$PATH"
export VIRTUAL_ENV="/app/.venv"

echo "=== RoutePlanner (single image) ==="
echo "HOST=$HOST PORT=$PORT"
echo "DATABASE_URL=${DATABASE_URL:-sqlite:///routeplanner.db (default)}"

mkdir -p /app/instance

# --- 1. Wait for external DB only if needed ---
if echo "${DATABASE_URL}" | grep -qi "mysql"; then
  echo ">> Waiting for MySQL..."
  uv run python << 'PYEOF'
import os, time, sys
from urllib.parse import urlparse
url = os.getenv("DATABASE_URL","")
url_norm = url.replace("mysql+pymysql://","mysql://",1) if url.startswith("mysql+pymysql://") else url
parsed = urlparse(url_norm)
host = parsed.hostname or "localhost"
port = parsed.port or 3306
user = parsed.username or "root"
passwd = parsed.password or ""
database = parsed.path.lstrip("/") or "routeplanner"
try:
    import pymysql
except ImportError:
    print("pymysql not installed, skipping wait"); sys.exit(0)
for i in range(30):
    try:
        conn = pymysql.connect(host=host, port=port, user=user, password=passwd, database=database, connect_timeout=2)
        conn.close(); print(f"  MySQL ready at {host}:{port}/{database}"); sys.exit(0)
    except Exception as e:
        print(f"  [{i+1}/30] MySQL not ready: {e}"); time.sleep(2)
print("MySQL not ready in time", file=sys.stderr); sys.exit(1)
PYEOF
elif echo "${DATABASE_URL}" | grep -qi "postgres"; then
  echo ">> Waiting for PostgreSQL..."
  uv run python << 'PYEOF'
import os, time, sys
from urllib.parse import urlparse
url = os.getenv("DATABASE_URL","")
parsed = urlparse(url)
host = parsed.hostname or "localhost"
port = parsed.port or 5432
try:
    import psycopg2
except ImportError:
    print("psycopg2 not installed, skipping wait"); sys.exit(0)
for i in range(30):
    try:
        conn = psycopg2.connect(host=host, port=port, user=parsed.username, password=parsed.password, dbname=parsed.path.lstrip("/"))
        conn.close(); print(f"  PostgreSQL ready at {host}:{port}"); sys.exit(0)
    except Exception as e:
        print(f"  [{i+1}/30] pg not ready: {e}"); time.sleep(2)
print("Postgres not ready", file=sys.stderr); sys.exit(1)
PYEOF
else
  echo ">> Using SQLite (no external DB wait)"
fi

# --- 2. Migrations ---
echo ">> Running migrations (flask db upgrade)..."
uv run flask db upgrade 2>&1 | head -n 20 || echo "  (migrations warning, continuing)"

# --- 3. Ensure tables exist ---
echo ">> Ensuring tables (db.create_all)..."
uv run python << 'PYEOF'
from app import app
from models import db
with app.app_context():
    from models.users import User
    from models.api_storage import API_Storage
    from models.locations import Location
    from models.routes import RouteHistory
    db.create_all()
    print("  tables ensured")
PYEOF

# stamp alembic to avoid repeated "already exists" warnings
uv run flask db stamp head 2>&1 | head -n 5 || true

# --- 4. Seed admin (idempotent) ---
echo ">> Seeding admin..."
uv run python << 'PYEOF'
import os
from app import app
from models import db
from models.users import User, UserRole
admin_user = os.getenv("ADMIN_USERNAME","admin")
admin_email = os.getenv("ADMIN_EMAIL","admin@routeplanner.local")
admin_pass = os.getenv("ADMIN_PASSWORD","Admin123!")
with app.app_context():
    u = User.query.filter_by(username=admin_user).first()
    if u:
        print(f"  admin exists: {u.username} ({u.role.value})")
        if u.role != UserRole.ADMIN:
            u.role = UserRole.ADMIN; db.session.commit(); print("  promoted to ADMIN")
        if os.getenv("ADMIN_FORCE_RESET","false").lower() == "true":
            u.password = admin_pass; db.session.commit(); print("  password reset via ADMIN_FORCE_RESET")
    else:
        by_email = User.query.filter_by(email=admin_email).first()
        if by_email:
            by_email.role = UserRole.ADMIN; db.session.commit(); print(f"  promoted existing email {admin_email} to ADMIN")
        else:
            new_admin = User(username=admin_user, email=admin_email, password=admin_pass, role=UserRole.ADMIN)
            new_admin.is_active = True
            db.session.add(new_admin); db.session.commit()
            print(f"  created admin: {admin_user}")
    print(f"  total users: {User.query.count()}")
PYEOF

# --- 5. Quick demo check ---
uv run python << 'PYEOF'
import os
from app import app
from models.users import User
admin_user=os.getenv("ADMIN_USERNAME","admin")
admin_pass=os.getenv("ADMIN_PASSWORD","Admin123!")
with app.app_context():
    try:
        u=User.query.filter_by(username=admin_user).first()
        if u and u.is_active and u.check_password(admin_pass):
            print(f"  ✅ DEMO READY: {admin_user} / {admin_pass} -> http://localhost:{os.getenv('PORT','8003')}/users/signin")
        elif not u:
            print(f"  ❌ demo missing: '{admin_user}' not found")
        elif not u.is_active:
            print(f"  ❌ demo inactive: '{admin_user}'")
        else:
            print(f"  ❌ demo password mismatch for '{admin_user}' (hint: ADMIN_FORCE_RESET=true)")
    except Exception as e:
        print(f"  demo check error: {e}")
PYEOF

echo "========================================"
echo "  RoutePlanner READY"
echo "  App:   http://localhost:${PORT}"
echo "  Health: http://localhost:${PORT}/health"
echo "  Login: http://localhost:${PORT}/users/signin (${ADMIN_USERNAME:-admin} / ${ADMIN_PASSWORD:-Admin123!})"
echo "========================================"

# --- 6. Start ---
echo ">> Starting gunicorn on $HOST:$PORT"
exec gunicorn --bind "$HOST:$PORT" --workers 2 --threads 4 --timeout 120 --access-logfile - --error-logfile - app:app
