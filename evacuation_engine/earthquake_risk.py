"""
Earthquake Risk Assessment Engine - Professional V1
====================================================
Module: evacuation_engine/earthquake_risk.py

Purpose:
    Provides deterministic risk scoring heuristics based on magnitude, depth,
    and epicentral distance for the National Capital Region (Delhi NCR) disaster
    decision-support platform.

    The engine evaluates incoming or simulated earthquake events based on
    four primary physical parameters:
      1. magnitude  : Reported magnitude (energy released at source)
      2. depth_km   : Hypocentral focal depth in kilometers
      3. latitude   : Epicentral latitude (WGS 84 decimal degrees)
      4. longitude  : Epicentral longitude (WGS 84 decimal degrees)

Methodology:
    Individual hazard factors are evaluated using deterministic, piecewise linear
    heuristics that produce normalized sub-scores from 0.0 to 100.0:
      - Magnitude Score : Higher magnitude yields a higher heuristic score.
      - Depth Score     : Shallower focal depth yields a higher heuristic score.
      - Distance Score  : Closer epicentral proximity to Delhi yields a higher heuristic score.

    These scores are heuristic indicator metrics designed for decision support
    and priority ranking. They do not simulate detailed wave propagation,
    soil-structure interaction, structural damage states, or site-specific basin amplification.
"""

import math
from enum import Enum
from typing import Any, Dict, Optional


# ===========================================================================
# 1. REFERENCE GEOGRAPHIC COORDINATES & GEODESY
# ===========================================================================
# Central reference datum for Delhi National Capital Territory (NCT/NCR)
DELHI_NCR_REF_LATITUDE: float = 28.6139
DELHI_NCR_REF_LONGITUDE: float = 77.2090

# Mean volumetric Earth radius in kilometers (standard spherical approximation)
EARTH_RADIUS_KM: float = 6371.0

# Delhi NCR Regional Bounding Box (for spatial indexing and boundary checks)
DELHI_NCR_BOUNDS: Dict[str, float] = {
    "min_latitude": 27.80,
    "max_latitude": 29.30,
    "min_longitude": 76.50,
    "max_longitude": 77.80,
}


# ===========================================================================
# 2. RISK LEVELS SPECIFICATION
# ===========================================================================
class RiskLevel(str, Enum):
    """
    Standard four-tier disaster risk classification aligned across
    the platform database schema, evacuation engine, and UI alert system.
    """
    LOW = "Low"
    MODERATE = "Moderate"
    HIGH = "High"
    SEVERE = "Severe"


# List of ordered risk levels from lowest to highest
RISK_LEVEL_ORDER = [
    RiskLevel.LOW,
    RiskLevel.MODERATE,
    RiskLevel.HIGH,
    RiskLevel.SEVERE,
]


# ===========================================================================
# 3. COMPONENT SCORING THRESHOLDS & NORMALIZATION CONSTANTS
# ===========================================================================

# --- Magnitude Scoring Thresholds ---
# Piecewise threshold anchors for magnitude scoring
MAGNITUDE_THRESHOLDS: Dict[str, float] = {
    "MIN_MONITORED": 3.0,   # Baseline threshold below which score is 0.0
    "LOW_MAX": 4.2,         # Upper boundary for low-magnitude tier
    "MODERATE_MAX": 5.4,    # Upper boundary for moderate-magnitude tier
    "HIGH_MAX": 6.4,        # Upper boundary for high-magnitude tier
    "SEVERE_MIN": 6.5,      # Lower boundary for severe-magnitude tier
}

# Magnitude normalization ceiling at which score reaches 100.0
MAGNITUDE_MAX_NORMALIZATION: float = 8.0

