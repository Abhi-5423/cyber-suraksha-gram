import csv
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
MODEL_PATH = BASE_DIR / "instance" / "ml_scam_classifier.joblib"
DEFAULT_DATASET = BASE_DIR / "data" / "training_messages.csv"

URL_PATTERN = re.compile(r"https?://\S+|www\.\S+|\b[a-z0-9-]+\.(?:com|in|net|org|xyz|top|click|loan)\S*", re.I)
NON_WORD_PATTERN = re.compile(r"[^a-z0-9\s]+", re.I)


def normalize_text(text):
    value = (text or "").lower()
    value = URL_PATTERN.sub(" URLTOKEN ", value)
    value = NON_WORD_PATTERN.sub(" ", value)
    return re.sub(r"\s+", " ", value).strip().lower()


def load_training_rows(paths=None):
    dataset_paths = [Path(path) for path in (paths or [DEFAULT_DATASET])]
    rows = []
    for path in dataset_paths:
        if not path.exists():
            continue
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                text = row.get("text") or row.get("message") or row.get("sms") or row.get("url") or row.get("URL")
                label = row.get("label") or row.get("class") or row.get("type") or row.get("status")
                if not text or not label:
                    continue
                normalized_label = str(label).strip().lower()
                if normalized_label in {"spam", "fraud", "phishing", "malicious", "bad", "1"}:
                    label_value = "fraud"
                elif normalized_label in {"ham", "safe", "legitimate", "benign", "good", "0"}:
                    label_value = "safe"
                else:
                    continue
                rows.append({"text": text.strip(), "label": label_value, "category": row.get("category", "General")})
    return rows


def train_classifier(dataset_paths=None, model_path=MODEL_PATH):
    try:
        import joblib
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
        from sklearn.metrics import accuracy_score, classification_report
        from sklearn.model_selection import train_test_split
        from sklearn.pipeline import Pipeline
    except ImportError as exc:
        raise RuntimeError("Install ML dependencies with: python -m pip install -r requirements.txt") from exc

    rows = load_training_rows(dataset_paths)
    if len(rows) < 10:
        raise ValueError("At least 10 labeled training rows are required.")

    texts = [normalize_text(row["text"]) for row in rows]
    labels = [row["label"] for row in rows]
    stratify = labels if len(set(labels)) > 1 and min(labels.count(label) for label in set(labels)) >= 2 else None
    x_train, x_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.25, random_state=42, stratify=stratify
    )

    pipeline = Pipeline(
        [
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1, max_features=8000)),
            ("clf", LogisticRegression(max_iter=1000, class_weight="balanced")),
        ]
    )
    pipeline.fit(x_train, y_train)
    predictions = pipeline.predict(x_test)
    metrics = {
        "accuracy": accuracy_score(y_test, predictions),
        "report": classification_report(y_test, predictions, zero_division=0),
        "rows": len(rows),
    }

    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"pipeline": pipeline, "metrics": metrics}, model_path)
    return metrics


def _load_model():
    if not MODEL_PATH.exists():
        return None
    try:
        import joblib

        return joblib.load(MODEL_PATH)
    except Exception:
        return None


def _transformer_signal(message):
    try:
        from transformers import pipeline
    except ImportError:
        return None

    try:
        classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
        result = classifier(message, candidate_labels=["cyber fraud", "safe message", "phishing"])
    except Exception:
        return None
    return {"labels": result.get("labels", []), "scores": result.get("scores", [])}


def predict_scam(message, use_transformer=False):
    normalized = normalize_text(message)
    model_bundle = _load_model()
    if not model_bundle:
        return {
            "available": False,
            "label": "unknown",
            "fraud_probability": None,
            "confidence": 0,
            "model": "not-trained",
            "recommendation": "Train the AI model with scripts/train_model.py for ML confidence scoring.",
        }

    pipeline = model_bundle["pipeline"]
    label = pipeline.predict([normalized])[0]
    probabilities = {}
    if hasattr(pipeline.named_steps["clf"], "predict_proba"):
        classes = list(pipeline.named_steps["clf"].classes_)
        scores = pipeline.predict_proba([normalized])[0]
        probabilities = dict(zip(classes, scores))
    fraud_probability = float(probabilities.get("fraud", 1.0 if label == "fraud" else 0.0))
    confidence = int(round(max(probabilities.values(), default=fraud_probability) * 100))
    transformer = _transformer_signal(message) if use_transformer else None
    return {
        "available": True,
        "label": label,
        "fraud_probability": round(fraud_probability, 4),
        "confidence": confidence,
        "model": "tfidf-logistic-regression",
        "metrics": model_bundle.get("metrics", {}),
        "transformer_signal": transformer,
        "recommendation": "Treat as suspicious and verify officially." if label == "fraud" else "No strong ML fraud signal found; continue basic safety checks.",
    }
