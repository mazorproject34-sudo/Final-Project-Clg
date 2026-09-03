from fastapi import APIRouter

router = APIRouter(prefix="/shelters", tags=["Shelters"])


@router.get("/")
def list_shelters():
    """Placeholder for shelter locations and capacities endpoint."""
    return {"shelters": []}
