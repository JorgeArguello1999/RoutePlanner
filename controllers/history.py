from flask import render_template
from models import db
from models.routes import RouteHistory
from models.locations import Location

def get_history_page(request_obj):
    # Fetch history for current user
    from flask import session
    user_id = session.get('user_id')

    
    history_items = RouteHistory.query.filter_by(user_id=user_id).order_by(RouteHistory.created_at.desc()).all()
    
    return render_template('history/index.html', history=history_items)

def save_route_controller(data):
    from flask import session
    user_id = session.get('user_id')
    
    try:
        # Extract data
        start_id = data.get('start_id')
        end_id = data.get('end_id')
        mid_id = data.get('mid_id')
        
        # Helper to get name/coords if ID provided
        start_name = data.get('start_name')
        start_lat = data.get('start_lat')
        start_lon = data.get('start_lon')
        
        if start_id:
            loc = Location.query.get(start_id)
            if loc:
                start_name = loc.name or loc.city
                start_lat = loc.latitude
                start_lon = loc.longitude

        end_name = data.get('end_name')
        end_lat = data.get('end_lat')
        end_lon = data.get('end_lon')
        if end_id:
            loc = Location.query.get(end_id)
            if loc:
                end_name = loc.name or loc.city
                end_lat = loc.latitude
                end_lon = loc.longitude

        mid_name = data.get('mid_name')
        mid_lat = data.get('mid_lat')
        mid_lon = data.get('mid_lon')
        if mid_id:
            loc = Location.query.get(mid_id)
            if loc:
                mid_name = loc.name or loc.city
                mid_lat = loc.latitude
                mid_lon = loc.longitude

        new_history = RouteHistory(
            user_id=user_id,
            start_id=start_id,
            start_name=start_name,
            start_lat=start_lat,
            start_lon=start_lon,
            end_id=end_id,
            end_name=end_name,
            end_lat=end_lat,
            end_lon=end_lon,
            mid_id=mid_id,
            mid_name=mid_name,
            mid_lat=mid_lat,
            mid_lon=mid_lon,
            distance_km=data.get('distance_km'),
            estimated_time_min=data.get('estimated_time_min')
        )
        
        db.session.add(new_history)
        db.session.commit()
        
        return {"message": "Route saved successfully", "id": new_history.id}
    except Exception as e:
        db.session.rollback()
        print(f"Error saving route: {e}")
        return {"error": "Failed to save route"}, 500

def delete_route_controller(route_id):
    from flask import session
    user_id = session.get('user_id')
    
    route = RouteHistory.query.filter_by(id=route_id, user_id=user_id).first()
    if route:
        try:
            db.session.delete(route)
            db.session.commit()
            return {"message": "Route deleted"}
        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500
    return {"error": "Route not found"}, 404
