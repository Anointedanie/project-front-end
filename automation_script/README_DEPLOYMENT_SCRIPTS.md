# Kubernetes Deployment Scripts - Quick Reference

## 📦 What Was Created

Four Python scripts and documentation for automated Kubernetes deployment:

### 1. **check_prerequisites.py** ✅
Pre-flight check script that validates everything before deployment.

**Usage:**
```bash
./check_prerequisites.py
```

**Checks:**
- ✓ Python 3.6+ installed
- ✓ kubectl installed and working
- ✓ Kubernetes cluster connection
- ✓ cert-manager installed
- ✓ All required YAML files exist
- ✓ Current namespace state

**When to use:** Run this BEFORE deploying to catch issues early.

---

### 2. **deploy_frontend.py** 🚀
Main deployment automation script.

**Usage:**
```bash
./deploy_frontend.py
```

**What it does:**
1. Checks if namespace `ecommerce-frontend-ns` exists (exits if yes)
2. Creates namespace using `kubectl apply -f deployment/namespace.yaml`
3. Checks for secret `ecommerce-frontend-tls-secret` and deletes if exists
4. Checks for ClusterIssuer `letsencrypt-prod` and creates if missing
5. Creates certificate using `kubectl apply -f deployment/certificate.yaml`
6. Deploys: deployment.yaml, service.yaml, frontend-ingress.yaml
7. Gets and displays ingress endpoints

**Features:**
- ✅ Colorful output with progress indicators
- ✅ Automatic error detection
- ✅ Helpful error messages
- ✅ Step-by-step execution
- ✅ Waits for ingress to get IP/hostname

---

### 3. **destroy_frontend.py** 🗑️
Cleanup script that safely removes all deployed resources.

**Usage:**
```bash
# Non-interactive (default) - auto-approves
./destroy_frontend.py

# Delete ClusterIssuer too
./destroy_frontend.py --delete-issuer

# Interactive mode (requires confirmation)
./destroy_frontend.py --interactive
```

**What it does:**
1. Checks if namespace `ecommerce-frontend-ns` exists
2. Shows all resources that will be deleted
3. Deletes namespace (removes deployment, service, ingress, certificate, secrets)
4. Waits for namespace deletion to complete
5. Optionally deletes ClusterIssuer with `--delete-issuer` flag

**Features:**
- ✅ **Non-interactive by default** - Perfect for CI/CD
- ✅ Optional interactive mode with `--interactive`
- ✅ Shows resource count before deletion
- ✅ Handles ClusterIssuer separately (shared resource)
- ✅ Waits for complete deletion
- ✅ Provides verification commands

**When to use:** When you need to clean up everything and redeploy from scratch.

---

### 4. **Documentation**

| File | Purpose |
|------|---------|
| `QUICK_DEPLOY.md` | 3-step quick start guide |
| `DEPLOYMENT_AUTOMATION.md` | Complete script documentation with troubleshooting |
| `EKS_DEPLOYMENT_GUIDE.md` | Full EKS deployment guide (ECR, GitHub Actions, etc.) |

---

## 🚀 Quick Start (3 Commands)

### Step 1: Fix filename (important!)
```bash
mv deployment/frontend-ingres.yaml deployment/frontend-ingress.yaml
```

### Step 2: Check prerequisites
```bash
./check_prerequisites.py
```

### Step 3: Deploy!
```bash
./deploy_frontend.py
```

---

## 📋 Prerequisites Checklist

Before running the deployment:

- [ ] **kubectl installed** - `kubectl version --client`
- [ ] **Cluster access** - `kubectl cluster-info`
- [ ] **cert-manager installed** - `kubectl get pods -n cert-manager`
- [ ] **Ingress file renamed** - `deployment/frontend-ingress.yaml` exists
- [ ] **All YAML files present** in `deployment/` folder:
  - [ ] namespace.yaml
  - [ ] clusterissuer.yaml
  - [ ] certificate.yaml
  - [ ] deployment.yaml
  - [ ] service.yaml
  - [ ] frontend-ingress.yaml

---

## 🔧 Installation of Missing Prerequisites

### Install kubectl
```bash
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/
```

### Connect to EKS Cluster
```bash
aws eks update-kubeconfig --region us-east-1 --name ecommerce-cluster
kubectl get nodes
```

