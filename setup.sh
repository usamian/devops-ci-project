#!/bin/bash
# ========================================
# Atlas-AI CI/CD Pipeline - Complete Setup Script
# This script sets up the entire project from scratch
# ========================================

set -e  # Exit on any error

echo "========================================="
echo "  Atlas-AI CI/CD Pipeline Setup"
echo "========================================="
echo ""

# Step 1: Check if Docker is installed
echo "[1/7] Checking Docker installation..."
if ! command -v docker &> /dev/null; then
    echo "Docker not found. Please install Docker first."
    echo "Run: sudo apt install docker.io docker-compose"
    exit 1
fi
echo "✅ Docker is installed: $(docker --version)"

# Step 2: Check if Docker Compose is installed
echo ""
echo "[2/7] Checking Docker Compose..."
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "Docker Compose not found. Please install Docker Compose."
    exit 1
fi
echo "✅ Docker Compose is installed"

# Step 3: Stop any existing containers
echo ""
echo "[3/7] Stopping existing containers..."
docker compose down 2>/dev/null || true
echo "✅ Existing containers stopped"

# Step 4: Start services
echo ""
echo "[4/7] Starting services..."
docker compose up -d
echo "✅ Services started"

# Step 5: Wait for services to be ready
echo ""
echo "[5/7] Waiting for services to start (this may take 1-2 minutes)..."
sleep 30

# Step 6: Verify services
echo ""
echo "[6/7] Verifying services..."

# Check Jenkins
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8080 | grep -q "200"; then
    echo "✅ Jenkins is running at http://localhost:8080"
else
    echo "⚠️  Jenkins is not ready yet. Wait a bit more and check: http://localhost:8080"
fi

# Check SonarQube
if curl -s -o /dev/null -w "%{http_code}" http://localhost:9000 | grep -q "200"; then
    echo "✅ SonarQube is running at http://localhost:9000"
else
    echo "⚠️  SonarQube is not ready yet. Wait a bit more and check: http://localhost:9000"
fi

# Step 7: Display information
echo ""
echo "========================================="
echo "  Setup Complete!"
echo "========================================="
echo ""
echo "Services running:"
echo "  - Jenkins:     http://localhost:8080"
echo "  - SonarQube:   http://localhost:9000"
echo ""
echo "Credentials:"
echo "  - Jenkins:     admin / admin123"
echo "  - SonarQube:   admin / admin"
echo ""
echo "Next steps:"
echo "  1. Access Jenkins at http://localhost:8080"
echo "  2. Complete initial setup if needed"
echo "  3. Create pipeline job (if not exists)"
echo "  4. Push code to trigger pipeline"
echo ""
echo "To stop: docker compose down"
echo "To start: docker compose up -d"
echo ""
