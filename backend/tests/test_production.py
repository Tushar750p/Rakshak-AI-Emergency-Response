from backend.app.production import AuthService, EncryptionContract, NotificationGateway, AgencyDispatchGateway
from backend.app.route_engine import rank_routes

def test_rbac():
    assert AuthService.authorize("DISPATCHER", "responder:assign")
    assert not AuthService.authorize("PUBLIC", "responder:assign")

def test_mfa_secret():
    assert len(AuthService.new_mfa_secret()) >= 32

def test_notification_fails_closed():
    assert not NotificationGateway().send_sms("+910000000000", "test").accepted

def test_agency_dispatch_fails_closed():
    assert not AgencyDispatchGateway().dispatch("police", "RK-1", "police").accepted

def test_route_hazard_penalty():
    routes=[{"id":"a","duration_minutes":10,"latitude":20,"longitude":73}]
    hazards=[{"latitude":20,"longitude":73,"radius_km":5,"type":"fire"}]
    assert rank_routes(routes,hazards)[0]["hazard_penalty"] > 0

def test_encryption_key_is_not_assumed():
    assert isinstance(EncryptionContract.key_configured(), bool)
