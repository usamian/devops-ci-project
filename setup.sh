#!/bin/bash
# ============================================
# Atlas-AI CI/CD Pipeline - Setup Script
# Purpose: Start all services automatically
# ============================================

echo "=========================================="
echo "  Starting Atlas-AI CI/CD Pipeline"
echo "=========================================="
echo ""

# Step 1: Go to project folder
echo "[1/4] Going to project folder..."
cd "$(dirname "$0")"
echo "✅ Current folder: $(pwd)"

# Step 2: Stop old containers if running
echo ""
echo "[2/4] Stopping old containers..."
docker compose down 2>/dev/null || true
echo "✅ Old containers stopped"

# Step 3: Start services
echo ""
echo "[3/4] Starting services..."
docker compose up -d
echo "✅ Services started"

# Step 4: Wait
echo ""
echo "[4/4] Waiting for services to start..."
sleep 30

# Show status
echo ""
echo "=========================================="
echo "  Status Check"
echo "=========================================="
echo ""

# Check Jenkins
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8080 | grep -q "200"; then
    echo "✅ Jenkins is running at http://localhost:8080"
else
    echo "⏳ Jenkins is starting... Please wait 1-2 minutes"
    echo "   Then open: http://localhost:8080"
fi

# Check SonarQube
if curl -s -o /dev/null -w "%{http_code}" http://localhost:9000 | grep -q "200"; then
    echo "✅ SonarQube is running at http://localhost:9000"
else
    echo "⏳ SonarQube is starting... Please wait 1-2 minutes"
    echo "   Then open: http://localhost:9000"
fi

# Show credentials
echo ""
echo "=========================================="
echo "  Login Credentials"
echo "=========================================="
echo "Jenkins:"
echo "  URL:      http://localhost:8080"
echo "  Username: admin"
echo "  Password: admin123"
echo ""
echo "SonarQube:"
echo "  URL:      http://localhost:9000"
echo "  Username: admin"
echo "  Password: admin"
echo ""
echo "=========================================="
echo "  Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Open browser and go to http://localhost:8080"
echo "  2. Login with: admin / admin123"
echo "  3. Create pipeline job if not exists"
echo "  4. Start coding!"
echo ""
echo "To stop: docker compose down"
echo "To start again: ./setup.sh"
echo ""
