#!/bin/bash
# ========================================
# Docker Installation Script for Ubuntu/Debian
# ========================================

echo "========================================="
echo "  Docker Installation Script Starting..."
echo "========================================="

# Step 1: System ko update karo (purane packages ko latest lao)
echo "[1/5] Updating package index..."
sudo apt-get update -y

# Step 2: Pehle se installed Docker remove karo (conflict avoid karne ke liye)
echo "[2/5] Removing old Docker versions..."
sudo apt-get remove -y docker docker-engine docker.io containerd runc 2>/dev/null

# Step 3: Required packages install karo
echo "[3/5] Installing dependencies..."
sudo apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# Step 4: Docker GPG key add karo (security ke liye)
echo "[4/5] Adding Docker GPG key..."
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Step 5: Docker repository add karo
echo "[5/5] Adding Docker repository..."
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Step 6: Docker install karo
echo "Installing Docker Engine..."
sudo apt-get update -y
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Step 7: Docker service start karo
echo "Starting Docker service..."
sudo systemctl start docker
sudo systemctl enable docker

# Step 8: Current user ko Docker group mein add karo (sudo bina chalne ke liye)
echo "Adding user to docker group..."
sudo usermod -aG docker $USER

# Verification
echo "========================================="
echo "  Docker Installation Complete!"
echo "========================================="
echo ""
echo "Docker version:"
docker --version
echo ""
echo "Docker Compose version:"
docker-compose --version
echo ""
echo "IMPORTANT: Log out and log back in for docker group changes to take effect."
echo "Test with: docker run hello-world"
