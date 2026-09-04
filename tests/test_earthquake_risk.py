"""
Automated Unit Tests for Earthquake Risk Assessment Engine
===========================================================
Module: tests/test_earthquake_risk.py

Validates:
  1. validate_earthquake_inputs
  2. calculate_magnitude_score
  3. calculate_depth_score
  4. calculate_distance_to_delhi_km
  5. calculate_distance_score
  6. calculate_composite_risk_score
  7. classify_earthquake_risk_level
  8. assess_earthquake_risk
"""

import math
import pytest

from evacuation_engine.earthquake_risk import (
    DELHI_NCR_REF_LATITUDE,
    DELHI_NCR_REF_LONGITUDE,
    RiskLevel,
    assess_earthquake_risk,
    calculate_composite_risk_score,
    calculate_depth_score,
    calculate_distance_score,
    calculate_distance_to_delhi_km,
    calculate_magnitude_score,
    classify_earthquake_risk_level,
    validate_earthquake_inputs,
)


# ===========================================================================
# 1. validate_earthquake_inputs Tests
# ===========================================================================
class TestValidateEarthquakeInputs:
    """Tests for validate_earthquake_inputs."""

    def test_valid_typical_inputs(self):
        """Standard valid inputs within physical limits should not raise."""
        validate_earthquake_inputs(
            magnitude=5.2,
            depth_km=25.0,
            latitude=28.6139,
            longitude=77.2090,
        )

    @pytest.mark.parametrize(
        "mag,depth,lat,lon",
        [
            (0.0, 0.0, -90.0, -180.0),      # Minimum physical boundaries
            (10.0, 700.0, 90.0, 180.0),     # Maximum physical boundaries
            (4.3, 10.0, 28.7240, 77.1890),   # Representative NCR case
            (0.0, 350.0, 0.0, 0.0),          # Mid-range coordinates
        ],
    )
    def test_valid_boundary_combinations(self, mag, depth, lat, lon):
        """Boundary physical coordinates and values should pass validation."""
        validate_earthquake_inputs(magnitude=mag, depth_km=depth, latitude=lat, longitude=lon)

    @pytest.mark.parametrize("invalid_mag", [-0.01, -1.0, -5.5])
    def test_negative_magnitude_raises_value_error(self, invalid_mag):
        """Negative magnitude must raise ValueError."""
        with pytest.raises(ValueError, match="Magnitude .* out of physical bounds"):
            validate_earthquake_inputs(invalid_mag, 10.0, 28.6, 77.2)

    @pytest.mark.parametrize("invalid_mag", [10.01, 11.0, 50.0])
    def test_magnitude_above_10_raises_value_error(self, invalid_mag):
        """Magnitude above 10.0 must raise ValueError."""
        with pytest.raises(ValueError, match="Magnitude .* out of physical bounds"):
            validate_earthquake_inputs(invalid_mag, 10.0, 28.6, 77.2)

    @pytest.mark.parametrize("invalid_depth", [-0.01, -1.0, -100.0])
    def test_negative_depth_raises_value_error(self, invalid_depth):
        """Negative focal depth must raise ValueError."""
        with pytest.raises(ValueError, match="Focal depth .* out of physical bounds"):
            validate_earthquake_inputs(5.0, invalid_depth, 28.6, 77.2)

    @pytest.mark.parametrize("invalid_depth", [700.01, 750.0, 1000.0])
    def test_depth_above_700_raises_value_error(self, invalid_depth):
        """Focal depth exceeding 700 km must raise ValueError."""
        with pytest.raises(ValueError, match="Focal depth .* out of physical bounds"):
            validate_earthquake_inputs(5.0, invalid_depth, 28.6, 77.2)

    @pytest.mark.parametrize("invalid_lat", [-90.01, -95.0, 90.01, 120.0])
    def test_latitude_outside_range_raises_value_error(self, invalid_lat):
        """Latitude outside [-90, 90] must raise ValueError."""
        with pytest.raises(ValueError, match="Latitude .* out of valid geographic range"):
            validate_earthquake_inputs(5.0, 10.0, invalid_lat, 77.2)

    @pytest.mark.parametrize("invalid_lon", [-180.01, -200.0, 180.01, 200.0])
    def test_longitude_outside_range_raises_value_error(self, invalid_lon):
        """Longitude outside [-180, 180] must raise ValueError."""
        with pytest.raises(ValueError, match="Longitude .* out of valid geographic range"):
            validate_earthquake_inputs(5.0, 10.0, 28.6, invalid_lon)

    @pytest.mark.parametrize(
        "bad_val",
        [float("nan"), float("inf"), float("-inf")],
    )
    def test_nan_and_inf_inputs_raise_value_error(self, bad_val):
        """NaN and infinity for any coordinate or metric must raise ValueError."""
        with pytest.raises(ValueError):
            validate_earthquake_inputs(bad_val, 10.0, 28.6, 77.2)
        with pytest.raises(ValueError):
            validate_earthquake_inputs(5.0, bad_val, 28.6, 77.2)
        with pytest.raises(ValueError):
            validate_earthquake_inputs(5.0, 10.0, bad_val, 77.2)
        with pytest.raises(ValueError):
            validate_earthquake_inputs(5.0, 10.0, 28.6, bad_val)

    @pytest.mark.parametrize(
        "invalid_type",
        [None, "string", [1], True, False],
    )
    def test_non_numeric_inputs_raise_value_error(self, invalid_type):
        """Non-numeric values (None, str, list, bool) must raise ValueError."""
        with pytest.raises(ValueError):
            validate_earthquake_inputs(invalid_type, 10.0, 28.6, 77.2)
        with pytest.raises(ValueError):
            validate_earthquake_inputs(5.0, invalid_type, 28.6, 77.2)
        with pytest.raises(ValueError):
            validate_earthquake_inputs(5.0, 10.0, invalid_type, 77.2)
        with pytest.raises(ValueError):
            validate_earthquake_inputs(5.0, 10.0, 28.6, invalid_type)


