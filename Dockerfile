FROM python:3.11-slim # Базовый образ — Python 3.11 slim (уменьшенный)

WORKDIR /app # Рабочая директория внутри контейнера

COPY app/requirements.txt . # Копируем requirements.txt в контейнер
RUN pip install --no-cache-dir -r requirements.txt # Устанавливаем Python-пакеты (–no-cache-dir = уменьшить размер образа)

COPY app/ . # Копируем весь код приложения из app/ в контейнер

EXPOSE 8000  # Порт, который контейнер "экспонирует" (документация)

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]  # Команда запуска (uvicorn = ASGI-сервер, main:app = файл main.py, переменная app)
