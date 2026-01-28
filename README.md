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

1. Clone the repository.
2. Install dependencies:

    ```bash
    uv pip install -r requirements.txt
    # or
    uv sync
    ```

3. Set up environment variables (`.env`).
4. Run the application:

    ```bash
    flask run
    ```

## Docker Support

You can run the application and a PostgreSQL database easily using Docker Compose.

### Prerequisites

- Docker and Docker Compose installed on your machine.

### How to Run

1. **Build and Start:**

    ```bash
    docker-compose up --build
    ```

    To run in background mode (detached):

    ```bash
    docker-compose up --build -d
    ```

2. **Access the Application:**
    Open your browser and navigate to:
    [http://localhost:5000](http://localhost:5000)

3. **Stop the Application:**

    ```bash
    docker-compose down
    ```

### Configuration

- **Ports:**
  - Web Application: `5000`
  - PostgreSQL Database: `5432`

- **Database:**
  - A PostgreSQL container is spun up automatically.
  - Data is persisted in a docker volume `postgres_data`.

- **Development:**
  - The current directory is mounted into the container at `/app`.

### Production Deployment

To run the application in a production-like environment (using `gunicorn` and `nginx`, or simply the production-config container):

1. **Build and Start (Production):**

    ```bash
    docker-compose -f docker-compose.prod.yml up --build -d
    ```

2. **Stop (Production):**

    ```bash
    docker-compose -f docker-compose.prod.yml down
    ```

3. **Notes:**
    - Uses `docker-compose.prod.yml`.
    - Disables debug mode.
    - Uses a production WSGI server (if configured in Dockerfile) or simply sets `FLASK_ENV=production`.
