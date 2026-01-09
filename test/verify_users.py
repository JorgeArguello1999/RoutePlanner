import sys
import os
import json

# Ensure root directory is in python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from models import db
from models.users import User, UserRole

def verify_users_endpoints():
    print("Starting Users Endpoint Verification...")
    
    with app.test_client() as client:
        with app.app_context():
            # Setup test user
            user = User.query.filter_by(email='user_test@example.com').first()
            if not user:
                user = User(username='user_test', email='user_test@example.com', password_hash='hash', role=UserRole.USER)
                user.password = 'password123'
                db.session.add(user)
                db.session.commit()
            
            # Ensure password is known
            user.password = 'password123'
            db.session.commit()
            
            user_id = user.id
            print(f"Test User ID: {user_id}")

        # Simulate Login
        with client.session_transaction() as sess:
            sess['user_id'] = user_id
            sess['username'] = 'user_test'
            sess['role'] = 'user'

        # 1. Test Profile Update (Success)
        print("\n[TEST] Profile Update (Success)")
        payload = {"username": "user_test_updated", "email": "user_test_updated@example.com"}
        res = client.post('/users/update', data=json.dumps(payload), content_type='application/json')
        print(f"Status: {res.status_code}")
        print(f"Response: {res.get_json()}")
        if res.status_code == 200:
             print("SUCCESS")
        else:
             print("FAILED")

        # 2. Test Profile Update (Fail - Duplicate)
        print("\n[TEST] Profile Update (Fail - Duplicate)")
        # Try to update to existing username (itself is fine, but lets create another user temporarily or just assume same name is handled)
        # Actually same name is fine, let's create a conflict
        with app.app_context():
             conflict_user = User(username='conflict', email='conflict@example.com', password_hash='hash', role=UserRole.USER)
             db.session.add(conflict_user)
             db.session.commit()
        
        payload = {"username": "conflict"}
        res = client.post('/users/update', data=json.dumps(payload), content_type='application/json')
        print(f"Status: {res.status_code}")
        print(f"Response: {res.get_json()}")
        if res.status_code == 400:
             print("SUCCESS: Duplicate caught")
        else:
             print("FAILED: Duplicate not caught")

        # 3. Test Password Change (Success)
        print("\n[TEST] Password Change (Success)")
        payload = {
            "current_password": "password123", 
            "new_password": "newpassword123", 
            "confirm_password": "newpassword123"
        }
        res = client.post('/users/change-password', data=json.dumps(payload), content_type='application/json')
        print(f"Status: {res.status_code}")
        print(f"Response: {res.get_json()}")
        if res.status_code == 200:
             print("SUCCESS")
        else:
             print("FAILED")

        # 4. Verify New Password Login Logic
        with app.app_context():
            u = User.query.get(user_id)
            if u.check_password("newpassword123"):
                print("SUCCESS: Database password updated correctly")
            else:
                print("FAILED: Database password not updated")

        # Clean up
        with app.app_context():
            db.session.delete(u)
            c = User.query.filter_by(username='conflict').first()
            if c: db.session.delete(c)
            db.session.commit()

if __name__ == "__main__":
    verify_users_endpoints()