# ===========================================================================
# 2. calculate_magnitude_score Tests
# ===========================================================================
class TestCalculateMagnitudeScore:
    """Tests for calculate_magnitude_score."""

    @pytest.mark.parametrize(
        "magnitude,expected_score",
        [
            (3.0, 0.0),     # Baseline threshold
            (4.2, 35.0),    # Low tier upper threshold
            (5.4, 60.0),    # Moderate tier upper threshold
            (6.4, 80.0),    # High tier upper threshold
            (6.5, 85.0),    # Severe tier lower threshold
        ],
    )
    def test_required_magnitude_boundaries(self, magnitude, expected_score):
        """Verify scores at specified magnitude boundaries: 3.0, 4.2, 5.4, 6.4, 6.5."""
        score = calculate_magnitude_score(magnitude)
        assert score == pytest.approx(expected_score, abs=0.01)

    @pytest.mark.parametrize(
        "magnitude,expected_score",
        [
            (0.0, 0.0),     # Sub-monitored zero
            (1.5, 0.0),     # Sub-monitored below 3.0
            (2.99, 0.0),    # Just below MIN_MONITORED
            (3.6, 17.5),    # Midpoint [3.0, 4.2]: (0.6 / 1.2) * 35.0 = 17.5
            (4.8, 47.5),    # Midpoint [4.2, 5.4]: 35 + (0.6 / 1.2) * 25.0 = 47.5
            (5.9, 70.0),    # Midpoint [5.4, 6.4]: 60 + (0.5 / 1.0) * 20.0 = 70.0
            (6.45, 82.5),   # Midpoint [6.4, 6.5]: 80 + (0.05 / 0.1) * 5.0 = 82.5
            (7.25, 92.5),   # Midpoint [6.5, 8.0]: 85 + (0.75 / 1.5) * 15.0 = 92.5
            (8.0, 100.0),   # Normalization ceiling
            (9.0, 100.0),   # Beyond ceiling capped at 100
            (10.0, 100.0),  # Max magnitude capped at 100
        ],
    )
    def test_representative_magnitude_cases(self, magnitude, expected_score):
        """Verify piecewise linear interpolation across intermediate magnitude intervals."""
        score = calculate_magnitude_score(magnitude)
        assert score == pytest.approx(expected_score, abs=0.01)

    def test_magnitude_score_for_4_point_3(self):
        """Check magnitude=4.3 specifically (matches complete example)."""
        score = calculate_magnitude_score(4.3)
        assert score == pytest.approx(37.08, abs=0.01)

    @pytest.mark.parametrize("invalid_mag", [-0.01, -1.0, 10.01, 15.0])
    def test_invalid_magnitude_bounds_raise_value_error(self, invalid_mag):
        """Magnitude outside [0.0, 10.0] must raise ValueError."""
        with pytest.raises(ValueError, match="Magnitude .* out of physical bounds"):
            calculate_magnitude_score(invalid_mag)

    @pytest.mark.parametrize("bad_val", [float("nan"), float("inf"), float("-inf")])
    def test_nan_and_inf_magnitude_raise_value_error(self, bad_val):
        """NaN and inf magnitude must raise ValueError."""
        with pytest.raises(ValueError):
            calculate_magnitude_score(bad_val)

    @pytest.mark.parametrize("invalid_type", [None, "4.2", True, [3.0]])
    def test_non_numeric_magnitude_raises_value_error(self, invalid_type):
        """Non-numeric magnitude must raise ValueError."""
        with pytest.raises(ValueError):
            calculate_magnitude_score(invalid_type)


