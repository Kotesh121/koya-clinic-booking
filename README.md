# Koya Clinic Booking

FastAPI + SQLAlchemy booking API, with a React (Vite + TypeScript) web page that FastAPI serves after it is built.

| Level | How it's done |
|---|---|
| 1 | `/reset`, `/slots`, `POST /bookings`, `GET /bookings/{id}` |
| 2 | `core/security.py` API key check; validation, trimming and lower-cased email in `services/booking_service.py` |
| 3 | Partial unique index (one confirmed booking per slot) enforced by the DB; `DELETE /bookings/{id}` |
| 4 | `idempotency_keys` table (key + body hash + stored response); cursor pagination on `GET /bookings` |
| 5 | `attempts` table, 5 per email per 60s, `Retry-After` on 429 (`core/rate_limit.py`) |

## Run locally

Backend (terminal 1):
```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # Windows: copy .env.example .env  -> then set API_KEY
uvicorn app.main:app --reload
```

Frontend, dev mode with hot reload (terminal 2):
```bash
cd frontend
cp .env.example .env               # set VITE_API_KEY to the same value as API_KEY
npm install
npm run dev                        # http://localhost:5173 (proxies API calls to :8000)
```

Or build the React app and let FastAPI serve it at http://127.0.0.1:8000:
```bash
cd frontend && npm install && npm run build
```

Swagger is at `/docs`. Locally the API uses SQLite; set `DATABASE_URL` to your Neon string for Postgres.

## Tests

```bash
pip install pytest httpx
pytest
```

## Deploy (Render + Neon)

1. Push to a public GitHub repo.
2. Render -> New Web Service -> pick the repo.
   - Build command: `pip install -r requirements.txt && cd frontend && npm install && npm run build`
   - Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Env vars: `DATABASE_URL` (Neon string), `API_KEY`, and `VITE_API_KEY` (same value as `API_KEY`; needed at build time)
3. Base URL and web page URL are both your Render URL.
