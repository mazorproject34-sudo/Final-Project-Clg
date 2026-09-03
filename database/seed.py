"""
Database Seed Script for Disaster Decision-Support Platform.

IMPORTANT: All records in this file are STRICTLY SIMULATED DEVELOPMENT AND TEST DATA.
Geographic coordinates represent an illustrative test study grid (~10 km x 10 km in the Chennai region:
13.04 N - 13.11 N, 80.18 E - 80.28 E) to validate map rendering, threshold alerts, shelter allocations,
and dynamic routing algorithms. They do NOT represent real or live disaster observations.
"""

import json
import sqlite3
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
DB_PATH = CURRENT_DIR / "disaster_platform.db"

# ---------------------------------------------------------------------------
# SIMULATED DEVELOPMENT / TEST DATASET
# ---------------------------------------------------------------------------

# 1. Simulated Hazard Events (2 Flood, 2 Earthquake)
# Note: model_id remains NULL because ML models are not yet trained.
SIMULATED_HAZARD_EVENTS = [
    {
        "id": "evt-flood-001",
        "hazard_type": "flood",
        "latitude": 13.0825,
        "longitude": 80.2705,
        "water_level_m": 6.2,
        "rainfall_mm": 145.0,
        "earthquake_magnitude": None,
        "earthquake_depth_km": None,
        "severity": "Severe",
        "risk_score": 88.5,
        "risk_level": "Severe",
        "model_id": None,
        "raw_features_json": json.dumps({
            "scenario": "test_severe_inundation",
            "simulated_water_level_m": 6.2,
            "simulated_rainfall_mm": 145.0,
            "description": "Critical simulated river confluence inundation scenario"
        }),
    },
    {
        "id": "evt-flood-002",
        "hazard_type": "flood",
        "latitude": 13.0450,
        "longitude": 80.2400,
        "water_level_m": 3.8,
        "rainfall_mm": 65.0,
        "earthquake_magnitude": None,
        "earthquake_depth_km": None,
        "severity": "Moderate",
        "risk_score": 46.0,
        "risk_level": "Moderate",
        "model_id": None,
        "raw_features_json": json.dumps({
            "scenario": "test_moderate_waterlogging",
            "simulated_water_level_m": 3.8,
            "simulated_rainfall_mm": 65.0,
            "description": "Moderate simulated urban canal runoff scenario"
        }),
    },
    {
        "id": "evt-quake-001",
        "hazard_type": "earthquake",
        "latitude": 13.0600,
        "longitude": 80.2100,
        "water_level_m": None,
        "rainfall_mm": None,
        "earthquake_magnitude": 6.1,
        "earthquake_depth_km": 12.0,
        "severity": "High",
        "risk_score": 79.0,
        "risk_level": "High",
        "model_id": None,
        "raw_features_json": json.dumps({
            "scenario": "test_high_seismic",
            "simulated_magnitude": 6.1,
            "simulated_depth_km": 12.0,
            "description": "Simulated shallow seismic event producing high simulated seismic hazard"
        }),
    },
    {
        "id": "evt-quake-002",
        "hazard_type": "earthquake",
        "latitude": 13.1100,
        "longitude": 80.1800,
        "water_level_m": None,
        "rainfall_mm": None,
        "earthquake_magnitude": 3.8,
        "earthquake_depth_km": 35.0,
        "severity": "Low",
        "risk_score": 22.5,
        "risk_level": "Low",
        "model_id": None,
        "raw_features_json": json.dumps({
            "scenario": "test_minor_tremor",
            "simulated_magnitude": 3.8,
            "simulated_depth_km": 35.0,
            "description": "Simulated deep minor tremor scenario"
        }),
    },
]

# 2. Simulated Safe Shelters (4 test facilities with varying capacity/occupancy)
SIMULATED_SHELTERS = [
    {
        "id": "shl-north-community",
        "name": "North Sector Test Safe Center",
        "latitude": 13.0950,
        "longitude": 80.2600,
        "address": "Test Study Grid - Sector North",
        "capacity": 500,
        "occupied": 120,
        "status": "Open",
        "contact_phone": "+91-98765-00001",
    },
    {
        "id": "shl-central-stadium",
        "name": "Central Complex (Test Shelter)",
        "latitude": 13.0700,
        "longitude": 80.2500,
        "address": "Test Study Grid - Sector Central",
        "capacity": 1200,
        "occupied": 1140,
        "status": "Open",
        "contact_phone": "+91-98765-00002",
    },
    {
        "id": "shl-east-school",
        "name": "East Zone School (Test Shelter)",
        "latitude": 13.0800,
        "longitude": 80.2850,
        "address": "Test Study Grid - Sector East",
        "capacity": 300,
        "occupied": 300,
        "status": "Full",
        "contact_phone": "+91-98765-00003",
    },
    {
        "id": "shl-west-auditorium",
        "name": "West Ridge Hall (Test Inactive)",
        "latitude": 13.0500,
        "longitude": 80.1900,
        "address": "Test Study Grid - Sector West",
        "capacity": 400,
        "occupied": 0,
        "status": "Closed",
        "contact_phone": "+91-98765-00004",
    },
]

