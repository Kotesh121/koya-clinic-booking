from concurrent.futures import ThreadPoolExecutor

from tests.conftest import H


def book(client, slot="s1", email="ada@example.com", name="Ada Obi", headers=None):
    return client.post("/bookings", json={"slot_id": slot, "name": name, "email": email}, headers={**H, **(headers or {})})


# ---- Level 1 / 2
def test_auth_required(client):
    assert client.get("/slots").status_code == 401
    assert client.get("/slots", headers={"X-API-Key": "nope"}).json() == {"error": "missing or invalid API key"}
    assert client.post("/bookings", json={}).status_code == 401


def test_slots_sorted_and_filtered(client):
    s = client.get("/slots", headers=H).json()["slots"]
    assert [x["id"] for x in s] == ["past", "s2", "s1", "s3"]
    assert all(x["available"] for x in s)
    only = client.get("/slots?provider=Dr Okafor", headers=H).json()["slots"]
    assert [x["id"] for x in only] == ["s3"]


def test_book_and_get(client):
    r = book(client, name="  Ada Obi ", email="  ADA@Example.com ")
    assert r.status_code == 201
    b = r.json()
    assert b["status"] == "confirmed" and b["email"] == "ada@example.com" and b["name"] == "Ada Obi"
    got = client.get(f"/bookings/{b['id']}", headers=H)
    assert got.status_code == 200 and got.json() == b
    assert client.get("/bookings/nope", headers=H).status_code == 404
    slots = {x["id"]: x["available"] for x in client.get("/slots", headers=H).json()["slots"]}
    assert slots["s1"] is False and slots["s2"] is True


def test_validation(client):
    for body in [{}, {"slot_id": "s1", "name": "A"}, {"slot_id": "s1", "name": " ", "email": "a@b.co"},
                 {"slot_id": "s1", "name": "A", "email": "not-an-email"}, {"slot_id": 5, "name": "A", "email": "a@b.co"}]:
        r = client.post("/bookings", json=body, headers=H)
        assert r.status_code == 400 and "error" in r.json(), body
    assert client.post("/bookings", content=b"{bad", headers={**H, "Content-Type": "application/json"}).status_code == 400
    assert book(client, slot="missing").status_code == 404
    assert book(client, slot="past").status_code == 400


# ---- Level 3
def test_double_booking_and_cancel(client):
    first = book(client)
    assert first.status_code == 201
    assert book(client, email="bob@example.com").status_code == 409
    bid = first.json()["id"]
    c = client.delete(f"/bookings/{bid}", headers=H)
    assert c.status_code == 200 and c.json()["status"] == "cancelled"
    assert client.delete(f"/bookings/{bid}", headers=H).status_code == 409
    assert client.delete("/bookings/nope", headers=H).status_code == 404
    assert book(client, email="bob@example.com").status_code == 201  # slot freed


def test_concurrent_same_slot(client):
    def go(i):
        return book(client, email=f"user{i}@example.com").status_code

    with ThreadPoolExecutor(max_workers=12) as ex:
        codes = list(ex.map(go, range(12)))
    assert codes.count(201) == 1
    assert codes.count(409) == 11


# ---- Level 4
def test_idempotency(client):
    h = {"Idempotency-Key": "k1"}
    a = book(client, headers=h)
    b = book(client, headers=h)
    assert a.status_code == 201 and b.status_code == 201 and a.json()["id"] == b.json()["id"]
    assert book(client, name="Someone Else", headers=h).status_code == 422
    # replaying a conflict returns the same conflict
    h2 = {"Idempotency-Key": "k2"}
    assert book(client, email="bob@example.com", headers=h2).status_code == 409
    assert book(client, email="bob@example.com", headers=h2).status_code == 409
    # only one confirmed booking exists
    assert len(client.get("/bookings?email=ada@example.com", headers=H).json()["bookings"]) == 1


def test_idempotency_concurrent(client):
    def go(_):
        return book(client, headers={"Idempotency-Key": "same"})

    with ThreadPoolExecutor(max_workers=8) as ex:
        rs = list(ex.map(go, range(8)))
    assert {r.status_code for r in rs} == {201}
    assert len({r.json()["id"] for r in rs}) == 1


def test_pagination(client):
    for s in ("s1", "s2", "s3"):
        assert book(client, slot=s).status_code == 201
    r = client.get("/bookings?email=ADA@example.com&limit=2", headers=H).json()
    assert [b["slot_id"] for b in r["bookings"]] == ["s1", "s2"] and r["next_cursor"]
    r2 = client.get(f"/bookings?email=ada@example.com&limit=2&cursor={r['next_cursor']}", headers=H).json()
    assert [b["slot_id"] for b in r2["bookings"]] == ["s3"] and r2["next_cursor"] is None
    for bad in ("0", "51", "abc"):
        assert client.get(f"/bookings?email=ada@example.com&limit={bad}", headers=H).status_code == 400
    assert client.get("/bookings", headers=H).status_code == 400


# ---- Level 5
def test_rate_limit(client):
    codes = [book(client, slot="missing", email="spam@example.com").status_code for _ in range(5)]
    assert codes == [404] * 5
    r = book(client, slot="missing", email="spam@example.com")
    assert r.status_code == 429
    assert 1 <= int(r.headers["Retry-After"]) <= 60
    assert book(client, email="other@example.com").status_code == 201
