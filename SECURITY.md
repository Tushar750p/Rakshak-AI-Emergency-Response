# Security baseline

Rakshak AI handles potentially sensitive emergency reports. This repository is a prototype and is not approved for real emergency dispatch.

## Required before production
- TLS everywhere and encrypted storage
- Strong authentication with MFA for operators/responders
- RBAC and least privilege
- Server-side validation of every report and upload
- Malware scanning and content-type/size limits for media
- Rate limiting, abuse prevention and duplicate-report controls
- Audit logging for evidence access and dispatch actions
- Secrets stored outside source control
- Short-lived signed media URLs
- Data retention/deletion policy appropriate to jurisdiction
- Privacy notice and explicit location/camera consent
- Security review, penetration testing and incident-response plan
- Legal/government authorization before integrating with emergency services

Never place API keys, service credentials, emergency-dispatch credentials, or private certificates in this repository.
