from typing import Any

from fastapi import APIRouter, Body, Depends, Query
from sqlalchemy.orm import Session

from app.core.security import require_api_key
from app.database import get_db
from app.services import booking_service as svc

router = APIRouter(dependencies=[Depends(require_api_key)])


@router.post("/reset")
def reset(payload: Any = Body(default=None), db: Session = Depends(get_db)):
    return {"ok": True, "slots": svc.replace_slots(db, payload)}


@router.get("/slots")
def slots(provider: str | None = Query(default=None), db: Session = Depends(get_db)):
    return {"slots": svc.list_slots(db, provider)}
