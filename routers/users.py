from flask import Flask
from flask import Blueprint

users = Blueprint('users', __name__, url_prefix='/users')

@users.route('/signin', endpoint='signin')
def users_home():
    return "Users Home Page"

@users.route('/signup', endpoint='signup')
def users_signup():
    return "Users Signup Page"