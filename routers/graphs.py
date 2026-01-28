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

from controllers.export import generate_route_pdf
@graphs.route('/export_pdf', methods=['GET', 'POST'])
@login_required
def export_route_pdf():
    user_id = session.get('user_id')
    
    # Support both GET (legacy/simple) and POST (with map image)
    if request.method == 'POST':
        data = request.get_json()
        if not data:
            data = request.form
            
        u = int(data.get('u')) if data.get('u') else None
        v = int(data.get('v')) if data.get('v') else None
        mid = int(data.get('mid')) if data.get('mid') else None
        
        try:
            mid_lat = float(data.get('mid_lat')) if data.get('mid_lat') else None
            mid_lon = float(data.get('mid_lon')) if data.get('mid_lon') else None
        except (ValueError, TypeError):
             mid_lat = None
             mid_lon = None
             
        map_image = data.get('map_image')
    else:
        u = request.args.get('u', type=int)
        v = request.args.get('v', type=int)
        mid = request.args.get('mid', type=int)
        mid_lat = request.args.get('mid_lat', type=float)
        mid_lon = request.args.get('mid_lon', type=float)
        map_image = None

    # Generate Graph Image (re-using controller logic)
    graph_img = generate_location_graph(user_id, start_id=u, end_id=v, mid_id=mid, mid_coords=(mid_lat, mid_lon) if mid_lat else None)
    
    # Gather Details
    from models.locations import Location
    start_name = "Start"
    end_name = "End"
    start_coords = ""
    end_coords = ""
    mid_name = None
    mid_coords_str = ""

    import math
    def haversine(lat1, lon1, lat2, lon2):
        if lat1 is None or lon1 is None or lat2 is None or lon2 is None: return 0
        R = 6371
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2) * math.sin(dlambda/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c

    total_dist = 0
    # Fetch Locations
    loc_start = Location.query.get(u) if u else None
    loc_end = Location.query.get(v) if v else None
    
    if loc_start: 
        start_name = loc_start.name or loc_start.city
        start_coords = f"{loc_start.latitude}, {loc_start.longitude}"
    
    if loc_end: 
        end_name = loc_end.name or loc_end.city
        end_coords = f"{loc_end.latitude}, {loc_end.longitude}"

    if loc_start and loc_end:
        if mid:
            loc_mid = Location.query.get(mid)
            if loc_mid:
                mid_name = loc_mid.name or loc_mid.city
                mid_coords_str = f"{loc_mid.latitude}, {loc_mid.longitude}"
                d1 = haversine(loc_start.latitude, loc_start.longitude, loc_mid.latitude, loc_mid.longitude)
                d2 = haversine(loc_mid.latitude, loc_mid.longitude, loc_end.latitude, loc_end.longitude)
                total_dist = d1 + d2
        elif mid_lat and mid_lon:
             mid_name = "Custom Point"
             mid_coords_str = f"{mid_lat}, {mid_lon}"
             d1 = haversine(loc_start.latitude, loc_start.longitude, mid_lat, mid_lon)
             d2 = haversine(mid_lat, mid_lon, loc_end.latitude, loc_end.longitude)
             total_dist = d1 + d2
        else:
             total_dist = haversine(loc_start.latitude, loc_start.longitude, loc_end.latitude, loc_end.longitude)

    # Time (60 km/h)
    hours = total_dist / 60
    mins = int(hours * 60)
    time_str = f"{mins} min" if mins < 60 else f"{hours:.1f} hr"

    details = {
        'username': session.get('username', 'User'),
        'start_name': start_name,
        'start_coords': start_coords,
        'end_name': end_name,
        'end_coords': end_coords,
        'mid_name': mid_name,
        'mid_coords': mid_coords_str,
        'distance': f"{total_dist:.2f}",
        'time': time_str
    }

    pdf_file = generate_route_pdf(graph_img, details, map_image_base64=map_image)
    
    return send_file(
        pdf_file,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'route_report_{u}_{v}.pdf'
    )