# ===========================================================================
# 3. calculate_depth_score Tests
# ===========================================================================
class TestCalculateDepthScore:
    """Tests for calculate_depth_score."""

    @pytest.mark.parametrize(
        "depth,expected_score",
        [
            (0.0, 100.0),  # Surface hypocenter
            (15.0, 85.0),  # Very shallow upper threshold
            (35.0, 60.0),  # Shallow upper threshold
            (70.0, 35.0),  # Intermediate depth upper threshold
        ],
    )
    def test_required_depth_boundaries(self, depth, expected_score):
        """Verify scores at specified depth boundaries: 0, 15, 35, 70."""
        score = calculate_depth_score(depth)
        assert score == pytest.approx(expected_score, abs=0.01)

    @pytest.mark.parametrize(
        "depth,expected_score",
        [
            (7.5, 92.5),    # Midpoint [0, 15]: 100 - (7.5 / 15) * 15 = 92.5
            (10.0, 90.0),   # 10 km depth from complete example
            (25.0, 72.5),   # Midpoint [15, 35]: 85 - (10 / 20) * 25 = 72.5
            (52.5, 47.5),   # Midpoint [35, 70]: 60 - (17.5 / 35) * 25 = 47.5
            (160.0, 17.5),  # Midpoint [70, 250]: 35 - (90 / 180) * 35 = 17.5
            (250.0, 0.0),   # Attenuation endpoint (score = 0.0)
            (400.0, 0.0),   # Deep hypocenter capped at 0.0
            (700.0, 0.0),   # Max physical depth capped at 0.0
        ],
    )
    def test_representative_depth_cases(self, depth, expected_score):
        """Verify piecewise linear interpolation across intermediate depth intervals."""
        score = calculate_depth_score(depth)
        assert score == pytest.approx(expected_score, abs=0.01)

    @pytest.mark.parametrize("invalid_depth", [-0.01, -5.0, 700.01, 800.0])
    def test_invalid_depth_bounds_raise_value_error(self, invalid_depth):
        """Depth outside [0.0, 700.0] must raise ValueError."""
        with pytest.raises(ValueError, match="Focal depth .* out of physical bounds"):
            calculate_depth_score(invalid_depth)

    @pytest.mark.parametrize("bad_val", [float("nan"), float("inf"), float("-inf")])
    def test_nan_and_inf_depth_raise_value_error(self, bad_val):
        """NaN and inf depth must raise ValueError."""
        with pytest.raises(ValueError):
            calculate_depth_score(bad_val)

    @pytest.mark.parametrize("invalid_type", [None, "15.0", False, [10]])
    def test_non_numeric_depth_raises_value_error(self, invalid_type):
        """Non-numeric depth must raise ValueError."""
        with pytest.raises(ValueError):
            calculate_depth_score(invalid_type)


