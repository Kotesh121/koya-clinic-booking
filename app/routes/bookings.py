from typing import Any

from fastapi import APIRouter, Body, Depends, Header, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.security import require_api_key
from app.database import get_db
from app.schemas.booking import booking_out
from app.services import booking_service as svc

router = APIRouter(dependencies=[Depends(require_api_key)])


@router.post("/bookings")
def create_booking(
    payload: Any = Body(default=None),
    idempotency_key: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    status, body, headers = svc.create_booking(db, payload, idempotency_key)
    db.commit()
    return JSONResponse(body, status_code=status, headers=headers)


@router.get("/bookings")
def list_bookings(
    email: str | None = Query(default=None),
    limit: str | None = Query(default=None),
    cursor: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return svc.list_bookings(db, email, limit, cursor)


@router.get("/bookings/{booking_id}")
def get_booking(booking_id: str, db: Session = Depends(get_db)):
    return booking_out(svc.get_booking(db, booking_id))


@router.delete("/bookings/{booking_id}")
def cancel_booking(booking_id: str, db: Session = Depends(get_db)):
    return svc.cancel_booking(db, booking_id)
