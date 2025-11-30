#!/bin/bash

# SQLBot Kubernetes Deployment Script
# Usage: ./deploy.sh [namespace] [action]
# Actions: apply, delete, status

NAMESPACE=${1:-sqlbot}
ACTION=${2:-apply}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_kubectl() {
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed. Please install kubectl first."
        exit 1
    fi
}

apply_resources() {
    log_info "Deploying SQLBot to namespace: $NAMESPACE"
    
    # Create namespace first
    log_info "Creating namespace..."
    kubectl apply -f "$SCRIPT_DIR/namespace.yaml"
    
    # Apply secrets and configmaps
    log_info "Applying secrets and configmaps..."
    kubectl apply -f "$SCRIPT_DIR/secrets.yaml"
    kubectl apply -f "$SCRIPT_DIR/configmap.yaml"
    
    # Apply PVCs
    log_info "Creating persistent volume claims..."
    kubectl apply -f "$SCRIPT_DIR/pvc.yaml"
    
    # Deploy PostgreSQL
    log_info "Deploying PostgreSQL..."
    kubectl apply -f "$SCRIPT_DIR/postgres.yaml"
    
    # Wait for PostgreSQL to be ready
    log_info "Waiting for PostgreSQL to be ready..."
    kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=postgres -n $NAMESPACE --timeout=120s
    
    # Deploy Redis
    log_info "Deploying Redis..."
    kubectl apply -f "$SCRIPT_DIR/redis.yaml"
    
    # Wait for Redis to be ready
    log_info "Waiting for Redis to be ready..."
    kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=redis -n $NAMESPACE --timeout=60s
    
    # Deploy SQLBot application
    log_info "Deploying SQLBot application..."
    kubectl apply -f "$SCRIPT_DIR/sqlbot.yaml"
    
    # Apply Ingress
    log_info "Applying Ingress rules..."
    kubectl apply -f "$SCRIPT_DIR/ingress.yaml"
    
    # Apply HPA
    log_info "Applying HorizontalPodAutoscaler..."
    kubectl apply -f "$SCRIPT_DIR/hpa.yaml"
    
    # Wait for SQLBot to be ready
    log_info "Waiting for SQLBot to be ready..."
    kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=sqlbot -n $NAMESPACE --timeout=180s
    
    log_info "Deployment completed successfully!"
    show_status
}

delete_resources() {
    log_warn "Deleting SQLBot deployment from namespace: $NAMESPACE"
    
    read -p "Are you sure you want to delete all resources? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Deletion cancelled."
        exit 0
    fi
    
    kubectl delete -f "$SCRIPT_DIR/hpa.yaml" --ignore-not-found
    kubectl delete -f "$SCRIPT_DIR/ingress.yaml" --ignore-not-found
    kubectl delete -f "$SCRIPT_DIR/sqlbot.yaml" --ignore-not-found
    kubectl delete -f "$SCRIPT_DIR/redis.yaml" --ignore-not-found
    kubectl delete -f "$SCRIPT_DIR/postgres.yaml" --ignore-not-found
    
    log_warn "PVCs are not deleted to preserve data. Delete manually if needed:"
    log_warn "  kubectl delete -f $SCRIPT_DIR/pvc.yaml"
    
    log_info "Deletion completed."
}

show_status() {
    log_info "SQLBot deployment status:"
    echo ""
    echo "=== Pods ==="
    kubectl get pods -n $NAMESPACE -o wide
    echo ""
    echo "=== Services ==="
    kubectl get services -n $NAMESPACE
    echo ""
    echo "=== Ingress ==="
    kubectl get ingress -n $NAMESPACE
    echo ""
    echo "=== HPA ==="
    kubectl get hpa -n $NAMESPACE
    echo ""
    echo "=== PVCs ==="
    kubectl get pvc -n $NAMESPACE
}

# Main script
check_kubectl

case $ACTION in
    apply)
        apply_resources
        ;;
    delete)
        delete_resources
        ;;
    status)
        show_status
        ;;
    *)
        echo "Usage: $0 [namespace] [apply|delete|status]"
        echo "  namespace: Kubernetes namespace (default: sqlbot)"
        echo "  action: apply (default), delete, or status"
        exit 1
        ;;
esac
