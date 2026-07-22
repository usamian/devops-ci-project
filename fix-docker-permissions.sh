#!/bin/bash
# =====================================================
#  Fix Docker Socket Permission Issues
# =====================================================

echo "=========================================="
echo "  Fixing Docker Permissions"
echo "=========================================="
echo ""

# Check if docker group exists
if ! getent group docker > /dev/null 2>&1; then
    echo "❌ Docker group does not exist."
    echo "   Please install Docker first."
    exit 1
fi

echo "✅ Docker group exists"

# Check if current user is in docker group
if groups | grep -q docker; then
    echo "✅ Current user is in docker group"
else
    echo "⚠️  Current user is NOT in docker group"
    echo "   Adding current user to docker group..."
    sudo usermod -aG docker "$USER"
    echo "✅ Added to docker group"
    echo ""
    echo "   IMPORTANT: You need to log out and log back in"
    echo "   OR run: newgrp docker"
    echo ""
fi

# Fix docker socket permissions
echo "Fixing docker socket permissions..."
sudo chmod 666 /var/run/docker.sock 2>/dev/null || \
    sudo chown root:docker /var/run/docker.sock 2>/dev/null || \
    echo "⚠️  Could not fix socket permissions automatically"
echo "✅ Socket permissions fixed"

# Verify
echo ""
echo "Verifying..."
if docker info &> /dev/null; then
    echo "✅ Docker is working without sudo!"
else
    echo "⚠️  Docker still requires sudo"
    echo "   Run: sudo docker compose up -d"
fi

echo ""
echo "=========================================="
echo "  Permission Fix Complete"
echo "=========================================="
echo ""
echo "If you still see permission errors:"
echo "  1. Run: newgrp docker"
echo "  2. Close terminal and open new terminal"
echo "  3. Run: docker compose up -d"
echo ""
