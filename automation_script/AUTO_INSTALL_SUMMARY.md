# Auto-Installation Summary

## ✅ Updated: check_prerequisites.py

The script now auto-installs **ALL** missing components needed for deployment.

---

## 🔧 Auto-Install Capabilities

### 1. **Python 3.12.3**
- **When:** Python is missing, Python 2.x, or Python < 3.6
- **Method:** Uses deadsnakes PPA
- **Time:** ~30-60 seconds

### 2. **kubectl**
- **When:** kubectl command not found
- **Method:** Downloads from official Kubernetes release
- **Time:** ~10-20 seconds

### 3. **Docker** ⭐ NEW
- **When:** Docker not installed
- **Method:** Official Docker repository for Ubuntu/Debian
- **Includes:**
  - Docker Engine
  - Docker CLI
  - containerd
  - Docker Buildx
  - Docker Compose plugin
- **Auto-starts:** Docker daemon if not running
- **Time:** ~60-90 seconds

### 4. **AWS CLI** ⭐ NEW
- **When:** AWS CLI not found
- **Method:** Official AWS CLI v2 installer
- **Time:** ~20-30 seconds

### 5. **Nginx Ingress Controller with AWS Load Balancer** ⭐ NEW
- **When:** ingress-nginx namespace doesn't exist
- **Method:** Applies deployment files in order:
  1. `../deployment/aws-load-balancer-controller-sa.yaml` (Service Account)
  2. `../deployment/aws_lb_controller.yaml` (AWS LB Controller)
  3. `../deployment/nginx-ingress-nlb.yaml` (Nginx Ingress with NLB)
- **Waits for:** Pods to be ready (up to 5 minutes)
- **Time:** ~60-120 seconds

### 6. **cert-manager**
- **When:** cert-manager namespace doesn't exist
- **Method:** Official cert-manager manifest
- **Time:** ~60-120 seconds

### 7. **EKS Cluster Connection**
- **When:** Cannot connect to Kubernetes cluster
- **Command:** `aws eks update-kubeconfig --region us-east-1 --name ecommerce-eks`
- **Time:** ~2-5 seconds

---

## 📋 Complete Check List

The script now validates and auto-installs:

### ✅ System Requirements:
- Python 3.12.3+ (auto-install)
- kubectl (auto-install)
- Docker (auto-install) ⭐ NEW
- AWS CLI (auto-install) ⭐ NEW

### ✅ AWS Configuration:
- AWS credentials (validation only)
- ECR authentication (validation only)
- ECR repository `ecommerce/frontend` (validation only)
- ECR images (informational)

### ✅ Kubernetes Cluster:
- Cluster connectivity (auto-configure EKS)
- Nginx ingress controller (auto-install) ⭐ NEW
- cert-manager (auto-install)

### ✅ Deployment Files:
- All 6 YAML files in `../deployment/` folder

---

## 🚀 Installation Order

When running on a **clean environment**, installations happen in this order:

```
1. Python 3.12.3          (~30-60s)
2. kubectl                (~10-20s)
3. Docker                 (~60-90s)
4. AWS CLI                (~20-30s)
5. Configure AWS creds    (manual - user must run: aws configure)
6. ECR authentication     (manual - user must authenticate)
7. EKS cluster config     (~2-5s)
8. Nginx Ingress          (~60-120s)
   - AWS LB Controller SA
   - AWS LB Controller
   - Nginx Ingress NLB
9. cert-manager           (~60-120s)

Total time (first run): ~4-7 minutes
```

---

## 💡 Usage Examples

### Example 1: Clean CI/CD Runner (GitHub Actions)

```yaml
- name: Setup prerequisites (auto-installs everything)
  run: |
    cd automation_script
    sudo ./check_prerequisites.py
```

**Output:**
```
✓ Python 3.12.3+                           v3.12.3
⚠ kubectl not found - installing automatically...
  Installing kubectl...
  ✓ kubectl installed successfully
✓ kubectl                                  v1.35.1

⚠ Docker not found - installing automatically...
  Installing Docker...
  ✓ Docker installed successfully
✓ Docker                                   Docker version 28.2.2

⚠ AWS CLI not found - installing automatically...
  Installing AWS CLI...
  ✓ AWS CLI installed successfully
✓ AWS CLI                                  aws-cli/2.33.17

✓ AWS credentials                          Account: 793796654438
✓ ECR authentication                       Authenticated
✓ ECR repository 'ecommerce/frontend'      793796654438.dkr.ecr...
✓ Kubernetes cluster connection

⚠ Nginx ingress controller not found - installing automatically...
  Installing Nginx Ingress Controller...
  Step 1/3: Applying AWS Load Balancer Controller Service Account...
  ✓ Service account applied
  Step 2/3: Applying AWS Load Balancer Controller...
  ✓ AWS Load Balancer Controller applied
  Step 3/3: Applying Nginx Ingress Controller with NLB...
  ✓ Nginx Ingress Controller is ready
✓ Nginx ingress controller                 Running

✓ cert-manager namespace
✓ cert-manager pods running

✓ All checks passed! Ready to deploy.
```

