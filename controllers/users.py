# Flask 
from flask import render_template, url_for
from flask import session
from flask import redirect

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

# GET / Signin Page / Handler
def signin_page(request_form):
    """ Render the signin page """
    if request_form.method == 'GET':
        return render_template(f"{TEMPLATES_DIR}signin.html")

    elif request_form.method == 'POST':
        username = request_form.form.get('username')
        password = request_form.form.get('password')
        user = User.query.filter_by(username=username).first()

        message = "Invalid username or password"
        if user and user.check_password(password):
            message = "Signin successful"
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role.value
            return redirect('/dashboard')

        return render_template(f"{TEMPLATES_DIR}signin.html", message=message)

# GET / Signup Page / Handler
def signup_page(request_form):
    """ Render the signup page """
    if request_form.method == 'GET':
        return render_template(f"{TEMPLATES_DIR}signup.html")

    elif request_form.method == 'POST':
        username = request_form.form.get('username')
        email = request_form.form.get('email')
        password = request_form.form.get('password')
        confirm_password = request_form.form.get('confirm_password')
        terms_accepted = request_form.form.get('terms_accepted')

        # Validation
        if password != confirm_password:
             return render_template(f"{TEMPLATES_DIR}signup.html", result={
                "username": username,
                "email": email,
                "message": "Passwords do not match"
            })
        
        if not terms_accepted:
            return render_template(f"{TEMPLATES_DIR}signup.html", result={
                "username": username,
                "email": email,
                "message": "You must agree to the terms and conditions"
            })

        answer = create_user(username, email, password)
        return render_template(f"{TEMPLATES_DIR}signup.html", result=answer)

# POST / Create User
def create_user(username: str, email: str, password: str) -> UserSignupResponse:
    """ Create a new user in the database """
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

# GET / Signout Page / Handler
def signout_page(request):
    """ Sign out the current user """
    session.clear()
    return redirect(url_for('home_page.home'))

# GET/POST / Update Profile
def update_profile_page(request_form):
    """ Handle profile updates """
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    
    if request_form.method == 'GET':
        # If the request asks for JSON, return JSON (for API/Testing)
        if request_form.headers.get('Content-Type') == 'application/json':
             return {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role.value
            }
        
        # Otherwise render the template
        return render_template(f"{TEMPLATES_DIR}update.html", user=user)

    elif request_form.method == 'POST':
        is_json = request_form.is_json
        data = request_form.get_json() if is_json else request_form.form
        
        new_username = data.get('username')
        new_email = data.get('email')
        
        message = None
        error = None

        # Validation
        if new_username and new_username != user.username:
            if User.query.filter_by(username=new_username).first():
                error = "Username already taken"
            else:
                user.username = new_username
            
        if not error and new_email and new_email != user.email:
            if User.query.filter_by(email=new_email).first():
                error = "Email already taken"
            else:
                user.email = new_email
            
        try:
            if not error:
                db.session.commit()
                # Update session if username changed
                session['username'] = user.username
                message = "Profile updated successfully"
            
            if is_json:
                if error: return {"error": error}, 400
                return {"message": message}
            
            return render_template(f"{TEMPLATES_DIR}update.html", user=user, message=message, error=error)

        except Exception as e:
            db.session.rollback()
            if is_json: return {"error": str(e)}, 500
            return render_template(f"{TEMPLATES_DIR}update.html", user=user, error="An error occurred"), 500

# GET/POST / Change Password
def change_password_page(request_form):
    """ Handle password changes """
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    
    if request_form.method == 'GET':
        return {"message": "Submit POST request with current_password, new_password, and confirm_password"}

    elif request_form.method == 'POST':
        data = request_form.form if request_form.form else request_form.get_json()
        
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')
        
        if not user.check_password(current_password):
            return {"error": "Incorrect current password"}, 401
            
        if new_password != confirm_password:
            return {"error": "New passwords do not match"}, 400
            
        if not new_password:
            return {"error": "New password cannot be empty"}, 400
            
        try:
            user.password = new_password
            db.session.commit()
            return {"message": "Password changed successfully"}
        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500