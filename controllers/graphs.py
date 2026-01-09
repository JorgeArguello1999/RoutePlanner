import io
import math
import networkx as nx
import matplotlib
matplotlib.use('Agg') # Use non-interactive backend
import matplotlib.pyplot as plt
from flask import send_file, session
from models.locations import Location

def generate_location_graph(user_id, highlight_pair=None):
    """
    Generates a PNG image of the user's location graph.
    Nodes are positioned by (longitude, latitude).
    highlight_pair: tuple of (id1, id2) to highlight edge.
    """
    locations = Location.query.filter_by(user_id=user_id).all()
    
    if not locations:
        # Create an empty plot or specific placeholder if no locations
        plt.figure(figsize=(8, 6))
        plt.text(0.5, 0.5, 'No locations found', ha='center', va='center')
        plt.axis('off')
    else:
        # Create Graph
        G = nx.Graph()
        pos = {}
        labels = {}
        
        for loc in locations:
            # Position: (longitude, latitude) - x, y
            # Note: Maps usually have Longitude as X, Latitude as Y
            pos[loc.id] = (loc.longitude, loc.latitude)
            G.add_node(loc.id)
            labels[loc.id] = loc.name or loc.city

        plt.figure(figsize=(10, 8))
        
        import math

        def haversine(lat1, lon1, lat2, lon2):
            R = 6371  # Earth radius in kilometers
            phi1, phi2 = math.radians(lat1), math.radians(lat2)
            dphi = math.radians(lat2 - lat1)
            dlambda = math.radians(lon2 - lon1)
            
            a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2) * math.sin(dlambda/2)**2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
            return R * c
        
        # Draw Nodes
        nx.draw_networkx_nodes(G, pos, node_size=700, node_color='skyblue')
        
        # Draw Labels
        nx.draw_networkx_labels(G, pos, labels=labels, font_size=9, font_weight='bold')

        # Draw Edges (Complete Graph)
        if len(locations) > 1:
            edges = []
            edge_labels = {}
            colors = []
            widths = []
            
            # Sort pair for consistent comparison
            h_pair = tuple(sorted(highlight_pair)) if highlight_pair else None

            for i in range(len(locations)):
                for j in range(i + 1, len(locations)):
                    u = locations[i]
                    v = locations[j]
                    
                    # Calculate Haversine Distance (km)
                    dist = haversine(u.latitude, u.longitude, v.latitude, v.longitude)
                    
                    G.add_edge(u.id, v.id, weight=dist)
                    edges.append((u.id, v.id))
                    edge_labels[(u.id, v.id)] = f"{dist:.2f} km"
                    
                    # Check for highlight
                    current_pair = tuple(sorted((u.id, v.id)))
                    if h_pair and h_pair == current_pair:
                        colors.append('red')
                        widths.append(3.0)
                    else:
                        colors.append('gray')
                        widths.append(1.0)
            
            # Draw edges
            nx.draw_networkx_edges(G, pos, edgelist=edges, width=widths, alpha=0.6, edge_color=colors, style='dashed')
            
            # Draw edge labels
            nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=8, font_color='black')
        
        plt.title("Location Graph (Haversine Distance - km)")
        plt.xlabel("Longitude")
        plt.ylabel("Latitude")
        plt.grid(True)
        # Keeping axis on to show relative coordinates/grid
        plt.axis('on') 

    # Save to buffer
    img_io = io.BytesIO()
    plt.savefig(img_io, format='png', bbox_inches='tight')
    plt.close()
    img_io.seek(0)
    
    return img_io
