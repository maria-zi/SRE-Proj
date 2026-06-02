#!/bin/bash
set -e      # exit on error

echo "Deploying Telecom System to Kubernetes..."

if ! command -v kubectl &> /dev/null; then       # Проверяем, установлен ли kubectl
    echo "kubectl not found. Install minikube/k3s first."
    exit 1
fi

kubectl create namespace telecom --dry-run=client -o yaml | kubectl apply -f -   # Создаём namespace если нет (--dry-run=client = не отправлять в K8s, -o yaml = вывести YAML)


# Применяем манифесты по порядку (сначала Secret, потом ConfigMap, потом PVC, потом Deployment и т.д.)

echo "Applying Kubernetes manifests..."
kubectl apply -f k8s/secret.yaml -n telecom
kubectl apply -f k8s/configmap.yaml -n telecom
kubectl apply -f k8s/pvc.yaml -n telecom
kubectl apply -f k8s/deployment.yaml -n telecom
kubectl apply -f k8s/service.yaml -n telecom
kubectl apply -f k8s/hpa.yaml -n telecom
kubectl apply -f k8s/networkpolicy.yaml -n telecom
kubectl apply -f k8s/ingress.yaml -n telecom


# Ждем до 120 секунд, пока поды не станут ready


echo "Waiting for pods to be ready..."
kubectl wait --for=condition=ready pod --selector=app=telecom-api -n telecom --timeout=120s


# Проверяем деплой
echo "checking deployment..."
kubectl get pods -n telecom
kubectl get hpa -n telecom
kubectl get services -n telecom


# Показываем детали HPA
echo "HPA status:"
kubectl describe hpa telecom-api-hpa -n telecom

echo "Telecom System deployed to Kubernetes!"
echo "API: kubectl port-forward svc/telecom-api 8000:80 -n telecom"
