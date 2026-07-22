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
echo "[1/5] Checking Docker..."
if ! docker info &> /dev/null; then
    echo "❌ Docker is not running. Please start Docker first."
    echo "   Try: sudo systemctl start docker"
    exit 1
fi
echo "✅ Docker is running"

# Check Docker Compose
echo ""
echo "[2/5] Checking Docker Compose..."
if ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not installed."
    echo "   Try: sudo apt install docker-compose-plugin"
    exit 1
fi
echo "✅ Docker Compose is available"

# Stop old containers
echo ""
echo "[3/5] Cleaning old containers..."
docker compose down 2>/dev/null || true
echo "✅ Cleaned"

# Start services
echo ""
echo "[4/5] Starting services..."
docker compose up -d
echo "✅ Services starting"

# Wait
echo ""
echo "[5/5] Waiting for services (45 seconds)..."
sleep 45

# Status
echo ""
echo "=========================================="
echo "  Service Status"
echo "=========================================="
echo ""

check_service() {
    local name=$1
    local url=$2
    if curl -s -o /dev/null -w "%{http_code}" "$url" | grep -q "200"; then
        echo "✅ $name - READY at $url"
    else
        echo "⏳ $name - starting... please wait and open $url"
    fi
}

check_service "Jenkins"     "http://localhost:8080"
check_service "SonarQube"   "http://localhost:9000"

echo ""
echo "=========================================="
echo "  Login Info"
echo "=========================================="
echo "Jenkins:"
echo "  URL:      http://localhost:8080"
echo "  User:     admin"
echo "  Password: admin123"
echo ""
echo "SonarQube:"
echo "  URL:      http://localhost:9000"
echo "  User:     admin"
echo "  Password: admin"
echo ""
echo "=========================================="
echo "  Done!"
echo "=========================================="
echo ""
echo "To stop later: cd $PROJECT_DIR && docker compose down"
echo "To restart: ./setup.sh"
echo ""
