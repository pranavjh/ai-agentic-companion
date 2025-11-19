#!/bin/bash

# AI Agentic Companion - Web UI Launcher

echo "=================================="
echo "AI Agentic Companion - Web UI"
echo "=================================="
echo ""

# Activate virtual environment
source venv/bin/activate

# Start Flask application
cd src/web
python app.py
