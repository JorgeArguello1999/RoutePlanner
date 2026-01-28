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
@graphs.route('/export_pdf')
@login_required
def export_route_pdf():
    user_id = session.get('user_id')
    u = request.args.get('u', type=int)
    v = request.args.get('v', type=int)
    mid = request.args.get('mid', type=int)
    mid_lat = request.args.get('mid_lat', type=float)
    mid_lon = request.args.get('mid_lon', type=float)

    # Generate Graph Image (re-using controller logic to get the image buffer)
    graph_img = generate_location_graph(user_id, start_id=u, end_id=v, mid_id=mid, mid_coords=(mid_lat, mid_lon) if mid_lat else None)
    
    # Gather Details (In a real app, logic would be separated to return data struct, here we approximate)
    from models.locations import Location
    # Fetch names for the PDF
    start_name = "Start"
    end_name = "End"
    if u:
        loc = Location.query.get(u)
        if loc: start_name = loc.name or loc.city
    if v:
        loc = Location.query.get(v)
        if loc: end_name = loc.name or loc.city

    import math
    def haversine(lat1, lon1, lat2, lon2):
        R = 6371
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2) * math.sin(dlambda/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c

    total_dist = 0
    # Calculate Distances
    loc_start = Location.query.get(u) if u else None
    loc_end = Location.query.get(v) if v else None
    
    if loc_start and loc_end:
        if mid:
            loc_mid = Location.query.get(mid)
            if loc_mid:
                d1 = haversine(loc_start.latitude, loc_start.longitude, loc_mid.latitude, loc_mid.longitude)
                d2 = haversine(loc_mid.latitude, loc_mid.longitude, loc_end.latitude, loc_end.longitude)
                total_dist = d1 + d2
        elif mid_lat and mid_lon:
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
        'end_name': end_name,
        'mid_name': "Custom Point" if (mid or (mid_lat and mid_lon)) else None, # Simplified for custom
        'distance': f"{total_dist:.2f}",
        'time': time_str
    }

    pdf_file = generate_route_pdf(graph_img, details)
    
    return send_file(
        pdf_file,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'route_report_{u}_{v}.pdf'
    )
