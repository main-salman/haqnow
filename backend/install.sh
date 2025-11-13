#!/bin/bash

# Note: Virus scanning now uses VirusTotal API (cloud-based)
# No local antivirus installation needed
# Just add VIRUSTOTAL_API_KEY to .env file

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
uv venv
source ./venv/bin/activate
uv pip install -r requirements.txt

echo "✅ Backend dependencies installed"
echo "🦠 Virus scanning: Configure VIRUSTOTAL_API_KEY in .env"
