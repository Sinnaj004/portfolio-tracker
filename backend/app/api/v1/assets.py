from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.services.asset_service import asset_service
from app.models.models import User
from app.api.deps import get_current_admin_user
from fastapi import BackgroundTasks

router = APIRouter()


@router.post("/refresh-prices", status_code=status.HTTP_200_OK)
def refresh_all_prices(
        background_tasks: BackgroundTasks,
        db: Session = Depends(get_db),
        current_admin: User = Depends(get_current_admin_user)
):
    # Die Funktion wird "gequeued" und sofort 202 zurückgegeben
    background_tasks.add_task(asset_service.update_all_assets_prices, db)

    return {"message": "Globales Update wurde im Hintergrund gestartet."}