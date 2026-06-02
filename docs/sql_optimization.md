# SQL Optimization Guide

Руководство по оптимизации PostgreSQL-запросов для телеком-системы.

## Чек-лист оптимизации

### 1. EXPLAIN ANALYZE

```sql
EXPLAIN (ANALYZE, BUFFERS) 
SELECT * FROM clients WHERE phone = '89001234567';
```

**Что смотреть:**
- `Seq Scan` vs `Index Scan` → если Seq Scan на большой таблице → добавить индекс
- `actual time` → реальное время выполнения
- `rows` → сколько строк возвращено
- `cost` → плановая стоимость запроса

### 2. Индексы

```sql
-- Индекс для быстрого поиска по телефону
CREATE INDEX idx_clients_phone ON clients(phone);

-- Составной индекс для JOIN + фильтрации
CREATE INDEX idx_services_client_active ON services(client_id) WHERE status='active';

-- Частичный индекс для активных услуг (уменьшает размер индекса)
```

### 3. CTE и материализация

**Проблема:** PostgreSQL материализует CTE (в старых версиях), что может быть медленно.

**Решение:**

```sql
-- Переписать в подзапрос (часто быстрее)
SELECT * FROM (
    SELECT c.id, c.name, SUM(s.price) as total
    FROM clients c
    JOIN services s ON c.id = s.client_id
    GROUP BY c.id
) WHERE total > 1000;

-- Или использовать MATERIALIZED явно (PostgreSQL 12+)
WITH client_spending AS MATERIALIZED (
    SELECT ...
)
```

### 4. Оконные функции

```sql
-- TOP-10 клиентов с оконной функцией
WITH client_spending AS (
    SELECT 
        c.id, c.name,
        SUM(s.price) as total_spending,
        ROW_NUMBER() OVER (ORDER BY SUM(s.price) DESC) as rank
    FROM clients c
    JOIN services s ON c.id = s.client_id
    WHERE s.status = 'active'
    GROUP BY c.id, c.name
)
SELECT * FROM client_spending WHERE rank <= 10;
```

### 5. Материализованные представления

```sql
-- Для дорогих агрегаций (ARPU, выручка за месяц)
CREATE VIEW daily_revenue_view AS
SELECT 
    DATE(created_at) as date,
    SUM(amount) as daily_revenue
FROM payments
GROUP BY DATE(created_at);

-- Или материализованное (кэшируется)
CREATE MATERIALIZED VIEW mv_daily_revenue AS
SELECT ...
WITH DATA;

-- Обновлять по расписанию
REFRESH MATERIALIZED VIEW mv_daily_revenue;
```

### 6. Партиционирование

```sql
-- Для таблиц логов/платежей (по времени)
CREATE TABLE payments (
    id SERIAL,
    amount DECIMAL,
    created_at TIMESTAMP
) PARTITION BY RANGE (created_at);

-- Создаём партиции на год вперёд
CREATE TABLE payments_2025_q1 PARTITION OF payments
    FOR VALUES FROM ('2025-01-01') TO ('2025-04-01');
```

### 7. Мониторинг

```sql
-- Горячие запросы (требует pg_stat_statements)
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
```

## EXPLAIN пример
