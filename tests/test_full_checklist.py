from app import db
from app.models import ChatHistory, QuizQuestion, QuizResult, ScamReport, User


def register_user(client, email="tester@example.com"):
    return client.post(
        "/register",
        data={
            "full_name": "Checklist Tester",
            "email": email,
            "village": "Rampur",
            "district": "Patna",
            "language": "en",
            "password": "StrongPass@123",
            "confirm_password": "StrongPass@123",
        },
        follow_redirects=True,
    )


def login_user(client, email="tester@example.com", password="StrongPass@123"):
    return client.post(
        "/login",
        data={"email": email, "password": password},
        follow_redirects=True,
    )


def logout_user(client):
    return client.get("/logout", follow_redirects=True)


def test_registration_login_dashboard_and_database_storage(client, app):
    response = register_user(client)
    assert response.status_code == 200
    assert b"Dashboard" in response.data

    with app.app_context():
        user = User.query.filter_by(email="tester@example.com").first()
        assert user is not None
        assert user.village == "Rampur"
        assert user.check_password("StrongPass@123")

    logout_user(client)
    response = login_user(client)
    assert response.status_code == 200
    assert b"Dashboard" in response.data


def test_scam_detector_persists_report(client, app):
    response = client.post(
        "/scam-checker",
        data={"message": "Urgent KYC verify account. Click link http://fraud-claim.xyz and share OTP."},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Risk Meter" in response.data
    assert b"High" in response.data

    with app.app_context():
        report = ScamReport.query.order_by(ScamReport.id.desc()).first()
        assert report is not None
        assert report.risk_score >= 60
        assert report.risk_level == "High"


def test_quiz_system_updates_score_and_result(client, app):
    register_user(client, email="quiz@example.com")
    with app.app_context():
        questions = QuizQuestion.query.order_by(QuizQuestion.id).limit(10).all()
        answers = {f"q{question.id}": question.correct_answer for question in questions}

    response = client.post("/quiz", data=answers, follow_redirects=True)
    assert response.status_code == 200
    assert b"Best Score" in response.data

    with app.app_context():
        user = User.query.filter_by(email="quiz@example.com").first()
        assert user.score == 100
        result = QuizResult.query.filter_by(user_id=user.id).first()
        assert result is not None
        assert result.score == 100


def test_language_switcher_sets_session_and_page_translates(client):
    response = client.get("/set-language/hi", follow_redirects=True)
    assert response.status_code == 200
    assert "जागरूकता".encode("utf-8") in response.data

    response = client.get("/set-language/mai", follow_redirects=True)
    assert response.status_code == 200
    assert b'value="en" selected' in response.data


def test_voice_assistant_chatbot_page_and_storage(client, app):
    page = client.get("/chatbot")
    assert page.status_code == 200
    assert b'id="voiceStart"' in page.data
    assert b'id="speakReply"' in page.data

    js = client.get("/static/js/app.js")
    assert js.status_code == 200
    assert b"SpeechRecognition" in js.data
    assert b"SpeechSynthesisUtterance" in js.data
    assert b"hi-IN" in js.data
    assert b"en-IN" in js.data

    register_user(client, email="chat@example.com")
    response = client.post("/chatbot", data={"message": "UPI safety tips"}, follow_redirects=True)
    assert response.status_code == 200
    assert b"UPI safety" in response.data

    with app.app_context():
        user = User.query.filter_by(email="chat@example.com").first()
        chat = ChatHistory.query.filter_by(user_id=user.id).first()
        assert chat is not None
        assert "UPI" in chat.response


def test_admin_panel_access_and_pdf_certificate(client):
    response = client.post(
        "/login",
        data={"email": "admin@cybersuraksha.in", "password": "Admin@12345"},
        follow_redirects=True,
    )
    assert response.status_code == 200

    admin = client.get("/admin")
    assert admin.status_code == 200
    assert b"Admin Dashboard" in admin.data

    users = client.get("/admin/users")
    assert users.status_code == 200
    assert b"Cyber Suraksha Admin" in users.data

    pdf = client.get("/certificate")
    assert pdf.status_code == 200
    assert pdf.headers["content-type"] == "application/pdf"
    assert pdf.data.startswith(b"%PDF")

