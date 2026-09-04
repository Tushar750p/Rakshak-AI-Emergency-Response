# Rakshak AI — Advanced Emergency Modules

## Women Safety
- Dedicated Women Safety SOS endpoint: `POST /api/women-safety/sos`
- Critical priority by default
- Silent SOS flag
- Optional trusted-contact list
- GPS coordinates and accuracy
- Operator-controlled dispatch boundary

## Nearby Emergency Resources
Resources can be registered with `POST /api/resources` using types such as:
- `police_station`
- `hospital`
- `ambulance_base`
- `fire_station`
- `disaster_center`

Use `GET /api/resources/nearby?lat=...&lon=...` or `GET /api/incidents/{id}/resources` for incident-specific matching and distance ranking.

The system identifies nearby resources; it does not falsely claim that a real emergency-service station has been alerted. Actual alerting requires authorized agency integrations.

## Responders
- Register responders with `POST /api/responders`
- List responders with `GET /api/responders`
- Assign a responder with `POST /api/incidents/{incident_id}/assign/{responder_id}`
- Push responder GPS with `POST /api/responders/{responder_id}/location`
- Real-time updates use the existing WebSocket hub

## Warning / Early Warning
- `POST /api/warnings` is an integration-ready ingestion endpoint for authorized warning feeds/operators.
- `GET /api/warnings/active?lat=...&lon=...` returns active warnings relevant to a location.
- Warnings support severity, event type, radius, issue/expiry times and source attribution.
- Earthquake prediction is **not** claimed. Rakshak is designed to consume official early-warning information.

## Offline Boundary
The public PWA already stores emergency submissions locally and retries when connectivity returns. A completely disconnected device cannot remotely alert a distant service without a communication path. Future native/edge integrations can use SMS, Bluetooth/mesh, LoRa or radio gateways where available.

## Production Security Still Required
The current prototype endpoints are integration-ready but are not a substitute for production authentication. Before agency deployment, add JWT/session authentication, RBAC, MFA, encrypted media/object storage, Postgres/PostGIS, rate limiting, signed evidence URLs, retention controls and a formal audit/security review.
