from flask import Blueprint, send_file, session
from controllers.graphs import generate_location_graph
from utils.auth import login_required

graphs = Blueprint('graphs', __name__, url_prefix='/graphs')

@graphs.route('/locations.png')
@login_required
def get_location_graph():
    user_id = session.get('user_id')
    img_io = generate_location_graph(user_id)
    return send_file(img_io, mimetype='image/png')
