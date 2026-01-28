from flask import Blueprint, request, jsonify
from utils.auth import login_required
from controllers.history import get_history_page, save_route_controller, delete_route_controller

history_bp = Blueprint('history', __name__, url_prefix='/history')

@history_bp.route('/', methods=['GET'])
@login_required
def index():
    return get_history_page(request)

@history_bp.route('/save', methods=['POST'])
@login_required
def save():
    data = request.get_json()
    return save_route_controller(data)

@history_bp.route('/<int:route_id>', methods=['DELETE'])
@login_required
def delete(route_id):
    return delete_route_controller(route_id)
