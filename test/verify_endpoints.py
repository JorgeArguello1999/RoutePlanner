import sys
import os
import json

# Ensure root directory is in python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from models import db
from models.users import User, UserRole
from models.locations import Location

def run_tests():
    print("Starting API endpoint verification...")
    
    # Use test client
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            
            # Setup test user
            user = User.query.filter_by(email='api_test_v2@example.com').first()
            if not user:
                user = User(username='api_test_v2', email='api_test_v2@example.com', password_hash='hash', role=UserRole.USER)
                db.session.add(user)
                db.session.commit()
            
            user_id = user.id
            print(f"Test user id: {user_id}")

        # Simulate login by modifying session
        with client.session_transaction() as sess:
            sess['user_id'] = user_id
            sess['username'] = 'api_test_v2'

        # 1. Create Location (POST)
        print("\n[POST] /locations/")
        payload = {
            "name": "API Test Loc",
            "city": "Medellin",
            "country": "Colombia",
            "latitude": 6.2442,
            "longitude": -75.5812
        }
        res = client.post('/locations/', data=json.dumps(payload), content_type='application/json')
        print(f"Status: {res.status_code}")
        print(f"Response: {res.get_json()}")
        if res.status_code != 201:
            print("FAILED to create location")
            return
        
        loc_id = res.get_json()['id']

        # 2. Get Locations (GET)
        print("\n[GET] /locations/")
        res = client.get('/locations/')
        print(f"Status: {res.status_code}")
        data = res.get_json()
        print(f"Response: {data}")
        # Verify our location is there
        found = any(l['id'] == loc_id for l in data)
        if found:
            print("SUCCESS: Location found in list.")
        else:
            print("FAILED: Location not in list.")

        # 3. Update Location (PUT)
        print(f"\n[PUT] /locations/{loc_id}")
        update_payload = {"city": "Medellin Updated"}
        res = client.put(f'/locations/{loc_id}', data=json.dumps(update_payload), content_type='application/json')
        print(f"Status: {res.status_code}")
        print(f"Response: {res.get_json()}")
        if res.get_json()['city'] == "Medellin Updated":
             print("SUCCESS: Location updated.")
        else:
             print("FAILED: Location not updated.")

        # 4. Delete Location (DELETE)
        print(f"\n[DELETE] /locations/{loc_id}")
        res = client.delete(f'/locations/{loc_id}')
        print(f"Status: {res.status_code}")
        print(f"Response: {res.get_json()}")
        
        # Verify deletion
        with app.app_context():
            loc = Location.query.get(loc_id)
            if not loc:
                print("SUCCESS: Location deleted from DB.")
            else:
                print("FAILED: Location still exists in DB.")

if __name__ == "__main__":
    run_tests()
