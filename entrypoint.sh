#!/bin/sh
set -e

PORT=${PORT:-8003}
HOST=${HOST:-0.0.0.0}
FLASK_APP=${FLASK_APP:-app.py}

echo "=== RoutePlanner Entrypoint ==="
echo "HOST=$HOST PORT=$PORT"
echo "DATABASE_URL=${DATABASE_URL:-sqlite:///routeplanner.db (fallback)}"

# ---------------------------------------------------------
# 1. Wait for database (MySQL primary, PostgreSQL fallback)
# ---------------------------------------------------------
if echo "${DATABASE_URL}" | grep -qi "mysql"; then
  echo ">> Waiting for MySQL to be ready..."
  python3 << 'PYEOF'
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
  python3 << 'PYEOF'
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
if flask db upgrade; then
  echo "  Migrations applied successfully"
else
  echo "  WARNING: flask db upgrade failed, continuing (maybe no migrations needed)"
fi

# ---------------------------------------------------------
# 3. Ensure all tables exist (covers missing migrations for locations/route_history)
# ---------------------------------------------------------
echo ">> Ensuring all tables exist (db.create_all)..."
python3 << 'PYEOF'
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
flask db stamp head 2>&1 | head -n 20 || echo "  stamp head skipped (already stamped or not needed)"
flask db current 2>&1 | head -n 20 || true

# ---------------------------------------------------------
# 4. Seed default admin user (idempotent, con todos los permisos)
# ---------------------------------------------------------
echo ">> Seeding default admin user..."
python3 << 'PYEOF'
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
