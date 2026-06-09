# Online Deployment

## Render

1. Push this repository to GitHub.
2. Create a new Render Web Service from the repo.
3. Use:

```text
Build Command: pip install -r requirements.txt
Start Command: gunicorn wsgi:app
```

Set environment variables:

```text
SECRET_KEY=<strong random secret>
DATABASE_URL=<managed database url>
FLASK_ENV=production
```

The included `render.yaml` can also be used as a Render Blueprint.

## Railway

1. Push this repository to GitHub.
2. Create a Railway project from the repo.
3. Railway should detect the Python app. The included `railway.json` sets:

```text
Start Command: gunicorn wsgi:app
```

Set environment variables:

```text
SECRET_KEY=<strong random secret>
DATABASE_URL=<managed database url>
FLASK_ENV=production
```

Railway CLI option:

```powershell
railway init
railway up
```

## PythonAnywhere

1. Upload or clone the repository.
2. Create and activate a virtualenv.
3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. In the PythonAnywhere Web tab, set the WSGI file to import the app from `wsgi.py`.
5. Set environment variables such as `SECRET_KEY`.
6. Set `DATABASE_URL` and `FLASK_ENV=production` for hosted deployments.

## Important Production Notes

SQLite works for demos and competitions, but production deployments should use persistent storage or a managed database.

Screenshot OCR requires the system Tesseract engine. Some free hosting plans may not allow installing system packages, so OCR may show a warning while the rest of the app keeps working.

`gTTS` and some speech recognition paths may require internet access from the host.
