from routers.index import home_page
from routers.users import users

def register_routes(app):
    app.register_blueprint(home_page)
    app.register_blueprint(users)