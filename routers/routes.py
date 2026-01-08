from flask import Blueprint
from controllers import routes
from utils.auth import login_required

routes_page = Blueprint('routes', __name__, url_prefix='/routes')

@routes_page.route('/', endpoint='home', methods=['GET'])
@login_required
def protected():
    try:
        return routes.home()
    except Exception as e:
        print(e)
        return "An error occurred", 500