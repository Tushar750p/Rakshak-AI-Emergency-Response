"""Production integration contracts for Rakshak AI.

Adapters are intentionally provider-neutral. They fail closed until credentials,
agency authorization and real gateway implementations are configured.
"""
from __future__ import annotations
import hashlib, os, secrets, time
from dataclasses import dataclass
from typing import Any

ROLES = {"PUBLIC", "RESPONDER", "DISPATCHER", "SUPERVISOR", "ADMIN"}
PERMISSIONS = {
    "PUBLIC": {"incident:create", "safety:sos"},
    "RESPONDER": {"incident:read", "incident:update", "location:write"},
    "DISPATCHER": {"incident:read", "incident:update", "responder:assign", "warning:publish"},
    "SUPERVISOR": {"incident:read", "incident:update", "responder:assign", "warning:publish", "audit:read"},
    "ADMIN": {"*"},
}

@dataclass
class ProviderResult:
    accepted: bool
    provider: str
    status: str
    detail: str

class AuthService:
    """JWT-ready session primitives plus TOTP-compatible MFA secret generation."""
    @staticmethod
    def new_session_token() -> str:
        return secrets.token_urlsafe(32)
    @staticmethod
    def new_mfa_secret() -> str:
        return secrets.token_hex(20)
    @staticmethod
    def authorize(role: str, permission: str) -> bool:
        return role in ROLES and ("*" in PERMISSIONS.get(role, set()) or permission in PERMISSIONS.get(role, set()))

class NotificationGateway:
    def __init__(self):
        self.sms_provider = os.getenv("RAKSHAK_SMS_PROVIDER", "not_configured")
        self.whatsapp_provider = os.getenv("RAKSHAK_WHATSAPP_PROVIDER", "not_configured")
    def send_sms(self, to: str, body: str) -> ProviderResult:
        if self.sms_provider == "not_configured":
            return ProviderResult(False, self.sms_provider, "NOT_CONFIGURED", "Configure an authorized SMS provider before sending.")
        return ProviderResult(False, self.sms_provider, "ADAPTER_REQUIRED", "Provider adapter and credentials are required.")
    def send_whatsapp(self, to: str, body: str) -> ProviderResult:
        if self.whatsapp_provider == "not_configured":
            return ProviderResult(False, self.whatsapp_provider, "NOT_CONFIGURED", "Configure an authorized WhatsApp provider before sending.")
        return ProviderResult(False, self.whatsapp_provider, "ADAPTER_REQUIRED", "Provider adapter and credentials are required.")

class RelayGateway:
    SUPPORTED = {"bluetooth", "mesh", "lora", "radio"}
    def queue(self, relay_type: str, payload: dict[str, Any]) -> ProviderResult:
        if relay_type not in self.SUPPORTED:
            return ProviderResult(False, relay_type, "UNSUPPORTED", "Unknown relay type.")
        digest = hashlib.sha256(repr(sorted(payload.items())).encode()).hexdigest()
        return ProviderResult(True, relay_type, "QUEUED", f"Gateway payload {digest[:16]} queued; physical gateway required.")

class AgencyDispatchGateway:
    """Safety-first contract: no real dispatch occurs without an approved agency adapter."""
    def dispatch(self, agency: str, incident_id: str, resource_type: str) -> ProviderResult:
        configured = os.getenv("RAKSHAK_AGENCY_INTEGRATION", "not_configured")
        if configured == "not_configured":
            return ProviderResult(False, agency, "NOT_CONFIGURED", "Official agency API/authorization is required; no dispatch was attempted.")
        return ProviderResult(False, agency, "ADAPTER_REQUIRED", "Approved agency adapter is required before live dispatch.")

class WarningFeedRegistry:
    """Registry for official warning adapters; ingestion is pull-based and auditable."""
    OFFICIAL = {"IMD", "NDMA", "NCS"}
    def sources(self) -> list[str]:
        return sorted(self.OFFICIAL)

class ObjectStorageContract:
    """S3-compatible storage contract. Local filesystem must not be assumed production storage."""
    def __init__(self):
        self.endpoint = os.getenv("RAKSHAK_OBJECT_STORAGE_ENDPOINT")
    def ready(self) -> bool:
        return bool(self.endpoint and os.getenv("RAKSHAK_OBJECT_STORAGE_BUCKET"))
    def signed_upload_policy(self, object_key: str) -> dict[str, Any]:
        if not self.ready():
            return {"ready": False, "status": "NOT_CONFIGURED"}
        return {"ready": True, "object_key": object_key, "expires_in": 300, "method": "PUT", "server_encryption": "required"}

class EncryptionContract:
    """Application-level envelope-encryption contract; keys must live in KMS/secret manager."""
    @staticmethod
    def digest(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()
    @staticmethod
    def key_configured() -> bool:
        return bool(os.getenv("RAKSHAK_KMS_KEY_ID"))
