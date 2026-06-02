from sqlalchemy import create_engine # Импортируем create_engine для создания соединения с БД
from sqlalchemy.ext.declarative import declarative_base # Импортируем declarative_base для создания моделей (ORM)
from sqlalchemy.orm import sessionmaker # Импортируем sessionmaker для создания сессий БД

DATABASE_URL = "postgresql://пользователь:пароль@хост:5432/бдtelecom" # URL подключения к PostgreSQL: пользователь:пароль@хост:порт/база_данных  db = postgresql-сервис в docker-compose/k8s, telecom = база и пользователь


engine = create_engine(DATABASE_URL)# Создаём движок БД (соединение с PostgreSQL) echo=True включит логирование SQL-запросов (для отладки)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)# Создаём фабрику сессий (используется для get_db)
# autocommit=False — не автокоммитить транзакции
# autoflush=False — не автофлешить перед запросами
# bind=engine — привязать к созданному движку
Base = declarative_base() # Создаём базовый класс для всех моделей БД (ORM)


def get_db(): # Функция-генератор для получения сессии БД (используется в Depends FastAPI)
    db = SessionLocal() # Создаём новую сессию БД
    try:
        yield db # Возвращаем сессию (yield = вернуть и продолжить работу)
    finally:
        db.close() # Всегда закрываем сессию после завершения запроса (даже если ошибка)
