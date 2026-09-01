"""
Seed script for RoutePlanner - creates default admin user with all permissions.
Usable standalone: `uv run python seed.py` or `python seed.py`
Idempotent: does not duplicate if already exists.
"""
import os
import sys

# Allow running without DATABASE_URL set (fallback to sqlite in config.py)
from app import app
from models import db
from models.users import User, UserRole

def seed_admin():
    admin_user = os.getenv("ADMIN_USERNAME", "admin")
    admin_email = os.getenv("ADMIN_EMAIL", "admin@routeplanner.local")
    admin_pass = os.getenv("ADMIN_PASSWORD", "Admin123!")

    with app.app_context():
        # Ensure tables exist first (same as entrypoint)
        try:
            from models.api_storage import API_Storage
            from models.locations import Location
            from models.routes import RouteHistory
            db.create_all()
        except Exception as e:
            print(f"[seed] db.create_all warning: {e}")

        existing = User.query.filter_by(username=admin_user).first()
        if existing:
            print(f"[seed] Admin user already exists: {existing.username} ({existing.role.value})")
            if existing.role != UserRole.ADMIN:
                existing.role = UserRole.ADMIN
                db.session.commit()
                print(f"[seed] Promoted {existing.username} to ADMIN")
            return existing

        by_email = User.query.filter_by(email=admin_email).first()
        if by_email:
            print(f"[seed] User with email {admin_email} exists ({by_email.username}), promoting to ADMIN")
            by_email.role = UserRole.ADMIN
            db.session.commit()
            return by_email

        try:
            new_admin = User(username=admin_user, email=admin_email, password=admin_pass, role=UserRole.ADMIN)
            new_admin.is_active = True
            db.session.add(new_admin)
            db.session.commit()
            print(f"[seed] Created ADMIN user: {admin_user} / {admin_email}")
            print(f"[seed] Password: {admin_pass}")
            return new_admin
        except Exception as e:
            db.session.rollback()
            print(f"[seed] Failed to create admin: {e}", file=sys.stderr)
            sys.exit(1)

if __name__ == "__main__":
    seed_admin()
