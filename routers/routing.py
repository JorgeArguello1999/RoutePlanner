"""Routing API router (backend OSRM proxy)."""

from flask import Blueprint, jsonify, request

from controllers.routing import RoutingError, get_road_route, parse_coordinate
from utils.auth import login_required

routing_bp = Blueprint("routing", __name__, url_prefix="/api")


def _waypoints_from_query(args):
    """Build a waypoint list from GET query parameters."""
    coordinates = args.get("coordinates")
    if coordinates:
        waypoints = []
        for chunk in coordinates.split(";"):
            if "," not in chunk:
                continue
            lon_raw, lat_raw = chunk.split(",", 1)
            waypoints.append(
                {
                    "latitude": parse_coordinate(lat_raw.strip(), "latitude"),
                    "longitude": parse_coordinate(lon_raw.strip(), "longitude"),
                }
            )
        return waypoints

    origin_lat = args.get("a_lat", args.get("origin_lat"))
    origin_lon = args.get("a_lon", args.get("origin_lon"))
    dest_lat = args.get("b_lat", args.get("destination_lat"))
    dest_lon = args.get("b_lon", args.get("destination_lon"))
    if origin_lat is None or origin_lon is None or dest_lat is None or dest_lon is None:
        return None
    waypoints = [
        {"latitude": origin_lat, "longitude": origin_lon},
        {"latitude": dest_lat, "longitude": dest_lon},
    ]
    mid_lat = args.get("mid_lat", args.get("m_lat"))
    mid_lon = args.get("mid_lon", args.get("m_lon"))
    if mid_lat is not None and mid_lon is not None:
        waypoints.insert(1, {"latitude": mid_lat, "longitude": mid_lon})
    return waypoints


def _waypoints_from_body(data):
    """Build a waypoint list from a POST JSON payload."""
    if not isinstance(data, dict):
        return None
    if isinstance(data.get("waypoints"), list):
        return data.get("waypoints")
    if isinstance(data.get("points"), list):
        return data.get("points")
    origin = data.get("origin") or data.get("start") or data.get("pointA")
    destination = data.get("destination") or data.get("end") or data.get("pointB")
    intermediate = data.get("intermediate") or data.get("mid") or data.get("pointMid")
    if origin and destination:
        waypoints = [origin]
        if intermediate:
            waypoints.append(intermediate)
        waypoints.append(destination)
        return waypoints
    return None


@routing_bp.route("/route", methods=["GET", "POST"])
@login_required
def get_route():
    """Return road route geometry via the server-side OSRM proxy."""
    try:
        if request.method == "GET":
            raw_waypoints = _waypoints_from_query(request.args)
        else:
            raw_waypoints = _waypoints_from_body(request.get_json(silent=True))
        if not raw_waypoints:
            return jsonify({"code": "InvalidInput", "message": (
                "Provide waypoints as JSON {waypoints: [{latitude, longitude}, ...]} "
                "or GET params ?a_lat=&a_lon=&b_lat=&b_lon=&mid_lat=&mid_lon="
            )}), 400
        result = get_road_route(raw_waypoints)
        return jsonify(result)
    except RoutingError as exc:
        return jsonify({"code": "RoutingError", "message": exc.message}), exc.status_code
    except Exception as exc:  # noqa: BLE001 - return JSON instead of HTML 500
        print(f"Unexpected routing error: {exc}")
        return jsonify({"code": "InternalError", "message": "Failed to calculate route"}), 500
