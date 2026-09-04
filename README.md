# Rakshak AI — Emergency Response Platform

Rakshak AI is a safety-focused emergency incident intake, coordination and response platform designed for **daily real-world use** by the public, responders and authorized command-center operators.

The platform is designed around one principle: **capture an emergency quickly, preserve useful evidence and location context, coordinate authorized responders, and keep working through unreliable connectivity without allowing AI to make high-impact dispatch decisions on its own.**

> **Important:** Rakshak AI is an emergency-response software platform, not a replacement for official emergency services. Real police, ambulance or fire dispatch requires authorized agency integrations and operational approval.

## Platform capabilities

### Public emergency reporting

- Accident reporting
- Violence / fight reporting
- Fire reporting
- Medical emergency reporting
- Road blockage reporting
- Other incident reporting
- GPS coordinates and timestamps
- Description and incident context
- Browser camera access
- Photo/video evidence capture and upload
- Live-location telemetry when available
- Offline queueing when the network/API is unavailable

### Command Center

- Live incident queue
- Priority-based incident view
- Map-based incident visualization with Leaflet/OpenStreetMap
- Incident detail and audit events
- Acknowledge → dispatch → resolve workflow
- Evidence access
- Real-time WebSocket events
- Polling fallback for connectivity resilience

### Responder operations

- Responder dashboard
- Active incident queue
- Incident claiming workflow
- Arrived / resolved status updates
- Responder GPS telemetry
- Backend responder registration
- Responder-to-incident assignment contract
- Responder availability state tracking

### Women Safety

- Dedicated Women Safety interface
- SOS workflow
- Silent SOS option
- GPS capture
- Trusted-contact data field
- Critical-priority safety event handling
- Command-center broadcast event

### Nearby emergency resources

Rakshak can maintain and query nearby resources such as:

- Police resources
- Hospitals
- Fire resources
- Ambulance resources
- Other registered response resources

The backend includes distance-based nearby-resource discovery and incident-specific resource lookup.

### Public safety dashboard

The public dashboard provides privacy-conscious aggregate information such as:

- Total reports
- Active incidents
- Critical active incidents
- Incident-type distribution
- Public incident status updates
- Last refresh time

Reporter identity, private descriptions, private evidence and responder details are intentionally excluded from the public view.

## AI-assisted safety architecture

Rakshak includes an **AI-assistance contract** for operator support.

The AI layer can evaluate incident information and return:

- Suggested priority
- Confidence
- Explainable signals
- Human-review requirement
- Dispatch-authority boundary

### AI safety rule

**AI does not autonomously dispatch police, ambulance or fire services.** AI output is advisory and must remain under an authorized human/operator workflow unless a formally approved agency integration explicitly defines otherwise.

This prevents a model error from directly creating a high-impact emergency dispatch.

## Connectivity and offline architecture

Rakshak is designed for environments where connectivity may be unreliable.

Current resilience features include:

- Browser-side offline incident queue using IndexedDB
- Automatic retry when connectivity returns
- Local incident preservation when the API cannot be reached
- PWA/service-worker foundation
- WebSocket + polling fallback for command-center updates
- Relay gateway contracts for future physical communication paths

The production architecture also defines adapters for:

- Bluetooth
- Mesh networking
- LoRa
- Radio / other relay systems

### Offline limitation

A device with **zero available communication path cannot transmit an alert to a remote command center**. Rakshak can preserve the incident locally and forward it when an available network or relay path returns. Browser APIs alone cannot guarantee direct LoRa/radio transmission without compatible hardware and an authorized gateway.

## Live camera and future live video

The public web app supports browser camera access and evidence capture/upload.

For true remote real-time live video, the production architecture is intended to use:

- WebRTC
- Authenticated signaling
- Short-lived session authorization
- TURN for difficult NAT/network environments
- Explicit user consent
- Session/audit controls
- Secure media transport

A normal file upload is **not** treated as a real-time video call.

## Security architecture

Rakshak follows a defense-in-depth approach rather than claiming that any system is impossible to hack.

Current security-oriented controls/contracts include:

- Role-based access-control model
- Public / responder / dispatcher / supervisor / admin role separation
- MFA primitive and authentication-service contract
- Fail-closed notification adapters
- Fail-closed agency-dispatch adapter
- Evidence MIME/type validation
- 25 MB evidence limit
- SHA-256 evidence integrity hash
- Incident audit events
- Controlled responder assignment model
- Privacy-conscious public dashboard
- Explicit human approval boundary for emergency dispatch
- Production readiness checks

