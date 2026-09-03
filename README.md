# Intelligent Multi-Hazard Disaster Risk Assessment, Early Warning and Dynamic Evacuation Decision-Support Platform

## Overview
An integrated, intelligent decision-support system designed to assess disaster risks, trigger timely early warnings, and compute dynamic, safe evacuation routes during emergencies. The initial implementation focuses on two major disasters: **Floods** and **Earthquakes**.

The platform evaluates hazard risk levels, identifies inundated or seismically damaged impassable road links, and dynamically reroutes citizens to the nearest safe shelters with available capacity.

---

## Technology Stack

- **Backend:** Python 3, FastAPI, Uvicorn, Pydantic
- **Frontend:** React 18, Vite, Vanilla CSS
- **Geospatial & Mapping:** Leaflet.js, OpenStreetMap
- **Database:** SQLite (local relational persistence)
- **Machine Learning:** Scikit-learn, Pandas, NumPy
  - *Flood:* Risk level classification based on rainfall and hydrological indicators
  - *Earthquake:* Hazard severity / seismic risk classification based on seismic magnitude and intensity indicators
- **Evacuation Engine:** NetworkX / Graph algorithms (Dijkstra & A* with dynamic hazard penalty weighting)
- **Testing:** Pytest

---

## High-Level Modules

1. **Data Layer (`data/`):** Historical and simulated sensor readings for flood and earthquake events, safe shelter locations, and local road network GeoJSON.
2. **Database Layer (`database/`):** SQLite schema, database connection management, and initial seed scripts.
3. **Machine Learning Pipeline (`ml/`):** Training scripts, inference wrappers, and exploratory notebooks for flood and earthquake risk assessment.
4. **Evacuation Decision-Support Engine (`evacuation_engine/`):** Dynamic graph builder, hazard avoidance weighting, and capacity-aware shelter allocation.
5. **Backend REST API (`backend/`):** FastAPI endpoints serving hazard predictions, early warning alerts, shelter statuses, and computed evacuation routes.
6. **Web Dashboard (`frontend/`):** Interactive React + Vite map interface featuring real-time alert banners, hazard overlays, and routing panels.
7. **Verification & Testing (`tests/`):** Unit and integration test suites for ML inference, routing algorithms, and API endpoints.
8. **Documentation (`docs/`):** System architecture specifications, data flow diagrams, and academic project report notes.

---

## Planned Development Phases

- **Phase 1: Project Foundation & Data Engineering**
  - Establish directory structure, base schemas, and data ingestion templates.
- **Phase 2: Machine Learning Models**
  - Develop and evaluate flood risk classification and earthquake hazard severity classification models.
- **Phase 3: Evacuation Decision-Support Engine**
  - Implement road network graph construction, dynamic hazard zone penalty masking, and safe shelter allocation algorithms.
- **Phase 4: Backend API Development**
  - Build FastAPI endpoints connecting ML inference, evacuation routing, and SQLite persistence.
- **Phase 5: Interactive Frontend Dashboard**
  - Implement React + Vite UI with Leaflet map visualization for hazard zones, shelters, and dynamic evacuation corridors.
- **Phase 6: Integration, Testing & Documentation**
  - Perform end-to-end testing, validate edge cases, and finalize architecture and project documentation.
