#!/bin/bash

# Check if running in Replit
if [ -z "$REPLIT" ]; then
  echo "Running locally: setting up virtual environment..."

  # Create venv if it doesn't exist
  if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
  fi

  # Activate venv
  source venv/bin/activate
fi

# Install dependencies
pip install -r backend/requirements.txt

# Run backend and frontend
python backend/qanda_api.py &
npm --prefix frontend run dev
