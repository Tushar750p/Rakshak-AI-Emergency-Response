from __future__ import annotations

from typing import Any


def assess_incident(incident: dict[str, Any]) -> dict[str, Any]:
    """Deterministic AI-assistance placeholder.

    This service assists operators; it never dispatches emergency services.
    A future ML model can replace the rule layer without changing the API.
    """
    t = str(incident.get("type", "Other")).lower()
    text = str(incident.get("description", "")).lower()
    women = bool(incident.get("women_safety"))
    signals = []
    if women or "assault" in text or "attack" in text:
        signals.append("personal-safety risk")
    if "fire" in t or "smoke" in text:
        signals.append("fire/smoke")
    if "medical" in t or "unconscious" in text or "bleeding" in text:
        signals.append("medical risk")
    if "accident" in t or "crash" in text:
        signals.append("road collision")
    priority = "CRITICAL" if women or t in {"violence", "fire"} else "HIGH" if t in {"accident", "medical emergency"} else "MEDIUM"
    confidence = 0.90 if women else 0.80 if signals else 0.55
    return {
        "priority_suggestion": priority,
        "confidence": confidence,
        "signals": signals,
        "human_review_required": True,
        "dispatch_authority": "authorized_operator_only",
    }
