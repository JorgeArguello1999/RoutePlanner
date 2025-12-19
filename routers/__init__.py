from routers.index import home_page
from routers.users import users
from routers.dashboard import dashboard_page

def register_routes(app):
    app.register_blueprint(home_page)
    app.register_blueprint(users)
    app.register_blueprint(dashboard_page)