from flask import Blueprint

from controllers import index

home_page = Blueprint('home_page', __name__, url_prefix='/')

@home_page.route('/')
def home():
    try:
        return index.home()
    except Exception as e:
        print(e)
        return "An error occurred", 500