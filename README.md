# Cyber Suraksha Gram

Rural Cyber Fraud Awareness & Protection Platform built with Flask, SQLite, SQLAlchemy, Flask-Login, WTForms, Bootstrap 5 and JavaScript.

## Platform Features

- Cyber threat intelligence widgets with animated counters.
- Live scam alert center at `/alerts`, with admin publishing at `/admin/alerts`.
- AI scam analyzer with OCR screenshot support, risk percentage, threat breakdown and recommended action.
- Cyber Champion XP, badges, achievements, daily challenge streaks and leaderboard.
- Interactive dashboard with Chart.js progress charts and learning path progress.
- Fraud reporting wizard with evidence upload and recovery guidance.
- QR scam awareness center at `/qr-safety` and success stories at `/stories`.
- English and Hindi language support with guest `localStorage` and logged-in database preference.
- 3D branding with model-viewer GLB logos, WebP fallback, favicon set, branded splash screen, Open Graph preview and PDF certificate watermark.

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
  translations/        English and Hindi JSON translation files
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

When you run `python run.py` or `python app.py`, the terminal prints:

```text
Server Running:
Local: http://127.0.0.1:5000
Public: https://<your-deployment-url>
```

Open the app locally with the Local URL during development. After deployment, open the hosted Public URL such as `https://cyber-suraksha-gram.onrender.com`.

## Mobile Testing on Same Wi-Fi

1. Connect your computer and phone to the same Wi-Fi network.
2. Start the Flask app:

```powershell
python run.py
```

3. Find your computer's local IP address.

Windows:

```powershell
ipconfig
```

Look for `IPv4 Address`, for example `192.168.1.25`.

Linux:

```bash
ip addr
```

Look for your Wi-Fi interface address, usually starting with `192.168.x.x` or `10.x.x.x`.

4. On your phone browser, open the Network URL printed in the terminal for local Wi-Fi testing, or use the hosted deployment URL after publishing:

```text
http://<local-ip>:5000
```

Example:

```text
http://192.168.1.25:5000
```

Deployed example:

```text
https://cyber-suraksha-gram.onrender.com
```

If it does not open, allow Python/Flask through Windows Firewall and confirm both devices are on the same Wi-Fi.

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
python -m pytest
```

## Database Migrations

Schema changes are documented in `migrations/`. The app also runs a lightweight SQLite-safe schema check on startup for the quiz `difficulty` column and creates the quiz history table with SQLAlchemy.

## Deployment

Use `wsgi:app` as the WSGI entrypoint. On Render or Railway, set:

```text
SECRET_KEY=<strong random secret>
DATABASE_URL=sqlite:///cyber_suraksha.db
FLASK_ENV=production
```

For PythonAnywhere, create a web app, install requirements in a virtualenv, and point WSGI to `wsgi.py`.

See [docs/ONLINE_DEPLOYMENT.md](docs/ONLINE_DEPLOYMENT.md) for Render, Railway, and PythonAnywhere steps.
