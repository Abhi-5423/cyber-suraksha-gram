from app.security import sanitize_text


def test_sanitize_text_removes_script():
    assert "<script" not in sanitize_text("<script>alert(1)</script>OTP")


def test_csrf_enabled_in_normal_config():
    from app.config import Config

    assert Config.SESSION_COOKIE_HTTPONLY is True
    assert Config.SESSION_COOKIE_SAMESITE == "Lax"


def test_load_user_rejects_invalid_session_id(app):
    from app import login_manager

    with app.app_context():
        assert login_manager._user_callback("not-an-int") is None
