#!/bin/bash

# Install Python deps
source venv/bin/activate
pip install --break-system-packages -r backend/requirements.txt

# Start FastAPI backend
cd backend
uvicorn qanda_api:app --host 0.0.0.0 --port 8000 
