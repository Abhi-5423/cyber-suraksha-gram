# Cyber Suraksha Gram

Rural Cyber Fraud Awareness & Protection Platform built with Flask, SQLite, SQLAlchemy, Flask-Login, WTForms, Bootstrap 5 and JavaScript.

## Project Structure

```text
app/
  __init__.py          Flask app factory, extensions, security headers
  config.py            Environment-based configuration
  forms.py             WTForms validation
  models.py            SQLAlchemy database models
  routes.py            Pages, APIs, auth, RBAC, admin
  seed.py              Awareness articles, 50 quiz questions, default admin
  services/
    fraud_detector.py  Rule-based scam detection engine
    chatbot.py         Hindi/English cyber assistant
    certificate.py     PDF certificate generation
  static/css/styles.css
  static/js/app.js     Dark mode, counters, PWA, voice assistant
  templates/           Bootstrap 5 responsive pages
  translations/        English, Hindi, Bhojpuri, Maithili JSON
tests/                 Unit, integration, API and security tests
docs/                  Design and deployment documentation
```

## Run Locally

Fast start on Windows:

```powershell
.\start.ps1
```

Or with Command Prompt:

```bat
start.bat
```

Manual setup:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:SECRET_KEY="change-this-in-production"
python run.py
```

Open `http://127.0.0.1:5000`.

Default admin:

```text
Email: admin@cybersuraksha.in
Password: Admin@12345
```

Change the default password after first login.

## API

`POST /api/scam-check`

```json
{"message":"Urgent KYC verify account click link and share OTP"}
```

Returns:

```json
{"risk_score":95,"risk_level":"High","matched_rules":[],"recommendation":"..."}
```

AI-only endpoint:

```text
POST /api/ai-scam-check
```

Train the ML classifier:

```powershell
python scripts/train_model.py
```

See [docs/ML_TRAINING.md](docs/ML_TRAINING.md).

Screenshot OCR and voice:

```text
POST /api/ocr-scam-check
POST /api/voice/transcribe
POST /api/voice/speak
```

Python packages are included in `requirements.txt`: `pytesseract`, `Pillow`, `SpeechRecognition`, and `gTTS`.

For screenshot OCR, install the system Tesseract OCR engine and make sure `tesseract.exe` is available on PATH. The app will continue running and show a clear warning if Tesseract is missing.

## Security

The app uses CSRF protection, password hashing, SQLAlchemy parameterized queries, input sanitization, secure session flags, RBAC, rate limiting and security headers. Set `SECRET_KEY` and `DATABASE_URL` through environment variables in production.

## Tests

```powershell
pytest
```

## Deployment

Use `wsgi:app` as the WSGI entrypoint. On Render or Railway, set:

```text
SECRET_KEY=<strong random secret>
DATABASE_URL=sqlite:///cyber_suraksha.db
```

For PythonAnywhere, create a web app, install requirements in a virtualenv, and point WSGI to `wsgi.py`.

See [docs/ONLINE_DEPLOYMENT.md](docs/ONLINE_DEPLOYMENT.md) for Render, Railway, and PythonAnywhere steps.
