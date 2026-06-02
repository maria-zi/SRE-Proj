#!/bin/bash

echo "=== Telecom System Health Check ==="

echo -e "\nCPU/Memory:" # CPU/Memory статистика контейнеров
docker stats --no-stream | grep telecom  # --no-stream = показать один раз (не обновлять постоянно)

echo -e "\nRunning containers:" # Запущенные контейнеры
docker ps --filter "name=telecom"

echo -e "\nLogs (last 20 lines):"  # Логи (последние 20 строк)
docker logs telecom-system-app-1 --tail 20

echo -e "\nAPI Response:"  # Ответ API
curl -s http://localhost:8000/health | python3 -m json.tool  # -s = silently (не показывать прогресс)  python3 -m json.tool = pretty-print JSON
 
echo -e "\nDatabase connection:" # Проверка подключения к БД
docker exec telecom-system-db-1 psql -U telecom -d telecom -c "SELECT count(*) as clients FROM clients;"

echo -e "\nHealth check completed"
