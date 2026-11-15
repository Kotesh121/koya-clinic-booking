import os
import tempfile
from datetime import datetime, timedelta, timezone

_tmp = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/test.db"
os.environ["API_KEY"] = "test-key"
os.environ["SEED_DEMO_SLOTS"] = "false"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

H = {"X-API-Key": "test-key"}


def iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


@pytest.fixture()
def client():
    with TestClient(app) as c:
        now = datetime.now(timezone.utc)
        slots = [
            {"id": "s1", "provider": "Dr Ade", "start": iso(now + timedelta(days=2)), "end": iso(now + timedelta(days=2, minutes=30))},
            {"id": "s2", "provider": "Dr Ade", "start": iso(now + timedelta(days=1)), "end": iso(now + timedelta(days=1, minutes=30))},
            {"id": "s3", "provider": "Dr Okafor", "start": iso(now + timedelta(days=3)), "end": iso(now + timedelta(days=3, minutes=30))},
            {"id": "past", "provider": "Dr Ade", "start": iso(now - timedelta(days=1)), "end": iso(now - timedelta(days=1) + timedelta(minutes=30))},
        ]
        r = c.post("/reset", json={"slots": slots}, headers=H)
        assert r.status_code == 200
        yield c
