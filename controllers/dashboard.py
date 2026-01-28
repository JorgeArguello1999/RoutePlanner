import json
from flask import render_template, session
from models.locations import Location
from models.routes import RouteHistory

# Template directory
TEMPLATES_DIR = 'map/'

def home():
    user_id = session.get('user_id')
    locations = []
    locations_count = 0
    history_count = 0
    
    if user_id:
        locations_query = Location.query.filter_by(user_id=user_id).all()
        locations_count = len(locations_query)
        locations = [loc.to_dict() for loc in locations_query]
        
        history_count = RouteHistory.query.filter_by(user_id=user_id).count()

    return render_template(
        f'{TEMPLATES_DIR}dashboard.html',
        locations_count=locations_count,
        history_count=history_count,
        locations=json.dumps(locations)
    )