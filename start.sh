#!/bin/bash

# Install Python deps
pip install --break-system-packages -r backend/requirements.txt

# Start FastAPI backend
cd backend
nohup uvicorn qanda_api:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
cd ..

# Start frontend with Vite
cd frontend
npm install
npm run dev
