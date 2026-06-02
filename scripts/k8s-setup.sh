#!/bin/bash
set -e

echo "Deploying Telecom System to Kubernetes..."

if ! command -v kubectl &> /dev/null; then
    echo "kubectl not found. Install minikube/k3s first."
    exit 1
fi

kubectl create namespace telecom --dry-run=client -o yaml | kubectl apply -f -

echo "Applying Kubernetes manifests..."
kubectl apply -f k8s/secret.yaml -n telecom
kubectl apply -f k8s/configmap.yaml -n telecom
kubectl apply -f k8s/pvc.yaml -n telecom
kubectl apply -f k8s/deployment.yaml -n telecom
kubectl apply -f k8s/service.yaml -n telecom
kubectl apply -f k8s/hpa.yaml -n telecom
kubectl apply -f k8s/networkpolicy.yaml -n telecom
kubectl apply -f k8s/ingress.yaml -n telecom

echo "Waiting for pods to be ready..."
kubectl wait --for=condition=ready pod --selector=app=telecom-api -n telecom --timeout=120s

echo "checking deployment..."
kubectl get pods -n telecom
kubectl get hpa -n telecom
kubectl get services -n telecom

echo "HPA status:"
kubectl describe hpa telecom-api-hpa -n telecom

echo "Telecom System deployed to Kubernetes!"
echo "API: kubectl port-forward svc/telecom-api 8000:80 -n telecom"