### Install cert-manager
```bash
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Wait for it to be ready
kubectl wait --for=condition=ready pod -l app=cert-manager -n cert-manager --timeout=300s
```

---

## 📊 Script Output Example

### check_prerequisites.py Output:
```
============================================================
        Pre-Deployment Prerequisites Check
============================================================

System Requirements:
✓ Python 3.6+                             v3.10.12
✓ kubectl                                 Client Version: v1.28.0

Kubernetes Cluster:
✓ Kubernetes cluster connection
  Current context: arn:aws:eks:us-east-1:123456789:cluster/ecommerce-cluster

cert-manager (for SSL certificates):
✓ cert-manager namespace
✓ cert-manager pods running

Deployment Files:
✓ Namespace config                        deployment/namespace.yaml
✓ ClusterIssuer config                    deployment/clusterissuer.yaml
✓ Certificate config                      deployment/certificate.yaml
✓ Deployment config                       deployment/deployment.yaml
✓ Service config                          deployment/service.yaml
✓ Ingress config                          deployment/frontend-ingress.yaml

Current State:
✗ ecommerce-frontend-ns namespace         Does not exist (ready for deployment)

============================================================
                    Summary
============================================================

✓ All checks passed! Ready to deploy.

Run deployment with: ./deploy_frontend.py
```

### deploy_frontend.py Output:
```
======================================================================
  E-COMMERCE FRONTEND DEPLOYMENT AUTOMATION
======================================================================

[STEP 1] Checking if namespace 'ecommerce-frontend-ns' exists...
ℹ Namespace 'ecommerce-frontend-ns' does not exist

[STEP 2] Creating namespace 'ecommerce-frontend-ns'...
✓ Applied deployment/namespace.yaml

[STEP 3] Checking if secret 'ecommerce-frontend-tls-secret' exists...
ℹ Secret 'ecommerce-frontend-tls-secret' does not exist (this is expected)

[STEP 4] Checking if ClusterIssuer 'letsencrypt-prod' exists...
✓ Applied deployment/clusterissuer.yaml

[STEP 5] Creating Let's Encrypt certificate...
✓ Applied deployment/certificate.yaml

[STEP 6] Deploying application resources...
✓ Applied deployment/deployment.yaml
✓ Applied deployment/service.yaml
✓ Applied deployment/frontend-ingress.yaml

[STEP 7] Retrieving ingress endpoints...
✓ Ingress configured with the following hosts:
  → https://frontend.yourdomain.com

======================================================================
  DEPLOYMENT COMPLETED SUCCESSFULLY! 🎉
======================================================================

Access your application at:
  https://frontend.yourdomain.com
```

---

## 🔄 Common Workflows

### Initial Deployment
```bash
# 1. Check everything is ready
./check_prerequisites.py

# 2. Deploy
./deploy_frontend.py

# 3. Verify
kubectl get all -n ecommerce-frontend-ns
kubectl get certificate -n ecommerce-frontend-ns
```

### Update Deployment (Code Changes)
```bash
# Option 1: Just update the deployment (if only code changed)
kubectl apply -f deployment/deployment.yaml
kubectl rollout restart deployment/ecommerce-frontend -n ecommerce-frontend-ns

# Option 2: Full redeploy (nuclear option)
kubectl delete namespace ecommerce-frontend-ns
./deploy_frontend.py
```

### Check Status After Deployment
```bash
# View all resources
kubectl get all -n ecommerce-frontend-ns

# Check pods
kubectl get pods -n ecommerce-frontend-ns

# View logs
kubectl logs -f deployment/ecommerce-frontend -n ecommerce-frontend-ns

# Check SSL certificate
kubectl get certificate -n ecommerce-frontend-ns
kubectl describe certificate -n ecommerce-frontend-ns

# Get ingress URL
kubectl get ingress -n ecommerce-frontend-ns
```

---

## ⚠️ Important Notes

### 1. Namespace Protection
The deployment script **will exit immediately** if `ecommerce-frontend-ns` namespace already exists. This prevents accidental redeployment.

To redeploy:
```bash
kubectl delete namespace ecommerce-frontend-ns
./deploy_frontend.py
```

