# SQLBot Kubernetes Deployment

This directory contains Kubernetes manifests for deploying SQLBot.

## Prerequisites

- Kubernetes cluster (v1.24+)
- kubectl configured to access your cluster
- Ingress controller (nginx-ingress recommended)
- Storage class available for PVCs

## Quick Start

```bash
# Make deploy script executable
chmod +x deploy.sh

# Deploy SQLBot
./deploy.sh sqlbot apply

# Check status
./deploy.sh sqlbot status

# Delete deployment
./deploy.sh sqlbot delete
```

## Manual Deployment

```bash
# Create namespace
kubectl apply -f namespace.yaml

# Apply secrets and configmaps
kubectl apply -f secrets.yaml
kubectl apply -f configmap.yaml

# Create PVCs
kubectl apply -f pvc.yaml

# Deploy PostgreSQL
kubectl apply -f postgres.yaml

# Deploy Redis
kubectl apply -f redis.yaml

# Deploy SQLBot
kubectl apply -f sqlbot.yaml

# Apply Ingress
kubectl apply -f ingress.yaml

# Apply HPA
kubectl apply -f hpa.yaml
```

## Configuration

### Secrets (secrets.yaml)

Update the following secrets for production:
- `POSTGRES_PASSWORD`: PostgreSQL password
- `SECRET_KEY`: JWT secret key (generate a new one!)
- `DEFAULT_PWD`: Default user password

### ConfigMap (configmap.yaml)

Update the following for your environment:
- `BACKEND_CORS_ORIGINS`: Allowed origins
- Embedding model settings

### Ingress (ingress.yaml)

Update the following:
- `host`: Your domain name
- TLS configuration for HTTPS

### Storage (pvc.yaml)

Update the following:
- `storageClassName`: Your cluster's storage class
- Storage sizes based on your needs

## Files

| File | Description |
|------|-------------|
| `namespace.yaml` | SQLBot namespace |
| `configmap.yaml` | Application configuration |
| `secrets.yaml` | Sensitive configuration |
| `pvc.yaml` | Persistent volume claims |
| `postgres.yaml` | PostgreSQL with pgvector |
| `redis.yaml` | Redis cache |
| `sqlbot.yaml` | SQLBot application deployment |
| `ingress.yaml` | Ingress rules |
| `hpa.yaml` | Horizontal Pod Autoscaler |
| `deploy.sh` | Deployment script |

## Monitoring

```bash
# View logs
kubectl logs -f deployment/sqlbot -n sqlbot

# Describe pod
kubectl describe pod -l app.kubernetes.io/name=sqlbot -n sqlbot

# Port forward for local access
kubectl port-forward svc/sqlbot-service 8000:8000 -n sqlbot
```

## Scaling

The HPA will automatically scale based on CPU and memory usage. You can also manually scale:

```bash
kubectl scale deployment sqlbot --replicas=5 -n sqlbot
```

## GPU Support

For GPU-accelerated embedding models, add the following to the SQLBot deployment:

```yaml
resources:
  limits:
    nvidia.com/gpu: 1
nodeSelector:
  accelerator: nvidia-gpu
```

## Troubleshooting

1. **Pod stuck in Pending**: Check PVC status and storage class availability
2. **Pod CrashLoopBackOff**: Check logs for startup errors
3. **Database connection failed**: Ensure PostgreSQL pod is ready
4. **Ingress not working**: Verify ingress controller is installed and running
