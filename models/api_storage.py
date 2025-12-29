from models import db

class API_Storage(db.Model):
    __tablename__ = "api_storage"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(80), nullable=False)
    _api_key = db.Column("api_key", db.String(256), nullable=False)
    
    # Foreign Key to User
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('api_keys', lazy=True))

    @property
    def api_key(self):
        from utils.encryption import Encryption
        encryption = Encryption()
        if self._api_key:
            return encryption.decrypt_value(self._api_key)
        return None

    @api_key.setter
    def api_key(self, value):
        from utils.encryption import Encryption
        encryption = Encryption()
        self._api_key = encryption.encrypt_value(value)

    def __repr__(self):
        return f'<API_Storage {self.name}>'