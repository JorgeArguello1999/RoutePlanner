from flask import Blueprint
from flask import request

from controllers.users import signup_page, signin_page, signout_page

users = Blueprint('users', __name__, url_prefix='/users')

@users.route('/signup', endpoint='signup', methods=['GET', 'POST'])
def users_home():
    try: 
        return signup_page(request)
    except Exception as e:
        print(e)
        return "An error occurred", 500

@users.route('/signin', endpoint='signin', methods=['GET', 'POST'])
def users_signin():
    try:
        return signin_page(request)
    except Exception as e:
        print(e)
        return "An error occurred", 500

@users.route('/signout', endpoint='signout', methods=['GET'])
def users_signout():
    try:
        return signout_page(request)
    except Exception as e:
        print(e)
        return "An error occurred", 500