# ===========================================================================
# 4. calculate_distance_to_delhi_km Tests
# ===========================================================================
class TestCalculateDistanceToDelhiKm:
    """Tests for calculate_distance_to_delhi_km."""

    def test_distance_at_delhi_reference_point(self):
        """Distance from reference coordinates to itself must be 0.0 km."""
        dist = calculate_distance_to_delhi_km(
            DELHI_NCR_REF_LATITUDE,
            DELHI_NCR_REF_LONGITUDE,
        )
        assert dist == 0.0

    def test_complete_example_distance(self):
        """Latitude 28.7240, Longitude 77.1890 should yield approximately 12.40 km."""
        dist = calculate_distance_to_delhi_km(28.7240, 77.1890)
        assert dist == pytest.approx(12.40, abs=0.05)

    def test_custom_reference_coordinates(self):
        """Distance computation with explicit custom reference point."""
        # Distance between (0, 0) and (0, 1 degree longitude) along equator
        # 1 degree along equator ~ 6371 * pi / 180 ~ 111.19 km
        dist = calculate_distance_to_delhi_km(
            latitude=0.0,
            longitude=1.0,
            ref_lat=0.0,
            ref_lon=0.0,
        )
        assert dist == pytest.approx(111.19, abs=0.1)

    def test_distance_symmetry(self):
        """Distance from A to B should equal distance from B to A."""
        lat_a, lon_a = 28.6139, 77.2090
        lat_b, lon_b = 29.0000, 78.0000
        dist_ab = calculate_distance_to_delhi_km(lat_b, lon_b, ref_lat=lat_a, ref_lon=lon_a)
        dist_ba = calculate_distance_to_delhi_km(lat_a, lon_a, ref_lat=lat_b, ref_lon=lon_b)
        assert dist_ab == dist_ba

    @pytest.mark.parametrize("invalid_lat", [-90.01, 90.01, -100.0, 100.0])
    def test_invalid_latitude_raises_value_error(self, invalid_lat):
        """Latitude outside [-90, 90] must raise ValueError."""
        with pytest.raises(ValueError, match="Latitude .* out of valid geographic range"):
            calculate_distance_to_delhi_km(invalid_lat, 77.2)

    @pytest.mark.parametrize("invalid_lon", [-180.01, 180.01, -200.0, 200.0])
    def test_invalid_longitude_raises_value_error(self, invalid_lon):
        """Longitude outside [-180, 180] must raise ValueError."""
        with pytest.raises(ValueError, match="Longitude .* out of valid geographic range"):
            calculate_distance_to_delhi_km(28.6, invalid_lon)

    @pytest.mark.parametrize("bad_val", [float("nan"), float("inf"), float("-inf")])
    def test_nan_and_inf_coordinates_raise_value_error(self, bad_val):
        """NaN or inf coordinates must raise ValueError."""
        with pytest.raises(ValueError):
            calculate_distance_to_delhi_km(bad_val, 77.2)
        with pytest.raises(ValueError):
            calculate_distance_to_delhi_km(28.6, bad_val)

    @pytest.mark.parametrize("invalid_type", [None, "28.6", True])
    def test_non_numeric_coordinates_raise_value_error(self, invalid_type):
        """Non-numeric coordinates must raise ValueError."""
        with pytest.raises(ValueError):
            calculate_distance_to_delhi_km(invalid_type, 77.2)
        with pytest.raises(ValueError):
            calculate_distance_to_delhi_km(28.6, invalid_type)


