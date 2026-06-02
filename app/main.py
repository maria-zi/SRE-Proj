from fastapi import FastAPI, Depends, HTTPException # Импортируем FastAPI приложение и Depends для DI (внедрение зависимостей)
from sqlalchemy.orm import Session # Импортируем Session для работы с БД через SQLAlchemy
from sqlalchemy import text, func # Импортируем text для сырых SQL-запросов и func для агрегатных функций (SUM, COUNT, AVG)
import redis # Импортируем redis клиент для кэширования
import json # Импортируем json для сериализации кэша
import time  # Добавлено для метрик


from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST # Импортируем метрики Prometheus 
from starlette.responses import Response


from models import Client, Service, Payment # Импортируем модели из models.py

from database import get_db, engine # Импортируем get_db и engine из database.py


Base.metadata.create_all(bind=engine) # Создаём все таблицы в БД (если их нет) при запуске приложения




app = FastAPI(title="Telecom Client Management System", version="1.0.0") # Создаём FastAPI приложение title = название API (показывается в Swagger UI) version = версия API



redis_client = redis.Redis(host="redis", port=6379, decode_responses=True) # Создаём подключение к Redis (хост = имя сервиса в docker-compose/k8s) decode_responses=True = возвращать строки вместо байтов

# === МЕТРИКИ PROMETHEUS  ===

REQUEST_COUNT = Counter( # Счётчик запросов (растёт с каждым запросом)
    'api_requests_total',           # имя метрики
    'Total API requests',           # описание
    ['method', 'endpoint', 'status']  # лейблы (группировка)
)


REQUEST_DURATION = Histogram( # Дительность запросов (p50, p95, p99)
    'api_request_duration_seconds',  # имя метрики
    'API request duration',          # описание
    ['method', 'endpoint']           # лейблы
)


# === MIDDLEWARE ДЛЯ СБОРА МЕТРИК  ===
@app.middleware("http")
async def collect_metrics(request):
    # Начало запроса (записываем время)
    start_time = time.time()
    
    # Продолжаем обработку запроса (вызываем следующий middleware или роут)
    from starlette.types import CallNext
    response = await call_next(request)
    
    # Конец запроса (вычисляем длительность)
    duration = time.time() - start_time
    
    # Записываем метрику REQUEST_COUNT (увеличиваем счётчик)
    REQUEST_COUNT.labels(
        method=request.method,           # GET, POST, ...
        endpoint=request.url.path,       # /clients, /reports/top-clients, ...
        status=response.status_code      # 200, 404, 500, ...
    ).inc()  # inc() = увеличить на 1
    
    # Записываем метрику REQUEST_DURATION (записываем длительность)
    REQUEST_DURATION.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)  # observe() = записать значение
    
    return response


# POST /clients — создать нового клиента
@app.post("/clients")
def create_client(name: str, phone: str, db: Session = Depends(get_db)):
    # Создаём экземпляр клиента
    client = Client(name=name, phone=phone)
    # Добавляем в сессию БД
    db.add(client)
    # Коммитим транзакцию (сохраняем в БД)
    db.commit()
    # refresh = обновить объект из БД (получить сгенерированный id)
    db.refresh(client)
    # Очищаем кэш списка клиентов (потому что добавили новый)
    redis_client.delete("clients:all")
    # Возвращаем созданного клиента
    return client

# POST /clients/{client_id}/services — добавить услугу клиенту
@app.post("/clients/{client_id}/services")
def add_service(client_id: int, name: str, price: float, db: Session = Depends(get_db)):
    # Создаём услугу с client_id = foreign key
    service = Service(client_id=client_id, name=name, price=price)
    # Добавляем в БД
    db.add(service)
    # Коммитим
    db.commit()
    # refresh = получить service.id
    db.refresh(service)
    # Очищаем кэш конкретного клиента
    redis_client.delete(f"client:{client_id}")
    # Очищаем кэш всех клиентов
    redis_client.delete("clients:all")
    # Возвращаем услугу
    return service

# GET /clients — получить всех клиентов с кэшированием
@app.get("/clients")
def get_clients(db: Session = Depends(get_db)):
    # Пробуем взять из кэша Redis
    cached = redis_client.get("clients:all")
    # Если есть в кэше → парсим JSON и возвращаем
    if cached:
        return json.loads(cached)
    # Иначе делаем запрос к БД
    clients = db.query(Client).all()
    # Превращаем ORM-объекты в dict для JSON
    result = [{"id": c.id, "name": c.name, "phone": c.phone} for c in clients]
    # Кэшируем на 300 секунд (5 минут)
    redis_client.setex("clients:all", 300, json.dumps(result))
    # Возвращаем результат
    return result

