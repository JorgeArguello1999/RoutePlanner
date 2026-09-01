from flask import Blueprint, jsonify
import os
from sqlalchemy import text

health = Blueprint('health', __name__, url_prefix='/health')

@health.route('', methods=['GET'])
def health_check():
    """Liveness + DB + demo user status. Always 200 if app is up; details in json."""
    from models import db
    from models.users import User

    result = {
        "status": "ok",
        "service": "RoutePlanner",
        "port": os.getenv("PORT", "8003"),
        "db": "unknown",
        "demo_ready": False,
        "demo_user": os.getenv("ADMIN_USERNAME", "admin"),
        "hint": None,
    }
    # DB check
    try:
        db.session.execute(text("SELECT 1"))
        result["db"] = "ok"
    except Exception as e:
        result["db"] = f"error: {e}"
        result["status"] = "degraded"
        result["hint"] = "DB connection failed - check DATABASE_URL and db container"
        return jsonify(result), 200

    # Demo user check (doesn't require password to be exposed)
    try:
        admin_user = os.getenv("ADMIN_USERNAME", "admin")
        admin_pass = os.getenv("ADMIN_PASSWORD", "Admin123!")
        u = User.query.filter_by(username=admin_user).first()
        if not u:
            result["demo_ready"] = False
            result["hint"] = f"Demo user '{admin_user}' does not exist. Check entrypoint logs (seeding) or run: docker compose exec web python seed.py"
        elif not u.is_active:
            result["demo_ready"] = False
            result["hint"] = f"Demo user '{admin_user}' is inactive. Enable it in /configuration or DB."
        elif not u.check_password(admin_pass):
            result["demo_ready"] = False
            result["hint"] = f"Password in DB does not match ADMIN_PASSWORD env. Fix: ADMIN_FORCE_RESET=true docker compose up -d (or change ADMIN_PASSWORD)"
            result["admin_role"] = u.role.value if hasattr(u.role, 'value') else str(u.role)
        else:
            result["demo_ready"] = True
            result["admin_role"] = u.role.value if hasattr(u.role, 'value') else str(u.role)
            result["admin_email"] = u.email
            result["hint"] = f"Login at /users/signin with {admin_user} / {admin_pass}"
    except Exception as e:
        result["demo_ready"] = False
        result["hint"] = f"Error checking demo: {e}"

    return jsonify(result), 200


@health.route('/demo', methods=['GET'])
def demo_check():
    """Dedicated demo status - same check but explicit endpoint for deploy."""
    return health_check()
