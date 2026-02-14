# Prerequisite Checks Guide

This document explains what each check does and the guidance provided when checks fail.

## 📋 Check Summary

| Check | What It Does | What To Do If It Fails |
|-------|--------------|------------------------|
| Python 3.6+ | Verifies Python version | Install/upgrade Python |
| kubectl | Checks kubectl is installed | Install kubectl |
| Cluster Connection | Tests connection to K8s cluster | Connect to cluster (see below) |
| cert-manager namespace | Checks if cert-manager exists | Install cert-manager (see below) |
| cert-manager pods | Verifies cert-manager pods running | Wait or check logs (see below) |
| Deployment Files | Checks all 6 YAML files exist | Ensure files in ../deployment/ |
| Namespace State | Shows if namespace already exists | Delete if redeploying |

---

## 🔍 Detailed Check Information

### 1. Python 3.6+ ✅

**What it checks:**
- Python version is 3.6 or higher

**Success output:**
```
✓ Python 3.6+                             v3.10.12
```

**Failure guidance:**
```
✗ Python 3.6+                             v2.7.18
```
Install Python 3.6+:
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip

# macOS
brew install python3

# Verify
python3 --version
```

---

### 2. kubectl ✅

**What it checks:**
- kubectl command is available
- Can get client version

**Success output:**
```
✓ kubectl                                 Client Version: v1.28.0
```

**Failure guidance:**
```
✗ kubectl                                 Not found
```
Install kubectl:
```bash
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/

# Verify
kubectl version --client
```

---

### 3. Kubernetes Cluster Connection ✅

**What it checks:**
- Can connect to Kubernetes cluster
- `kubectl cluster-info` succeeds

**Success output:**
```
✓ Kubernetes cluster connection
  Current context: arn:aws:eks:us-east-1:123456789:cluster/ecommerce-cluster
```

**Failure output:**
```
✗ Kubernetes cluster connection
  ⚠ Cannot connect to Kubernetes cluster
  For EKS: aws eks update-kubeconfig --region REGION --name CLUSTER_NAME
  For local: minikube start (or check your kubeconfig)
  Verify: kubectl config current-context
```

**What to do:**

**For AWS EKS:**
```bash
# Update kubeconfig to connect to your cluster
aws eks update-kubeconfig \
  --region us-east-1 \
  --name ecommerce-cluster

# Verify connection
kubectl cluster-info
kubectl get nodes
```

**For local development (minikube/kind):**
```bash
# Start minikube
minikube start

# Or kind
kind create cluster

# Verify
kubectl cluster-info
```

**Check current context:**
```bash
# See all contexts
kubectl config get-contexts

# See current context
kubectl config current-context

# Switch context
kubectl config use-context CONTEXT_NAME
```

---

### 4. cert-manager Namespace ✅

**What it checks:**
- cert-manager namespace exists
- Required for SSL certificate automation

**Success output:**
```
✓ cert-manager namespace
```

**Failure output:**
```
✗ cert-manager namespace
  ⚠ cert-manager not found (required for SSL certificates)
  Install: kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
  Wait for ready: kubectl wait --for=condition=ready pod -l app=cert-manager -n cert-manager --timeout=300s
```

**What to do:**

Install cert-manager (required for Let's Encrypt SSL certificates):
```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Wait for it to be ready (takes 1-2 minutes)
kubectl wait --for=condition=ready pod \
  -l app=cert-manager \
  -n cert-manager \
  --timeout=300s

# Verify installation
kubectl get pods -n cert-manager
```

Expected output after installation:
```
NAME                                      READY   STATUS    RESTARTS   AGE
cert-manager-7d8f9c5b6d-abc12            1/1     Running   0          2m
cert-manager-cainjector-6d7c8f9b-xyz34   1/1     Running   0          2m
cert-manager-webhook-5c9d7f6b8d-def56    1/1     Running   0          2m
```

---

### 5. cert-manager Pods Running ✅

**What it checks:**
- All cert-manager pods have status "Running"
- cert-manager is operational

**Success output:**
```
✓ cert-manager pods running
```

**Failure output (pods not running):**
```
✗ cert-manager pods running
  ⚠ cert-manager pods are not all running
  Check status: kubectl get pods -n cert-manager
  View logs: kubectl logs -n cert-manager deployment/cert-manager
  Wait: kubectl wait --for=condition=ready pod -l app=cert-manager -n cert-manager --timeout=300s
```

**Failure output (can't get status):**
```
✗ cert-manager pods running
  ⚠ Cannot get cert-manager pod status
  Check: kubectl get pods -n cert-manager
