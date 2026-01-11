from functools import wraps
from flask import session, redirect, url_for, request

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is logged in
        if 'user_id' not in session:
            return redirect(url_for('users.signin'))
        
        return f(*args, **kwargs)
    return decorated_function

def admin_or_key_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 1. Check if user is admin
        if session.get('role') == 'admin':
            return f(*args, **kwargs)
        
        # 2. Check if user has entered the correct key (stored in session)
        if session.get('config_access') is True:
            return f(*args, **kwargs)
            
        # 3. If neither, redirect to config login
        # We pass the 'next' URL to redirect back after successful login
        return redirect(url_for('configuration.config_login', next=request.url))
    return decorated_function