# Technical Report - RoutePlanner

## 1. Project Configuration and Modular Structure

The RoutePlanner project has been developed using the Python Flask microframework, implementing a Model-View-Controller (MVC) software architecture to ensure code scalability and maintainability. This structure allows for the decoupling of business logic, user interface, and data management. To organize the application routes efficiently, Flask's Blueprint functionality has been utilized. This facilitates the division of the application into separate logical components, such as user management, location administration, graph generation, and the main dashboard. The directory structure reflects this modular architecture, with distinct folders for models (SQLAlchemy), controllers (business logic), routers (HTTP endpoints), templates (Jinja2), and static assets.

## 2. MySQL Database Integration

Data persistence is managed through a MySQL relational database management system. To interact with the database from the Python application, the project employs Flask-SQLAlchemy, which provides a robust and efficient Object-Relational Mapping (ORM) layer. This allows for data manipulation using Python classes and objects instead of raw SQL queries, improving code readability and security. The database schema is maintained and versioned using Flask-Migrate, ensuring safe and incremental structural changes. The system implements comprehensive Create, Read, Update, and Delete (CRUD) operations for its core entities, primarily Users and Locations.

![User Management Interface](manageusers.png)
*Figure 1: The User Management interface allowing administrators to control system access.*

## 3. Graph Management and Routing Algorithm

The functional core of the route planner lies in its ability to model geographical locations as a mathematical graph and calculate optimal routes. For this purpose, the NetworkX library is used. The system dynamically constructs a graph where each location stored in the database becomes a node. The edges or connections between these nodes are established by calculating the real distance between them using the Haversine formula, which accounts for the Earth's curvature to offer adequate geographical precision. To determine the most efficient route, Dijkstra's Algorithm has been implemented. This algorithm explores the graph to find the shortest path between an origin node and a destination node, minimizing the total weight of the traversed edges.

![Route Calculation and Graph Visualization](routes.png)
*Figure 2: Visualization of a calculated route, highlighting the optimal path derived from Dijkstra's algorithm.*

## 4. User Interface and User Experience (UX)

The user interface has been designed using the AdminLTE 3 framework, which is built upon Bootstrap 5. This guarantees a modern, clean, and fully responsive design that adapts to different screen sizes and devices. The main dashboard integrates an interactive map powered by the Leaflet.js library. This map allows users to visualize their saved locations, interact with markers, and select geographical points intuitively. User experience is enhanced through the use of JavaScript for dynamic page updates without full reloads, providing immediate feedback via visual indicators during actions such as saving a location or calculating a route.

![Main Dashboard with Interactive Map](dashboard.png)
*Figure 3: The main application dashboard featuring the interactive map and navigation controls.*

## 5. Routes and Controllers

The system's API follows RESTful principles, defining clear and standardized endpoints for each resource. HTTP operations (GET, POST, PUT, DELETE) are used semantically to indicate the action to be performed on resources. Data validation logic is centralized in the controller layer, ensuring that only data meeting integrity and format requirements is processed and stored. This strict separation between route definitions and business logic facilitates unit testing and code reuse across different parts of the application.

## 6. Code Quality and Security

The project adheres to high standards of code quality and security. Sensitive configuration, such as database credentials and session secret keys, is managed through environment variables loaded from a `.env` file, preventing confidential information from being exposed in the source code. The authentication system uses secure cryptographic functions provided by the `werkzeug.security` library for password hashing and verification.

![User Configuration](userconfig.png)
*Figure 4: User configuration settings where security parameters and personal details are managed.*

## 7. Advanced Functionalities: PDF Export and History

A standout feature is the advanced PDF report generation system. This functionality combines frontend and backend technologies to produce a document that faithfully represents the user's view. On the client side, the `html2canvas` library is used to capture the exact visual state of the interactive Leaflet map, including zoom level and marker positions. This capture is sent to the server where it is processed alongside route data. The backend performs precise calculations using the Haversine formula to determine exact total distance and estimated travel time. Finally, the `fpdf2` library assembles a professional PDF document containing the captured map image, the schematic graph generated by NetworkX, and detailed coordinate tables. Additionally, the system maintains a comprehensive history of all planned trips.

![Trip History Log](TripHistory.png)
*Figure 5: The Trip History log displaying previously calculated routes and their details.*
