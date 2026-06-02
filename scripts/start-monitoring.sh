#!/bin/bash
set -e

echo "Starting Monitoring Stack (Prometheus + Grafana)..."

# Проверяем, что docker-compose установлен
if ! command -v docker-compose &> /dev/null; then
    echo "docker-compose not found. Installing..."
    sudo apt-get update
    sudo apt-get install -y docker-compose
fi

# Запускаем monitoring stack
echo "Starting monitoring services..."
docker-compose -f docker-compose.monitoring.yml up -d

# Ждём запуска
sleep 5

echo "Monitoring Stack started!"
echo ""
echo "Доступ к сервисам:"
echo "  • Prometheus:    http://localhost:9090"
echo "  • Grafana:       http://localhost:3000 (login: admin / telecompass)"
echo "  • PostgreSQL:    http://localhost:9187/metrics"
echo "  • Node Exporter: http://localhost:9100/metrics"
echo "  • cAdvisor:      http://localhost:8081"
echo ""
echo "Следующие шаги:"
echo "  1. Открой Grafana: http://localhost:3000"
echo "  2. Добавь дашборды (Import) или используй готовые:"
echo "     - Prometheus: Dashboard 8999"
echo "     - Node Exporter: Dashboard 1860"
echo "     - cAdvisor: Dashboard 193"
echo "  3. Создай алерты для важеных метрик (CPU > 80%, Memory > 90%)"
echo ""
echo "тобы остановить:"
echo "  docker-compose -f docker-compose.monitoring.yml down"
