from app.services.fraud_detector import analyze_message


def test_high_risk_message_detection():
    result = analyze_message("Urgent KYC verify account click link http://fake-loan.xyz share OTP")
    assert result["risk_score"] >= 60
    assert result["risk_level"] == "High"
    assert any(item["rule"] == "OTP" for item in result["matched_rules"])


def test_low_risk_message_detection():
    result = analyze_message("Your bank branch will remain closed on Sunday.")
    assert result["risk_level"] == "Low"