### Example 2: Local Machine (with some tools)

```bash
./check_prerequisites.py
```

**Output:**
```
✓ Python 3.12.3+                           v3.12.3
✓ kubectl                                  v1.35.1
✓ Docker                                   Docker version 28.2.2
✓ AWS CLI                                  aws-cli/2.33.17
✓ AWS credentials                          Account: 793796654438
✓ ECR authentication                       Authenticated
✓ ECR repository 'ecommerce/frontend'      793796654438.dkr.ecr...
✓ Kubernetes cluster connection
✓ Nginx ingress controller                 Running
✓ cert-manager namespace
✓ cert-manager pods running

✓ All checks passed! Ready to deploy.
```

---

## ⚠️ Manual Steps Required

### 1. AWS Credentials Configuration

**If you see:**
```
✗ AWS credentials                          Not configured
  ⚠ AWS credentials not configured
  Configure: aws configure
```

**Fix:**
```bash
# Option 1: Interactive configuration
aws configure

# Option 2: Environment variables
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="us-east-1"

# Option 3: GitHub Actions (use secrets)
- uses: aws-actions/configure-aws-credentials@v4
  with:
    aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
    aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
    aws-region: us-east-1
```

### 2. ECR Authentication

**If you see:**
```
✗ ECR authentication                       Not authenticated
  ⚠ Not authenticated to ECR
```

**Fix:**
```bash
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  793796654438.dkr.ecr.us-east-1.amazonaws.com
```

---

## 🎯 Benefits

### For CI/CD:
- ✅ **Zero manual setup** - Script installs everything
- ✅ **Reproducible environments** - Same setup every time
- ✅ **Non-interactive** - No prompts or user input
- ✅ **Fast execution** - Only installs what's missing

### For Local Development:
- ✅ **Safe** - Won't reinstall existing tools
- ✅ **Smart** - Checks before installing
- ✅ **Helpful** - Clear error messages and guidance
- ✅ **Complete** - Validates entire stack

---

## 📊 Expected Timing

### First Run (Clean Environment):
- Python 3.12.3: ~30-60 seconds
- kubectl: ~10-20 seconds
- Docker: ~60-90 seconds
- AWS CLI: ~20-30 seconds
- EKS configuration: ~2-5 seconds
- Nginx Ingress: ~60-120 seconds
- cert-manager: ~60-120 seconds
- **Total: ~4-7 minutes**

### Subsequent Runs (Everything Installed):
- All checks: ~5-10 seconds

---

## 🐛 Troubleshooting

### Issue: Docker Installation Fails

**Symptom:** "Failed to install Docker"

**Solution:**
```bash
# Ensure system is Ubuntu/Debian
lsb_release -a

# Update package lists
sudo apt-get update

# Install manually if needed
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```

### Issue: Nginx Ingress Pods Not Ready

**Symptom:** "Nginx Ingress installed but not yet ready"

**Solution:**
```bash
# Check pod status
kubectl get pods -n ingress-nginx

# Check events
kubectl get events -n ingress-nginx --sort-by='.lastTimestamp'

# View logs
kubectl logs -n ingress-nginx -l app.kubernetes.io/name=ingress-nginx

# Wait manually
kubectl wait --for=condition=ready pod \
  -l app.kubernetes.io/name=ingress-nginx \
  -n ingress-nginx --timeout=600s
```

### Issue: AWS LB Controller Fails

**Symptom:** Failed to apply AWS LB controller

**Solution:**
```bash
# Ensure IAM role is attached to service account
kubectl describe sa aws-load-balancer-controller -n kube-system

# Check AWS LB controller logs
kubectl logs -n kube-system deployment/aws-load-balancer-controller
```

---

## 🎉 Summary

The `check_prerequisites.py` script is now a **fully automated deployment preparation tool** that:

1. ✅ Validates your entire deployment stack
2. ✅ Auto-installs ALL missing components
3. ✅ Works in CI/CD and local environments
4. ✅ Provides clear error messages and guidance
5. ✅ Safe - only installs what's missing

**Run it before every deployment to ensure your environment is ready!**

```bash
cd automation_script
./check_prerequisites.py
```