# --- Hypocentral Depth Scoring Thresholds (km) ---
# Piecewise threshold anchors for focal depth scoring (shallower = higher score)
DEPTH_THRESHOLDS_KM: Dict[str, float] = {
    "VERY_SHALLOW_MAX": 15.0,  # Boundary for shallowest focal depth bracket
    "SHALLOW_MAX": 35.0,       # Boundary for standard crustal depth bracket
    "INTERMEDIATE_MAX": 70.0,   # Boundary for intermediate depth bracket
    "DEEP_MIN": 70.0,          # Lower boundary for deep hypocenter bracket
}

# Maximum focal depth normalization endpoint where depth score reaches 0.0
DEPTH_MAX_NORMALIZATION_KM: float = 250.0

# Backward compatibility alias
DEPTH_MAX_ATTENUATION_KM: float = DEPTH_MAX_NORMALIZATION_KM

# --- Epicentral Distance Scoring Thresholds to Delhi NCR (km) ---
# Piecewise threshold anchors for distance to Delhi reference point (closer = higher score)
DISTANCE_THRESHOLDS_KM: Dict[str, float] = {
    "NEAR_FIELD_MAX": 60.0,        # Boundary for local near-field zone
    "SUB_REGIONAL_MAX": 180.0,     # Boundary for sub-regional zone
    "FAR_REGIONAL_MAX": 380.0,     # Boundary for regional zone
    "DISTANT_MIN": 380.0,          # Lower boundary for distant regional zone
}

# Maximum epicentral distance normalization endpoint where distance score reaches 0.0
DISTANCE_MAX_NORMALIZATION_KM: float = 700.0

# Backward compatibility alias
DISTANCE_MAX_ATTENUATION_KM: float = DISTANCE_MAX_NORMALIZATION_KM

# --- Factor Weights for Composite Scoring ---
# Linear weighting factors for composite heuristic risk score (must sum to 1.0)
MAGNITUDE_WEIGHT: float = 0.50
DEPTH_WEIGHT: float = 0.20
DISTANCE_WEIGHT: float = 0.30

# Verify weights sum exactly to 1.0
assert math.isclose(MAGNITUDE_WEIGHT + DEPTH_WEIGHT + DISTANCE_WEIGHT, 1.0), "Factor weights must sum to 1.0"


# ===========================================================================
# 4. COMPOSITE RISK SCORE THRESHOLDS (0 - 100 Scale)
# ===========================================================================
# Maps normalized composite hazard scores (0.0 to 100.0) to categorical RiskLevel.
RISK_SCORE_THRESHOLDS: Dict[RiskLevel, Dict[str, float]] = {
    RiskLevel.LOW: {
        "min_score": 0.0,
        "max_score": 34.99,
        "description": "Low heuristic risk tier: routine monitoring",
    },
    RiskLevel.MODERATE: {
        "min_score": 35.0,
        "max_score": 59.99,
        "description": "Moderate heuristic risk tier: elevated monitoring and advisory status",
    },
    RiskLevel.HIGH: {
        "min_score": 60.0,
        "max_score": 79.99,
        "description": "High heuristic risk tier: response readiness and route review",
    },
    RiskLevel.SEVERE: {
        "min_score": 80.0,
        "max_score": 100.0,
        "description": "Severe heuristic risk tier: emergency protocol activation",
    },
}


