#!/bin/bash
# Docker Installation Script for Ubuntu/Debian on WSL2

echo "🐳 Installing Docker Engine..."

# Update the apt package index
echo "📦 Updating apt package index..."
sudo apt-get update

# Install prerequisites
echo "🔧 Installing prerequisites..."
sudo apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# Add Docker's official GPG key
echo "🔑 Adding Docker's official GPG key..."
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Set up the repository
echo "📚 Setting up Docker repository..."
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Update apt package index again
echo "🔄 Updating package index with Docker repository..."
sudo apt-get update

# Install Docker Engine, containerd, and Docker Compose
echo "⚙️ Installing Docker Engine, containerd, and Docker Compose..."
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Add current user to docker group (optional - allows running docker without sudo)
echo "👤 Adding current user to docker group..."
sudo usermod -aG docker $USER

# Start Docker service
echo "🚀 Starting Docker service..."
sudo service docker start

# Verify installation
echo ""
echo "✅ Docker installation complete!"
echo ""
echo "🔍 Verifying installation..."
sudo docker --version
sudo docker compose version

echo ""
echo "⚠️  IMPORTANT: To run Docker commands without sudo, you need to:"
echo "   1. Log out and log back in (or restart WSL)"
echo "   2. Or run: newgrp docker"
echo ""
echo "🧪 Test Docker with: docker run hello-world"


