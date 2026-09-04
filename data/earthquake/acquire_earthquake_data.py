"""
Earthquake Data Acquisition Script - Two-Tier USGS ComCat FDSN API
====================================================================
Module: data/earthquake/acquire_earthquake_data.py

Purpose:
    Acquires historical earthquake records for seismic risk assessment in Delhi NCR
    using the USGS Comprehensive Earthquake Catalog (ComCat) FDSN Event Web Service.

Two-Tier Geographic Scope:
    -------------------------------------------------------------------------
    Tier 1 (Local Delhi NCR Epicenters - Near-Field):
        - Latitude Range : 27.5° N to 30.0° N
        - Longitude Range: 76.0° E to 78.5° E
        - Min Magnitude  : 2.5 (Captures local intra-plate faults: Sohna, Mathura, MDSF)
    -------------------------------------------------------------------------
    Tier 2 (Regional Himalayan & Indo-Gangetic Impact Zone - Far-Field):
        - Latitude Range : 26.0° N to 33.5° N
        - Longitude Range: 73.5° E to 82.5° E
        - Min Magnitude  : 4.5 (Captures major regional thrust earthquakes whose long-period
                                ground shaking amplifies in the deep Delhi sedimentary basin)
    -------------------------------------------------------------------------

Historical Time Window:
    - Start Date: 1990-01-01 (Modern digital telemetry era)
    - End Date  : Current UTC date

Deduplication:
    - Events matching both spatial/magnitude criteria are merged and deduplicated
      strictly by `event_id`.
    - Results are sorted chronologically in descending order (newest to oldest).

Extracted Core Fields (Preserved Data Contract):
    1. event_id     : Unique USGS identifier
    2. event_time   : UTC ISO 8601 timestamp (YYYY-MM-DDTHH:MM:SSZ)
    3. latitude     : Epicentral latitude in decimal degrees (WGS 84)
    4. longitude    : Epicentral longitude in decimal degrees (WGS 84)
    5. depth_km     : Focal depth in kilometers
    6. magnitude    : Primary reported magnitude
    7. mag_type     : Magnitude determination scale (e.g., 'mb', 'ml', 'mw')

Constraints & Guardrails:
    - Keeps existing sample files unchanged.
    - No database schema modifications.
    - No ML labels or ML models trained.
    - Uses Python standard library only (no external dependencies required).
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# Directory paths relative to this script
SCRIPT_DIR = Path(__file__).resolve().parent

# Existing sample files (Kept unchanged for test references)
SAMPLE_RAW_PATH = SCRIPT_DIR / "raw_earthquakes_delhi_ncr.json"
SAMPLE_PARSED_PATH = SCRIPT_DIR / "sample_earthquakes_delhi_ncr.json"

# New targets for two-tier full historical dataset
HISTORICAL_RAW_PATH = SCRIPT_DIR / "raw_earthquakes_historical.json"
HISTORICAL_PARSED_PATH = SCRIPT_DIR / "historical_earthquakes_delhi_regional.json"

# USGS ComCat FDSN API Endpoints
USGS_QUERY_URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"
USGS_COUNT_URL = "https://earthquake.usgs.gov/fdsnws/event/1/count"

# Two-Tier Scope Specifications
TIER_1_CONFIG: Dict[str, Any] = {
    "name": "Tier 1 (Local Delhi NCR)",
    "minlatitude": 27.5,
    "maxlatitude": 30.0,
    "minlongitude": 76.0,
    "maxlongitude": 78.5,
    "minmagnitude": 2.5,
}

TIER_2_CONFIG: Dict[str, Any] = {
    "name": "Tier 2 (Regional Himalayan Belt)",
    "minlatitude": 26.0,
    "maxlatitude": 33.5,
    "minlongitude": 73.5,
    "maxlongitude": 82.5,
    "minmagnitude": 4.5,
}

DEFAULT_START_TIME = "1990-01-01"


def get_current_utc_date() -> str:
    """Returns today's date formatted as YYYY-MM-DD in UTC."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def build_usgs_query_url(
    tier_config: Dict[str, Any],
    start_time: str = DEFAULT_START_TIME,
    end_time: Optional[str] = None,
    limit: int = 20000,
    order_by: str = "time",
    is_count_query: bool = False,
) -> str:
    """
    Constructs the USGS ComCat FDSN API URL for a specific tier configuration.
    
    Parameters:
      tier_config     : Dictionary with minlatitude, maxlatitude, minlongitude, maxlongitude, minmagnitude
      start_time      : Earliest event origin time (ISO 8601 string: YYYY-MM-DD)
      end_time        : Latest event origin time (defaults to current UTC date)
      limit           : Max events per query (USGS FDSN max is 20000 per single request)
      order_by        : Sort order ('time' sorts descending)
      is_count_query  : If True, targets the /count endpoint instead of /query
    """
    if end_time is None:
        end_time = get_current_utc_date()

    params: Dict[str, Any] = {
        "format": "geojson",
        "minlatitude": tier_config["minlatitude"],
        "maxlatitude": tier_config["maxlatitude"],
        "minlongitude": tier_config["minlongitude"],
        "maxlongitude": tier_config["maxlongitude"],
        "minmagnitude": tier_config["minmagnitude"],
        "starttime": start_time,
        "endtime": end_time,
    }

    if not is_count_query:
        params["limit"] = limit
        params["orderby"] = order_by

    base_url = USGS_COUNT_URL if is_count_query else USGS_QUERY_URL
    return f"{base_url}?{urlencode(params)}"


