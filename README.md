# NovaSphere Dashboard

Real-time AI analytics dashboard built with FastAPI + WebSockets + Tailwind/Alpine/Chart.js.

## Architecture

- **Backend:** FastAPI (async), WebSocket broadcast via ConnectionManager, background data generator.
- **Auth:** JWT (HS256) + bcrypt, cookie-based session.
- **DB:** SQLAlchemy (SQLite dev, Postgres-ready via `DATABASE_URL`).
- **Frontend:** Tailwind CSS + Alpine.js + Chart.js, auto-reconnecting WebSocket.
- **Config:** `.env` via python-dotenv.

## Run

```bash
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --host 0.0.0.0 --port 8080
```

Open http://127.0.0.1:8080

## Docker

```bash
docker build -t novasphere .
docker run -p 8080:8080 novasphere
```

## Tests

```bash
pytest -q
```
EOF