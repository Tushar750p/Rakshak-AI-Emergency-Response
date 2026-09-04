import os
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from .ai_assist import assess_incident
from .production import (
    NotificationGateway,
    RelayGateway,
    WarningFeedRegistry,
    ObjectStorageContract,
    EncryptionContract,
)
from .route_engine import provider_contract

router = APIRouter(prefix="/api/production", tags=["production"])


class AIAssessmentIn(BaseModel):
    type: str = Field(min_length=1, max_length=80)
    description: str = Field(default="", max_length=2000)
    women_safety: bool = False
    latitude: float | None = None
    longitude: float | None = None


@router.post("/ai/assess")
def ai_assess(payload: AIAssessmentIn):
    """Return operator assistance only; never dispatches emergency services."""
    return assess_incident(payload.model_dump())


@router.get("/readiness")
def readiness():
    storage = ObjectStorageContract()
    return {
        "auth_rbac": True,
        "mfa_primitive": True,
        "ai_assistance": True,
        "official_warning_registry": WarningFeedRegistry().sources(),
        "sms": NotificationGateway().sms_provider != "not_configured",
        "whatsapp": NotificationGateway().whatsapp_provider != "not_configured",
        "physical_relays": sorted(RelayGateway.SUPPORTED),
        "postgres_postgis": False,
        "object_storage": storage.ready(),
        "kms": EncryptionContract.key_configured(),
        "safe_route_contract": provider_contract(),
        "agency_dispatch": os.getenv("RAKSHAK_AGENCY_INTEGRATION", "not_configured") != "not_configured",
        "live_dispatch_allowed": False,
    }
