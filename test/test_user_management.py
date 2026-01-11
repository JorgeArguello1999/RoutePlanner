
import unittest
from flask import Flask, session
from routers.configuration import configuration
from models import db, init_db
from models.users import User, UserRole
from models.locations import Location
import os

class TestUserManagement(unittest.TestCase):
    def setUp(self):
        # Point to the correct templates folder relative to CWD or script
        template_dir = os.path.join(os.getcwd(), 'templates')
        self.app = Flask(__name__, template_folder=template_dir)
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['SECRET_KEY'] = 'test'
        
        init_db(self.app)
        self.app.register_blueprint(configuration)
        
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()
            # Create a test user
            self.user = User(username='testuser', email='test@test.com', password='password123', role=UserRole.USER)
            db.session.add(self.user)
            db.session.commit()
            
            # Create some locations
            loc = Location(user_id=self.user.id, city='Test City', country='Test Country', latitude=10.0, longitude=10.0)
            db.session.add(loc)
            db.session.commit()
            
            self.user_id = self.user.id

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def login_as_admin(self):
        with self.client.session_transaction() as sess:
            sess['user_id'] = 999
            sess['role'] = 'admin'

    def test_update_role(self):
        self.login_as_admin()
        response = self.client.post(f'/config/users/{self.user_id}/role', data={'role': 'admin'})
        self.assertEqual(response.status_code, 302) # Redirects back
        
        with self.app.app_context():
            user = User.query.get(self.user_id)
            self.assertEqual(user.role, UserRole.ADMIN)

    def test_update_password(self):
        self.login_as_admin()
        new_pass = 'newpassword123'
        response = self.client.post(f'/config/users/{self.user_id}/password', data={'password': new_pass})
        self.assertEqual(response.status_code, 302)
        
        with self.app.app_context():
            user = User.query.get(self.user_id)
            # Since the controller does user.password = new_pass which hashes it (via setter),
            # we should check check_password
            self.assertTrue(user.check_password(new_pass))

    def test_delete_routes(self):
        self.login_as_admin()
        response = self.client.post(f'/config/users/{self.user_id}/delete-routes')
        self.assertEqual(response.status_code, 302)
        
        with self.app.app_context():
            count = Location.query.filter_by(user_id=self.user_id).count()
            self.assertEqual(count, 0)
            
    def test_delete_user_admin_success(self):
        # Set Env Key
        os.environ['CONFIG_ACCESS_KEY'] = 'secretkey'

        # 1. Create administrator user with password
        with self.app.app_context():
            admin = User(username='admin', email='admin@test.com', password='adminpass', role=UserRole.ADMIN)
            db.session.add(admin)
            db.session.commit()
            admin_id = admin.id
            
        with self.client.session_transaction() as sess:
            sess['user_id'] = admin_id
            sess['role'] = 'admin'
            
        # 2. Try delete with CONFIG_ACCESS_KEY (not admin db pass)
        response = self.client.post(f'/config/users/{self.user_id}/delete', data={'confirmation_password': 'secretkey'})
        self.assertEqual(response.status_code, 302)
        
        with self.app.app_context():
             user = User.query.get(self.user_id)
             self.assertIsNone(user)
             
    def test_delete_user_admin_fail_password(self):
         # 1. Create administrator user
        with self.app.app_context():
            admin = User(username='admin2', email='admin2@test.com', password='adminpass', role=UserRole.ADMIN)
            db.session.add(admin)
            db.session.commit()
            admin_id = admin.id
            
        with self.client.session_transaction() as sess:
            sess['user_id'] = admin_id
            sess['role'] = 'admin'
            
        # 2. Try delete with WRONG password
        # Expect 403 status code but with HTML content (our error page)
        response = self.client.post(f'/config/users/{self.user_id}/delete', data={'confirmation_password': 'wrongpass'})
        self.assertEqual(response.status_code, 403)
        self.assertIn(b'Action Failed', response.data) # Check for text from error.html
        
        with self.app.app_context():
             user = User.query.get(self.user_id)
             self.assertIsNotNone(user)
             
    def test_delete_user_key_success(self):
        os.environ['CONFIG_ACCESS_KEY'] = 'secretkey'
        
        with self.client.session_transaction() as sess:
            sess['config_access'] = True
            
        # 2. Try delete with correct key
        response = self.client.post(f'/config/users/{self.user_id}/delete', data={'confirmation_password': 'secretkey'})
        self.assertEqual(response.status_code, 302)
        
        with self.app.app_context():
             user = User.query.get(self.user_id)
             self.assertIsNone(user)

if __name__ == '__main__':
    unittest.main()
