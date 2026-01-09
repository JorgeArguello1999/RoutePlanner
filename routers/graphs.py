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
    mid = request.args.get('mid', type=int)
    mid_lat = request.args.get('mid_lat', type=float)
    mid_lon = request.args.get('mid_lon', type=float)
    
    highlight = []
    if u and v:
        if mid:
            highlight = [(u, mid), (mid, v)]
        elif mid_lat is not None and mid_lon is not None:
            # For custom mid locations, we pass the custom info 
            # Controller will handle the tuple structure/IDs for custom points
            pass # Logic handled in controller call
        else:
            highlight = [(u, v)]

    img_io = generate_location_graph(user_id, start_id=u, end_id=v, mid_id=mid, mid_coords=(mid_lat, mid_lon) if mid_lat else None)
    return send_file(img_io, mimetype='image/png')
