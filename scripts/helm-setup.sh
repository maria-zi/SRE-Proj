#!/bin/bash
set -e

echo "Deploying Telecom System with Helm..."

if ! command -v helm &> /dev/null; then  # Проверяем helm
    echo "Helm not found. Installing Helm..."
    curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash  # Скрипт установки Helm (официальный)
fi

if ! command -v kubectl &> /dev/null; then  # Проверяем kubectl
    echo "kubectl not found. Install minikube/k3s first."
    exit 1
fi

# Добавляем Helm repo (Bitnami — популярный репозиторий чартов)
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update


if ! kubectl get namespace telecom &> /dev/null; then  #проверка сущест ли неймспейс если нет создает
    echo "Creating namespace 'telecom'..."
    kubectl create namespace telecom
else
    echo "Namespace 'telecom' already exists"
fi

# Деплоим через Helm
echo "Installing Helm chart..."
helm upgrade --install telecom ./helm/telecom-chart \  # upgrade --install = если существует → обновить, если нет → установить
  --namespace telecom \  
  --values ./helm/telecom-chart/values.yaml   # --values = файл значений (переопределяет defaults в чарте)

# Ждём запускподов
echo "Waiting for pods to be ready..."
kubectl wait --for=condition=ready pod --selector=app=telecom-api -n telecom --timeout=120s

# Проверяем
echo "checking deployment..."
kubectl get pods -n telecom
kubectl get svc -n telecom
kubectl get hpa -n telecom

echo "Helm deployment completed!"
echo "API: kubectl port-forward svc/telecom-api 8000:80 -n telecom"
