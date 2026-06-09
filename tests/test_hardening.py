import json

from app import db
from app.config import TestingConfig
from app.models import ScamReport, User
from app.services.certificate import level_for_score
from app.services.chatbot import assistant_reply
from app.services.fraud_detector import analyze_message


PUBLIC_GET_ROUTES = [
    "/",
    "/about",
    "/about-cyber-fraud",
    "/awareness",
    "/scam-checker",
    "/chatbot",
    "/help",
    "/leaderboard",
    "/login",
    "/register",
    "/report-fraud",
    "/manifest.json",
    "/service-worker.js",
]


def register(client, email="citizen@example.com"):
    return client.post(
        "/register",
        data={
            "full_name": "Citizen User",
            "email": email,
            "village": "Rampur",
            "district": "Patna",
            "language": "en",
            "password": "StrongPass@123",
            "confirm_password": "StrongPass@123",
        },
        follow_redirects=True,
    )


def login_admin(client):
    return client.post(
        "/login",
        data={"email": "admin@cybersuraksha.in", "password": "Admin@12345"},
        follow_redirects=True,
    )


def test_public_get_routes_render(client):
    for route in PUBLIC_GET_ROUTES:
        response = client.get(route)
        assert response.status_code == 200, route


def test_protected_routes_do_not_expose_to_anonymous_users(client):
    for route in ["/dashboard", "/quiz", "/certificate"]:
        response = client.get(route)
        assert response.status_code == 302, route
        assert "/login" in response.headers["Location"]

    for route in ["/admin", "/admin/articles", "/admin/quiz", "/admin/reports", "/admin/users"]:
        response = client.get(route)
        assert response.status_code == 401, route


def test_citizen_cannot_access_admin_routes(client):
    register(client)
    for route in ["/admin", "/admin/articles", "/admin/quiz", "/admin/reports", "/admin/users"]:
        response = client.get(route)
        assert response.status_code == 403, route


def test_all_admin_routes_render_for_admin(client):
    login_admin(client)
    for route in ["/admin", "/admin/articles", "/admin/quiz", "/admin/reports", "/admin/users"]:
        response = client.get(route)
        assert response.status_code == 200, route


def test_admin_handles_corrupt_report_analysis(client, app):
    with app.app_context():
        db.session.add(
            ScamReport(
                message="legacy record",
                risk_score=50,
                risk_level="Medium",
                analysis="not-json",
            )
        )
        db.session.commit()

    login_admin(client)
    response = client.get("/admin")
    assert response.status_code == 200
    assert b"Admin Dashboard" in response.data


def test_admin_users_invalid_post_and_self_demote_are_safe(client):
    login_admin(client)
    invalid = client.post("/admin/users", data={"user_id": "abc", "abc-role": "admin"}, follow_redirects=True)
    assert invalid.status_code == 200
    assert b"Invalid user selected" in invalid.data

    self_demote = client.post("/admin/users", data={"user_id": "1", "1-role": "citizen"}, follow_redirects=True)
    assert self_demote.status_code == 200
    assert b"cannot remove your own administrator role" in self_demote.data


def test_language_switcher_blocks_external_referrer(client):
    response = client.get("/set-language/hi", headers={"Referer": "https://evil.example/phish"})
    assert response.status_code == 302
    assert response.headers["Location"] == "/"


def test_api_scam_check_works_when_csrf_is_enabled():
    class CsrfEnabledConfig(TestingConfig):
        WTF_CSRF_ENABLED = True

    from app import create_app

    csrf_app = create_app(CsrfEnabledConfig)
    with csrf_app.test_client() as client:
        response = client.post("/api/scam-check", json={"message": "OTP click http://bad.xyz urgent"})
        assert response.status_code == 200
        assert response.json["risk_level"] in {"Medium", "High"}


def test_security_headers_present(client):
    response = client.get("/")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "SAMEORIGIN"
    assert "microphone=(self)" in response.headers["Permissions-Policy"]


def test_services_cover_edge_cases():
    assert level_for_score(85) == "Cyber Suraksha Champion"
    assert level_for_score(60) == "Cyber Safety Star"
    assert level_for_score(1) == "Cyber Awareness Learner"

    hindi = assistant_reply("OTP क्या है", language="hi")
    assert "OTP" in hindi

    result = analyze_message("Visit cybercrime.gov.in for help")
    assert not any(item.get("value") == "cybercrime.gov.in" for item in result["matched_rules"])
