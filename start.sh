#!/bin/bash

# Install Python deps
pip install --break-system-packages -r backend/requirements.txt


# Start frontend with Vite
cd frontend
npm install
npm run dev
cd ..

# Start FastAPI backend
cd backend
uvicorn qanda_api:app --host 0.0.0.0 --port 8000 &

