from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate  # <--- Import Migrate

db = SQLAlchemy()
migrate = Migrate()  # <--- Instantiate Migrate

def init_db(app):
    """
    Initializes DB and Migrations.
    """
    db.init_app(app)
    
    # Initialize Migrate with app and db
    migrate.init_app(app, db) 

    # We still need the app context to import models so Alembic detects them
    with app.app_context():
        from models.users import User
        from models.api_storage import API_Storage
        from models.locations import Location
        from models.routes import RouteHistory
        # Import other models here...

        # NOTE: When using migrations, we usually DISABLE db.create_all()
        # db.create_all()