@echo off
cd /d "%~dp0backend"
pip install -r requirements.txt --quiet
uvicorn main:app --reload --port 8000
