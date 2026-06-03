#!/bin/bash
set -e    # set -e = выходить при первой же ошибке (exit on error)

echo " Installing Telecom System..."

# Проверка, что мы в папке telecom-system
if [ ! -f "docker-compose.yml" ]; then
    echo " docker-compose.yml not found!"
    echo "Убедись, что ты в папке telecom-system:"
    echo "   cd telecom-system"
    exit 1
fi

echo "Находим docker-compose.yml"

# Шаг 2: Проверка и установка Docker
if ! command -v docker &> /dev/null; then
    echo "Docker не найден. Устанавливаем..."
    sudo apt-get update
    sudo apt-get install -y docker.io docker-compose
else
    echo " Docker установлен ($(docker --version))"
fi

# Шаг 3: Проверка, что Docker запущен
if ! docker ps &> /dev/null; then
    echo "Docker не запущен. Запусти Docker Desktop сначала."
    exit 1
fi

echo " Docker запущен"

# Шаг 4: Проверка docker-compose
if ! command -v docker-compose &> /dev/null; then
    echo "docker-compose не найден"
    exit 1
fi

echo "docker-compose установлен ($(docker-compose --version))"

# Шаг 5: Сборка образов (обновляем код перед запуском)
echo "Сборка Docker образов..."
docker-compose build --no-cache app

# Шаг 6: Запуск контейнеров
echo "Запуск контейнеров..."
docker-compose up -d

# Шаг 7: Ждём запуска сервисов
echo "Ожидание запуска сервисов (PostgreSQL может запуститься не сразу)..."
sleep 10

# Шаг 8: Проверка health endpoint (до 5 попыток)
echo "Проверка здоровья API..."
for i in {1..5}; do
    if curl -f http://localhost:8000/health &> /dev/null; then
        echo " API здоров (попытка $i/5)"
        break
    fi
    
    if [ $i -eq 5 ]; then
        echo " API не здоров после 5 попыток"
        echo " Логи приложения:"
        docker-compose logs app
        exit 1
    fi
    
    echo "Ожидание... (попытка $i/5)"
    sleep 2
done

# ============================================
# Шаг 9: Проверка через Nginx
# ============================================
if curl -f http://localhost/health &> /dev/null; then
    echo " Nginx работает (через http://localhost)"
else
    echo "Nginx может не работать (но API работает)"
fi

# ============================================
# Шаг 10: Вывод результата
# ============================================
echo ""
echo "Telecom System запущен!"
echo ""
echo " Запущенные контейнеры:"
docker ps --filter "name=telecom-system"
echo ""
echo "API Swagger UI: http://localhost:8000/docs"
echo "Через Nginx: http://localhost"
echo ""
echo " Полезные команды:"
echo "  docker-compose logs -f      # Логи всех контейнеров"
echo "  docker-compose logs -f app  # Логи только API"
echo "  docker-compose down         # Остановить все контейнеры"
echo "  docker-compose down -v      # Остановить + удалить БД"
