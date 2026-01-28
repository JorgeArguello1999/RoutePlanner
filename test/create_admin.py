import sys
import os

# Add parent directory to path to allow importing app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from models import db
from models.users import User, UserRole

def create_admin():
    with app.app_context():
        # Check if admin already exists
        admin = User.query.filter_by(role=UserRole.ADMIN).first()
        if admin:
            print(f"Admin user already exists: {admin.username}")
            return

        try:
            # Create new admin user
            # You can customize these details or pass them as args
            username = "admin"
            email = "admin@example.com"
            password = "secure_admin_password" # In a real scenario, use env var or input

            new_admin = User(
                username=username,
                email=email,
                password=password,
                role=UserRole.ADMIN
            )
            
            db.session.add(new_admin)
            db.session.commit()
            print(f"Successfully created admin user: {username} ({email})")
            
        except Exception as e:
            db.session.rollback()
            print(f"Failed to create admin user: {e}")
            sys.exit(1)

if __name__ == "__main__":
    create_admin()
