#!/bin/bash
set -e

echo "Deploying Telecom System with Helm..."

if ! command -v helm &> /dev/null; then
    echo "Helm not found. Installing Helm..."
    curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
fi

if ! command -v kubectl &> /dev/null; then
    echo "kubectl not found. Install minikube/k3s first."
    exit 1
fi

# Добавляем Helm repo
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

# Создаём namespace
kubectl create namespace telecom --dry-run=client -o yaml | kubectl apply -f -

# Деплоим через Helm
echo "Installing Helm chart..."
helm upgrade --install telecom ./helm/telecom-chart \
  --namespace telecom \
  --values ./helm/telecom-chart/values.yaml

# Ждём запуска
echo "Waiting for pods to be ready..."
kubectl wait --for=condition=ready pod --selector=app=telecom-api -n telecom --timeout=120s

# Проверяем
echo "checking deployment..."
kubectl get pods -n telecom
kubectl get svc -n telecom
kubectl get hpa -n telecom

echo "Helm deployment completed!"
echo "API: kubectl port-forward svc/telecom-api 8000:80 -n telecom"
