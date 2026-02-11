# Kubernetes Manifests for EKS Deployment

This directory contains Kubernetes manifest files for deploying the e-commerce frontend to Amazon EKS.

## Files

- `namespace.yaml` - Creates the production namespace
- `deployment.yaml` - Defines the frontend deployment
- `service.yaml` - Exposes the frontend via AWS LoadBalancer
- `hpa.yaml` - Configures horizontal pod autoscaling

## Quick Start

### 1. Update deployment.yaml

Edit `deployment.yaml` and replace the image URI with your ECR repository:

```yaml
image: YOUR_AWS_ACCOUNT_ID.dkr.ecr.YOUR_REGION.amazonaws.com/ecommerce-frontend:latest
```

Get your AWS account ID:
```bash
aws sts get-caller-identity --query Account --output text
```

### 2. Apply manifests

```bash
# Apply all manifests
kubectl apply -f k8s/

# Or apply individually
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/hpa.yaml
```

### 3. Verify deployment

```bash
# Check all resources
kubectl get all -n production

# Get LoadBalancer URL
kubectl get service ecommerce-frontend -n production

# Check pod logs
kubectl logs -f deployment/ecommerce-frontend -n production
```

### 4. Access the application

```bash
# Get the LoadBalancer URL
FRONTEND_URL=$(kubectl get service ecommerce-frontend -n production -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

# Open in browser
echo "Frontend URL: http://$FRONTEND_URL"
```

## Configuration

### Scaling

To manually scale the deployment:

```bash
# Scale to 3 replicas
kubectl scale deployment ecommerce-frontend --replicas=3 -n production

# Or edit deployment
kubectl edit deployment ecommerce-frontend -n production
```

The HPA will automatically scale between 2-10 replicas based on CPU/memory usage.

### Resource Limits

Current settings:
- **Requests**: 100m CPU, 128Mi memory (minimum guaranteed)
- **Limits**: 200m CPU, 256Mi memory (maximum allowed)

Adjust in `deployment.yaml` based on your needs.

### Health Checks

- **Liveness Probe**: Restarts pod if it fails (checks port 80)
- **Readiness Probe**: Removes pod from service if not ready

## Troubleshooting

### Pods not starting

```bash
# Check pod status
kubectl get pods -n production

# Describe pod for events
kubectl describe pod POD_NAME -n production

# View pod logs
kubectl logs POD_NAME -n production
```

### LoadBalancer not created

```bash
# Check service events
kubectl describe service ecommerce-frontend -n production

# Verify AWS Load Balancer
aws elbv2 describe-load-balancers --query "LoadBalancers[?contains(LoadBalancerName, 'ecommerce')].LoadBalancerArn"
```

### Image pull errors

Ensure EKS nodes have permission to pull from ECR:

```bash
# Find node IAM role
aws eks describe-nodegroup \
    --cluster-name ecommerce-cluster \
    --nodegroup-name standard-workers \
    --query "nodegroup.nodeRole" --output text

# Attach ECR policy
aws iam attach-role-policy \
    --role-name ROLE_NAME \
    --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly
```

## Clean Up

To remove all resources:

```bash
# Delete all resources in the namespace
kubectl delete all --all -n production

# Delete the namespace
kubectl delete namespace production
```

## See Also

- [EKS_DEPLOYMENT_GUIDE.md](../EKS_DEPLOYMENT_GUIDE.md) - Complete deployment guide
- [AWS EKS Documentation](https://docs.aws.amazon.com/eks/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
