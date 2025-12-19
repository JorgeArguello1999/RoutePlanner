from flask import Blueprint
from flask import request
from controllers import users as us 

users = Blueprint('users', __name__, url_prefix='/users')

@users.route('/signup', endpoint='signup', methods=['GET', 'POST'])
def users_home():
    try: 
        return us.signup_page(request)
    except Exception as e:
        print(e)
        return "An error occurred", 500