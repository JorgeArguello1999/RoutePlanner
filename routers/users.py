from flask import Blueprint
from controllers.users import create_user

users = Blueprint('users', __name__, url_prefix='/users')

@users.route('/signin', endpoint='signin')
def users_home():
    create_user()
    return "Users Home Page"

@users.route('/signup', endpoint='signup')
def users_signup():
    return "Users Signup Page"