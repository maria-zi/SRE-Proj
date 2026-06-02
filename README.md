# 📱 Telecom Client Management System

High-load телеком-система для управления клиентами, услугами и платежами с полным CI/CD, Kubernetes-деплоем, Helm-чартами и мониторингом (Prometheus + Grafana).

---

## 📋 Оглавление

- [О проекте](#-о-проекте)
- [Архитектура системы](#-архитектура-системы)
- [Стек технологий](#-стек-технологий)
- [Структура репозитория](#-структура-репозитория)
- [API Endpoints](#-api-endpoints)
- [Как запустить](#-как-запустить)
  - [Локально (Docker Compose)](#-локально-docker-compose)
  - [С мониторингом (Prometheus + Grafana)](#-с-мониторингом-prometheus--grafana)
  - [В Kubernetes (Minikube)](#-в-kubernetes-minikube)
  - [Через Helm](#-через-helm)
- [Где посмотреть результаты](#-где-посмотреть-результаты)
- [SQL Оптимизация](#-sql-оптимизация)
- [Troubleshooting](#-troubleshooting)

---

##  О проекте

Проект реализует **полноценную телеком-систему** с:

- ✅ **REST API** на FastAPI (Python)
- ✅ **PostgreSQL** база данных с сложными SQL-запросами (CTE, оконные функции, агрегации)
- ✅ **Redis** кэширование для high-load (кэш ответов API на 5 минут)
- ✅ **Nginx** реверс-прокси с балансировкой
- ✅ **Docker** контейнеризация всего стека
- ✅ **Kubernetes** деплой (Deployments, Services, HPA, NetworkPolicy, Ingress)
- ✅ **Helm Charts** (Umbrella chart с зависимостями PostgreSQL + Redis)
- ✅ **CI/CD** GitHub Actions (тесты, линтинг, автоматический деплой)
- ✅ **Monitoring** Prometheus + Grafana (метрики API, CPU, память, PostgreSQL)
- ✅ **Security** NetworkPolicy, Secret, Resource limits
- ✅ **Documentation** Swagger UI, SQL optimization guide

**Use case:** Управление клиентами телеком-компании, их услугами, платежами, расчёт долга, TOP-10 клиентов по тратам, ежедневная выручка.

---

##  Архитектура системы

| Компонент | Порт | Описание | Функции |
|-----------|------|----------|---------|
| **USER (Браузер)** | - | Пользовательский интерфейс | - Запрашивает API через браузер |
| **Nginx (Reverse Proxy)** | 80 | Входная точка, балансировка | - Проксирует запросы → FastAPI<br>- Распределяет нагрузку между 3 репликами<br>- Static files, SSL termination |
| **FastAPI App** | 8000 | REST API (3 реплики, HPA 3-10) | - `/clients` — CRUD клиентов<br>- `/reports/top-clients` — TOP-10 (CTE + Window)<br>- `/reports/daily-revenue` — выручка за 30 дней<br>- `/metrics` — Prometheus metrics<br>- Redis кэш (5 минут) |
| **PostgreSQL** | 5432 | Основная база данных | - `clients` — клиенты<br>- `services` — услуги<br>- `payments` — платежи<br>- Индексы, CTE, оконные функции |
| **Redis** | 6379 | Кэш ответов API | - Кэширует ответы на 5 минут<br>- Ускоряет GET /clients (5 мин кэш) |
| **Prometheus** | 9090 | Сбор метрик | - Метрики API (requests, latency)<br>- CPU, память container<br>- PostgreSQL metrics<br>- Node/cAdvisor metrics |
| **Grafana** | 3000 | Визуализация и алерты | - Дашборды (CPU, память, запросы)<br>- Алерты (CPU > 80%, Memory > 90%)<br>- Импортированные дашборды (1860, 193, 9628) |

### Как работает (по шагам)

| Шаг | Компонент | Действие |
|-----|-----------|----------|
| 1 | **Пользователь** | Делает запрос к API (например, `GET /clients`) |
| 2 | **Nginx** | Проксирует запрос → FastAPI (балансировка между 3 репликами) |
| 3 | **FastAPI** | Проверяет **Redis кэш** → если есть → возвращает кэш (5 мин) |
| 4 | **FastAPI** | Если нет в кэше → делает запрос → **PostgreSQL** |
| 5 | **PostgreSQL** | Выполняет запрос (с индексами, CTE, оконными функциями) |
| 6 | **FastAPI** | Кэширует ответ в **Redis** на 5 минут → возвращает пользователю |
| 7 | **Prometheus** | Собирает метрики (CPU, память, запросы/сек, latency) каждые 15 сек |
| 8 | **Grafana** | Визуализирует метрики (дашборды) + отправляет алерты |

---

##  Стек технологий

| Категория | Технология | Версия | Назначение |
|-----------|------------|--------|------------|
| **Backend** | FastAPI | 0.109.0 | REST API фреймворк |
| **Python** | Python | 3.11 | Язык программирования |
| **ORM** | SQLAlchemy | 2.0.25 | Работа с БД (Python → SQL) |
| **Database** | PostgreSQL | 15 | Основная база данных |
| **Cache** | Redis | 7 (alpine) | Кэширование ответов API |
| **Proxy** | Nginx | alpine | Reverse proxy, балансировка |
| **Container** | Docker | 24 | Контейнеризация |
| **Orchestration** | Kubernetes | 1.28 | Оркестрация контейнеров |
| **Package Manager** | Helm | 3.12 | Управление K8s манифестами |
| **CI/CD** | GitHub Actions | latest | Автоматизация тестов и деплоя |
| **Monitoring** | Prometheus | 2.45 | Сбор метрик |
| **Visualization** | Grafana | 10.0 | Дашборды и алерты |
| **Exporter** | postgres-exporter | 0.14 | Метрики PostgreSQL |
| **Monitoring** | cAdvisor | 0.47 | Метрики Docker контейнеров |

---

## 📁 Структура репозитория

```text
telecom-system/
├── README.md                           # Этот файл
├── docker-compose.yml                  # Запуск локально (API + DB + Redis + Nginx)
├── docker-compose.monitoring.yml       # Запуск мониторинга (Prometheus + Grafana)
├── Dockerfile                          # Образ FastAPI приложения
├── nginx.conf                          # Конфиг Nginx (reverse proxy)
│
├── app/                                # FastAPI приложение
│   ├── main.py                         # API endpoints + Prometheus metrics
│   ├── models.py                       # SQLAlchemy модели (clients, services, payments)
│   ├── database.py                     # Подключение к PostgreSQL
│   └── requirements.txt                # Python зависимости
│
├── k8s/                                # Kubernetes манифесты (без Helm)
│   ├── deployment.yaml                 # Deployments (api, postgres, redis)
│   ├── service.yaml                    # Services (ClusterIP)
│   ├── hpa.yaml                        # HorizontalPodAutoscaler (3-10 реплик)
│   ├── secret.yaml                     # Secrets (пароли БД)
│   ├── configmap.yaml                  # ConfigMap (REDIS_HOST, log-level)
│   ├── networkpolicy.yaml              # NetworkPolicy (запрет трафика между подами)
│   ├── ingress.yaml                    # Ingress (внешний роутинг)
│   └── pvc.yaml                        # PersistentVolumeClaim (хранилище для PostgreSQL)
│
├── helm/                               # Helm Charts
│   └── telecom-chart/
│       ├── Chart.yaml                  # Описание чарта + зависимости (PostgreSQL + Redis)
│       ├── values.yaml                 # Значения по умолчанию (replicas, resources, HPA)
│       └── templates/
│           ├── deployment.yaml         # Helm шаблон Deployment
│           ├── service.yaml            # Helm шаблон Service
│           └── hpa.yaml                # Helm шаблон HPA
│
├── scripts/                            # Скрипты для запуска
│   ├── setup.sh                        # Запуск локально (docker-compose)
│   ├── k8s-setup.sh                    # Запуск в Kubernetes (kubectl apply)
│   ├── helm-setup.sh                   # Запуск через Helm (helm upgrade --install)
│   ├── start-monitoring.sh             # Запуск Prometheus + Grafana
│   ├── backup.sh                       # Бэкап PostgreSQL (pg_dump + gzip)
│   └── healthcheck.sh                  # Проверка здоровья (статус, логи, контейнеры)
│
├── prometheus/                         # Конфигурация Prometheus
│   └── prometheus.yml                  # Scrape configs (api, postgres, node, cadvisor)
│
├── grafana/                            # Конфигурация Grafana
│   └── provisioning/
│       └── datasources/
│           └── prometheus.yml          # Авто-подключение к Prometheus
│
├── .github/
│   └── workflows/
│       └── ci.yml                      # CI/CD pipeline (тесты → деплой)
│
└── docs/
    └── sql_optimization.md             # Руководство по оптимизации SQL (EXPLAIN, индексы, CTE)
```

---

## 🔌 API Endpoints

| Method | Endpoint | Описание | Пример |
|--------|----------|----------|--------|
| **GET** | `/health` | Проверка здоровья | `curl http://localhost:8000/health` |
| **GET** | `/docs` | Swagger UI (интерактивная документация) | `http://localhost:8000/docs` |
| **GET** | `/metrics` | Prometheus метрики | `curl http://localhost:8000/metrics` |
| **POST** | `/clients?name=Иван&phone=8900...` | Создать клиента | `curl -X POST "http://localhost:8000/clients?name=Иван&phone=89001234567"` |
| **GET** | `/clients` | Все клиенты (с кэшем 5 мин) | `curl http://localhost:8000/clients` |
| **GET** | `/clients/{id}` | Клиент с долгом и услугами | `curl http://localhost:8000/clients/1` |
| **POST** | `/clients/{id}/services?name=Интернет&price=500` | Добавить услугу | `curl -X POST "http://localhost:8000/clients/1/services?name=Интернет&price=500"` |
| **GET** | `/reports/top-clients?limit=10` | TOP-10 клиентов по тратам (CTE + Window) | `curl http://localhost:8000/reports/top-clients?limit=10` |
| **GET** | `/reports/daily-revenue` | Ежедневная выручка за 30 дней | `curl http://localhost:8000/reports/daily-revenue` |

---

## 🚀 Как запустить

### 📦 Локально (Docker Compose)

**Самый простой способ** — одна команда:

```bash
# 1. Перейди в папку проекта
cd telecom-system

# 2. Сделай скрипты исполняемыми
chmod +x scripts/*.sh

# 3. Запусти проект
./scripts/setup.sh
```

**Что делает скрипт:**

1. Проверяет, установлен ли Docker
2. Если нет — устанавливает Docker + docker-compose
3. Запускает 4 контейнера: API, PostgreSQL, Redis, Nginx
4. Проверяет health endpoint
5. Показывает URL для доступа

**Проверь, что работает:**

```bash
# Проверь контейнеры
docker ps

# Проверь API
curl http://localhost:8000/health
# Должно вернуть: {"status":"healthy","service":"telecom-api"}

# Создай тестового клиента
curl -X POST "http://localhost:8000/clients?name=Иван&phone=89001234567"

# Получи всех клиентов
curl http://localhost:8000/clients

# Открой Swagger UI
# http://localhost:8000/docs
```

---

### 📊 С мониторингом (Prometheus + Grafana)

```bash
# 1. Сначала запусти основное приложение
./scripts/setup.sh

# 2. Запусти мониторинг
./scripts/start-monitoring.sh
```

**После этого открой:**

| Сервис | URL | Login/Password |
|--------|-----|----------------|
| **API** | http://localhost:8000/docs | - |
| **Prometheus** | http://localhost:9090 | - |
| **Grafana** | http://localhost:3000 | admin / telecompass |
| **PostgreSQL Metrics** | http://localhost:9187/metrics | - |
| **Node Exporter** | http://localhost:9100/metrics | - |
| **cAdvisor** | http://localhost:8081 | - |

**В Grafana импортируй дашборды:**

1. Dashboard → Import
2. Введи ID:
   - **Node Exporter**: `1860` (CPU, память, диск)
   - **cAdvisor**: `193` (Docker контейнеры)
   - **PostgreSQL**: `9628` (DB connections, queries)
   - **Prometheus**: `8999` (сам Prometheus)

---

### ☸️ В Kubernetes (Minikube)

```bash
# 1. Установи Minikube (если нет)
# macOS:
brew install minikube

# Linux:
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube

# 2. Запусти Minikube
minikube start

# 3. Деплой в Kubernetes
cd telecom-system
./scripts/k8s-setup.sh
```

**После этого:**

```bash
# Открой API через port-forward
kubectl port-forward svc/telecom-api 8000:80 -n telecom

# Открой в браузере
http://localhost:8000/docs

# Проверь поды
kubectl get pods -n telecom

# Проверь HPA
kubectl get hpa -n telecom
kubectl describe hpa telecom-api-hpa -n telecom
```

---

### 🛠️ Через Helm

```bash
# 1. Установи Helm (если нет)
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# 2. Запусти через Helm
cd telecom-system
./scripts/helm-setup.sh
```

**Что делает скрипт:**

1. Устанавливает Helm (если нет)
2. Добавляет репозиторий Bitnami
3. Создаёт namespace `telecom`
4. Запускает Helm chart (устанавливает API + PostgreSQL + Redis)
5. Ждёт готовности подов
6. Показывает статус

---

## 👀 Где посмотреть результаты

### 1. API (Swagger UI)

**URL:** `http://localhost:8000/docs`

Там **интерактивная документация** со всеми endpoints. Можно тестировать прямо в браузере.

---

### 2. Метрики Prometheus

**URL:** `http://localhost:9090`

**Что посмотреть:**

- **Graph** → введи `api_requests_total` → увидишь рост счётчика
- **Graph** → введи `api_request_duration_seconds` → увидишь latency
- **Status** → Targets → проверить, что все scrape targets зелёные

---

### 3. Дашборды Grafana

**URL:** `http://localhost:3000`

**Login:** `admin`  
**Password:** `telecompass`

**Что посмотреть:**

1. **Home** → Dashboard → Import
2. Введи ID: `1860` (Node Exporter) → Load → Save
3. Теперь в меню дашборд **Node Exporter** — покажет CPU, память, диск, сеть

---

### 4. PostgreSQL

```bash
# Зайди в PostgreSQL
docker exec -it telecom-system-db-1 psql -U telecom -d telecom

# Покажи таблицы
\dt

# Посмотри клиентов
SELECT * FROM clients;

# Посмотри TOP-10 клиентов (тот же запрос, что в API)
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

---

### 5. Redis (кэш)

```bash
# Зайди в Redis
docker exec -it telecom-system-redis-1 redis-cli

# Покажи ключи кэша
KEYS *

# Посмотри значение кэша (например, список клиентов)
GET clients:all

# Очисти кэш
FLUSHALL
```

---

### 6. Логи контейнеров

```bash
# Логи API
docker logs telecom-system-app-1 -f

# Логи PostgreSQL
docker logs telecom-system-db-1 -f

# Логи всех контейнеров
docker-compose logs -f
```

---

### 7. Kubernetes (если деплоил в K8s)

```bash
# Поды
kubectl get pods -n telecom

# Логи пода
kubectl logs -f deployment/telecom-api -n telecom

# HPA статус
kubectl describe hpa telecom-api-hpa -n telecom

# Service
kubectl get svc -n telecom

# NetworkPolicy
kubectl get networkpolicy -n telecom
```

---

## 📈 SQL Оптимизация

Подробная инструкция в **`docs/sql_optimization.md`**:

- ✅ **EXPLAIN ANALYZE** — как читать план выполнения
- ✅ **Индексы** — когда создавать, составные, частичные
- ✅ **CTE** — проблемы материализации, как переписать в подзапрос
- ✅ **Оконные функции** — ROW_NUMBER(), RANK(), SUM() OVER()
- ✅ **Материализованные view** — кэширование дорогих агрегаций
- ✅ **Партиционирование** — для таблиц >1 млн строк
- ✅ **Мониторинг** — pg_stat_statements, горячие запросы

**Пример оптимизации:**

```sql
-- До (Seq Scan, 0.123 мс)
SELECT * FROM clients WHERE phone = '89001234567';

-- Создаём индекс
CREATE INDEX idx_clients_phone ON clients(phone);

-- После (Index Scan, 0.089 мс, в 2 раза быстрее)
EXPLAIN (ANALYZE) SELECT * FROM clients WHERE phone = '89001234567';
```

---

## 🔧 Troubleshooting

### docker-compose: command not found

```bash
sudo apt-get update
sudo apt-get install -y docker-compose
```

---

### Permission denied

```bash
sudo usermod -aG docker $USER
newgrp docker
```

---

### Ports already in use (80/8000 заняты)

```bash
# Проверь, кто использует порт
sudo lsof -i :8000
sudo lsof -i :80

# Убей процесс (замени PID)
kill -9 PID
```

---

### Контейнеры не стартуют

```bash
# Посмотри логи
docker-compose logs -f app
docker-compose logs -f db

# Перезапусти
docker-compose down
docker-compose up -d
```

---

### База данных не подключается

```bash
# Проверь, что PostgreSQL запущен
docker ps | grep postgres

# Зайди в PostgreSQL
docker exec -it telecom-system-db-1 psql -U telecom -d telecom

# Проверь таблицы
\dt
```

---

### Prometheus не видит метрики

```bash
# Проверь, что /metrics доступен
curl http://localhost:8000/metrics

# Проверь, что Prometheus скрапит
# http://localhost:9090/status → Targets → telecom-api → зелёный
```

---

### Grafana не подключается к Prometheus

```bash
# Проверь DataSource
# http://localhost:3000 → Configuration → Data Sources → Prometheus → Save & Test

# Должно быть: "Datasource is working"
```

---

