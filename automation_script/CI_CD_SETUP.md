# CI/CD Setup Guide

Complete guide for using `check_prerequisites.py` in CI/CD pipelines.

## 🚀 Quick Start for CI/CD

```bash
# Single command setup - installs everything automatically!
cd automation_script
./check_prerequisites.py
```

That's it! The script will automatically install:
- ✅ Python 3.12.3 (if missing or too old)
- ✅ kubectl (if missing)
- ✅ EKS cluster connection (ecommerce-eks)
- ✅ cert-manager (if missing)

---

## 📋 What Gets Auto-Installed

### 1. Python 3.12.3

**When:** Python is missing, Python 2.x, or Python < 3.6

**Method:**
```bash
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt-get update -qq
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
  python3.12 python3.12-venv python3.12-dev python3-pip
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1
```

**Time:** ~30-60 seconds

**Note:** After Python installation, you may need to re-run the script with `python3 check_prerequisites.py`

---

### 2. kubectl

**When:** kubectl command not found

**Method:**
```bash
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/
```

**Time:** ~10-20 seconds

---

### 3. EKS Cluster Connection

**When:** Cannot connect to Kubernetes cluster

**Command:**
```bash
aws eks update-kubeconfig --region us-east-1 --name ecommerce-eks
```

**Time:** ~2-5 seconds

**Requirements:**
- AWS CLI installed and configured
- Valid AWS credentials with EKS access

---

### 4. cert-manager

**When:** cert-manager namespace doesn't exist

**Method:**
```bash
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
kubectl wait --for=condition=ready pod -l app=cert-manager -n cert-manager --timeout=300s
```

**Time:** ~60-120 seconds

---

## 🔧 CI/CD Pipeline Examples

### GitHub Actions

```yaml
name: Deploy Frontend

on:
  push:
    branches:
      - main

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1

      - name: Setup prerequisites (auto-installs everything)
        run: |
          cd automation_script
          sudo ./check_prerequisites.py

      - name: Deploy to EKS
        run: |
          cd automation_script
          ./deploy_frontend.py
```

---

### GitLab CI/CD

```yaml
deploy:
  image: ubuntu:latest
  stage: deploy
  before_script:
    - apt-get update -qq
    - apt-get install -y curl sudo software-properties-common
  script:
    - cd automation_script
    - ./check_prerequisites.py  # Auto-installs everything
    - ./deploy_frontend.py
  only:
    - main
```

---

### AWS CodeBuild

```yaml
version: 0.2

phases:
  pre_build:
    commands:
      - echo "Setting up prerequisites..."
      - cd automation_script
      - ./check_prerequisites.py  # Auto-installs everything

  build:
    commands:
      - echo "Deploying to EKS..."
      - ./deploy_frontend.py
```

---

### Jenkins Pipeline

```groovy
pipeline {
    agent {
        docker {
            image 'ubuntu:latest'
            args '-u root:root'
        }
    }

    stages {
        stage('Setup Prerequisites') {
            steps {
                sh '''
                    apt-get update -qq
                    apt-get install -y curl sudo software-properties-common
                    cd automation_script
                    ./check_prerequisites.py
                '''
            }
        }

        stage('Deploy') {
            steps {
                sh '''
                    cd automation_script
                    ./deploy_frontend.py
                '''
            }
        }
    }
}
```

---

## ⚙️ Environment Variables for CI/CD

Set these in your CI/CD platform:

| Variable | Description | Required |
|----------|-------------|----------|
| `AWS_ACCESS_KEY_ID` | AWS access key | Yes |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | Yes |
| `AWS_REGION` | AWS region (default: us-east-1) | No |

---

## 🎯 Version Checking Logic

The script intelligently handles Python versions:

| Python Version | Status | Action |
|----------------|--------|--------|
| 3.12.0+ | ✅ Perfect | Continue |
| 3.6-3.11 | ⚠️ OK | Show upgrade recommendation |
| < 3.6 | ❌ Too old | Auto-install 3.12.3 |
| 2.x | ❌ Too old | Auto-install 3.12.3 |
| Not installed | ❌ Missing | Auto-install 3.12.3 |

---

## ⏱️ Expected Timing

**First run (clean environment):**
- Python installation: ~30-60 seconds
- kubectl installation: ~10-20 seconds
- EKS configuration: ~2-5 seconds
- cert-manager installation: ~60-120 seconds
- **Total:** ~2-4 minutes

**Subsequent runs (everything installed):**
- Prerequisite checks only: ~5-10 seconds

---

## 🐛 Troubleshooting CI/CD

### Issue: Permission Denied

**Symptom:**
```
Permission denied when running apt-get or moving files
```

**Solution:**
```yaml
# GitHub Actions - use sudo
- run: sudo ./check_prerequisites.py

# GitLab/Jenkins - run as root or install sudo
- apt-get install -y sudo
```

