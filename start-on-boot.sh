#!/bin/bash
# ============================================
# Auto-start services after laptop restart
# ============================================

PROJECT_DIR="/home/unknown/Videos/Atlas-AI"

echo "=========================================="
echo "  Auto-Starting CI/CD Pipeline"
echo "=========================================="
echo ""

# Wait for Docker to be ready
echo "Waiting for Docker to start..."
while ! docker info &> /dev/null; do
    sleep 2
done
echo "✅ Docker is ready"

# Go to project folder
cd "$PROJECT_DIR" || exit 1

# Start services
docker compose up -d

# Wait
sleep 30

# Show status
echo ""
echo "Services started:"
docker compose ps

echo ""
echo "Jenkins: http://localhost:8080"
echo "SonarQube: http://localhost:9000"
