from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text # Импортируем типы колонок БД (integer, string, float, datetime, foreign key, text)
from sqlalchemy.orm import relationship # Импортируем relationship для связей между таблицами (ORM relationships)
from datetime import datetime # Импортируем datetime для автовременной метки created_at
from database import Base # Импортируем Base из database.py (базовый класс для всех моделей)

class Client(Base): # Модель таблицы clients (клиенты)
    __tablename__ = "clients" # Имя таблицы в БД
    
    id = Column(Integer, primary_key=True, index=True) # id — первичный ключ, индекс, автогенерация
    name = Column(String(100), nullable=False)   # name — строка до 100 символов, обязательное поле (не может быть NULL)
    phone = Column(String(20), unique=True, nullable=False, index=True)  # phone — строка до 20 символов, уникальный, обязательный, с индексом (для быстрого поиска)
    created_at = Column(DateTime, default=datetime.utcnow)  # created_at — дата/время создания записи, по умолчанию текущее время UTC
    
    services = relationship("Service", back_populates="client") # Связь с таблицей services (один клиент → много услуг), back_populates = обратная связь
    payments = relationship("Payment", back_populates="client") # Связь с таблицей payments (один клиент → много платежей)


class Service(Base): # Модель таблицы services (услуги клиентов)
    __tablename__ = "services"
    
    id = Column(Integer, primary_key=True, index=True) # id — первичный ключ, индекс
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False) # client_id — внешний ключ на clients.id, обязательное поле
    name = Column(String(100), nullable=False)  # name — название услуги (например, "Интернет")
    price = Column(Float, nullable=False)   # price — цена услуги (float для дробных чисел)
    status = Column(String(20), default="active")  # status — статус услуги (active/suspended/cancelled), по умолчанию "active"
    
    client = relationship("Client", back_populates="services") # Обратная связь с Client (много услуг → один клиент)

class Payment(Base): # Модель таблицы payments (платежи клиентов)
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True) # id — первичный ключ, индекс
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False) # client_id — внешний ключ на clients.id, обязательное поле
    amount = Column(Float, nullable=False)  # amount — сумма платежа (float)
    description = Column(Text) # description — описание платежа (текст, может быть NULL)
    created_at = Column(DateTime, default=datetime.utcnow)# created_at — дата платежа, по умолчанию текущее время
    
    client = relationship("Client", back_populates="payments") # Обратная связь с Client (много платежей → один клиент)
