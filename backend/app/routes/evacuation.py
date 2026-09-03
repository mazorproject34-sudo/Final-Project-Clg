from fastapi import APIRouter

router = APIRouter(prefix="/evacuation", tags=["Evacuation"])


@router.post("/route")
def calculate_route():
    """Placeholder for evacuation route calculation endpoint."""
    return {"message": "Evacuation route calculation placeholder"}
