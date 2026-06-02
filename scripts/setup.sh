#!/bin/bash
set -e    # set -e = выходить при первой же ошибке (exit on error)

echo "Installing Telecom System..."         # Выводим сообщение

if ! command -v docker &> /dev/null; then     # Проверяем, установлен ли docker
    echo "Installing Docker..."                  # Если нет — устанавливаем
    sudo apt-get update
    sudo apt-get install -y docker.io docker-compose
fi

echo "Starting services..."         # Запускаем сервисы через docker-compose
docker-compose up -d                # -d = detached (в фоне)
 
sleep 5                           # Ждем 5 секунд для запуска сервисов

echo "Checking health..."            # Проверяем health endpoint
curl -f http://localhost:8000/health || curl -f http://localhost/health      # -f = fail silently (возвращать код ошибки если HTTP != 200)
                                                                              # || = если первый не удался, попробуй второй (через nginx)
echo "Telecom System is running!"
echo "API: http://localhost:8000"
echo "Through Nginx: http://localhost"
