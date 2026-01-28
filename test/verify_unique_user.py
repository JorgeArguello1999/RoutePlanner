import sys
import os

# Ensure root directory is in python path so we can import 'app' and 'models'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from models import db
from models.users import User, UserRole
from sqlalchemy.exc import IntegrityError

def verify():
    with app.app_context():
        # Clean up test users first
        existing = User.query.filter_by(username='test_unique').all()
        for u in existing:
            db.session.delete(u)
        db.session.commit()

        # Create first user
        u1 = User(username='test_unique', email='test_unique@example.com', password='password')
        db.session.add(u1)
        db.session.commit()
        print("Created first user.")

        # Try to create duplicate user
        try:
            u2 = User(username='test_unique', email='other@example.com', password='password')
            db.session.add(u2)
            db.session.commit()
            print("ERROR: Created duplicate user! Constraint is MISSING.")
            sys.exit(1)
        except IntegrityError:
            db.session.rollback()
            print("SUCCESS: Duplicate user rejected by DB (IntegrityError). Constraint is ACTIVE.")
        except Exception as e:
            print(f"ERROR: Unexpected exception: {e}")
            sys.exit(1)

        # Cleanup
        u1 = User.query.filter_by(username='test_unique').first()
        if u1:
            db.session.delete(u1)
            db.session.commit()

if __name__ == '__main__':
    verify()
