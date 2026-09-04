# Rakshak AI — Production Architecture

## Mission
Rakshak AI is designed as an emergency incident intake and response-coordination platform. The public client captures evidence and consented location data; a secure backend validates and stores the incident; AI assists classification and prioritization; authorized control-room staff verify and dispatch responders.

## Core flow
Public app → secure API → incident validation → AI assistance → control-room queue → authorized dispatch → responder tracking → resolution/audit.

## Production components
- Web/PWA and native mobile clients
- API gateway + authentication/authorization
- PostgreSQL/PostGIS incident database
- Object storage for evidence
- Redis/pub-sub for real-time updates
- WebSocket/SSE channel for command-center updates
- AI service for image/video classification and confidence scoring
- Notification service for push/SMS/email integrations
- Maps/routing service for geocoding, ETA and responder routing
- Immutable audit/event log
- Monitoring, rate limiting, abuse detection and encrypted secrets

## Safety boundaries
- Prototype never contacts real emergency services.
- AI recommendations must not be treated as authoritative emergency decisions.
- High-impact dispatch should require an authorized control-room workflow unless a formally approved integration defines otherwise.
- Location and media access must be explicit, minimal, revocable and protected by role-based access controls.
- Evidence should retain original bytes, timestamps, source metadata and cryptographic hashes where legally appropriate.

## MVP-to-production roadmap
1. Replace demo incident state with backend persistence.
2. Add authenticated public reporting and operator accounts.
3. Add PostGIS incident map and real-time event stream.
4. Add secure media upload and evidence hashes.
5. Add AI classification with confidence + human review.
6. Add responder entities, assignment and location telemetry.
7. Add push notifications and approved emergency-service adapters.
8. Add security testing, audit controls, retention policies and deployment infrastructure.
