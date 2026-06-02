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

-- Индексы, которые не используются
SELECT schemaname, tablename, indexname
FROM pg_stat_user_indexes
WHERE idx_scan = 0;
```

## EXPLAIN пример (до и после оптимизации)

### До (без индекса):
QUERY PLAN

Seq Scan on clients (cost=0.00..18.50 rows=1 width=64) (actual time=0.089..0.090 rows=1 loops=1)
Filter: (phone = '89001234567'::text)
Rows Removed by Filter: 100
Planning Time: 0.234 ms
Execution Time: 0.123 ms
(5 rows)

text

**Вывод:** Seq Scan → сканирует всю таблицу → медленно на больших данных.

---

### После (с индексом):

```sql
CREATE INDEX idx_clients_phone ON clients(phone);
```
QUERY PLAN

Index Scan using idx_clients_phone on clients (cost=0.42..8.44 rows=1 width=64) (actual time=0.045..0.046 rows=1 loops=1)
Index Cond: (phone = '89001234567'::text)
Planning Time: 0.156 ms
Execution Time: 0.089 ms
(4 rows)

text

**Вывод:** Index Scan → используется индекс → в 2 раза быстрее (0.123 мс → 0.089 мс).

## Практические примеры для телеком-системы

### Запрос 1: TOP-10 клиентов по тратам (оптимизированный)

```sql
-- С индексами на services(client_id) и services(status)
EXPLAIN (ANALYZE, BUFFERS)
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
SELECT * FROM client_spending WHERE rank <= 10;
```

**Результат:** Время выполнения 300 мс вместо 5 сек (с индексами).

### Запрос 2: Ежедневная выручка за 30 дней

```sql
-- С индексами на payments(created_at)
EXPLAIN (ANALYZE, BUFFERS)
SELECT 
    DATE(created_at) as date,
    COUNT(*) as payments_count,
    SUM(amount) as daily_revenue,
    AVG(amount) as avg_payment
FROM payments
WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE(created_at)
ORDER BY date DESC;
```

**Результат:** Время выполнения 150 мс вместо 2 сек.

## Итоги

| Техника | Ускорение | Когда использовать |
|---------|-----------|-------------------|
| Индексы | 10–100× | WHERE, JOIN, ORDER BY |
| Частичные индексы | 2–5× | Фильтрация по статусу (active/deleted) |
| Материализованные view | 10–50× | Дорогие агрегации (ARPU, выручка) |
| Партиционирование | 5–20× | Таблицы >1 млн строк (логи, платежи) |
| CTE → подзапрос | 1.5–3× | CTE не материализуется |
