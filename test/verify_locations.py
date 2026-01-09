import sys
import os

# Ensure root directory is in python path so we can import 'app' and 'models'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from models import db
from models.users import User
from models.locations import Location

def verify():
    print("Starting verification...")
    with app.app_context():
        # Create tables (safely creates 'locations' if it doesn't exist)
        db.create_all()

        # Get or create a test user
        user = User.query.filter_by(email='test_geo@example.com').first()
        if not user:
            print("Creating test user...")
            user = User(username='test_geo', email='test_geo@example.com', password_hash='dummyhash')
            db.session.add(user)
            db.session.commit()
        else:
            print(f"Using existing user: {user.username}")
        
        # Create a location
        print("Creating test location...")
        loc = Location(
            user_id=user.id,
            name="Verification Point",
            city="Bogota",
            country="Colombia",
            latitude=4.7110,
            longitude=-74.0721
        )
        db.session.add(loc)
        db.session.commit()

        print(f"Successfully created: {loc}")
        
        # Verify relationship
        # Re-query user to ensure caching doesn't hide issues
        user = User.query.get(user.id)
        print(f"User {user.username} has {len(user.locations)} locations.")
        found = False
        for l in user.locations:
            if l.id == loc.id:
                print(f"Found location in user.locations: {l}")
                found = True
                break
        
        if not found:
            print("ERROR: Location not found in user.locations!")
        
        # Cleanup
        print("Cleaning up...")
        db.session.delete(loc)
        # Optional: delete user if we created it? Better to leave it or check if it was new. 
        # For this test, I'll just delete the location to keep DB clean-ish.
        db.session.commit()
        print("Verification complete.")

if __name__ == "__main__":
    verify()
