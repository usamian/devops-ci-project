#!/bin/bash

# Docker Install Script (Ubuntu/Debian)

set -e

echo "Updating packages..."
sudo apt update -y

echo "Installing Docker..."
sudo apt install -y docker.io

echo "Enabling Docker service..."
sudo systemctl enable --now docker

echo "Adding current user to docker group..."
sudo usermod -aG docker $USER

echo "Checking Docker version..."
docker --version

echo "Docker installation complete! You may need to log out and back in for group changes."