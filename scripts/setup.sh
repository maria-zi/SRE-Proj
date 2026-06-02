#!/bin/bash
set -e

echo "Installing Telecom System..."

if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    sudo apt-get update
    sudo apt-get install -y docker.io docker-compose
fi

echo "Starting services..."
docker-compose up -d

sleep 5

echo "Checking health..."
curl -f http://localhost:8000/health || curl -f http://localhost/health

echo "Telecom System is running!"
echo "API: http://localhost:8000"
echo "Through Nginx: http://localhost"
