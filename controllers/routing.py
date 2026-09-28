"""OSRM routing proxy controller.

Provides server-side access to the public OSRM demo server so the
frontend does not depend on direct browser-to-OSRM calls (CORS,
mixed-content, rate limits). All identifiers and messages are in English.
"""

import json
import os
import urllib.parse
import urllib.request
import urllib.error

OSRM_BASE_URL = os.getenv("OSRM_BASE_URL", "https://router.project-osrm.org")
OSRM_TIMEOUT_SECONDS = float(os.getenv("OSRM_TIMEOUT", "10"))
OSRM_PROFILE = os.getenv("OSRM_PROFILE", "driving")
MAX_WAYPOINTS = 10


class RoutingError(Exception):
    """Raised when input validation or the upstream OSRM call fails."""

    def __init__(self, message, status_code=502):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def parse_coordinate(value, field_name):
    """Parse a latitude/longitude value and validate its range."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise RoutingError(f"Invalid coordinate for {field_name}: {value!r}", 400)
    if "lat" in field_name and not -90 <= number <= 90:
        raise RoutingError(f"Latitude out of range for {field_name}: {number}", 400)
    if ("lon" in field_name or "lng" in field_name) and not -180 <= number <= 180:
        raise RoutingError(f"Longitude out of range for {field_name}: {number}", 400)
    return number


def normalize_waypoints(raw_waypoints):
    """Normalize a waypoint list into [(latitude, longitude), ...]."""
    if not isinstance(raw_waypoints, list) or not 2 <= len(raw_waypoints) <= MAX_WAYPOINTS:
        raise RoutingError(
            f"waypoints must be a list with 2 to {MAX_WAYPOINTS} items", 400
        )
    normalized = []
    for index, item in enumerate(raw_waypoints):
        if isinstance(item, (list, tuple)) and len(item) == 2:
            lat_raw, lon_raw = item
        elif isinstance(item, dict):
            lat_raw = item.get("latitude", item.get("lat"))
            lon_raw = item.get("longitude", item.get("lon", item.get("lng")))
        else:
            raise RoutingError(f"Invalid waypoint at index {index}: {item!r}", 400)
        lat = parse_coordinate(lat_raw, f"waypoints[{index}].latitude")
        lon = parse_coordinate(lon_raw, f"waypoints[{index}].longitude")
        normalized.append((lat, lon))
    return normalized


def build_osrm_url(waypoints):
    """Build the upstream OSRM request URL for normalized waypoints."""
    coords = ";".join(f"{lon},{lat}" for lat, lon in waypoints)
    params = urllib.parse.urlencode(
        {"overview": "full", "geometries": "geojson", "steps": "false"}
    )
    return f"{OSRM_BASE_URL}/route/v1/{OSRM_PROFILE}/{coords}?{params}"


def fetch_osrm_route(waypoints):
    """Call OSRM and return a simplified route payload."""
    url = build_osrm_url(waypoints)
    request = urllib.request.Request(
        url, headers={"User-Agent": "RoutePlanner/1.0", "Accept": "application/json"}
    )
    try:
        with urllib.request.urlopen(request, timeout=OSRM_TIMEOUT_SECONDS) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise RoutingError(f"OSRM upstream HTTP {exc.code}", 502)
    except urllib.error.URLError as exc:
        raise RoutingError(f"OSRM upstream unreachable: {exc.reason}", 502)
    except TimeoutError:
        raise RoutingError("OSRM upstream timeout", 504)
    except (ValueError, json.JSONDecodeError):
        raise RoutingError("OSRM upstream returned invalid JSON", 502)

    if payload.get("code") != "Ok" or not payload.get("routes"):
        reason = payload.get("code", "NoRoute")
        raise RoutingError(f"OSRM could not build route: {reason}", 422)

    route = payload["routes"][0]
    return {
        "code": "Ok",
        "source": "osrm-proxy",
        "distance_km": round(route.get("distance", 0) / 1000, 2),
        "duration_min": round(route.get("duration", 0) / 60),
        "routes": [
            {
                "distance": route.get("distance"),
                "duration": route.get("duration"),
                "geometry": route.get("geometry"),
            }
        ],
    }


def get_road_route(raw_waypoints):
    """Validate input and return the OSRM route payload."""
    waypoints = normalize_waypoints(raw_waypoints)
    return fetch_osrm_route(waypoints)
