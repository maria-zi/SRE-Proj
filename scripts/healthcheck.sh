#!/bin/bash

echo "=== Telecom System Health Check ==="

echo -e "\nCPU/Memory:"
docker stats --no-stream | grep telecom

echo -e "\nRunning containers:"
docker ps --filter "name=telecom"

echo -e "\nLogs (last 20 lines):"
docker logs telecom-system-app-1 --tail 20

echo -e "\nAPI Response:"
curl -s http://localhost:8000/health | python3 -m json.tool

echo -e "\nDatabase connection:"
docker exec telecom-system-db-1 psql -U telecom -d telecom -c "SELECT count(*) as clients FROM clients;"

echo -e "\nHealth check completed"