### 2. Filename Issue
Your ingress file is named `frontend-ingres.yaml` (missing 's'). The script expects `frontend-ingress.yaml`.

**Fix it:**
```bash
mv deployment/frontend-ingres.yaml deployment/frontend-ingress.yaml
```

### 3. SSL Certificate Timing
Let's Encrypt SSL certificates can take **2-5 minutes** to be issued. Be patient!

Check status:
```bash
kubectl describe certificate -n ecommerce-frontend-ns
```

### 4. DNS Configuration
Make sure your domain (configured in ingress) points to the LoadBalancer IP/hostname:

```bash
# Get LoadBalancer address
kubectl get ingress ecommerce-frontend-ingress -n ecommerce-frontend-ns

# Check DNS
dig frontend.yourdomain.com
```

---

## 🐛 Troubleshooting Quick Reference

| Issue | Quick Fix |
|-------|-----------|
| `kubectl not found` | Install kubectl (see prerequisites) |
| `Cannot connect to cluster` | `aws eks update-kubeconfig --region us-east-1 --name ecommerce-cluster` |
| `cert-manager not found` | Install cert-manager (see prerequisites) |
| `Pods not starting` | `kubectl describe pod <pod-name> -n ecommerce-frontend-ns` |
| `Certificate not issued` | Check DNS, wait 5 mins, check cert-manager logs |
| `Ingress no IP` | Wait 2-3 mins, check AWS LB controller logs |
| `404 errors` | Check ingress rules, verify service endpoints |

---

## 📚 Documentation Structure

```
.
├── check_prerequisites.py          ← Pre-flight validation script
├── deploy_frontend.py              ← Main deployment automation
├── QUICK_DEPLOY.md                 ← 3-step quick start
├── DEPLOYMENT_AUTOMATION.md        ← Complete script documentation
├── EKS_DEPLOYMENT_GUIDE.md         ← Full EKS setup guide
└── deployment/
    ├── namespace.yaml              ← Namespace config
    ├── clusterissuer.yaml          ← Let's Encrypt issuer
    ├── certificate.yaml            ← SSL certificate request
    ├── deployment.yaml             ← App deployment
    ├── service.yaml                ← Kubernetes service
    └── frontend-ingress.yaml       ← Ingress (rename from frontend-ingres.yaml!)
```

---

## 🎯 Recommended Workflow

### First Time Setup
1. Read `QUICK_DEPLOY.md`
2. Run `./check_prerequisites.py`
3. Fix any issues
4. Run `./deploy_frontend.py`
5. Wait for SSL certificate (2-5 minutes)
6. Access your app!

### Daily Development
1. Make code changes
2. Build new Docker image
3. Push to ECR
4. Update image tag in `deployment/deployment.yaml`
5. `kubectl apply -f deployment/deployment.yaml`
6. `kubectl rollout status deployment/ecommerce-frontend -n ecommerce-frontend-ns`

### Complete Redeployment
1. `kubectl delete namespace ecommerce-frontend-ns`
2. Wait for deletion: `kubectl get namespace ecommerce-frontend-ns`
3. `./deploy_frontend.py`

---

## 💡 Pro Tips

1. **Always run prerequisites check first** - Saves time debugging
2. **Use kubectl port-forward for testing** - `kubectl port-forward -n ecommerce-frontend-ns deployment/ecommerce-frontend 8080:80`
3. **Watch pod status during deployment** - `kubectl get pods -n ecommerce-frontend-ns -w`
4. **Check events if things fail** - `kubectl get events -n ecommerce-frontend-ns --sort-by='.lastTimestamp'`
5. **Use stern for better log viewing** - `stern ecommerce-frontend -n ecommerce-frontend-ns` (if installed)

---

## 🆘 Need Help?

1. Check `DEPLOYMENT_AUTOMATION.md` for detailed troubleshooting
2. Check `EKS_DEPLOYMENT_GUIDE.md` for EKS-specific issues
3. Run `./check_prerequisites.py` to diagnose setup issues
4. Check pod logs: `kubectl logs -f deployment/ecommerce-frontend -n ecommerce-frontend-ns`
5. Check events: `kubectl get events -n ecommerce-frontend-ns`

---

**Happy Deploying! 🚀**
