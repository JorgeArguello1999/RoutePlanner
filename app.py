from dotenv import load_dotenv
from os import getenv
load_dotenv()

from flask import Flask

# Routes 
from routers import register_routes

app = Flask(__name__)
app.config['SECRET_KEY'] = getenv('SECRET_KEY')

register_routes(app)

if __name__ == "__main__":
    app.run(debug=getenv('DEBUG'))