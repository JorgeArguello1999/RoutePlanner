from flask import Blueprint

from utils.auth import login_required

from controllers import dashboard

# Protected Home Page
dashboard_page = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@dashboard_page.route('/', endpoint='home', methods=['GET'])
@login_required
def protected():
    try:
        return dashboard.home()
    except Exception as e:
        print(e)
        return "An error occurred", 500
