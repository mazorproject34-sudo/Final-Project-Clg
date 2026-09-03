# System Architecture

## Architecture Overview
The system follows a decoupled, modular 3-tier architecture:
1. **Frontend Presentation & Geospatial Visualization:** React + Vite with Leaflet and OpenStreetMap.
2. **Application & Service API:** FastAPI providing asynchronous endpoints for hazards, alerts, evacuation paths, and shelters.
3. **Core Computation Layer:**
   - **Machine Learning Engine:** Flood risk classification and earthquake hazard severity classification.
   - **Dynamic Evacuation Engine:** NetworkX graph routing with dynamic hazard penalty avoidance.
   - **Database Layer:** SQLite for local relational storage.

```
+-------------------------------------------------------------+
|                 React + Vite (Web UI)                       |
|  [ Leaflet Map ]   [ Alert Banners ]   [ Evacuation Panel ]  |
+------------------------------+------------------------------+
                               | REST API (HTTP/JSON)
+------------------------------v------------------------------+
|                     FastAPI Backend                         |
|  [ /hazards ]   [ /alerts ]   [ /evacuation ]   [ /shelters]|
+---------------+------------------------------+--------------+
                |                              |
      +---------v----------+         +---------v----------+
      |  ML Models Engine  |         | Evacuation Engine  |
      | - Flood Risk       |         | - Pathfinding      |
      | - Earthquake Class.|         | - Shelter Allocator|
      +---------+----------+         +---------+----------+
                |                              |
+---------------v------------------------------v--------------+
|                     SQLite Database                         |
|      (shelters, hazard_events, alerts, evacuation_logs)     |
+-------------------------------------------------------------+
```
