"""Level 5: max N booking attempts per email per window, stored in the DB so it
survives restarts and works across workers."""
import math
import time

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.booking import Attempt


def check_and_record(db: Session, email: str) -> int | None:
    """Return None and record the attempt if allowed, else seconds to wait."""
    if db.get_bind().dialect.name == "postgresql":
        # serialise concurrent attempts for the same email
        db.execute(text("SELECT pg_advisory_xact_lock(hashtext(:e))"), {"e": email})

    limit = settings.rate_limit_attempts
    window = settings.rate_limit_window_seconds
    now = time.time()
    times = db.scalars(
        select(Attempt.ts)
        .where(Attempt.email == email, Attempt.ts > now - window)
        .order_by(Attempt.ts)
    ).all()

    if len(times) >= limit:
        frees_at = times[len(times) - limit] + window
        return max(1, math.ceil(frees_at - now))

    db.add(Attempt(email=email, ts=now))
    db.flush()
    return None
