from fastapi import APIRouter

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("/")
def get_active_alerts():
    """Placeholder for active early warning alerts endpoint."""
    return {"alerts": []}