# 3. Simulated Alerts (Linked to active test scenarios)
SIMULATED_ALERTS = [
    {
        "id": "alt-flood-001",
        "hazard_event_id": "evt-flood-001",
        "hazard_type": "flood",
        "alert_level": "Evacuation",
        "title": "[TEST SCENARIO] Evacuation Order - Lowland Inundation",
        "message": (
            "DEVELOPMENT TEST: Simulated river level at 6.2m. Evacuation advised toward "
            "North Sector Test Safe Center. Avoid flooded riverside corridors."
        ),
        "is_active": 1,
    },
    {
        "id": "alt-flood-002",
        "hazard_event_id": "evt-flood-002",
        "hazard_type": "flood",
        "alert_level": "Advisory",
        "title": "[TEST SCENARIO] Flood Advisory - Waterlogging",
        "message": (
            "DEVELOPMENT TEST: Simulated rainfall causing localized pooling. Exercise caution "
            "along low-lying test corridors."
        ),
        "is_active": 1,
    },
    {
        "id": "alt-quake-001",
        "hazard_event_id": "evt-quake-001",
        "hazard_type": "earthquake",
        "alert_level": "Warning",
        "title": "[TEST SCENARIO] Earthquake Warning - Seismic Event",
        "message": (
            "DEVELOPMENT TEST: Simulated M6.1 shallow event. Caution advised near "
            "simulated structural impact zones within 1,500m of epicenter."
        ),
        "is_active": 1,
    },
]

# 4. Simulated Hazard Impact Zones (Dynamic routing obstacle buffers)
SIMULATED_IMPACT_ZONES = [
    {
        "id": "zone-flood-001",
        "hazard_event_id": "evt-flood-001",
        "zone_type": "inundation_buffer",
        "center_latitude": 13.0825,
        "center_longitude": 80.2705,
        "radius_meters": 1200.0,
        "penalty_multiplier": 500.0,
        "is_active": 1,
    },
    {
        "id": "zone-block-001",
        "hazard_event_id": "evt-flood-001",
        "zone_type": "road_blockage",
        "center_latitude": 13.0780,
        "center_longitude": 80.2650,
        "radius_meters": 250.0,
        "penalty_multiplier": 1000.0,
        "is_active": 1,
    },
    {
        "id": "zone-quake-001",
        "hazard_event_id": "evt-quake-001",
        "zone_type": "seismic_impact_buffer",
        "center_latitude": 13.0600,
        "center_longitude": 80.2100,
        "radius_meters": 1500.0,
        "penalty_multiplier": 150.0,
        "is_active": 1,
    },
]


def seed_database(db_path: Path = DB_PATH) -> dict:
    """
    Populates the database with simulated test records.
    Uses INSERT OR IGNORE to remain idempotent, prevent duplicate inserts,
    and avoid triggering foreign-key cascade deletions on existing parent records.
    """
    if not db_path.exists():
        raise FileNotFoundError(
            f"Database file not found at: {db_path}. Please run init_db.py first."
        )

    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA foreign_keys = ON;")
        cursor = conn.cursor()

        # 1. Insert Hazard Events (model_id is NULL)
        cursor.executemany(
            """
            INSERT OR IGNORE INTO hazard_events (
                id, hazard_type, latitude, longitude, water_level_m,
                rainfall_mm, earthquake_magnitude, earthquake_depth_km,
                severity, risk_score, risk_level, model_id, raw_features_json
            ) VALUES (
                :id, :hazard_type, :latitude, :longitude, :water_level_m,
                :rainfall_mm, :earthquake_magnitude, :earthquake_depth_km,
                :severity, :risk_score, :risk_level, :model_id, :raw_features_json
            )
            """,
            SIMULATED_HAZARD_EVENTS,
        )

        # 2. Insert Shelters
        cursor.executemany(
            """
            INSERT OR IGNORE INTO shelters (
                id, name, latitude, longitude, address,
                capacity, occupied, status, contact_phone
            ) VALUES (
                :id, :name, :latitude, :longitude, :address,
                :capacity, :occupied, :status, :contact_phone
            )
            """,
            SIMULATED_SHELTERS,
        )

        # 3. Insert Alerts
        cursor.executemany(
            """
            INSERT OR IGNORE INTO alerts (
                id, hazard_event_id, hazard_type, alert_level,
                title, message, is_active
            ) VALUES (
                :id, :hazard_event_id, :hazard_type, :alert_level,
                :title, :message, :is_active
            )
            """,
            SIMULATED_ALERTS,
        )

        # 4. Insert Hazard Impact Zones
        cursor.executemany(
            """
            INSERT OR IGNORE INTO hazard_impact_zones (
                id, hazard_event_id, zone_type, center_latitude,
                center_longitude, radius_meters, penalty_multiplier, is_active
            ) VALUES (
                :id, :hazard_event_id, :zone_type, :center_latitude,
                :center_longitude, :radius_meters, :penalty_multiplier, :is_active
            )
            """,
            SIMULATED_IMPACT_ZONES,
        )

        conn.commit()

        # Query and return row counts for verification
        tables = [
            "ml_models",
            "hazard_events",
            "alerts",
            "shelters",
            "hazard_impact_zones",
            "evacuation_logs",
        ]
        counts = {
            t: cursor.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            for t in tables
        }
        return counts

    except Exception as e:
        conn.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    row_counts = seed_database()
    print("Database seeding completed successfully.")
    print("Row counts by table:")
    for table, count in row_counts.items():
        print(f"  - {table}: {count}")
