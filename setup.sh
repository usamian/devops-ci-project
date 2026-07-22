#!/bin/bash
# =====================================================
#  Atlas-AI CI/CD Pipeline - Setup Script
#  Starts all services automatically
# =====================================================

set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

echo "=========================================="
echo "  Atlas-AI CI/CD Pipeline"
echo "=========================================="
echo ""

# Check Docker
echo "[1/6] Checking Docker..."
if ! docker info &> /dev/null; then
    echo "❌ Docker is not running."
    echo "   Start it with: sudo systemctl start docker"
    exit 1
fi
echo "✅ Docker is running"

# Check Docker Compose
echo ""
echo "[2/6] Checking Docker Compose..."
if ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not installed."
    echo "   Try: sudo apt install docker-compose-plugin"
    exit 1
fi
echo "✅ Docker Compose is available"

# Stop old containers
echo ""
echo "[3/6] Cleaning old containers..."
docker compose down 2>/dev/null || true
echo "✅ Cleaned"

# Start services
echo ""
echo "[4/6] Starting services..."
if ! docker compose up -d 2>&1; then
    echo ""
    echo "⚠️  Permission error detected!"
    echo "   Trying with sudo..."
    
    # Fix socket permissions
    sudo chmod 666 /var/run/docker.sock 2>/dev/null || true
    
    # Retry with sudo
    if sudo docker compose up -d 2>&1; then
        echo "✅ Services started with sudo"
    else
        echo "❌ Failed to start services"
        echo ""
        echo "Fix permanently:"
        echo "  1. Run: sudo ./fix-docker-permissions.sh"
        echo "  2. Or run: docker compose up -d"
        exit 1
    fi
else
    echo "✅ Services started"
fi

# Wait
echo ""
echo "[5/6] Waiting for services (45 seconds)..."
sleep 45

# Status
echo ""
echo "[6/6] Checking services..."
echo ""

check_service() {
    local name=$1
    local url=$2
    if curl -s -o /dev/null -w "%{http_code}" "$url" | grep -q "200"; then
        echo "✅ $name - READY at $url"
    else
        echo "⏳ $name - starting... open $url"
    fi
}

check_service "Jenkins"       "http://localhost:8080"
check_service "SonarQube"     "http://localhost:9000"

echo ""
echo "=========================================="
echo "  Login"
echo "=========================================="
echo "Jenkins:   http://localhost:8080   (admin / admin123)"
echo "SonarQube: http://localhost:9000   (admin / admin)"
echo ""
echo "=========================================="
echo "  Done!"
echo "=========================================="
echo ""
echo "Stop: docker compose down"
echo "Start again: ./setup.sh"
echo ""