# ===========================================================================
# 5. calculate_distance_score Tests
# ===========================================================================
class TestCalculateDistanceScore:
    """Tests for calculate_distance_score."""

    @pytest.mark.parametrize(
        "distance,expected_score",
        [
            (0.0, 100.0),   # Direct hit on Delhi NCR reference
            (60.0, 80.0),   # Near-field boundary
            (180.0, 55.0),  # Sub-regional boundary
            (380.0, 25.0),  # Far-regional boundary
        ],
    )
    def test_required_distance_boundaries(self, distance, expected_score):
        """Verify scores at specified distance boundaries: 0, 60, 180, 380."""
        score = calculate_distance_score(distance)
        assert score == pytest.approx(expected_score, abs=0.01)

    @pytest.mark.parametrize(
        "distance,expected_score",
        [
            (12.40, 95.87),   # Complete example distance (approx 95.87)
            (30.0, 90.0),     # Midpoint [0, 60]: 100 - (30 / 60) * 20 = 90.0
            (120.0, 67.5),    # Midpoint [60, 180]: 80 - (60 / 120) * 25 = 67.5
            (280.0, 40.0),    # Midpoint [180, 380]: 55 - (100 / 200) * 30 = 40.0
            (540.0, 12.5),    # Midpoint [380, 700]: 25 - (160 / 320) * 25 = 12.5
            (700.0, 0.0),     # Attenuation endpoint (score = 0.0)
            (1000.0, 0.0),    # Far distant capped at 0.0
        ],
    )
    def test_representative_distance_cases(self, distance, expected_score):
        """Verify piecewise linear interpolation across intermediate distance intervals."""
        score = calculate_distance_score(distance)
        assert score == pytest.approx(expected_score, abs=0.01)

    @pytest.mark.parametrize("invalid_dist", [-0.01, -10.0, -100.0])
    def test_negative_distance_raises_value_error(self, invalid_dist):
        """Negative distance must raise ValueError."""
        with pytest.raises(ValueError, match="Distance .* out of valid bounds"):
            calculate_distance_score(invalid_dist)

    @pytest.mark.parametrize("bad_val", [float("nan"), float("inf"), float("-inf")])
    def test_nan_and_inf_distance_raise_value_error(self, bad_val):
        """NaN and inf distance must raise ValueError."""
        with pytest.raises(ValueError):
            calculate_distance_score(bad_val)

    @pytest.mark.parametrize("invalid_type", [None, "60.0", True, [0]])
    def test_non_numeric_distance_raises_value_error(self, invalid_type):
        """Non-numeric distance must raise ValueError."""
        with pytest.raises(ValueError):
            calculate_distance_score(invalid_type)


# ===========================================================================
# 6. calculate_composite_risk_score Tests
# ===========================================================================
class TestCalculateCompositeRiskScore:
    """Tests for calculate_composite_risk_score."""

    def test_all_zeros(self):
        """All zero sub-scores must yield composite score of 0.0."""
        score = calculate_composite_risk_score(0.0, 0.0, 0.0)
        assert score == 0.0

    def test_all_hundreds(self):
        """All 100 sub-scores must yield composite score of 100.0."""
        score = calculate_composite_risk_score(100.0, 100.0, 100.0)
        assert score == 100.0

    def test_individual_component_weight_contributions(self):
        """Test isolated contributions using weights: mag=0.5, depth=0.2, dist=0.3."""
        # Magnitude only
        assert calculate_composite_risk_score(100.0, 0.0, 0.0) == 50.0
        # Depth only
        assert calculate_composite_risk_score(0.0, 100.0, 0.0) == 20.0
        # Distance only
        assert calculate_composite_risk_score(0.0, 0.0, 100.0) == 30.0

    def test_complete_example_composite_score(self):
        """Sub-scores 37.08, 90.00, 95.87 must yield 65.30."""
        # 37.08 * 0.5 + 90.0 * 0.2 + 95.87 * 0.3 = 18.54 + 18.00 + 28.761 = 65.301 -> 65.30
        score = calculate_composite_risk_score(37.08, 90.00, 95.87)
        assert score == pytest.approx(65.30, abs=0.01)

    @pytest.mark.parametrize(
        "bad_sub_score",
        [-0.01, -10.0, 100.01, 150.0],
    )
    def test_invalid_sub_scores_below_0_and_above_100(self, bad_sub_score):
        """Sub-scores outside [0.0, 100.0] must raise ValueError."""
        with pytest.raises(ValueError, match="out of valid normalized range"):
            calculate_composite_risk_score(bad_sub_score, 50.0, 50.0)
        with pytest.raises(ValueError, match="out of valid normalized range"):
            calculate_composite_risk_score(50.0, bad_sub_score, 50.0)
        with pytest.raises(ValueError, match="out of valid normalized range"):
            calculate_composite_risk_score(50.0, 50.0, bad_sub_score)

    @pytest.mark.parametrize("bad_val", [float("nan"), float("inf"), float("-inf")])
    def test_nan_and_inf_sub_scores_raise_value_error(self, bad_val):
        """NaN and inf sub-scores must raise ValueError."""
        with pytest.raises(ValueError):
            calculate_composite_risk_score(bad_val, 50.0, 50.0)
        with pytest.raises(ValueError):
            calculate_composite_risk_score(50.0, bad_val, 50.0)
        with pytest.raises(ValueError):
            calculate_composite_risk_score(50.0, 50.0, bad_val)

    @pytest.mark.parametrize("invalid_type", [None, "50", True])
    def test_non_numeric_sub_scores_raise_value_error(self, invalid_type):
        """Non-numeric sub-scores must raise ValueError."""
        with pytest.raises(ValueError):
            calculate_composite_risk_score(invalid_type, 50.0, 50.0)
        with pytest.raises(ValueError):
            calculate_composite_risk_score(50.0, invalid_type, 50.0)
        with pytest.raises(ValueError):
            calculate_composite_risk_score(50.0, 50.0, invalid_type)


