from routers.index import home_page
from routers.users import users
from routers.dashboard import dashboard_page
from routers.routes import routes_page

from routers.locations import locations

from routers.graphs import graphs

from routers.configuration import configuration

def register_routes(app):
    app.register_blueprint(home_page)
    app.register_blueprint(users)
    app.register_blueprint(dashboard_page)
    app.register_blueprint(routes_page)
    app.register_blueprint(locations)
    app.register_blueprint(graphs)
    app.register_blueprint(configuration)