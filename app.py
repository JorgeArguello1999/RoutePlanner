from dotenv import load_dotenv
from os import getenv
load_dotenv()

from flask import Flask

# Routes 
from routers.index import home_page
from routers.users import users

app = Flask(__name__)
app.config['SECRET_KEY'] = getenv('SECRET_KEY')

app.register_blueprint(home_page)
app.register_blueprint(users)

if __name__ == "__main__":
    app.run(debug=getenv('DEBUG'))