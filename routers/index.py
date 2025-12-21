from flask import Blueprint, redirect, url_for
from flask import request
from flask import session

from controllers import index

home_page = Blueprint('home_page', __name__, url_prefix='/')

@home_page.route('/')
def home():
    try:
        print(request.cookies)
        if 'user_id' not in session:
            return index.home()
        return redirect(url_for('dashboard.home'))

    except Exception as e:
        print(e)
        return "An error occurred", 500

@home_page.route('/about')
def about():
    try:
        return index.about()
    except Exception as e:
        print(e)
        return "An error occurred", 500