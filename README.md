# Rakshak AI — Emergency Response Platform

Rakshak AI is being built as a real-time emergency incident intake and coordination platform: public reports can carry GPS, timestamps, evidence and live updates into an operator command center.

## What is real now

- FastAPI backend with persistent SQLite incident database
- REST API for incident creation, listing, detail and status updates
- Evidence upload with type/size validation and SHA-256 hash
- GPS location telemetry stored against incidents
- WebSocket real-time event stream for the command center
- Browser camera + high-accuracy geolocation integration
- Docker deployment for the API
- Frontend automatically uses the API when available and keeps a demo fallback when it is offline

## Run the backend

### Docker

```bash
docker compose up --build
```

API: `http://localhost:8000`
Health check: `http://localhost:8000/api/health`

### Python

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Then serve the repository root from a local web server and open the site. Camera/GPS permissions work best on `localhost` or HTTPS.

## API surface

- `POST /api/incidents` — create a report
- `GET /api/incidents` — priority queue data
- `GET /api/incidents/{id}` — incident + audit events
- `PATCH /api/incidents/{id}/status` — operator workflow status
- `POST /api/incidents/{id}/evidence` — evidence upload + hash
- `POST /api/incidents/{id}/location` — live location point
- `WS /ws` — real-time incident/location events

## Next production layer

Replace the local SQLite store with PostgreSQL/PostGIS, add JWT/MFA + RBAC, object storage, Redis/pub-sub, WebRTC signaling + TURN for remote live video, AI-assisted multimodal classification with human review, responder location telemetry, observability, rate limiting and formal emergency-service adapters.

## Safety / deployment boundary

This software does **not** autonomously contact or dispatch real police, ambulance or fire services. Any real emergency-service integration must use authorized agency APIs/workflows and appropriate legal, privacy, security and operational approvals. AI output must remain advisory unless formally validated and authorized.
