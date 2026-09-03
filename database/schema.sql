-- SQLite Database Schema for Disaster Decision-Support Platform
-- Intelligent Multi-Hazard Disaster Risk Assessment, Early Warning and Dynamic Evacuation Decision-Support Platform

PRAGMA foreign_keys = ON;

-- 1. ML Models Table (Model Version Tracking)
CREATE TABLE IF NOT EXISTS ml_models (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    hazard_type TEXT NOT NULL CHECK (hazard_type IN ('flood', 'earthquake')),
    version TEXT NOT NULL,
    algorithm TEXT NOT NULL,
    accuracy_score REAL CHECK (accuracy_score >= 0.0 AND accuracy_score <= 1.0),
    metrics_json TEXT,
    trained_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Hazard Events Table (Observations & ML Risk Assessments)
CREATE TABLE IF NOT EXISTS hazard_events (
    id TEXT PRIMARY KEY,
    hazard_type TEXT NOT NULL CHECK (hazard_type IN ('flood', 'earthquake')),
    latitude REAL NOT NULL CHECK (latitude BETWEEN -90 AND 90),
    longitude REAL NOT NULL CHECK (longitude BETWEEN -180 AND 180),
    water_level_m REAL,
    rainfall_mm REAL,
    earthquake_magnitude REAL,
    earthquake_depth_km REAL,
    severity TEXT NOT NULL CHECK (severity IN ('Low', 'Moderate', 'High', 'Severe')),
    risk_score REAL NOT NULL CHECK (risk_score BETWEEN 0.0 AND 100.0),
    risk_level TEXT NOT NULL CHECK (risk_level IN ('Low', 'Moderate', 'High', 'Severe')),
    model_id TEXT,
    raw_features_json TEXT,
    reported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (model_id) REFERENCES ml_models(id)
);

-- 3. Alerts Table (Early Warning Notifications)
CREATE TABLE IF NOT EXISTS alerts (
    id TEXT PRIMARY KEY,
    hazard_event_id TEXT,
    hazard_type TEXT NOT NULL CHECK (hazard_type IN ('flood', 'earthquake')),
    alert_level TEXT NOT NULL CHECK (alert_level IN ('Advisory', 'Watch', 'Warning', 'Evacuation')),
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    is_active INTEGER DEFAULT 1 CHECK (is_active IN (0, 1)),
    issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    FOREIGN KEY (hazard_event_id) REFERENCES hazard_events(id) ON DELETE CASCADE
);

-- 4. Shelters Table (Safe Haven Locations & Capacities)
CREATE TABLE IF NOT EXISTS shelters (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    latitude REAL NOT NULL CHECK (latitude BETWEEN -90 AND 90),
    longitude REAL NOT NULL CHECK (longitude BETWEEN -180 AND 180),
    address TEXT,
    capacity INTEGER NOT NULL CHECK (capacity > 0),
    occupied INTEGER DEFAULT 0 CHECK (occupied >= 0 AND occupied <= capacity),
    status TEXT DEFAULT 'Open' CHECK (status IN ('Open', 'Full', 'Closed')),
    contact_phone TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Hazard Impact Zones Table (Dynamic Hazard-Aware Routing Data Contract)
CREATE TABLE IF NOT EXISTS hazard_impact_zones (
    id TEXT PRIMARY KEY,
    hazard_event_id TEXT,
    zone_type TEXT NOT NULL CHECK (zone_type IN ('inundation_buffer', 'seismic_impact_buffer', 'road_blockage')),
    center_latitude REAL NOT NULL,
    center_longitude REAL NOT NULL,
    radius_meters REAL NOT NULL CHECK (radius_meters > 0),
    penalty_multiplier REAL DEFAULT 100.0 CHECK (penalty_multiplier >= 1.0),
    is_active INTEGER DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (hazard_event_id) REFERENCES hazard_events(id) ON DELETE CASCADE
);

-- 6. Evacuation Logs Table (Route Calculations & Decision Auditing)
CREATE TABLE IF NOT EXISTS evacuation_logs (
    id TEXT PRIMARY KEY,
    origin_latitude REAL NOT NULL,
    origin_longitude REAL NOT NULL,
    assigned_shelter_id TEXT,
    routing_algorithm TEXT NOT NULL,
    total_distance_km REAL CHECK (total_distance_km >= 0),
    estimated_time_mins REAL CHECK (estimated_time_mins >= 0),
    hazard_avoidance_applied INTEGER DEFAULT 1 CHECK (hazard_avoidance_applied IN (0, 1)),
    route_geometry_json TEXT,
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (assigned_shelter_id) REFERENCES shelters(id)
);