### Recommended production security controls

Before real emergency deployment, the platform should additionally use:

- HTTPS/TLS everywhere
- Short-lived access/session tokens
- Fully implemented JWT/OIDC authentication
- TOTP/WebAuthn MFA for privileged operators
- Strict RBAC and least privilege
- Rate limiting and abuse protection
- CSRF/origin controls where applicable
- Secure HTTP headers
- Encrypted database and object storage
- KMS-managed encryption keys
- Malware/antivirus scanning for uploaded evidence
- Signed, expiring evidence URLs
- Data-retention and deletion policies
- Secrets stored only in deployment secret managers
- Centralized audit logging
- Security monitoring and alerting
- Regular dependency and vulnerability scanning
- Backup and disaster-recovery procedures
- Penetration testing before operational deployment

## Emergency-service integration boundary

Rakshak contains a production adapter contract for authorized agency integrations, but it does **not** pretend that a real government emergency API is connected when it is not.

Actual integration requires:

1. An authorized agency or service provider.
2. Documented API/protocol access.
3. Authentication and credential management.
4. Legal/privacy/security approval.
5. Operational testing and incident-response procedures.
6. Failover and acknowledgement handling.

Until those requirements are met, the agency gateway remains fail-closed.

## Official warning feeds

The architecture provides a warning-feed registry for sources such as:

- IMD
- NDMA
- National Centre for Seismology (NCS)

The current code provides the integration contract/registry rather than claiming a live official feed is already connected.

Rakshak **does not predict earthquakes**. It can consume and display authorized official warnings when an approved feed is integrated.

## Route and hazard intelligence

The route-engine contract supports hazard-aware route ranking so responders can consider known risk information.

It does **not** make an absolute "safe route" guarantee. Final route decisions remain subject to live conditions, authorized responders and local operational judgement.

## Backend architecture

```text
Public Web/PWA
     |
     | HTTPS / WebSocket
     v
FastAPI API
     |
     +---- Incident & Location Services
     |
     +---- Evidence Service
     |
     +---- Command Center Events
     |
     +---- Responder / Resource Services
     |
     +---- Women Safety SOS
     |
     +---- AI Operator Assistance
     |
     +---- Warning Feed Registry
     |
     +---- Route/Hazard Contract
     |
     +---- Notification / Relay / Agency Adapters
     |
     +---- Production Security Contracts
     |
     v
Current: SQLite
Production target: PostgreSQL + PostGIS + object storage + Redis/pub/sub
```

## Main project files

| File | Purpose |
|---|---|
| `index.html` | Public emergency reporting interface |
| `app.js` | GPS, camera, reporting, WebSocket and offline queue logic |
| `styles.css` | Main responsive UI styling |
| `command-center.html` | Authorized command-center dashboard |
| `responder.html` | Responder operations dashboard |
| `public-dashboard.html` | Privacy-conscious public safety dashboard |
| `women-safety.html` | Women Safety SOS interface |
| `sw.js` | PWA/service-worker foundation |
| `manifest.webmanifest` | Installable web-app metadata |
| `backend/app/main.py` | Core FastAPI incident API and event system |
| `backend/app/advanced.py` | Women SOS, resources, responders, warnings and assignment APIs |
| `backend/app/ai_assist.py` | Deterministic operator-assistance assessment layer |
| `backend/app/production.py` | RBAC, MFA, notification, relay, agency, storage and encryption contracts |
| `backend/app/production_routes.py` | Production readiness and AI-assessment API routes |
| `backend/app/route_engine.py` | Hazard-aware route-ranking contract |
| `backend/app/entrypoint.py` | Production FastAPI entrypoint and schema initialization |
| `backend/tests/test_production.py` | Production architecture tests |
| `.github/workflows/ci.yml` | Automated Python test workflow |
| `render.yaml` | Render deployment configuration |

## API surface

### Core APIs

- `GET /api/health` — health check
- `POST /api/incidents` — create incident
- `GET /api/incidents` — incident queue
- `GET /api/incidents/{id}` — incident details and events
- `PATCH /api/incidents/{id}/status` — update workflow status
- `POST /api/incidents/{id}/evidence` — upload evidence
- `POST /api/incidents/{id}/location` — add location telemetry
- `WS /ws` — real-time event stream

