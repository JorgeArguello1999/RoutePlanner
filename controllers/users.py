from models.users import User
from models import db

def create_user():
    new_user = User(username="testuser", email="testuser@example.com")
    db.session.add(new_user)
    db.session.commit()
    return True
