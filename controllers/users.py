# Flask 
from flask import render_template

# Models 
from models.users import User
from models import db

# Types
from typing import TypedDict, Literal
from models.users import UserRole

# Templates Directory
TEMPLATES_DIR = 'users/'

# User Data Type
class UserSignupResponse(TypedDict):
    username: str
    email: str
    message: Literal["User created successfully", "Username already exists"]

# GET / Signup Page / Handler
def signup_page(request_form):
    """ Render the signup page """
    if request_form.method == 'GET':
        return render_template(f"{TEMPLATES_DIR}signup.html")

    elif request_form.method == 'POST':
        username = request_form.form.get('username')
        email = request_form.form.get('email')
        password = request_form.form.get('password')
        answer = create_user(username, email, password)
        return render_template(f"{TEMPLATES_DIR}signup.html", result=answer)

# POST / Create User
def create_user(username: str, email: str, password: str) -> UserSignupResponse:
    """ """
    try:
        if User.query.filter_by(username=username).first():
            raise Exception("Username already exists")
            
        new_user = User(
            username=username, 
            email=email,
            password=password,
            role=UserRole.USER
        )
        db.session.add(new_user)
        db.session.commit()

        return {
            "username": username,
            "email": email,
            "message": "User created successfully"
        }

    except Exception as e:
        db.session.rollback()
        print(e)

        return {
            "username": username,
            "email": email,
            "message": "Username already exists"
        }
    
    finally:
        db.session.close()