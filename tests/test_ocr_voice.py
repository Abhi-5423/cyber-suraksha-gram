from io import BytesIO

from app.services.ocr import extract_text_from_image
from app.services.voice import synthesize_speech, transcribe_audio


def test_scam_checker_accepts_message_without_screenshot(client):
    response = client.post(
        "/scam-checker",
        data={"message": "Urgent OTP KYC click http://fraud.xyz"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Risk Meter" in response.data


def test_scam_checker_rejects_empty_text_and_empty_screenshot(client):
    response = client.post("/scam-checker", data={"message": ""}, follow_redirects=True)
    assert response.status_code == 200
    assert b"Paste a message or upload a screenshot" in response.data


def test_ocr_api_rejects_missing_screenshot(client):
    response = client.post("/api/ocr-scam-check", data={})
    assert response.status_code == 400
    assert "ocr" in response.json


def test_voice_transcribe_rejects_missing_audio(client):
    response = client.post("/api/voice/transcribe", data={})
    assert response.status_code == 400
    assert response.json["text"] == ""


def test_voice_speak_rejects_empty_text(client):
    response = client.post("/api/voice/speak", json={"text": ""})
    assert response.status_code == 400
    assert "error" in response.json


def test_voice_and_ocr_services_missing_files_are_safe():
    assert extract_text_from_image(None)["available"] is False
    assert transcribe_audio(None)["available"] is False
    assert synthesize_speech("")["available"] is False


def test_upload_field_rejects_non_image(client):
    response = client.post(
        "/scam-checker",
        data={
            "message": "",
            "screenshot": (BytesIO(b"not image"), "note.txt"),
        },
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Message Checker" in response.data