# GET /clients/{client_id} — получить клиента с долгом и услугами
@app.get("/clients/{client_id}")
def get_client(client_id: int, db: Session = Depends(get_db)):
    # Пробуем из кэша
    cached = redis_client.get(f"client:{client_id}")
    # Если есть → возвращаем
    if cached:
        return json.loads(cached)
    # Иначе ищем в БД
    client = db.query(Client).filter(Client.id == client_id).first()
    # Если не найден → ошибка 404
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    # Получаем все услуги клиента
    services = db.query(Service).filter(Service.client_id == client_id).all()
    # Сумма всех платежей клиента (scalar = одно значение, или 0 если NULL)
    total_paid = db.query(func.sum(Payment.amount)).filter(Payment.client_id == client_id).scalar() or 0
    # Сумма активных услуг
    total_services = sum(s.price for s in services if s.status == "active")
    # Долг = сумма услуг - сумма платежей
    debt = total_services - total_paid
    # Формируем ответ
    result = {
        "id": client.id,
        "name": client.name,
        "phone": client.phone,
        "services": [{"name": s.name, "price": s.price} for s in services],
        "total_paid": total_paid,
        "debt": round(debt, 2)  # округляем до 2 знаков
    }
    # Кэшируем на 300 секунд
    redis_client.setex(f"client:{client_id}", 300, json.dumps(result))
    # Возвращаем
    return result

# GET /reports/top-clients — TOP-10 клиентов по тратам (с CTE + оконной функцией)
@app.get("/reports/top-clients")
def get_top_clients(limit: int = 10, db: Session = Depends(get_db)):
    # Сырой SQL с CTE (Common Table Expression) и ROW_NUMBER() оконной функцией
    query = text("""
        WITH client_spending AS (
            SELECT 
                c.id, c.name, c.phone,
                SUM(s.price) as total_spending,  -- сумма всех услуг
                COUNT(s.id) as service_count,    -- количество услуг
                ROW_NUMBER() OVER (ORDER BY SUM(s.price) DESC) as rank  -- рейтинг по тратам
            FROM clients c
            JOIN services s ON c.id = s.client_id  -- JOIN с услугами
            WHERE s.status = 'active'  -- только активные услуги
            GROUP BY c.id, c.name, c.phone  -- группировка по клиенту
        )
        SELECT * FROM client_spending WHERE rank <= :limit ORDER BY total_spending DESC
    """)
    # Выполняем запрос с параметром :limit (защита от SQL injection)
    result = db.execute(query, {"limit": limit})
    # Превращаем строки результата в dict
    return [{"rank": row[5], "id": row[0], "name": row[1], "phone": row[2], "total_spending": float(row[3]), "service_count": row[4]} for row in result]

# GET /reports/daily-revenue — ежедневная выручка за 30 дней
@app.get("/reports/daily-revenue")
def get_daily_revenue(db: Session = Depends(get_db)):
    # SQL с DATE(), COUNT(), SUM(), AVG() и INTERVAL
    query = text("""
        SELECT DATE(created_at) as date, COUNT(*) as payments_count, 
               SUM(amount) as daily_revenue, AVG(amount) as avg_payment
        FROM payments 
        WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'  -- последние 30 дней
        GROUP BY DATE(created_at)  -- группировка по дате
        ORDER BY date DESC  -- сначала самые свежие
    """)
    # Выполняем
    result = db.execute(query)
    # Превращаем в dict (с проверкой NULL на 0)
    return [{"date": str(row[0]), "payments_count": row[1], "daily_revenue": float(row[2]) if row[2] else 0, "avg_payment": float(row[3]) if row[3] else 0} for row in result]

# GET /health — health check для Kubernetes (liveness/readiness probes)
@app.get("/health")
def health_check():
    # Возвращаем статус API
    return {"status": "healthy", "service": "telecom-api"}

# === ENDPOINT ДЛЯ METRICS (НОВОЕ) ===
@app.get("/metrics")
async def metrics():
    # Возвращаем метрики Prometheus в формате text/plain
    return Response(
        content=generate_latest(),  # генерируем метрики в текстовом формате
        headers={"Content-Type": CONTENT_TYPE_LATEST}  # Content-Type: text/plain; version=0.0.4
    )
