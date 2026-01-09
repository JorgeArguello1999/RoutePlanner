from flask import Blueprint, send_file, session, request
from controllers.graphs import generate_location_graph
from utils.auth import login_required

graphs = Blueprint('graphs', __name__, url_prefix='/graphs')

@graphs.route('/locations.png')
@login_required
def get_location_graph():
    user_id = session.get('user_id')
    u = request.args.get('u', type=int)
    v = request.args.get('v', type=int)
    highlight = (u, v) if u and v else None
    
    img_io = generate_location_graph(user_id, highlight_pair=highlight)
    return send_file(img_io, mimetype='image/png')
