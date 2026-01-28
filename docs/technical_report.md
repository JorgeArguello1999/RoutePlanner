# Technical Report - JAAG Maps Route Planner

## 1. Project Configuration & Modular Structure

**Compliance**: Rubric Point 1
The project is built using **Flask** and follows a modular **MVC (Model-View-Controller)** architecture.

- **Blueprints**: The application uses Flask Blueprints to organize routes (`routers/`) separating logic for Users, Locations, Graphs, and Dashboard.
- **Folder Structure**:
  - `app.py`: Entry point.
  - `models/`: Database models (SQLAlchemy).
  - `controllers/`: Business logic.
  - `routers/`: HTTP route definitions.
  - `templates/`: HTML files (Jinja2).
  - `static/`: CSS (AdminLTE), JS, Images.

## 2. MySQL Database Integration

**Compliance**: Rubric Point 2 & 3

- **Database**: MySQL is used as the persistent storage.
- **ORM**: The project uses **Flask-SQLAlchemy** for database interactions.
- **Migrations**: **Flask-Migrate** (Alembic) is configured for handling database schema changes.
- **Entities**:
  - `User`: Manages authentication and roles.
  - `Location`: Stores user-defined locations (Latitude/Longitude).
- **CRUD**: Full Create, Read, Update, Delete functionality is implemented for Locations via `controllers/locations.py` and `routers/locations.py`.

## 3. Graph Management & Routing Algorithm

**Compliance**: Rubric Point 4

- **Library**: **NetworkX** is used for graph manipulation and pathfinding.
- **Visualization**: **Matplotlib** is used to generate visual representations of the graph, which are rendered as PNG images.
- **Algorithm**: **Dijkstra's Shortest Path Algorithm** (`nx.shortest_path`) is implemented in `controllers/graphs.py` to calculate the optimal route between locations based on Haversine distance.
  - The graph is dynamically constructed from user locations.
  - Edges are weighted by distance.
  - The computed path is highlighted in Red in the generated graph image.

## 4. User Interface

**Compliance**: Rubric Point 5

- **Framework**: **AdminLTE 3** (based on **Bootstrap 5**) is used for the UI/UX.
- **Design**: The dashboard provides an interactive map (Leaflet.js) and a responsive sidebar navigation.
- **Feedback**: Users receive visual feedback (spinners, alerts) during actions like saving locations or calculating routes.

## 5. Routes & Controllers

**Compliance**: Rubric Point 6

- **Endpoints**: standardized RESTful-like endpoints (e.g., `/locations/` GET/POST, `/locations/<id>` PUT/DELETE).
- **Validation**: Input validation is handled in the controller layer.
- **Methods**: Proper use of HTTP verbs (GET, POST, PUT, DELETE).

## 6. Code Quality

**Compliance**: Rubric Point 7

- **Separation of Concerns**: Logic is strictly separated between Routers (HTTP handling) and Controllers (Business Logic).
- **Comments**: Code is documented with docstrings explainig functions.
- **Configuration**: Environment variables (`.env`) manage sensitive data like DB URLs.

## 7. Extra Functionalities

**Compliance**: Rubric Point 9

- **Authentication**: Secure Login/Signup system with password hashing (`werkzeug.security`).
- **PDF Export**: Users can export a PDF report of their calculated route, including the route details and the generated graph image.
- **Trip History**: Completed trips can be saved to a history log.

---

## 8. Architecture Diagram

```mermaid
graph TD
    User[User Browser] <-->|HTTP Requests| App[Flask App]
    subgraph Backend
        App --> Router[Routers (Blueprints)]
        Router --> Controller[Controllers]
        Controller --> Model[SQLAlchemy Models]
        Controller --> NetworkX[Graph Engine]
        Controller --> PDF[PDF Generator]
    end
    subgraph Data
        Model <--> MySQL[(MySQL Database)]
    end
    subgraph Output
        NetworkX -->|image/png| User
        PDF -->|application/pdf| User
    end
```