# ===========================================================================
# 5. INPUT VALIDATION
# ===========================================================================
def validate_earthquake_inputs(
    magnitude: float,
    depth_km: float,
    latitude: float,
    longitude: float,
) -> None:
    """
    Validates physical parameter boundaries for earthquake inputs.

    Raises:
        ValueError: If any parameter is None, non-numeric, NaN, infinite,
                    or outside physical boundary limits:
                      - magnitude  : [0.0, 10.0]
                      - depth_km   : [0.0, 700.0]
                      - latitude   : [-90.0, 90.0]
                      - longitude  : [-180.0, 180.0]
    """
    # 1. Magnitude validation
    if magnitude is None or not isinstance(magnitude, (int, float)) or isinstance(magnitude, bool):
        raise ValueError(f"Invalid magnitude '{magnitude}': must be a numeric value.")
    if math.isnan(magnitude) or math.isinf(magnitude) or magnitude < 0.0 or magnitude > 10.0:
        raise ValueError(f"Magnitude {magnitude} out of physical bounds [0.0, 10.0].")

    # 2. Depth validation (hypocenters range from 0 km to global observation limit ~700 km)
    if depth_km is None or not isinstance(depth_km, (int, float)) or isinstance(depth_km, bool):
        raise ValueError(f"Invalid depth_km '{depth_km}': must be a numeric value.")
    if math.isnan(depth_km) or math.isinf(depth_km) or depth_km < 0.0 or depth_km > 700.0:
        raise ValueError(f"Focal depth {depth_km} km out of physical bounds [0.0, 700.0] km.")

    # 3. Latitude validation (WGS 84 degrees)
    if latitude is None or not isinstance(latitude, (int, float)) or isinstance(latitude, bool):
        raise ValueError(f"Invalid latitude '{latitude}': must be a numeric value.")
    if math.isnan(latitude) or math.isinf(latitude) or latitude < -90.0 or latitude > 90.0:
        raise ValueError(f"Latitude {latitude} out of valid geographic range [-90.0, 90.0].")

    # 4. Longitude validation (WGS 84 degrees)
    if longitude is None or not isinstance(longitude, (int, float)) or isinstance(longitude, bool):
        raise ValueError(f"Invalid longitude '{longitude}': must be a numeric value.")
    if math.isnan(longitude) or math.isinf(longitude) or longitude < -180.0 or longitude > 180.0:
        raise ValueError(f"Longitude {longitude} out of valid geographic range [-180.0, 180.0].")


# ===========================================================================
# 6. COMPONENT CALCULATIONS (PART 2)
# ===========================================================================
def calculate_distance_to_delhi_km(
    latitude: float,
    longitude: float,
    ref_lat: float = DELHI_NCR_REF_LATITUDE,
    ref_lon: float = DELHI_NCR_REF_LONGITUDE,
) -> float:
    """
    Computes the great-circle geodesic distance in kilometers from an epicenter
    to the Delhi NCR reference datum using the Haversine formula.

    Parameters:
        latitude  (float): Epicentral latitude in decimal degrees.
        longitude (float): Epicentral longitude in decimal degrees.
        ref_lat   (float): Reference latitude (default: DELHI_NCR_REF_LATITUDE).
        ref_lon   (float): Reference longitude (default: DELHI_NCR_REF_LONGITUDE).

    Returns:
        float: Great-circle distance in kilometers (rounded to 2 decimal places).
    """
    if latitude is None or not isinstance(latitude, (int, float)) or isinstance(latitude, bool):
        raise ValueError(f"Invalid latitude '{latitude}': must be a numeric value.")
    if math.isnan(latitude) or math.isinf(latitude) or latitude < -90.0 or latitude > 90.0:
        raise ValueError(f"Latitude {latitude} out of valid geographic range [-90.0, 90.0].")

    if longitude is None or not isinstance(longitude, (int, float)) or isinstance(longitude, bool):
        raise ValueError(f"Invalid longitude '{longitude}': must be a numeric value.")
    if math.isnan(longitude) or math.isinf(longitude) or longitude < -180.0 or longitude > 180.0:
        raise ValueError(f"Longitude {longitude} out of valid geographic range [-180.0, 180.0].")

    phi1 = math.radians(ref_lat)
    phi2 = math.radians(latitude)
    delta_phi = math.radians(latitude - ref_lat)
    delta_lambda = math.radians(longitude - ref_lon)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    distance_km = EARTH_RADIUS_KM * c

    return round(distance_km, 2)


