from flask import Blueprint, request, jsonify, session
from controllers import locations as locations_controller
from utils.auth import login_required

locations = Blueprint('locations', __name__, url_prefix='/locations')

# Helper to get current user id from session
def get_current_user_id():
    return session.get('user_id')

@locations.route('/', methods=['GET'])
@login_required
def get_locations():
    try:
        user_id = get_current_user_id()
        result = locations_controller.get_locations(user_id)
        return jsonify(result), 200
    except Exception as e:
        print(f"Error getting locations: {e}")
        return jsonify({"error": "An error occurred"}), 500

@locations.route('/', methods=['POST'])
@login_required
def create_location():
    try:
        user_id = get_current_user_id()
        data = request.get_json()
        if not data:
             return jsonify({"error": "Invalid data"}), 400
             
        result = locations_controller.create_location(user_id, data)
        return jsonify(result), 201
    except Exception as e:
        print(f"Error creating location: {e}")
        return jsonify({"error": str(e)}), 500

@locations.route('/<int:location_id>', methods=['PUT'])
@login_required
def update_location(location_id):
    try:
        user_id = get_current_user_id()
        data = request.get_json()
        result = locations_controller.update_location(user_id, location_id, data)
        if result:
            return jsonify(result), 200
        else:
            return jsonify({"error": "Location not found"}), 404
    except Exception as e:
        print(f"Error updating location: {e}")
        return jsonify({"error": str(e)}), 500

@locations.route('/<int:location_id>', methods=['DELETE'])
@login_required
def delete_location(location_id):
    try:
        user_id = get_current_user_id()
        result = locations_controller.delete_location(user_id, location_id)
        if result:
            return jsonify({"message": "Location deleted"}), 200
        else:
            return jsonify({"error": "Location not found"}), 404
    except Exception as e:
        print(f"Error deleting location: {e}")
        return jsonify({"error": str(e)}), 500