# ===========================================================================
# 7. classify_earthquake_risk_level Tests
# ===========================================================================
class TestClassifyEarthquakeRiskLevel:
    """Tests for classify_earthquake_risk_level."""

    @pytest.mark.parametrize(
        "score,expected_level",
        [
            (0.0, RiskLevel.LOW),
            (34.99, RiskLevel.LOW),
            (35.0, RiskLevel.MODERATE),
            (59.99, RiskLevel.MODERATE),
            (60.0, RiskLevel.HIGH),
            (79.99, RiskLevel.HIGH),
            (80.0, RiskLevel.SEVERE),
            (100.0, RiskLevel.SEVERE),
        ],
    )
    def test_required_risk_score_boundaries(self, score, expected_level):
        """Verify classifications at exact boundary scores: 0, 34.99, 35, 59.99, 60, 79.99, 80, 100."""
        assert classify_earthquake_risk_level(score) == expected_level

    @pytest.mark.parametrize(
        "score,expected_level",
        [
            (15.0, RiskLevel.LOW),
            (45.0, RiskLevel.MODERATE),
            (65.30, RiskLevel.HIGH),
            (92.0, RiskLevel.SEVERE),
        ],
    )
    def test_representative_classifications(self, score, expected_level):
        """Verify classification of intermediate scores within each tier."""
        assert classify_earthquake_risk_level(score) == expected_level

    @pytest.mark.parametrize("invalid_score", [-0.01, -1.0, -50.0])
    def test_negative_composite_score_raises_value_error(self, invalid_score):
        """Composite score below 0.0 must raise ValueError."""
        with pytest.raises(ValueError, match="out of valid normalized range"):
            classify_earthquake_risk_level(invalid_score)

    @pytest.mark.parametrize("invalid_score", [100.01, 101.0, 200.0])
    def test_composite_score_above_100_raises_value_error(self, invalid_score):
        """Composite score above 100.0 must raise ValueError."""
        with pytest.raises(ValueError, match="out of valid normalized range"):
            classify_earthquake_risk_level(invalid_score)

    @pytest.mark.parametrize("bad_val", [float("nan"), float("inf"), float("-inf")])
    def test_nan_and_inf_composite_score_raises_value_error(self, bad_val):
        """NaN and inf composite scores must raise ValueError."""
        with pytest.raises(ValueError):
            classify_earthquake_risk_level(bad_val)

    @pytest.mark.parametrize("invalid_type", [None, "60.0", False, []])
    def test_non_numeric_composite_score_raises_value_error(self, invalid_type):
        """Non-numeric composite scores must raise ValueError."""
        with pytest.raises(ValueError):
            classify_earthquake_risk_level(invalid_type)


