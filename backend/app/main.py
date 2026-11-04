"""Run: python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000"""
from app.api.application import create_app

app = create_app()
