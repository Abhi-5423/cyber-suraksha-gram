from app.models import AwarenessArticle, DailyChallengeAttempt, FraudIncident, QuizQuestion, ScamAlert, User


def login_admin(client):
    return client.post(
        "/login",
        data={"email": "admin@cybersuraksha.in", "password": "Admin@12345"},
        follow_redirects=True,
    )


def register_payload(email="post-user@example.com"):
    return {
        "full_name": "Post User",
        "email": email,
        "village": "Rampur",
        "district": "Patna",
        "language": "en",
        "password": "StrongPass@123",
        "confirm_password": "StrongPass@123",
    }


def test_duplicate_registration_and_failed_login(client):
    payload = register_payload()
    first = client.post("/register", data=payload, follow_redirects=True)
    assert first.status_code == 200

    client.get("/logout")
    duplicate = client.post("/register", data=payload, follow_redirects=True)
    assert duplicate.status_code == 200
    assert b"already registered" in duplicate.data

    failed = client.post(
        "/login",
        data={"email": payload["email"], "password": "wrong-password"},
        follow_redirects=True,
    )
    assert failed.status_code == 200
    assert b"Invalid email or password" in failed.data


def test_logout_route(client):
    client.post("/register", data=register_payload("logout@example.com"), follow_redirects=True)
    response = client.get("/logout", follow_redirects=True)
    assert response.status_code == 200
    assert b"Cyber Suraksha Gram" in response.data


def test_report_fraud_post_prepares_guidance(client, app):
    response = client.post(
        "/report-fraud",
        data={"fraud_type": "Fake KYC", "message": "I paid money after receiving a fake KYC call from an unknown person.", "contact": "9999999999"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"1930" in response.data
    assert b"cybercrime.gov.in" in response.data
    with app.app_context():
        assert FraudIncident.query.filter_by(fraud_type="Fake KYC").first() is not None


def test_api_scam_check_rejects_missing_message(client):
    response = client.post("/api/scam-check", json={"message": ""})
    assert response.status_code == 400
    assert response.json["error"] == "message is required"


def test_ai_scam_check_api_returns_ml_shape(client):
    response = client.post("/api/ai-scam-check", json={"message": "Urgent OTP click http://bad.xyz"})
    assert response.status_code == 200
    assert {"available", "label", "confidence", "model"} <= set(response.json)


def test_voice_and_ocr_routes_registered(app):
    rules = {str(rule) for rule in app.url_map.iter_rules()}
    assert "/api/ocr-scam-check" in rules
    assert "/api/voice/transcribe" in rules
    assert "/api/voice/speak" in rules


def test_combined_scam_api_includes_ai_analysis(client):
    response = client.post("/api/scam-check", json={"message": "Urgent OTP click http://bad.xyz"})
    assert response.status_code == 200
    assert "ai_analysis" in response.json


def test_admin_article_post_sanitizes_and_stores(client, app):
    login_admin(client)
    response = client.post(
        "/admin/articles",
        data={
            "title": "<script>Bad</script>Safe Article",
            "category": "UPI",
            "language": "en",
            "content": "<p>Useful safety content</p><script>alert(1)</script>",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Article saved" in response.data

    with app.app_context():
        article = AwarenessArticle.query.filter(AwarenessArticle.title.contains("Safe Article")).first()
        assert article is not None
        assert "<script" not in article.title
        assert "<script" not in article.content


def test_admin_alert_post_publishes_alert(client, app):
    login_admin(client)
    response = client.post(
        "/admin/alerts",
        data={
            "title": "New QR Warning",
            "category": "QR Scam",
            "severity": "High",
            "language": "en",
            "content": "Do not scan unknown QR codes to receive money.",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Alert published" in response.data
    with app.app_context():
        assert ScamAlert.query.filter_by(title="New QR Warning").first() is not None


def test_daily_challenge_rewards_correct_answer(client, app):
    client.post("/register", data=register_payload("challenge@example.com"), follow_redirects=True)
    page = client.get("/daily-challenge")
    assert page.status_code == 200
    with app.app_context():
        from app.models import DailyChallenge

        challenge = DailyChallenge.query.order_by(DailyChallenge.challenge_date.desc()).first()
        answer = challenge.correct_answer
    response = client.post("/daily-challenge", data={"answer": answer}, follow_redirects=True)
    assert response.status_code == 200
    with app.app_context():
        user = User.query.filter_by(email="challenge@example.com").first()
        assert DailyChallengeAttempt.query.filter_by(user_id=user.id).first() is not None
        assert user.xp_points >= 25


def test_admin_quiz_post_stores_question(client, app):
    login_admin(client)
    response = client.post(
        "/admin/quiz",
        data={
            "question": "What should you never share with unknown callers?",
            "option_a": "OTP",
            "option_b": "Weather",
            "option_c": "Village name",
            "option_d": "Bus route",
            "correct_answer": "A",
            "category": "OTP Fraud",
            "difficulty": "Beginner",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Question saved" in response.data

    with app.app_context():
        question = QuizQuestion.query.filter_by(question="What should you never share with unknown callers?").first()
        assert question is not None
        assert question.correct_answer == "A"


def test_admin_can_promote_user_to_volunteer(client, app):
    client.post("/register", data=register_payload("volunteer@example.com"), follow_redirects=True)
    client.get("/logout")
    login_admin(client)

    with app.app_context():
        user = User.query.filter_by(email="volunteer@example.com").first()
        user_id = user.id

    response = client.post(
        "/admin/users",
        data={"user_id": str(user_id), f"{user_id}-role": "volunteer"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"User role updated" in response.data

    with app.app_context():
        assert User.query.filter_by(email="volunteer@example.com").first().role == "volunteer"