---

### Issue: AWS Credentials Not Found

**Symptom:**
```
Unable to locate credentials
```

**Solution:**
Ensure AWS credentials are set as environment variables or secrets in your CI/CD platform.

**GitHub Actions:**
```yaml
- uses: aws-actions/configure-aws-credentials@v4
  with:
    aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
    aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
    aws-region: us-east-1
```

---

### Issue: Python Installation Fails

**Symptom:**
```
Failed to add PPA or install Python 3.12
```

**Solution:**
Ensure the base image has `software-properties-common`:

```bash
apt-get update -qq
apt-get install -y software-properties-common
```

---

### Issue: kubectl Already Exists (Different Version)

**Symptom:**
kubectl exists but is old version

**Solution:**
The script will skip installation if kubectl exists. To force upgrade:

```bash
# Manually remove old kubectl
sudo rm /usr/local/bin/kubectl
# Then run the script
./check_prerequisites.py
```

---

## 📋 Prerequisites for the Script

The script itself needs:

| Requirement | Usually Available in CI/CD | Notes |
|-------------|---------------------------|-------|
| Ubuntu/Debian | ✅ Yes | ubuntu-latest, debian images |
| `apt-get` | ✅ Yes | Package manager |
| `sudo` | ✅ Yes | Most runners have it |
| Internet | ✅ Yes | For downloads |
| `curl` | ⚠️ Maybe | Install: `apt-get install -y curl` |

### Minimal Setup for CI/CD

If starting with a bare Ubuntu image:

```bash
apt-get update -qq
apt-get install -y curl sudo software-properties-common
cd automation_script
./check_prerequisites.py
```

---

## 🔒 Security Best Practices

### 1. Use Secrets for Credentials

**Never** hardcode AWS credentials. Always use CI/CD secrets:

```yaml
# GitHub Actions
env:
  AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
  AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
```

### 2. Use IAM Roles (Preferred)

For AWS services (CodeBuild, EC2), use IAM roles instead of access keys:

```yaml
# No credentials needed - uses IAM role
- ./check_prerequisites.py
```

### 3. Limit Permissions

Create a dedicated IAM user/role with only required permissions:
- `eks:DescribeCluster`
- `eks:ListClusters`
- `eks:AccessKubernetesApi`

---

## ✅ Verification

After the script runs, verify installations:

```bash
# Check Python version
python3 --version
# Expected: Python 3.12.3 or higher

# Check kubectl
kubectl version --client
# Expected: Client Version: v1.28.x

# Check cluster connection
kubectl cluster-info
# Expected: Kubernetes control plane is running

# Check cert-manager
kubectl get pods -n cert-manager
# Expected: 3 pods running
```

---

## 🎯 Benefits for CI/CD

✅ **Zero Manual Setup**
- No need to pre-install tools
- Script handles everything automatically

✅ **Reproducible Environments**
- Same setup on every run
- Consistent Python, kubectl, cert-manager versions

✅ **Fast Execution**
- Caches installed tools
- Only installs what's missing

✅ **Error Handling**
- Clear error messages
- Automatic retry logic
- Verification after installation

✅ **Non-Interactive**
- No prompts or user input
- Perfect for automated pipelines

---

## 📊 Expected Script Output in CI/CD

```
============================================================
        Pre-Deployment Prerequisites Check
============================================================

System Requirements:
✓ Python 3.12.3+                          v3.12.3
✓ kubectl                                 Client Version: v1.28.0

Kubernetes Cluster:
✓ Kubernetes cluster connection
  Current context: arn:aws:eks:us-east-1:123456789:cluster/ecommerce-eks

cert-manager (for SSL certificates):
✓ cert-manager namespace
✓ cert-manager pods running

Deployment Files:
✓ Namespace config                        ../deployment/namespace.yaml
✓ ClusterIssuer config                    ../deployment/clusterissuer.yaml
✓ Certificate config                      ../deployment/certificate.yaml
✓ Deployment config                       ../deployment/deployment.yaml
✓ Service config                          ../deployment/service.yaml
✓ Ingress config                          ../deployment/frontend-ingress.yaml

Current State:
✗ ecommerce-frontend-ns namespace         Does not exist (ready for deployment)

============================================================
                    Summary
============================================================

✓ All checks passed! Ready to deploy.

Run deployment with: ./deploy_frontend.py
```

---

## 🆘 Getting Help

If the script fails in CI/CD:

1. **Check the output** - Script provides detailed error messages
2. **Verify AWS credentials** - Most common issue
3. **Check internet connectivity** - Required for downloads
4. **Review CI/CD logs** - Look for specific error messages
5. **Test locally** - Run on your machine to isolate issues

---

**This script makes Kubernetes deployment setup completely automatic for CI/CD pipelines! 🎉**
