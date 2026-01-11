from flask import Blueprint, request
from controllers.configuration import index_page, login_page, update_role, update_password, delete_routes
from utils.auth import admin_or_key_required

configuration = Blueprint('configuration', __name__, url_prefix='/config')

@configuration.route('/', endpoint='config_index', methods=['GET'])
@admin_or_key_required
def config_index():
    return index_page(request)

@configuration.route('/login', endpoint='config_login', methods=['GET', 'POST'])
def config_login():
    return login_page(request)

@configuration.route('/users/<int:user_id>/role', endpoint='update_role', methods=['POST'])
@admin_or_key_required
def route_update_role(user_id):
    return update_role(request, user_id)

@configuration.route('/users/<int:user_id>/password', endpoint='update_password', methods=['POST'])
@admin_or_key_required
def route_update_password(user_id):
    return update_password(request, user_id)

@configuration.route('/users/<int:user_id>/delete-routes', endpoint='delete_routes', methods=['POST'])
@admin_or_key_required
def route_delete_routes(user_id):
    return delete_routes(request, user_id)
