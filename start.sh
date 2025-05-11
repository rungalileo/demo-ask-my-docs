#!/bin/bash

# Install Python dependencies
pip install --break-system-packages -r backend/requirements.txt

# Start FastAPI backend in background
cd backend
nohup uvicorn qanda_api:app --host 0.0.0.0 --port 8001 > backend.log 2>&1 &
cd ..

# Start frontend (Vite)
cd frontend
npm install
npm run dev -- --host 0.0.0.0 --port $PORT