#!/bin/bash

# Install ClamAV for virus scanning
echo "📦 Installing ClamAV antivirus..."
sudo apt-get update
sudo apt-get install -y clamav clamav-daemon clamav-freshclam

# Stop ClamAV services to configure
sudo systemctl stop clamav-daemon || true
sudo systemctl stop clamav-freshclam || true

# Update virus definitions
echo "🦠 Updating virus definitions (this may take a few minutes)..."
sudo freshclam || true

# Start ClamAV daemon
echo "🚀 Starting ClamAV daemon..."
sudo systemctl start clamav-daemon
sudo systemctl enable clamav-daemon
sudo systemctl start clamav-freshclam
sudo systemctl enable clamav-freshclam

echo "✅ ClamAV installed and running"

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
uv venv
source ./venv/bin/activate
uv pip install -r requirements.txt