# ===========================================================================
# 8. assess_earthquake_risk Tests
# ===========================================================================
class TestAssessEarthquakeRisk:
    """Tests for assess_earthquake_risk integrated pipeline."""

    def test_complete_user_example(self):
        """
        Verify the complete representative earthquake example:
          magnitude = 4.3
          depth_km = 10.0
          latitude = 28.7240
          longitude = 77.1890

        Expected approximately:
          distance = 12.40 km
          magnitude_score = 37.08
          depth_score = 90.00
          distance_score = 95.87
          composite_score = 65.30
          risk_level = RiskLevel.HIGH
        """
        result = assess_earthquake_risk(
            magnitude=4.3,
            depth_km=10.0,
            latitude=28.7240,
            longitude=77.1890,
        )

        assert result["magnitude"] == 4.3
        assert result["depth_km"] == 10.0
        assert result["latitude"] == 28.7240
        assert result["longitude"] == 77.1890
        assert result["distance_to_delhi_km"] == pytest.approx(12.40, abs=0.05)
        assert result["magnitude_score"] == pytest.approx(37.08, abs=0.01)
        assert result["depth_score"] == pytest.approx(90.00, abs=0.01)
        assert result["distance_score"] == pytest.approx(95.87, abs=0.01)
        assert result["composite_risk_score"] == pytest.approx(65.30, abs=0.01)
        assert result["risk_level"] == RiskLevel.HIGH

    def test_optional_raw_payload_included_when_provided(self):
        """When raw_payload is provided, it must be included in the return dictionary."""
        payload = {"source": "USGS", "event_id": "us7000test"}
        result = assess_earthquake_risk(
            magnitude=5.0,
            depth_km=20.0,
            latitude=28.6139,
            longitude=77.2090,
            raw_payload=payload,
        )
        assert "raw_payload" in result
        assert result["raw_payload"] == payload

    def test_optional_raw_payload_absent_when_omitted(self):
        """When raw_payload is not provided, 'raw_payload' key is not present in output."""
        result = assess_earthquake_risk(
            magnitude=5.0,
            depth_km=20.0,
            latitude=28.6139,
            longitude=77.2090,
        )
        assert "raw_payload" not in result

    def test_severe_scenario(self):
        """Direct shallow high-magnitude strike must evaluate to RiskLevel.SEVERE."""
        result = assess_earthquake_risk(
            magnitude=7.5,
            depth_km=5.0,
            latitude=DELHI_NCR_REF_LATITUDE,
            longitude=DELHI_NCR_REF_LONGITUDE,
        )
        assert result["risk_level"] == RiskLevel.SEVERE
        assert result["composite_risk_score"] >= 80.0

    def test_low_risk_scenario(self):
        """Distant deep low-magnitude event must evaluate to RiskLevel.LOW."""
        result = assess_earthquake_risk(
            magnitude=3.0,
            depth_km=200.0,
            latitude=32.0,
            longitude=80.0,
        )
        assert result["risk_level"] == RiskLevel.LOW
        assert result["composite_risk_score"] < 35.0

    @pytest.mark.parametrize(
        "bad_mag,bad_depth,bad_lat,bad_lon",
        [
            (-1.0, 10.0, 28.6, 77.2),     # Negative magnitude
            (11.0, 10.0, 28.6, 77.2),     # Magnitude > 10
            (5.0, -10.0, 28.6, 77.2),     # Negative depth
            (5.0, 750.0, 28.6, 77.2),     # Depth > 700
            (5.0, 10.0, -95.0, 77.2),     # Latitude < -90
            (5.0, 10.0, 95.0, 77.2),      # Latitude > 90
            (5.0, 10.0, 28.6, -185.0),    # Longitude < -180
            (5.0, 10.0, 28.6, 185.0),     # Longitude > 180
            (float("nan"), 10.0, 28.6, 77.2),
            (5.0, float("inf"), 28.6, 77.2),
        ],
    )
    def test_invalid_parameters_raise_value_error(self, bad_mag, bad_depth, bad_lat, bad_lon):
        """Pipeline should reject invalid inputs with ValueError."""
        with pytest.raises(ValueError):
            assess_earthquake_risk(
                magnitude=bad_mag,
                depth_km=bad_depth,
                latitude=bad_lat,
                longitude=bad_lon,
            )