### Advanced safety APIs

- `POST /api/women-safety/sos`
- `GET /api/resources/nearby`
- `GET /api/incidents/{id}/resources`
- `POST /api/resources`
- `GET /api/responders`
- `POST /api/responders`
- `POST /api/incidents/{id}/assign/{responder_id}`
- `POST /api/responders/{responder_id}/location`
- `POST /api/warnings`
- `GET /api/warnings/active`

### Production APIs

- `POST /api/production/ai/assess` — operator assistance only
- `GET /api/production/readiness` — production integration readiness status

## Local development

### Docker

```bash
docker compose up --build
```

API:

```text
http://localhost:8000
```

Health check:

```text
http://localhost:8000/api/health
```

### Python

```bash
cd backend
python -m venv .venv
```

Windows:

```bash
.venv\\Scripts\\activate
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run:

```bash
uvicorn app.entrypoint:app --reload --port 8000
```

Then serve the repository root from a local web server and open the site. Camera/GPS permissions work best on `localhost` or HTTPS.

## Testing

The repository includes automated tests for key production architecture contracts:

- RBAC permissions
- MFA primitive
- Fail-closed SMS/WhatsApp adapters
- Fail-closed agency dispatch
- Hazard-aware route penalty
- KMS configuration readiness

GitHub Actions runs the Python test suite on pushes and pull requests to `main`.

## Deployment

### Render

`render.yaml` defines the FastAPI web service, Python runtime, build command and production entrypoint.

The production entrypoint initializes the base database schema before importing advanced routes so schema-extension startup order is safe.

### GitHub Pages

The repository also contains a static frontend deployment workflow for GitHub Pages.

If GitHub Pages is not enabled/configured for GitHub Actions at the repository/account level, the Pages workflow can fail during the Pages configuration step even when the application code itself is valid. Enable Pages with **GitHub Actions** as the build/deployment source before relying on that workflow.

## Production roadmap

### Implemented foundation

- Public emergency intake
- GPS and location telemetry
- Camera/evidence capture
- Offline queue
- Command Center
- Responder dashboard
- Public safety dashboard
- Women Safety SOS
- Nearby-resource engine
- Responder registration/assignment contracts
- AI operator-assistance endpoint
- RBAC/MFA/security contracts
- Notification/relay/agency adapter contracts
- Warning-feed registry
- Hazard-aware route contract
- Automated CI tests

### Next production integrations

- PostgreSQL + PostGIS
- Redis/pub-sub for horizontally scalable real-time events
- S3-compatible object storage
- KMS-backed encryption
- Full OIDC/JWT/TOTP/WebAuthn authentication
- WebRTC live video + authenticated signaling + TURN
- SMS provider integration
- WhatsApp provider integration
- Authorized police/ambulance/fire dispatch integrations
- Live IMD/NDMA/NCS warning feeds
- Hardware-backed Bluetooth/mesh/LoRa/radio gateways
- Push notifications
- Malware scanning for evidence
- Central observability and SIEM integration
- Disaster recovery and multi-region resilience
- Independent security and penetration testing

## Operational principles

1. **Human-in-the-loop:** AI assists; authorized humans control high-impact emergency actions.
2. **Fail closed:** Missing credentials or unapproved integrations must not silently send real emergency traffic.
3. **Privacy by design:** Public views expose only information appropriate for public visibility.
4. **Evidence integrity:** Uploaded evidence is validated and hashed.
5. **Connectivity resilience:** Preserve emergency information locally and retry when communication returns.
6. **No false guarantees:** The platform does not claim impossible security, perfect routing, earthquake prediction or guaranteed emergency delivery.
7. **Auditable actions:** Important incident state changes are recorded as events.
8. **Least privilege:** Production roles and integrations should receive only the permissions they need.

## Security and safety disclaimer

Rakshak AI is intended to support emergency-response operations. It must not be represented as an officially connected emergency service unless the relevant agency has formally authorized and integrated it.

No software can honestly promise to be impossible to hack. Rakshak instead aims for layered security, least privilege, strong authentication, encryption, validation, auditability, monitoring and fail-closed integrations.

For emergencies, users should continue to use the appropriate official emergency channels available in their region.

## Repository

urlRakshak AI Repositoryhttps://github.com/Tushar750p/Rakshak-AI-Emergency-Response
