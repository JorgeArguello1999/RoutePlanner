import io
import math
import networkx as nx
import matplotlib
matplotlib.use('Agg') # Use non-interactive backend
import matplotlib.pyplot as plt
from flask import send_file, session
from models.locations import Location

def generate_location_graph(user_id, start_id=None, end_id=None, mid_id=None, mid_coords=None):
    """
    Generates a PNG image of the user's location graph.
    Nodes are positioned by (longitude, latitude).
    start_id, end_id: IDs of start and end nodes.
    mid_id: ID of intermediate node (existing location).
    mid_coords: Tuple (lat, lon) for custom intermediate point.
    """
    locations = Location.query.filter_by(user_id=user_id).all()
    
    if not locations:
        plt.figure(figsize=(8, 6))
        plt.text(0.5, 0.5, 'No locations found', ha='center', va='center')
        plt.axis('off')
    else:
        # Create Graph
        G = nx.Graph()
        pos = {}
        labels = {}
        
        # Add existing locations
        for loc in locations:
            pos[loc.id] = (loc.longitude, loc.latitude)
            G.add_node(loc.id)
            labels[loc.id] = loc.name or loc.city

        # Handle Custom Mid Point
        custom_id = -1
        if mid_coords:
            lat, lon = mid_coords
            pos[custom_id] = (lon, lat)
            G.add_node(custom_id)
            labels[custom_id] = "Custom Waypoint"

        plt.figure(figsize=(10, 8))
        
        # Draw Nodes
        # Separate normal nodes from custom node for different styling if needed
        # For simplicity, draw all
        node_colors = ['gold' if n == custom_id else 'skyblue' for n in G.nodes()]
        nx.draw_networkx_nodes(G, pos, node_size=700, node_color=node_colors)
        
        # Draw Labels
        nx.draw_networkx_labels(G, pos, labels=labels, font_size=9, font_weight='bold')

        def haversine(lat1, lon1, lat2, lon2):
            import math
            R = 6371
            phi1, phi2 = math.radians(lat1), math.radians(lat2)
            dphi = math.radians(lat2 - lat1)
            dlambda = math.radians(lon2 - lon1)
            a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2) * math.sin(dlambda/2)**2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
            return R * c

        # Determine Highlighting using Dijkstra
        highlight_edges = []
        path_nodes = []
        if start_id and end_id:
            try:
                 # Construct valid temporary graph for pathfinding
                PF_G = nx.Graph()
                # Add all locations as nodes
                for loc in locations:
                    PF_G.add_node(loc.id)
                if mid_coords:
                     PF_G.add_node(custom_id)

                # Add edges
                # 1. Existing locations
                for i in range(len(locations)):
                    for j in range(i + 1, len(locations)):
                        u = locations[i]
                        v = locations[j]
                        d = haversine(u.latitude, u.longitude, v.latitude, v.longitude)
                        PF_G.add_edge(u.id, v.id, weight=d)
                
                # 2. Custom Point Edges
                if mid_coords:
                    # Connect Custom Point to ALL other nodes to allow finding best path 
                    # OR just start/end if that's the requirement. 
                    # For a true "Route Planner", connecting to all lets Dijkstra decide.
                    # But per previous logic, it seemed to imply Custom is a waypoint between Start/End.
                    # Let's connect Custom to Start and End.
                    start_loc = next((l for l in locations if l.id == start_id), None)
                    end_loc = next((l for l in locations if l.id == end_id), None)
                    
                    if start_loc:
                        d = haversine(start_loc.latitude, start_loc.longitude, mid_lat, mid_lon)
                        PF_G.add_edge(start_id, custom_id, weight=d)
                    if end_loc:
                        d = haversine(mid_lat, mid_lon, end_loc.latitude, end_loc.longitude)
                        PF_G.add_edge(custom_id, end_id, weight=d)

                # Run Dijkstra
                path_nodes = nx.shortest_path(PF_G, source=start_id, target=end_id, weight='weight')
                
                # Create edges from path nodes
                for k in range(len(path_nodes) - 1):
                    u_node = path_nodes[k]
                    v_node = path_nodes[k+1]
                    highlight_edges.append(tuple(sorted((u_node, v_node))))
                    
            except nx.NetworkXNoPath:
                print("No path found between selected nodes.")
            except Exception as e:
                print(f"Pathfinding error: {e}")

        # Draw Edges (Complete Graph for existing locations)
        edges = []
        edge_labels = {}
        colors = []
        widths = []
        styles = []

        # 1. Edges between existing locations
        if len(locations) > 1:
            for i in range(len(locations)):
                for j in range(i + 1, len(locations)):
                    u = locations[i]
                    v = locations[j]
                    
                    dist = haversine(u.latitude, u.longitude, v.latitude, v.longitude)
                    
                    # Store edge info
                    uv_edge = tuple(sorted((u.id, v.id)))
                    
                    G.add_edge(u.id, v.id, weight=dist)
                    edges.append(uv_edge)
                    
                    # Calculate estimated time (assuming 60 km/h)
                    time_hours = dist / 60
                    time_minutes = int(time_hours * 60)
                    time_str = f"{time_minutes} min" if time_minutes < 60 else f"{time_hours:.1f} hr"
                    
                    # Only show label if it's on the path to reduce clutter
                    if uv_edge in highlight_edges:
                        edge_labels[uv_edge] = f"{dist:.2f} km\n({time_str})"
                    
                    if uv_edge in highlight_edges:
                        colors.append('red')
                        widths.append(3.0)
                        styles.append('solid')
                    else:
                        colors.append('lightgray') # Lighter for non-path
                        widths.append(1.0)
                        styles.append('dashed')

        # 2. Edges involving Customer Mid Point
        if mid_coords and start_id and end_id:
            # We re-calculate purely for drawing if they are part of the path
            # (If Dijkstra didn't choose them, we might not want to draw them prominently, 
            # but usually we want to show the Custom point connections if it exists).
            
            # Re-find Start/End locs
            start_loc = next((l for l in locations if l.id == start_id), None)
            end_loc = next((l for l in locations if l.id == end_id), None)
            mid_lat, mid_lon = mid_coords

            potential_custom_edges = []
            if start_loc:
                potential_custom_edges.append((start_id, custom_id, haversine(start_loc.latitude, start_loc.longitude, mid_lat, mid_lon)))
            if end_loc:
                 potential_custom_edges.append((custom_id, end_id, haversine(mid_lat, mid_lon, end_loc.latitude, end_loc.longitude)))
            
            for u_node, v_node, dist in potential_custom_edges:
                edge = tuple(sorted((u_node, v_node)))
                G.add_edge(u_node, v_node, weight=dist)
                edges.append(edge)
                
                time_hours = dist / 60
                time_minutes = int(time_hours * 60)
                time_str = f"{time_minutes} min" if time_minutes < 60 else f"{time_hours:.1f} hr"

                if edge in highlight_edges:
                     edge_labels[edge] = f"{dist:.2f} km\n({time_str})"
                     colors.append('red')
                     widths.append(3.0)
                     styles.append('solid')
                else:
                     # Draw custom connections even if not on path? Yes, usually.
                     edge_labels[edge] = f"{dist:.2f} km\n({time_str})"
                     colors.append('orange')
                     widths.append(2.0)
                     styles.append('dotted')

        # Draw edges
        nx.draw_networkx_edges(G, pos, edgelist=edges, width=widths, alpha=0.6, edge_color=colors, style=styles)
        
        # Draw edge labels
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=8, font_color='black')
        
        plt.title("Location Graph (Haversine Distance - km)")
        plt.xlabel("Longitude")
        plt.ylabel("Latitude")
        plt.grid(True)
        plt.axis('on') 

    # Save to buffer
    img_io = io.BytesIO()
    plt.savefig(img_io, format='png', bbox_inches='tight')
    plt.close()
    img_io.seek(0)
    
    return img_io