def calculate_magnitude_score(magnitude: float) -> float:
    """
    Computes a normalized heuristic score (0.0 to 100.0) based on earthquake magnitude.

    Uses continuous, piecewise linear interpolation mapped directly
    to MAGNITUDE_THRESHOLDS and MAGNITUDE_MAX_NORMALIZATION:
      - M <= 3.0 (MIN_MONITORED) : Score = 0.0
      - 3.0 < M < 4.2 (LOW_MAX)   : Score scales linearly from 0.0 to 35.0
      - 4.2 <= M < 5.4 (MODERATE): Score scales linearly from 35.0 to 60.0
      - 5.4 <= M < 6.4 (HIGH_MAX): Score scales linearly from 60.0 to 80.0
      - 6.4 <= M < 6.5 (SEVERE)  : Score scales linearly from 80.0 to 85.0
      - M >= 6.5 (SEVERE_MIN+)   : Score scales linearly from 85.0 to 100.0
                                   (capped at 100.0 at MAGNITUDE_MAX_NORMALIZATION = 8.0)

    Parameters:
        magnitude (float): Earthquake magnitude.

    Returns:
        float: Normalized score between 0.0 and 100.0 (rounded to 2 decimals).
    """
    if magnitude is None or not isinstance(magnitude, (int, float)) or isinstance(magnitude, bool):
        raise ValueError(f"Invalid magnitude '{magnitude}': must be a numeric value.")
    if math.isnan(magnitude) or math.isinf(magnitude) or magnitude < 0.0 or magnitude > 10.0:
        raise ValueError(f"Magnitude {magnitude} out of physical bounds [0.0, 10.0].")

    m_min = MAGNITUDE_THRESHOLDS["MIN_MONITORED"]       # 3.0
    m_low = MAGNITUDE_THRESHOLDS["LOW_MAX"]             # 4.2
    m_mod = MAGNITUDE_THRESHOLDS["MODERATE_MAX"]        # 5.4
    m_high = MAGNITUDE_THRESHOLDS["HIGH_MAX"]           # 6.4
    m_sev = MAGNITUDE_THRESHOLDS["SEVERE_MIN"]          # 6.5
    m_ceil = MAGNITUDE_MAX_NORMALIZATION                # 8.0

    if magnitude <= m_min:
        score = 0.0
    elif magnitude < m_low:
        score = (magnitude - m_min) / (m_low - m_min) * 35.0
    elif magnitude < m_mod:
        score = 35.0 + (magnitude - m_low) / (m_mod - m_low) * 25.0
    elif magnitude < m_high:
        score = 60.0 + (magnitude - m_mod) / (m_high - m_mod) * 20.0
    elif magnitude < m_sev:
        score = 80.0 + (magnitude - m_high) / (m_sev - m_high) * 5.0
    else:
        score = 85.0 + min((magnitude - m_sev) / (m_ceil - m_sev), 1.0) * 15.0

    return round(max(0.0, min(score, 100.0)), 2)