def fetch_usgs_data(query_url: str, timeout_seconds: int = 45) -> Dict[str, Any]:
    """
    Executes an HTTP GET request to the USGS ComCat API and returns the parsed JSON payload.
    Uses standard library urllib.request with educational/research User-Agent.
    """
    req = Request(
        url=query_url,
        headers={
            "User-Agent": "DisasterDecisionSupportPlatform/1.0 (Delhi NCR Study; Research)"
        },
        method="GET",
    )

    try:
        with urlopen(req, timeout=timeout_seconds) as response:
            if response.getcode() != 200:
                raise RuntimeError(f"USGS API returned HTTP status {response.getcode()}")
            raw_bytes = response.read()
            return json.loads(raw_bytes.decode("utf-8"))

    except HTTPError as e:
        logger.error("HTTP error from USGS API: %s %s", e.code, e.reason)
        raise
    except URLError as e:
        logger.error("Network connection error: %s", e.reason)
        raise
    except json.JSONDecodeError as e:
        logger.error("JSON parsing error: %s", e)
        raise


def extract_event_fields(raw_feature_collection: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Parses USGS GeoJSON FeatureCollection and maps records to the 7 core fields:
    
      1. event_id   : str   (USGS catalog event identifier)
      2. event_time : str   (ISO 8601 UTC timestamp)
      3. latitude   : float (WGS 84 Latitude)
      4. longitude  : float (WGS 84 Longitude)
      5. depth_km   : float (Focal hypocentral depth in km)
      6. magnitude  : float (Primary reported magnitude)
      7. mag_type   : str   (Magnitude calculation method)
    """
    features = raw_feature_collection.get("features", [])
    extracted_records: List[Dict[str, Any]] = []

    for feature in features:
        event_id = feature.get("id") or "UNKNOWN_ID"
        props = feature.get("properties") or {}
        geom = feature.get("geometry") or {}
        coords = geom.get("coordinates") or [None, None, None]

        # Convert epoch milliseconds to ISO 8601 UTC string
        epoch_ms = props.get("time")
        if epoch_ms is not None:
            time_iso = (
                datetime.fromtimestamp(epoch_ms / 1000.0, tz=timezone.utc)
                .strftime("%Y-%m-%dT%H:%M:%SZ")
            )
        else:
            time_iso = None

        # GeoJSON coordinates order: [longitude, latitude, depth_km]
        longitude = coords[0] if len(coords) > 0 else None
        latitude = coords[1] if len(coords) > 1 else None
        depth_km = coords[2] if len(coords) > 2 else None

        extracted_records.append({
            "event_id": event_id,
            "event_time": time_iso,
            "latitude": latitude,
            "longitude": longitude,
            "depth_km": depth_km,
            "magnitude": props.get("mag"),
            "mag_type": props.get("magType"),
        })

    return extracted_records


def merge_and_deduplicate(
    tier1_events: List[Dict[str, Any]],
    tier2_events: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Merges records from both tiers and eliminates duplicates using unique `event_id`.
    Returns the consolidated list sorted chronologically descending (newest first).
    """
    combined_dict: Dict[str, Dict[str, Any]] = {}

    # Ingest Tier 1
    for event in tier1_events:
        event_id = event["event_id"]
        if event_id not in combined_dict:
            combined_dict[event_id] = event

    # Ingest Tier 2 (deduplicating any overlap)
    duplicate_count = 0
    for event in tier2_events:
        event_id = event["event_id"]
        if event_id in combined_dict:
            duplicate_count += 1
        else:
            combined_dict[event_id] = event

    logger.info(
        "Deduplication complete: %d Tier 1 events, %d Tier 2 events, %d overlapping duplicates resolved.",
        len(tier1_events), len(tier2_events), duplicate_count
    )

    # Sort descending by event_time
    sorted_events = sorted(
        combined_dict.values(),
        key=lambda x: x["event_time"] or "",
        reverse=True
    )
    return sorted_events


def save_json_file(data: Any, target_path: Path, description: str) -> None:
    """Helper to save structured data to formatted JSON."""
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info("Saved %s to: %s", description, target_path)


def run_two_tier_acquisition(
    start_time: str = DEFAULT_START_TIME,
    end_time: Optional[str] = None,
    raw_output_path: Path = HISTORICAL_RAW_PATH,
    parsed_output_path: Path = HISTORICAL_PARSED_PATH,
) -> Dict[str, Any]:
    """
    Full pipeline execution routine for Two-Tier USGS acquisition:
      1. Builds queries for Tier 1 (Local NCR) and Tier 2 (Himalayan Regional).
      2. Executes API queries.
      3. Saves combined raw response to separate historical raw JSON.
      4. Extracts the 7 core fields from each tier.
      5. Merges and deduplicates events by `event_id`.
      6. Saves clean deduplicated dataset to separate historical parsed JSON.
      7. Returns summary statistics.
    """
    if end_time is None:
        end_time = get_current_utc_date()

    logger.info("Initiating Two-Tier Earthquake Acquisition (%s to %s)...", start_time, end_time)

    # 1. Fetch Tier 1
    url_tier1 = build_usgs_query_url(TIER_1_CONFIG, start_time=start_time, end_time=end_time)
    logger.info("Fetching Tier 1 (Local NCR): %s", url_tier1)
    raw_tier1 = fetch_usgs_data(url_tier1)
    events_tier1 = extract_event_fields(raw_tier1)
    logger.info("Tier 1 retrieved: %d events", len(events_tier1))

    # 2. Fetch Tier 2
    url_tier2 = build_usgs_query_url(TIER_2_CONFIG, start_time=start_time, end_time=end_time)
    logger.info("Fetching Tier 2 (Himalayan Regional): %s", url_tier2)
    raw_tier2 = fetch_usgs_data(url_tier2)
    events_tier2 = extract_event_fields(raw_tier2)
    logger.info("Tier 2 retrieved: %d events", len(events_tier2))

    # 3. Save combined raw payloads (preserving sample files)
    combined_raw_payload = {
        "metadata": {
            "source": "USGS ComCat FDSN Web Service",
            "start_time": start_time,
            "end_time": end_time,
            "tier1_config": TIER_1_CONFIG,
            "tier2_config": TIER_2_CONFIG,
            "queried_at": datetime.now(timezone.utc).isoformat(),
        },
        "tier1_raw": raw_tier1,
        "tier2_raw": raw_tier2,
    }
    save_json_file(combined_raw_payload, raw_output_path, "Two-Tier Raw USGS payloads")

    # 4. Merge & Deduplicate
    merged_events = merge_and_deduplicate(events_tier1, events_tier2)
    logger.info("Total unique consolidated events: %d", len(merged_events))

    # 5. Save consolidated parsed events (preserving sample files)
    save_json_file(merged_events, parsed_output_path, "Consolidated Two-Tier historical events")

    return {
        "start_time": start_time,
        "end_time": end_time,
        "tier1_count": len(events_tier1),
        "tier2_count": len(events_tier2),
        "total_unique_count": len(merged_events),
        "raw_file": str(raw_output_path),
        "parsed_file": str(parsed_output_path),
    }


if __name__ == "__main__":
    print("Executing Two-Tier USGS Historical Earthquake Acquisition...")
    summary = run_two_tier_acquisition()
    print("\nAcquisition Summary:")
    print(f"  Tier 1 Events (Local NCR): {summary['tier1_count']}")
    print(f"  Tier 2 Events (Regional Himalayan): {summary['tier2_count']}")
    print(f"  Total Unique Events: {summary['total_unique_count']}")
    print(f"  Raw JSON: {summary['raw_file']}")
    print(f"  Parsed JSON: {summary['parsed_file']}")

