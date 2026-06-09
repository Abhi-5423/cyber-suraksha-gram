from app.models import QuizQuestion, User


def test_home_page_loads(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Cyber Suraksha Gram" in response.data


def test_register_login_dashboard(client):
    response = client.post(
        "/register",
        data={
            "full_name": "Asha Devi",
            "email": "asha@example.com",
            "village": "Rampur",
            "district": "Patna",
            "language": "en",
            "password": "StrongPass@123",
            "confirm_password": "StrongPass@123",
        },
        follow_redirects=True,
    )
    assert b"Dashboard" in response.data


def test_api_scam_check(client):
    response = client.post("/api/scam-check", json={"message": "Urgent OTP required click http://bad.xyz"})
    assert response.status_code == 200
    assert response.json["risk_level"] in {"Medium", "High"}


def test_admin_requires_login(client):
    response = client.get("/admin")
    assert response.status_code in {302, 401}


def test_seeded_questions(app):
    with app.app_context():
        assert QuizQuestion.query.count() == 50
        assert User.query.filter_by(email="admin@cybersuraksha.in").first() is not None
