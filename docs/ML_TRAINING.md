# AI Scam Detection Training

The platform includes a trainable AI scam detector for competitions and final-year demonstrations.

## Supported Data Files

Place CSV files in `data/`:

```text
data/sms_spam.csv
data/cyber_fraud_messages.csv
data/phishing_urls.csv
```

Accepted text columns: `text`, `message`, `sms`, `url`, `URL`.

Accepted label columns: `label`, `class`, `type`, `status`.

Fraud labels: `spam`, `fraud`, `phishing`, `malicious`, `bad`, `1`.

Safe labels: `ham`, `safe`, `legitimate`, `benign`, `good`, `0`.

## Train

```powershell
python -m pip install -r requirements.txt
python scripts/train_model.py
```

The trained model is saved to:

```text
instance/ml_scam_classifier.joblib
```

## Runtime Behavior

`/api/ai-scam-check` returns AI-only predictions.

`/api/scam-check` returns both rule-based and AI analysis.

The web scam checker shows an AI confidence panel when a trained model is available.

Transformers support is optional. The default production path uses fast TF-IDF plus Logistic Regression.
