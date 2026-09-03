"""
Pydantic schemas for request validation and response models.
"""

from typing import Optional, List
from pydantic import BaseModel


class HazardPredictionRequest(BaseModel):
    hazard_type: str
    latitude: float
    longitude: float
    parameters: dict


class EvacuationRequest(BaseModel):
    origin_latitude: float
    origin_longitude: float
    preferred_shelter_id: Optional[str] = None
