from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text, func
import redis
import json

from models import Client, Service, Payment
from database import get_db, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Telecom Client Management System", version="1.0.0")

redis_client = redis.Redis(host="redis", port=6379, decode_responses=True)

@app.post("/clients")
def create_client(name: str, phone: str, db: Session = Depends(get_db)):
    client = Client(name=name, phone=phone)
    db.add(client)
    db.commit()
    db.refresh(client)
    redis_client.delete("clients:all")
    return client

@app.post("/clients/{client_id}/services")
def add_service(client_id: int, name: str, price: float, db: Session = Depends(get_db)):
    service = Service(client_id=client_id, name=name, price=price)
    db.add(service)
    db.commit()
    db.refresh(service)
    redis_client.delete(f"client:{client_id}")
    redis_client.delete("clients:all")
    return service

@app.get("/clients")
def get_clients(db: Session = Depends(get_db)):
    cached = redis_client.get("clients:all")
    if cached:
        return json.loads(cached)
    clients = db.query(Client).all()
    result = [{"id": c.id, "name": c.name, "phone": c.phone} for c in clients]
    redis_client.setex("clients:all", 300, json.dumps(result))
    return result

@app.get("/clients/{client_id}")
def get_client(client_id: int, db: Session = Depends(get_db)):
    cached = redis_client.get(f"client:{client_id}")
    if cached:
        return json.loads(cached)
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    services = db.query(Service).filter(Service.client_id == client_id).all()
    total_paid = db.query(func.sum(Payment.amount)).filter(Payment.client_id == client_id).scalar() or 0
    total_services = sum(s.price for s in services if s.status == "active")
    debt = total_services - total_paid
    result = {
        "id": client.id,
        "name": client.name,
        "phone": client.phone,
        "services": [{"name": s.name, "price": s.price} for s in services],
        "total_paid": total_paid,
        "debt": round(debt, 2)
    }
    redis_client.setex(f"client:{client_id}", 300, json.dumps(result))
    return result

@app.get("/reports/top-clients")
def get_top_clients(limit: int = 10, db: Session = Depends(get_db)):
    query = text("""
        WITH client_spending AS (
            SELECT 
                c.id, c.name, c.phone,
                SUM(s.price) as total_spending,
                COUNT(s.id) as service_count,
                ROW_NUMBER() OVER (ORDER BY SUM(s.price) DESC) as rank
            FROM clients c
            JOIN services s ON c.id = s.client_id
            WHERE s.status = 'active'
            GROUP BY c.id, c.name, c.phone
        )
        SELECT * FROM client_spending WHERE rank <= :limit ORDER BY total_spending DESC
    """)
    result = db.execute(query, {"limit": limit})
    return [{"rank": row[5], "id": row[0], "name": row[1], "phone": row[2], "total_spending": float(row[3]), "service_count": row[4]} for row in result]

@app.get("/reports/daily-revenue")
def get_daily_revenue(db: Session = Depends(get_db)):
    query = text("""
        SELECT DATE(created_at) as date, COUNT(*) as payments_count, 
               SUM(amount) as daily_revenue, AVG(amount) as avg_payment
        FROM payments WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
        GROUP BY DATE(created_at) ORDER BY date DESC
    """)
    result = db.execute(query)
    return [{"date": str(row[0]), "payments_count": row[1], "daily_revenue": float(row[2]) if row[2] else 0, "avg_payment": float(row[3]) if row[3] else 0} for row in result]

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "telecom-api"}
