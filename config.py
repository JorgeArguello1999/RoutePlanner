import os

# Clave Fernet válida por defecto (generada con Fernet.generate_key())
# Solo para desarrollo / fallback si no hay variable de entorno.
_DEFAULT_FERNET_KEY = "0A1glB0r_8tPpo8k9eeWZW3TXvkvCPpw1ZgBmsV5D6s="
_DEFAULT_SECRET = "dev-secret-key-change-in-production"

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY') or _DEFAULT_SECRET
    ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY') or _DEFAULT_FERNET_KEY
    # Fallback a sqlite para `uv run app.py` sin Docker; en Docker se inyecta mysql+pymysql://...
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL') or os.getenv('SQLALCHEMY_DATABASE_URI') or "sqlite:///routeplanner.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False