def calculate_depth_score(depth_km: float) -> float:
    """
    Computes a normalized heuristic score (0.0 to 100.0) based on hypocentral focal depth.

    Shallower hypocenters are assigned higher heuristic scores; deeper events are
    assigned lower heuristic scores using piecewise linear interpolation mapped directly
    to DEPTH_THRESHOLDS_KM and DEPTH_MAX_NORMALIZATION_KM:
      - depth <= 0.0 km                       : Score = 100.0
      - 0.0 < depth <= 15.0 km (VERY_SHALLOW) : Score scales linearly from 100.0 down to 85.0
      - 15.0 < depth <= 35.0 km (SHALLOW)     : Score scales linearly from 85.0 down to 60.0
      - 35.0 < depth <= 70.0 km (INTERMEDIATE): Score scales linearly from 60.0 down to 35.0
      - depth > 70.0 km (DEEP_MIN)            : Score scales linearly from 35.0 down to 0.0
                                                (reaches 0.0 at DEPTH_MAX_NORMALIZATION_KM = 250.0 km)

    Parameters:
        depth_km (float): Focal depth in kilometers.

    Returns:
        float: Normalized score between 0.0 and 100.0 (rounded to 2 decimals).
    """
    if depth_km is None or not isinstance(depth_km, (int, float)) or isinstance(depth_km, bool):
        raise ValueError(f"Invalid depth_km '{depth_km}': must be a numeric value.")
    if math.isnan(depth_km) or math.isinf(depth_km) or depth_km < 0.0 or depth_km > 700.0:
        raise ValueError(f"Focal depth {depth_km} km out of physical bounds [0.0, 700.0] km.")

    d_vshallow = DEPTH_THRESHOLDS_KM["VERY_SHALLOW_MAX"]  # 15.0
    d_shallow = DEPTH_THRESHOLDS_KM["SHALLOW_MAX"]        # 35.0
    d_inter = DEPTH_THRESHOLDS_KM["INTERMEDIATE_MAX"]     # 70.0
    d_ceil = DEPTH_MAX_NORMALIZATION_KM                  # 250.0

    if depth_km <= 0.0:
        score = 100.0
    elif depth_km < d_vshallow:
        score = 100.0 - (depth_km / d_vshallow) * 15.0
    elif depth_km < d_shallow:
        score = 85.0 - (depth_km - d_vshallow) / (d_shallow - d_vshallow) * 25.0
    elif depth_km < d_inter:
        score = 60.0 - (depth_km - d_shallow) / (d_inter - d_shallow) * 25.0
    else:
        score = max(0.0, 35.0 - (depth_km - d_inter) / (d_ceil - d_inter) * 35.0)

    return round(max(0.0, min(score, 100.0)), 2)


def calculate_distance_score(distance_km: float) -> float:
    """
    Computes a normalized heuristic score (0.0 to 100.0) based on epicentral distance
    to the Delhi NCR reference datum.

    Closer epicenters are assigned higher heuristic scores; farther events are
    assigned lower heuristic scores using piecewise linear interpolation mapped directly
    to DISTANCE_THRESHOLDS_KM and DISTANCE_MAX_NORMALIZATION_KM:
      - distance <= 0.0 km                    : Score = 100.0
      - 0.0 < distance <= 60.0 km (NEAR_FIELD): Score scales linearly from 100.0 down to 80.0
      - 60.0 < distance <= 180.0 km (SUB_REG) : Score scales linearly from 80.0 down to 55.0
      - 180.0 < distance <= 380.0 km (FAR_REG): Score scales linearly from 55.0 down to 25.0
      - distance > 380.0 km (DISTANT_MIN)     : Score scales linearly from 25.0 down to 0.0
                                                (reaches 0.0 at DISTANCE_MAX_NORMALIZATION_KM = 700.0 km)

    Parameters:
        distance_km (float): Epicentral distance to Delhi NCR in kilometers.

    Returns:
        float: Normalized score between 0.0 and 100.0 (rounded to 2 decimals).
    """
    if distance_km is None or not isinstance(distance_km, (int, float)) or isinstance(distance_km, bool):
        raise ValueError(f"Invalid distance_km '{distance_km}': must be a numeric value.")
    if math.isnan(distance_km) or math.isinf(distance_km) or distance_km < 0.0:
        raise ValueError(f"Distance {distance_km} km out of valid bounds [0.0, inf).")

    d_near = DISTANCE_THRESHOLDS_KM["NEAR_FIELD_MAX"]          # 60.0
    d_sub = DISTANCE_THRESHOLDS_KM["SUB_REGIONAL_MAX"]         # 180.0
    d_far = DISTANCE_THRESHOLDS_KM["FAR_REGIONAL_MAX"]         # 380.0
    d_ceil = DISTANCE_MAX_NORMALIZATION_KM                    # 700.0

    if distance_km <= 0.0:
        score = 100.0
    elif distance_km < d_near:
        score = 100.0 - (distance_km / d_near) * 20.0
    elif distance_km < d_sub:
        score = 80.0 - (distance_km - d_near) / (d_sub - d_near) * 25.0
    elif distance_km < d_far:
        score = 55.0 - (distance_km - d_sub) / (d_far - d_sub) * 30.0
    else:
        score = max(0.0, 25.0 - (distance_km - d_far) / (d_ceil - d_far) * 25.0)

    return round(max(0.0, min(score, 100.0)), 2)