```

**What to do:**

Check pod status:
```bash
kubectl get pods -n cert-manager
```

If pods are not running:
```bash
# Check events
kubectl get events -n cert-manager --sort-by='.lastTimestamp'

# Check specific pod
kubectl describe pod POD_NAME -n cert-manager

# View logs
kubectl logs -n cert-manager deployment/cert-manager
kubectl logs -n cert-manager deployment/cert-manager-webhook
kubectl logs -n cert-manager deployment/cert-manager-cainjector

# Wait for pods to be ready
kubectl wait --for=condition=ready pod \
  -l app=cert-manager \
  -n cert-manager \
  --timeout=300s
```

Common issues:
- **ImagePullBackOff:** Check internet connectivity
- **CrashLoopBackOff:** Check logs for error messages
- **Pending:** Check node resources (CPU/memory)

---

### 6. Deployment Files ✅

**What it checks:**
- All 6 required YAML files exist in `../deployment/` folder:
  1. namespace.yaml
  2. clusterissuer.yaml
  3. certificate.yaml
  4. deployment.yaml
  5. service.yaml
  6. frontend-ingress.yaml

**Success output:**
```
✓ Namespace config                        ../deployment/namespace.yaml
✓ ClusterIssuer config                    ../deployment/clusterissuer.yaml
✓ Certificate config                      ../deployment/certificate.yaml
✓ Deployment config                       ../deployment/deployment.yaml
✓ Service config                          ../deployment/service.yaml
✓ Ingress config                          ../deployment/frontend-ingress.yaml
```

**Failure output:**
```
✗ Namespace config                        ../deployment/namespace.yaml
  ⚠ Missing: ../deployment/namespace.yaml
  Ensure all YAML files are in the ../deployment/ folder
```

**What to do:**

Check if deployment folder exists:
```bash
ls -la ../deployment/
```

Ensure all files are present:
```bash
cd ../deployment
ls -1 *.yaml
```

Expected files:
- namespace.yaml
- clusterissuer.yaml
- certificate.yaml
- deployment.yaml
- service.yaml
- frontend-ingress.yaml (NOT frontend-ingres.yaml!)

If files are missing, they need to be created based on your infrastructure requirements.

---

### 7. Namespace State (Informational) ℹ️

**What it checks:**
- Whether `ecommerce-frontend-ns` namespace already exists
- This is informational, not a pass/fail check

**If namespace doesn't exist (ready to deploy):**
```
✗ ecommerce-frontend-ns namespace         Does not exist (ready for deployment)
```
This is good! You can proceed with deployment.

**If namespace exists:**
```
✓ ecommerce-frontend-ns namespace         Already exists
  ⚠ Deployment script will exit if namespace exists
  To redeploy: kubectl delete namespace ecommerce-frontend-ns
```

**What to do if redeploying:**

Delete the namespace:
```bash
# Delete namespace (removes all resources)
kubectl delete namespace ecommerce-frontend-ns

# Wait for deletion to complete (may take 30-60 seconds)
kubectl get namespace ecommerce-frontend-ns
# Should return: Error from server (NotFound)

# Now you can run deployment again
./deploy_frontend.py
```

---

## ✅ All Checks Passed

When all checks pass, you'll see:
```
============================================================
                    Summary
============================================================

✓ All checks passed! Ready to deploy.

Run deployment with: ./deploy_frontend.py
```

---

## ❌ Some Checks Failed

When checks fail, you'll see:
```
============================================================
                    Summary
============================================================

✗ 3 check(s) failed.

Please fix the issues above before deploying.
```

Follow the guidance provided for each failed check above.

---

## 🚀 Quick Troubleshooting Workflow

1. **Run the prerequisite checker:**
   ```bash
   cd automation_script
   ./check_prerequisites.py
   ```

2. **For each failed check:**
   - Read the guidance provided in the output
   - Run the suggested commands
   - Re-run the checker to verify the fix

3. **Once all checks pass:**
   ```bash
   ./deploy_frontend.py
   ```

---

## 📚 Additional Resources

- **AWS EKS:** [EKS Getting Started](https://docs.aws.amazon.com/eks/latest/userguide/getting-started.html)
- **kubectl:** [kubectl Installation](https://kubernetes.io/docs/tasks/tools/)
- **cert-manager:** [cert-manager Documentation](https://cert-manager.io/docs/)
- **Kubernetes Contexts:** [Configure Access to Multiple Clusters](https://kubernetes.io/docs/tasks/access-application-cluster/configure-access-multiple-clusters/)

---

**Need more help?** Check the full documentation in `DEPLOYMENT_AUTOMATION.md`.
