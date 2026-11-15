import hashlib
import json
import time
import uuid
from datetime import datetime, timezone

from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.core.rate_limit import check_and_record
from app.models.booking import Attempt, Booking, IdempotencyKey
from app.models.slot import Slot
from app.schemas.booking import EMAIL_RE, booking_out
from app.schemas.slot import slot_out

Result = tuple[int, dict, dict]  # status, body, headers


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _parse_ts(value: str) -> float:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.timestamp()


# ---------- slots ----------

def replace_slots(db: Session, data) -> int:
    if not isinstance(data, dict) or not isinstance(data.get("slots"), list):
        raise ApiError(400, "body must be {\"slots\": [...]}")
    new_slots = []
    for s in data["slots"]:
        if not isinstance(s, dict):
            raise ApiError(400, "each slot must be an object")
        for f in ("id", "provider", "start", "end"):
            if not isinstance(s.get(f), str) or not s[f].strip():
                raise ApiError(400, f"slot {f} is required")
        try:
            starts_at = _parse_ts(s["start"])
            _parse_ts(s["end"])
        except ValueError:
            raise ApiError(400, "slot start/end must be ISO date-times")
        new_slots.append(
            Slot(id=s["id"], provider=s["provider"], start=s["start"], end=s["end"], starts_at=starts_at)
        )
    if len({s.id for s in new_slots}) != len(new_slots):
        raise ApiError(400, "duplicate slot ids")

    db.execute(delete(Booking))
    db.execute(delete(IdempotencyKey))
    db.execute(delete(Attempt))
    db.execute(delete(Slot))
    db.add_all(new_slots)
    db.commit()
    return len(new_slots)


def list_slots(db: Session, provider: str | None) -> list[dict]:
    booked = set(db.scalars(select(Booking.slot_id).where(Booking.status == "confirmed")))
    q = select(Slot).order_by(Slot.starts_at, Slot.id)
    if provider is not None:
        q = q.where(Slot.provider == provider)
    return [slot_out(s, s.id not in booked) for s in db.scalars(q)]


# ---------- bookings ----------

def _process(db: Session, data) -> Result:
    """One booking attempt: validate (L2), rate limit (L5), book (L3)."""
    if not isinstance(data, dict):
        return 400, {"error": "body must be a JSON object"}, {}

    vals = {}
    for f in ("slot_id", "name", "email"):
        v = data.get(f)
        if not isinstance(v, str) or not v.strip():
            return 400, {"error": f"{f} is required"}, {}
        vals[f] = v.strip()
    email = vals["email"].lower()
    if not EMAIL_RE.match(email):
        return 400, {"error": "email is not valid"}, {}

    retry_after = check_and_record(db, email)
    if retry_after is not None:
        return 429, {"error": "too many booking attempts, try again later"}, {"Retry-After": str(retry_after)}

    slot = db.get(Slot, vals["slot_id"])
    if slot is None:
        return 404, {"error": "slot not found"}, {}
    if slot.starts_at <= time.time():
        return 400, {"error": "slot has already started"}, {}

    taken = db.scalar(
        select(Booking.seq).where(Booking.slot_id == slot.id, Booking.status == "confirmed")
    )
    if taken is not None:
        return 409, {"error": "slot already booked"}, {}

    booking = Booking(
        id=uuid.uuid4().hex,
        slot_id=slot.id,
        name=vals["name"],
        email=email,
        status="confirmed",
        created_at=_now_iso(),
    )
    try:
        with db.begin_nested():  # savepoint: a lost race must not undo the attempt record
            db.add(booking)
    except IntegrityError:
        return 409, {"error": "slot already booked"}, {}
    return 201, booking_out(booking), {}


def create_booking(db: Session, data, idem_key: str | None) -> Result:
    if not idem_key:
        return _process(db, data)

    # Level 4: idempotency
    body_hash = hashlib.sha256(
        json.dumps(data, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()

    row = db.get(IdempotencyKey, idem_key)
    if row is None:
        try:
            with db.begin_nested():
                db.add(IdempotencyKey(key=idem_key, request_hash=body_hash, status_code=0, response="{}"))
        except IntegrityError:  # a parallel request with the same key won
            row = db.get(IdempotencyKey, idem_key)

    if row is not None:
        if row.request_hash != body_hash:
            return 422, {"error": "Idempotency-Key was already used with a different request body"}, {}
        return row.status_code, json.loads(row.response), {}

    status, body, headers = _process(db, data)
    if status == 429:
        db.execute(delete(IdempotencyKey).where(IdempotencyKey.key == idem_key))
    else:
        db.execute(
            update(IdempotencyKey)
            .where(IdempotencyKey.key == idem_key)
            .values(status_code=status, response=json.dumps(body))
        )
    return status, body, headers


def get_booking(db: Session, booking_id: str) -> Booking:
    b = db.scalar(select(Booking).where(Booking.id == booking_id))
    if b is None:
        raise ApiError(404, "booking not found")
    return b


def cancel_booking(db: Session, booking_id: str) -> dict:
    b = get_booking(db, booking_id)
    if b.status == "cancelled":
        raise ApiError(409, "booking already cancelled")
    b.status = "cancelled"
    db.commit()
    return booking_out(b)


def list_bookings(db: Session, email: str | None, limit: str | None, cursor: str | None) -> dict:
    if not email or not email.strip():
        raise ApiError(400, "email is required")
    try:
        lim = 10 if limit is None else int(limit)
    except ValueError:
        raise ApiError(400, "limit must be an integer from 1 to 50")
    if not 1 <= lim <= 50:
        raise ApiError(400, "limit must be an integer from 1 to 50")

    q = select(Booking).where(Booking.email == email.strip().lower()).order_by(Booking.seq).limit(lim + 1)
    if cursor:
        try:
            q = q.where(Booking.seq > int(cursor))
        except ValueError:
            raise ApiError(400, "invalid cursor")
    rows = list(db.scalars(q))
    has_more = len(rows) > lim
    rows = rows[:lim]
    return {
        "bookings": [booking_out(b) for b in rows],
        "next_cursor": str(rows[-1].seq) if has_more else None,
    }