def calculate_composite_risk_score(
    magnitude_score: float,
    depth_score: float,
    distance_score: float,
) -> float:
    """
    Computes the weighted composite earthquake risk score from normalized sub-scores.

    This calculation is a deterministic decision-support heuristic designed for
    comparative risk ranking and situational triage; it is not a physical earthquake
    simulation or structural fragility model.

    Formula:
        composite_score = (
            magnitude_score * MAGNITUDE_WEIGHT
            + depth_score * DEPTH_WEIGHT
            + distance_score * DISTANCE_WEIGHT
        )

    Parameters:
        magnitude_score (float): Normalized magnitude sub-score [0.0, 100.0].
        depth_score     (float): Normalized focal depth sub-score [0.0, 100.0].
        distance_score  (float): Normalized epicentral distance sub-score [0.0, 100.0].

    Returns:
        float: Composite risk score normalized and clamped to [0.0, 100.0],
               rounded to 2 decimal places.

    Raises:
        ValueError: If any input score is None, non-numeric, NaN, infinite,
                    or outside [0.0, 100.0].
    """
    for name, val in [
        ("magnitude_score", magnitude_score),
        ("depth_score", depth_score),
        ("distance_score", distance_score),
    ]:
        if val is None or not isinstance(val, (int, float)) or isinstance(val, bool):
            raise ValueError(f"Invalid {name} '{val}': must be a numeric value.")
        if math.isnan(val) or math.isinf(val) or val < 0.0 or val > 100.0:
            raise ValueError(f"{name} {val} out of valid normalized range [0.0, 100.0].")

    raw_composite = (
        magnitude_score * MAGNITUDE_WEIGHT
        + depth_score * DEPTH_WEIGHT
        + distance_score * DISTANCE_WEIGHT
    )
    clamped_composite = max(0.0, min(raw_composite, 100.0))
    return round(clamped_composite, 2)


def classify_earthquake_risk_level(composite_score: float) -> RiskLevel:
    """
    Classifies a normalized composite risk score into a standard RiskLevel.

    This classification is a deterministic decision-support heuristic designed
    for situational awareness, advisory status, and evacuation staging; it does
    not represent a probabilistic or empirical building damage assessment.

    Boundary Mapping (anchored directly to RISK_SCORE_THRESHOLDS):
      - 0.00 to 34.99  : RiskLevel.LOW
      - 35.00 to 59.99 : RiskLevel.MODERATE
      - 60.00 to 79.99 : RiskLevel.HIGH
      - 80.00 to 100.0 : RiskLevel.SEVERE

    Parameters:
        composite_score (float): Normalized composite score in [0.0, 100.0].

    Returns:
        RiskLevel: Categorical risk tier (RiskLevel.LOW, RiskLevel.MODERATE,
                   RiskLevel.HIGH, or RiskLevel.SEVERE).

    Raises:
        ValueError: If composite_score is None, non-numeric, NaN, infinite,
                    or outside [0.0, 100.0].
    """
    if composite_score is None or not isinstance(composite_score, (int, float)) or isinstance(composite_score, bool):
        raise ValueError(f"Invalid composite_score '{composite_score}': must be a numeric value.")
    if math.isnan(composite_score) or math.isinf(composite_score) or composite_score < 0.0 or composite_score > 100.0:
        raise ValueError(f"Composite score {composite_score} out of valid normalized range [0.0, 100.0].")

    if composite_score >= RISK_SCORE_THRESHOLDS[RiskLevel.SEVERE]["min_score"]:
        return RiskLevel.SEVERE
    elif composite_score >= RISK_SCORE_THRESHOLDS[RiskLevel.HIGH]["min_score"]:
        return RiskLevel.HIGH
    elif composite_score >= RISK_SCORE_THRESHOLDS[RiskLevel.MODERATE]["min_score"]:
        return RiskLevel.MODERATE
    else:
        return RiskLevel.LOW


