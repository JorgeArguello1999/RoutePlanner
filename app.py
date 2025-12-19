from dotenv import load_dotenv
from os import getenv
load_dotenv()

from flask import Flask
from config import Config

# Models
from models import init_db

# Routes 
from routers import register_routes

app = Flask(__name__)
app.config.from_object(Config)

# Initialize DB and Migrations
init_db(app)

register_routes(app)

if __name__ == "__main__":
    app.run(debug=getenv('DEBUG'))