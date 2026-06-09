from app.services import ml_scam_detector
from app.services.ml_scam_detector import load_training_rows, normalize_text, predict_scam, train_classifier


def test_normalize_text_replaces_urls():
    normalized = normalize_text("Click https://fraud.xyz NOW!!!")
    assert "urltoken" in normalized
    assert "https" not in normalized


def test_load_training_rows_reads_seed_dataset():
    rows = load_training_rows()
    assert len(rows) >= 20
    assert {"fraud", "safe"} <= {row["label"] for row in rows}


def test_predict_scam_without_model_is_safe(monkeypatch, tmp_path):
    monkeypatch.setattr(ml_scam_detector, "MODEL_PATH", tmp_path / "missing.joblib")
    result = predict_scam("urgent otp click link")
    assert result["available"] is False
    assert result["label"] == "unknown"


def test_train_classifier_and_predict_with_temp_model(monkeypatch, tmp_path):
    pytest = __import__("pytest")
    pytest.importorskip("sklearn")
    pytest.importorskip("joblib")

    model_path = tmp_path / "model.joblib"
    metrics = train_classifier(model_path=model_path)
    assert model_path.exists()
    assert metrics["rows"] >= 20

    monkeypatch.setattr(ml_scam_detector, "MODEL_PATH", model_path)
    fraud = predict_scam("Urgent KYC OTP click http://fake.xyz")
    safe = predict_scam("Cyber awareness meeting at village office")
    assert fraud["available"] is True
    assert fraud["label"] in {"fraud", "safe"}
    assert 0 <= fraud["confidence"] <= 100
    assert safe["available"] is True
