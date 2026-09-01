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
    # Integration of verification as requested
    try:
        from test.verify_locations import verify
        print("Running startup verification...")
        verify()
    except Exception as e:
        print(f"Verification failed: {e}")

    def _parse_bool(v):
        if isinstance(v, bool):
            return v
        if v is None:
            return False
        return str(v).lower() in ("1", "true", "yes", "on")

    _debug = _parse_bool(getenv('DEBUG', 'False'))
    _host = getenv('HOST', '127.0.0.1')
    _port = int(getenv('PORT', '8003'))
    app.run(host=_host, port=_port, debug=_debug)