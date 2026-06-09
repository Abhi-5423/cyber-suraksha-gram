from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.ml_scam_detector import DEFAULT_DATASET, MODEL_PATH, train_classifier


def main():
    dataset_paths = [
        DEFAULT_DATASET,
        ROOT / "data" / "sms_spam.csv",
        ROOT / "data" / "cyber_fraud_messages.csv",
        ROOT / "data" / "phishing_urls.csv",
    ]
    metrics = train_classifier(dataset_paths=dataset_paths, model_path=MODEL_PATH)
    print(f"Model saved to: {MODEL_PATH}")
    print(f"Rows trained: {metrics['rows']}")
    print(f"Accuracy: {metrics['accuracy']:.3f}")
    print(metrics["report"])


if __name__ == "__main__":
    main()
