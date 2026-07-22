#!/bin/bash
# =====================================================
#  ATLAS-AI CI/CD PIPELINE - SETUP SCRIPT
#  This script starts all services automatically
# =====================================================

# ----- STEP 1: Print welcome message -----
echo "=========================================="
echo "  Starting Atlas-AI CI/CD Pipeline"
echo "=========================================="
echo ""

# ----- STEP 2: Go to project folder automatically -----
# "$0" means the script's own file path
# dirname extracts just the folder name
# This ensures script works no matter where you run it from
echo "[1/3] Going to project folder..."
cd "$(dirname "$0")"
echo "✅ Current folder: $(pwd)"

# ----- STEP 3: Stop old containers (if running) -----
# docker compose down = stop and remove containers
# 2>/dev/null hides error messages if no containers exist
# || true means "even if this command fails, continue anyway"
echo ""
echo "[2/3] Stopping old containers..."
docker compose down 2>/dev/null || true
echo "✅ Old containers stopped"

# ----- STEP 4: Start services -----
# docker compose up -d = start containers in background (detached mode)
echo ""
echo "[3/3] Starting services (Jenkins, SonarQube, PostgreSQL)..."
docker compose up -d
echo "✅ Services started"

# ----- STEP 5: Wait for services -----
# Services take time to initialize, so we wait
echo ""
echo "⏳ Waiting for services to start (30 seconds)..."
sleep 30

# ----- STEP 6: Check if Jenkins is running -----
echo ""
echo "=========================================="
echo "  Checking Services"
echo "=========================================="
echo ""

# curl = command to fetch webpage
# -s = silent mode (no progress bar)
# -o /dev/null = don't show the webpage content
# -w "%{http_code}" = show only the HTTP status code (200 = OK)
# grep -q "200" = check if status code contains "200"
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8080 | grep -q "200"; then
    echo "✅ Jenkins is READY at http://localhost:8080"
else
    echo "⏳ Jenkins is starting... Please wait 1-2 minutes"
    echo "   Then open: http://localhost:8080"
fi

# ----- STEP 7: Check if SonarQube is running -----
if curl -s -o /dev/null -w "%{http_code}" http://localhost:9000 | grep -q "200"; then
    echo "✅ SonarQube is READY at http://localhost:9000"
else
    echo "⏳ SonarQube is starting... Please wait 1-2 minutes"
    echo "   Then open: http://localhost:9000"
fi

# ----- STEP 8: Show login details -----
echo ""
echo "=========================================="
echo "  Login Credentials"
echo "=========================================="
echo ""
echo "JENKINS:"
echo "  URL:      http://localhost:8080"
echo "  Username: admin"
echo "  Password: admin123"
echo ""
echo "SONARQUBE:"
echo "  URL:      http://localhost:9000"
echo "  Username: admin"
echo "  Password: admin"
echo ""

# ----- STEP 9: Show next steps -----
echo "=========================================="
echo "  Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Open browser: http://localhost:8080"
echo "  2. Login with: admin / admin123"
echo "  3. Create pipeline job"
echo "  4. Start building!"
echo ""
echo "Commands you can use:"
echo "  ./setup.sh          = Start services"
echo "  docker compose down = Stop services"
echo ""
