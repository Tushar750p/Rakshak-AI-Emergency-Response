"""Safe-route engine abstraction.

Returns route candidates only; it never guarantees a route is safe. A production
adapter can connect this contract to an approved routing provider and live closures.
"""
from __future__ import annotations
from math import radians, sin, cos, asin, sqrt
from typing import Any

BLOCKED_TYPES = {"fire", "riot", "violence", "road_blockage"}

def distance_km(a_lat: float, a_lon: float, b_lat: float, b_lon: float) -> float:
    p1, p2 = radians(a_lat), radians(b_lat)
    dp, dl = radians(b_lat-a_lat), radians(b_lon-a_lon)
    x = sin(dp/2)**2 + cos(p1)*cos(p2)*sin(dl/2)**2
    return 6371 * 2 * asin(sqrt(x))

def rank_routes(routes: list[dict[str, Any]], active_hazards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out=[]
    for route in routes:
        penalty=0
        for h in active_hazards:
            if h.get("latitude") is not None and distance_km(route.get("latitude",0),route.get("longitude",0),h["latitude"],h["longitude"]) < float(h.get("radius_km",0)):
                penalty += 100 if str(h.get("type","")).lower() in BLOCKED_TYPES else 25
        item=dict(route); item["hazard_penalty"]=penalty; item["recommended_score"]=float(route.get("duration_minutes",0))+penalty; out.append(item)
    return sorted(out,key=lambda x:x["recommended_score"])

def provider_contract() -> dict[str, Any]:
    return {"required": ["routing_provider", "road_closure_feed", "official_warning_feed"], "mode": "operator_assist", "safe_guarantee": False}
