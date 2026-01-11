from flask import render_template, redirect, url_for, session, request
import os
from models.users import User, UserRole
from models.locations import Location
from models import db

TEMPLATES_DIR = 'configuration/'

def index_page(request):
    """Render the configuration dashboard"""
    # Placeholder for configuration data
    config_data = {
        "openweather_key": "Configured" if os.getenv('OPENWEATHER_API_KEY') else "Not Configured",
        "sensors_count": 0, # Placeholder
    }
    
    # Fetch all users and count their locations
    users = User.query.all()
    users_data = []
    for user in users:
        users_data.append({
            "id": user.id,
            "username": user.username,
            "role": user.role.value,
            "routes_count": len(user.locations)
        })
        
    return render_template(f"{TEMPLATES_DIR}index.html", config=config_data, users=users_data, roles=[r.value for r in UserRole])

def login_page(request):
    """Handle configuration login"""
    if request.method == 'GET':
        return render_template(f"{TEMPLATES_DIR}login.html")
    
    elif request.method == 'POST':
        key = request.form.get('access_key')
        env_key = os.getenv('CONFIG_ACCESS_KEY')
        
        if key == env_key:
            session['config_access'] = True
            next_url = request.args.get('next') or url_for('configuration.config_index')
            return redirect(next_url)
        
        return render_template(f"{TEMPLATES_DIR}login.html", error="Invalid Access Key")

def update_role(request, user_id):
    """Update user role"""
    user = User.query.get(user_id)
    if not user:
        return render_template(f'{TEMPLATES_DIR}error.html', error="User not found"), 404
        
    new_role = request.form.get('role')
    if new_role not in [r.value for r in UserRole]:
        return render_template(f'{TEMPLATES_DIR}error.html', error="Invalid role"), 400
        
    try:
        user.role = UserRole(new_role)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(e)
        return render_template(f'{TEMPLATES_DIR}error.html', error="Error updating role"), 500
        
    return redirect(url_for('configuration.config_index'))

def update_password(request, user_id):
    """Update user password"""
    user = User.query.get(user_id)
    if not user:
        return render_template(f'{TEMPLATES_DIR}error.html', error="User not found"), 404
        
    new_password = request.form.get('password')
    if not new_password:
        return render_template(f'{TEMPLATES_DIR}error.html', error="Password required"), 400
        
    try:
        user.password = new_password
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(e)
        return render_template(f'{TEMPLATES_DIR}error.html', error="Error updating password"), 500
        
    return redirect(url_for('configuration.config_index'))


def delete_routes(request, user_id):
    """Delete all text routes (locations) for a user"""
    user = User.query.get(user_id)
    if not user:
        return render_template(f'{TEMPLATES_DIR}error.html', error="User not found"), 404
        
    try:
        Location.query.filter_by(user_id=user_id).delete()
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(e)
        return render_template(f'{TEMPLATES_DIR}error.html', error="Error deleting routes"), 500
        
    return redirect(url_for('configuration.config_index'))

def delete_user(request, user_id):
    """Delete a user and their locations"""
    target_user = User.query.get(user_id)
    if not target_user:
        return render_template(f'{TEMPLATES_DIR}error.html', error="User not found"), 404
    
    confirmation_password = request.form.get('confirmation_password')
    if not confirmation_password:
        return render_template(f'{TEMPLATES_DIR}error.html', error="Confirmation password required"), 400
        
    # Verify Auth: Always check against CONFIG_ACCESS_KEY (Admin Password from Env)
    env_key = os.getenv('CONFIG_ACCESS_KEY')
    if confirmation_password != env_key:
         return render_template(f'{TEMPLATES_DIR}error.html', error="Invalid confirmation password (Env Key)"), 403
         
    try:
        # Delete locations first (if not cascading) - assumed cascade or manual
        Location.query.filter_by(user_id=user_id).delete()
        
        # Delete User
        db.session.delete(target_user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(e)
        return render_template(f'{TEMPLATES_DIR}error.html', error="Error deleting user"), 500
        
    return redirect(url_for('configuration.config_index'))
