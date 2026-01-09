from models import db
from models.locations import Location

def get_locations(user_id):
    """Retrieve all locations for a specific user"""
    locations = Location.query.filter_by(user_id=user_id).all()
    return [loc.to_dict() for loc in locations]

def create_location(user_id, data):
    """Create a new location for a user"""
    try:
        new_location = Location(
            user_id=user_id,
            name=data.get('name'),
            city=data.get('city'),
            country=data.get('country'),
            latitude=data.get('latitude'),
            longitude=data.get('longitude')
        )
        db.session.add(new_location)
        db.session.commit()
        return new_location.to_dict()
    except Exception as e:
        db.session.rollback()
        raise e

def update_location(user_id, location_id, data):
    """Update an existing location"""
    location = Location.query.filter_by(id=location_id, user_id=user_id).first()
    if not location:
        return None
    
    try:
        if 'name' in data:
            location.name = data.get('name')
        if 'city' in data:
            location.city = data.get('city')
        if 'country' in data:
            location.country = data.get('country')
        if 'latitude' in data:
            location.latitude = data.get('latitude')
        if 'longitude' in data:
            location.longitude = data.get('longitude')
        
        db.session.commit()
        return location.to_dict()
    except Exception as e:
        db.session.rollback()
        raise e

def delete_location(user_id, location_id):
    """Delete a location"""
    location = Location.query.filter_by(id=location_id, user_id=user_id).first()
    if not location:
        return False
    
    try:
        db.session.delete(location)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        raise e
