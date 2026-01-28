from datetime import datetime
from models import db

class RouteHistory(db.Model):
    __tablename__ = "route_history"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Start Point
    start_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=True)
    start_lat = db.Column(db.Float, nullable=True) # Used if start_id is null (unlikely with current UI but good for robustness)
    start_lon = db.Column(db.Float, nullable=True)
    start_name = db.Column(db.String(100), nullable=True) # Snapshot of name

    # End Point
    end_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=True)
    end_lat = db.Column(db.Float, nullable=True)
    end_lon = db.Column(db.Float, nullable=True)
    end_name = db.Column(db.String(100), nullable=True)

    # Mid Point (Optional)
    mid_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=True)
    mid_lat = db.Column(db.Float, nullable=True)
    mid_lon = db.Column(db.Float, nullable=True)
    mid_name = db.Column(db.String(100), nullable=True)

    # Metrics
    distance_km = db.Column(db.Float, nullable=False)
    estimated_time_min = db.Column(db.Integer, nullable=False)
    
    # Type of route saved (Road vs Graph metric mainly, but we store the result)
    route_type = db.Column(db.String(20), default='mixed') 

    created_at = db.Column(db.DateTime, default=datetime.now)

    # Relationships
    user = db.relationship('User', backref=db.backref('history', lazy=True))
    # We can add relationships to Location if needed, but simple FKs are often enough for history

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'start': {
                'id': self.start_id,
                'name': self.start_name,
                'lat': self.start_lat,
                'lon': self.start_lon
            },
            'end': {
                'id': self.end_id,
                'name': self.end_name,
                'lat': self.end_lat,
                'lon': self.end_lon
            },
            'mid': {
                'id': self.mid_id,
                'name': self.mid_name,
                'lat': self.mid_lat,
                'lon': self.mid_lon
            } if (self.mid_id or self.mid_lat) else None,
            'distance_km': self.distance_km,
            'estimated_time_min': self.estimated_time_min,
            'created_at': self.created_at.isoformat()
        }
