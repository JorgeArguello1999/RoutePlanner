import os

# Default valid Fernet key (generated with Fernet.generate_key())
# Development only / fallback when no environment variable is set.
_DEFAULT_FERNET_KEY = "0A1glB0r_8tPpo8k9eeWZW3TXvkvCPpw1ZgBmsV5D6s="
_DEFAULT_SECRET = "dev-secret-key-change-in-production"

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY') or _DEFAULT_SECRET
    ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY') or _DEFAULT_FERNET_KEY
    # Single-image default: SQLite (instance/routeplanner.db). Override with DATABASE_URL for MySQL/PostgreSQL
    # Examples:
    #   SQLite (default):  DATABASE_URL=  (empty)
    #   MySQL:             DATABASE_URL=mysql+pymysql://user:pass@host:3306/routeplanner
    #   PostgreSQL:        DATABASE_URL=postgresql+psycopg2://user:pass@host:5432/routeplanner
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL') or os.getenv('SQLALCHEMY_DATABASE_URI') or "sqlite:///routeplanner.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False