# ===========================================================================
# 7. INTEGRATED ASSESSMENT PIPELINE
# ===========================================================================
def assess_earthquake_risk(
    magnitude: float,
    depth_km: float,
    latitude: float,
    longitude: float,
    raw_payload: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Assesses seismic hazard risk for Delhi NCR by executing the complete
    decision-support heuristic pipeline.

    Execution Pipeline:
      1. validate_earthquake_inputs      : Validates physical parameter boundaries.
      2. calculate_magnitude_score       : Computes normalized magnitude sub-score.
      3. calculate_depth_score           : Computes normalized focal depth sub-score.
      4. calculate_distance_to_delhi_km  : Computes Haversine distance to Delhi NCR datum.
      5. calculate_distance_score        : Computes normalized epicentral distance sub-score.
      6. calculate_composite_risk_score  : Computes weighted composite score (0.0 to 100.0).
      7. classify_earthquake_risk_level  : Maps composite score to categorical RiskLevel enum.

    Parameters:
        magnitude   (float): Reported earthquake magnitude (e.g. mb, Mw).
        depth_km    (float): Focal hypocentral depth in kilometers.
        latitude    (float): Epicentral latitude in decimal degrees (WGS 84).
        longitude   (float): Epicentral longitude in decimal degrees (WGS 84).
        raw_payload (dict) : Optional raw USGS or sensor metadata dictionary.

    Returns:
        Dict[str, Any] containing:
            - magnitude            (float)    : Input magnitude
            - depth_km             (float)    : Input focal depth in km
            - latitude             (float)    : Input epicentral latitude
            - longitude            (float)    : Input epicentral longitude
            - distance_to_delhi_km (float)    : Geodesic distance to Delhi NCR datum in km
            - magnitude_score      (float)    : Normalized magnitude sub-score [0.0, 100.0]
            - depth_score          (float)    : Normalized focal depth sub-score [0.0, 100.0]
            - distance_score       (float)    : Normalized distance sub-score [0.0, 100.0]
            - composite_risk_score (float)    : Weighted composite risk score [0.0, 100.0]
            - risk_level           (RiskLevel): Categorical risk tier (RiskLevel enum)

    Raises:
        ValueError: If any physical parameter fails boundary validation.
    """
    # 1. Input validation
    validate_earthquake_inputs(magnitude, depth_km, latitude, longitude)

    # 2. Magnitude score
    magnitude_score = calculate_magnitude_score(magnitude)

    # 3. Depth score
    depth_score = calculate_depth_score(depth_km)

    # 4. Geodesic distance to Delhi NCR reference datum
    distance_to_delhi_km = calculate_distance_to_delhi_km(latitude, longitude)

    # 5. Distance score
    distance_score = calculate_distance_score(distance_to_delhi_km)

    # 6. Weighted composite risk score
    composite_risk_score = calculate_composite_risk_score(
        magnitude_score, depth_score, distance_score
    )

    # 7. Risk-level classification
    risk_level = classify_earthquake_risk_level(composite_risk_score)

    result: Dict[str, Any] = {
        "magnitude": magnitude,
        "depth_km": depth_km,
        "latitude": latitude,
        "longitude": longitude,
        "distance_to_delhi_km": distance_to_delhi_km,
        "magnitude_score": magnitude_score,
        "depth_score": depth_score,
        "distance_score": distance_score,
        "composite_risk_score": composite_risk_score,
        "risk_level": risk_level,
    }

    if raw_payload is not None:
        result["raw_payload"] = raw_payload

    return result
