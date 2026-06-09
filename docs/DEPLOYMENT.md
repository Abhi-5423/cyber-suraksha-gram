# Deployment Guide

## Render

Create a Python web service. Use `pip install -r requirements.txt` as the build command and `gunicorn wsgi:app` as the start command after adding gunicorn if your Render service requires it. Set `SECRET_KEY`.

## Railway

Create a Python project, set `SECRET_KEY`, install requirements and run `gunicorn wsgi:app`. Use a persistent volume or managed database for production data.

## PythonAnywhere

Upload the project, create a virtualenv, install requirements, and configure the WSGI file to import `app` from `wsgi.py`.

## Production Checklist

Set a strong `SECRET_KEY`, replace the seeded admin password, configure persistent storage, serve over HTTPS, monitor rate limits, and back up the database.
