import sys
import os
import io

# Ensure root directory is in python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from models import db
from models.users import User, UserRole
from models.locations import Location

def verify_graph_endpoint():
    print("Starting Graph Endpoint Verification...")
    
    with app.test_client() as client:
        with app.app_context():
            # Setup test user and locations
            user = User.query.filter_by(email='graph_test@example.com').first()
            if not user:
                user = User(username='graph_test', email='graph_test@example.com', password_hash='hash', role=UserRole.USER)
                db.session.add(user)
                db.session.commit()
            
            # Create two locations
            loc_a = Location(user_id=user.id, name="LocA", city="A", country="C", latitude=10, longitude=10)
            loc_b = Location(user_id=user.id, name="LocB", city="B", country="C", latitude=20, longitude=20)
            loc_mid = Location(user_id=user.id, name="LocMid", city="M", country="C", latitude=15, longitude=15)
            
            db.session.add_all([loc_a, loc_b, loc_mid])
            db.session.commit()
            
            u_id = loc_a.id
            v_id = loc_b.id
            m_id = loc_mid.id
            
            print(f"User ID: {user.id}")
            print(f"IDs: A={u_id}, B={v_id}, Mid={m_id}")

        # Simulate Login
        with client.session_transaction() as sess:
            sess['user_id'] = user.id

        # 1. Test Standard Path (A-B)
        print("\n[TEST] Standard Path A-B")
        res = client.get(f'/graphs/locations.png?u={u_id}&v={v_id}')
        print(f"Status: {res.status_code}")
        if res.status_code == 200 and res.mimetype == 'image/png':
             print("SUCCESS: Image returned.")
        else:
             print("FAILED")

        # 2. Test Existing Intermediate (A-Mid-B)
        print("\n[TEST] Intermediate Path A-Mid-B")
        res = client.get(f'/graphs/locations.png?u={u_id}&v={v_id}&mid={m_id}')
        print(f"Status: {res.status_code}")
        if res.status_code == 200 and res.mimetype == 'image/png':
             print("SUCCESS: Image returned with mid point.")
        else:
             print("FAILED")

        # 3. Test Custom Intermediate
        print("\n[TEST] Custom Intermediate")
        res = client.get(f'/graphs/locations.png?u={u_id}&v={v_id}&mid_lat=12.0&mid_lon=12.0')
        print(f"Status: {res.status_code}")
        if res.status_code == 200 and res.mimetype == 'image/png':
             print("SUCCESS: Image returned with custom point.")
        else:
             print("FAILED")

        # Clean up
        with app.app_context():
            db.session.delete(loc_a)
            db.session.delete(loc_b)
            db.session.delete(loc_mid)
            db.session.commit()

if __name__ == "__main__":
    verify_graph_endpoint()
