from datetime import datetime
from models import db

class Location(db.Model):
    __tablename__ = "locations"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Optional friendly name for the location (e.g. "Home", "Depot 1")
    name = db.Column(db.String(100), nullable=True)
    
    city = db.Column(db.String(100), nullable=False)
    country = db.Column(db.String(100), nullable=False)
    
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationship to User
    user = db.relationship('User', backref=db.backref('locations', lazy=True))

    def __repr__(self):
        return f'<Location {self.city}, {self.country} ({self.latitude}, {self.longitude})>'

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'city': self.city,
            'country': self.country,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
