#!/bin/bash
set -e
cd "$(dirname "$0")/backend"
pip install -r requirements.txt --quiet
exec uvicorn main:app --reload --port 8000
