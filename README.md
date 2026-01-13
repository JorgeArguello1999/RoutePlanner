# Route Planner

![Route Planner](static/imgs/logo_favicon.png)

**Route Planner** is a Flask-based web application designed for managing locations and visualizing routes using advanced graph algorithms.

## Features

### 🌍 Interactive Maps
- **Leaflet Integration**: Visualize locations and routes on an interactive map.
- **Route Planning**: Create and manage locations with ease.

### 🕸️ Graph & Network Analysis
Powered by **NetworkX** and **Matplotlib**, Route Planner offers powerful graph visualization capabilities:
- **Graph Representation**: Locations are treated as nodes in a network.
- **Routing Algorithms**: Calculate distances and optimal paths using the Haversine formula.
- **Visual Analytics**: Generate visual representations of your location network.

### 🔐 Secure Configuration
- **User Management**: Admin tools to manage users, roles, and permissions.
- **Secure Access**: Key-based authentication for sensitive configuration settings.
- **Environment Integration**: Securely loads credentials from environment variables.

## Technologies Used

This project leverages a modern Python stack:

### Backend
- **Flask**: Lightweight WSGI web application framework.
- **SQLAlchemy**: Powerful SQL toolkit and Object-Relational Mapping (ORM).
- **Flask-Migrate**: Alembic-based database migrations.
- **Cryptography**: Secure password hashing and encryption.

### Data Science & Graphs
- **NetworkX**: Creation, manipulation, and study of complex networks.
- **Matplotlib**: Comprehensive library for creating static, animated, and interactive visualizations.

### Frontend
- **Leaflet.js**: Leading open-source JavaScript library for mobile-friendly interactive maps.
- **Bootstrap 5 / AdminLTE**: Responsive, mobile-first front-end framework.

## Getting Started

1.  Clone the repository.
2.  Install dependencies:
    ```bash
    uv pip install -r requirements.txt
    # or
    uv sync
    ```
3.  Set up environment variables (`.env`).
4.  Run the application:
    ```bash
    flask run
    ```
