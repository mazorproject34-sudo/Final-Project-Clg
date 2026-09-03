from fastapi import APIRouter

router = APIRouter(prefix="/hazards", tags=["Hazards"])


@router.get("/")
def get_hazard_summary():
    """Placeholder for hazard summary endpoint."""
    return {"message": "Hazard risk assessment placeholder"}
