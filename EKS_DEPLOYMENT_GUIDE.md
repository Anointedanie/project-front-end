# Docker & EKS Deployment Guide

Complete guide for understanding the Dockerfile, building container images, and deploying to Amazon EKS using GitHub Actions with ECR.

## 📋 Table of Contents

1. [Understanding the Dockerfile](#understanding-the-dockerfile)
2. [Prerequisites](#prerequisites)
3. [AWS Setup](#aws-setup)
4. [GitHub Actions Setup](#github-actions-setup)
5. [EKS Deployment](#eks-deployment)
6. [Troubleshooting](#troubleshooting)

---

## 🐳 Understanding the Dockerfile

Our Dockerfile uses a **multi-stage build** pattern for optimal image size and security.

### Stage 1: Build Stage (Node.js)

```dockerfile
FROM node:18-alpine AS build
WORKDIR /app
```

**What it does:**
- Uses lightweight Node.js 18 Alpine Linux image (smaller size ~40MB vs ~900MB for standard Node)
- Sets `/app` as the working directory
- This stage is named `build` for reference in later stages

### Build Arguments & Environment Variables

```dockerfile
ARG REACT_APP_API_URL
ARG REACT_APP_ENV=production

ENV NODE_ENV=production
ENV REACT_APP_API_URL=${REACT_APP_API_URL}
ENV REACT_APP_ENV=${REACT_APP_ENV}
```

**What it does:**
- `ARG`: Defines build-time variables (passed during `docker build --build-arg`)
- `ENV`: Sets environment variables inside the container
- `REACT_APP_API_URL`: Backend API endpoint (baked into the React build)
- `NODE_ENV=production`: Optimizes React build for production

**Why it matters:**
- React apps are built at **build time**, not runtime
- The API URL gets embedded into the JavaScript bundle during the build
- Different environments (dev/staging/prod) need different builds with different API URLs

### Dependency Installation

```dockerfile
COPY package.json package-lock.json* ./
RUN if [ -f package-lock.json ]; then npm ci --only=production=false; else npm install; fi
```

**What it does:**
- Copies only package files first (optimizes Docker layer caching)
- Uses `npm ci` for faster, reproducible installs when lock file exists
- Falls back to `npm install` if no lock file present

**Why it matters:**
- Docker caches layers - if package.json hasn't changed, this layer is reused
- Significantly faster builds when dependencies don't change
- `npm ci` is 2-3x faster than `npm install` and guarantees reproducible builds

### Application Build

```dockerfile
COPY . .
RUN npm run build
RUN npm prune --production
```

**What it does:**
- Copies all source code into the image
- Runs `react-scripts build` to create optimized production bundle
- Removes dev dependencies to reduce size

**Output:**
- Optimized static files in `/app/build` directory
- Minified JavaScript and CSS (typically 70-80% smaller)
- Asset fingerprinting for cache busting (e.g., `main.a1b2c3d4.js`)

### Stage 2: Production Stage (Nginx)

```dockerfile
FROM nginx:alpine
```

**What it does:**
- Starts a fresh, clean Alpine Linux image with Nginx web server
- Previous build stage is discarded (only the `/app/build` output is kept)

**Why it matters:**
- Final image doesn't contain Node.js, npm, source code, or node_modules
- Dramatically smaller image size (~25MB vs ~400MB with Node.js)
- Reduced attack surface (fewer packages = fewer potential vulnerabilities)
- Nginx is optimized for serving static files

### Security Hardening

```dockerfile
RUN apk add --no-cache dumb-init
```

**What it does:**
- Installs `dumb-init` for proper signal handling in containers
- Ensures graceful shutdowns in Kubernetes (SIGTERM handling)

```dockerfile
RUN addgroup -g 101 -S nginx && \
    adduser -S -D -H -u 101 -h /var/cache/nginx -s /sbin/nologin -G nginx -g nginx nginx || true
```

**What it does:**
- Creates a non-root `nginx` user (UID/GID 101)
- Sets shell to `/sbin/nologin` (prevents shell access)
- `|| true` prevents failure if user already exists

```dockerfile
RUN chown -R nginx:nginx /usr/share/nginx/html && \
    chown -R nginx:nginx /var/cache/nginx && \
    chown -R nginx:nginx /var/log/nginx && \
    chown -R nginx:nginx /etc/nginx/conf.d && \
    touch /var/run/nginx.pid && \
    chown -R nginx:nginx /var/run/nginx.pid

USER nginx
```

**What it does:**
- Sets proper file ownership for all directories Nginx needs
- Creates and owns the PID file
- Switches to non-root user for running the container

**Why it matters:**
- Running as root is a major security risk
- Kubernetes security policies often require non-root containers
- Follows principle of least privilege
- Limits damage if container is compromised

### Final Configuration

```dockerfile
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/build /usr/share/nginx/html
```

**What it does:**
- Copies custom Nginx configuration
- Copies built React app from the build stage (`--from=build` references Stage 1)
- Only the compiled static files are copied, not source code

```dockerfile
EXPOSE 80
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost/ || exit 1
```

**What it does:**
- Documents that the container listens on port 80
- Defines a health check endpoint for Kubernetes liveness/readiness probes
- Checks every 30s, waits 5s on startup, fails after 3 consecutive failures

```dockerfile
ENTRYPOINT ["/usr/bin/dumb-init", "--"]
CMD ["nginx", "-g", "daemon off;"]
```

**What it does:**
- Uses `dumb-init` as PID 1 for proper signal handling
- Starts Nginx in foreground mode (required for Docker/Kubernetes)
- `daemon off;` prevents Nginx from backgrounding itself

**Why the multi-stage build is powerful:**
- Build stage: ~400MB (includes Node.js, npm, source code)
- Final stage: ~25MB (only Nginx + static files)
- 94% size reduction!

---

## 🔧 Prerequisites

### Local Development Tools

```bash
# Check if tools are installed
docker --version  # Requires 20.10+
aws --version     # Requires AWS CLI 2.0+
kubectl version --client  # Requires 1.28+
```

Install missing tools:

```bash
# Docker (Ubuntu/Debian)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER  # Add user to docker group

# AWS CLI v2
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/

# eksctl (optional, for cluster creation)
curl --silent --location "https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" | tar xz -C /tmp
sudo mv /tmp/eksctl /usr/local/bin
```

### AWS Account Requirements

- AWS Account with appropriate permissions
- IAM user with programmatic access
- Required IAM permissions:
  - **ECR**: AmazonEC2ContainerRegistryPowerUser
  - **EKS**: AmazonEKSClusterPolicy, AmazonEKSServicePolicy
  - **EC2**: For EKS worker nodes
  - **IAM**: For creating service roles
  - **CloudFormation**: For EKS stack creation

---

## ☁️ AWS Setup

### Step 1: Configure AWS CLI

```bash
# Configure AWS credentials
aws configure

# Input:
# AWS Access Key ID: [Your access key]
# AWS Secret Access Key: [Your secret key]
# Default region name: us-east-1
# Default output format: json

# Verify configuration
aws sts get-caller-identity
```

### Step 2: Create ECR Repository

```bash
# Create ECR repository for frontend images
aws ecr create-repository \
    --repository-name ecommerce-frontend \
    --region us-east-1 \
    --image-scanning-configuration scanOnPush=true \
    --encryption-configuration encryptionType=AES256 \
    --tags Key=Environment,Value=production Key=Project,Value=ecommerce

# Output will include (SAVE THIS):
# {
#     "repository": {
#         "repositoryUri": "123456789012.dkr.ecr.us-east-1.amazonaws.com/ecommerce-frontend",
#         "repositoryArn": "arn:aws:ecr:us-east-1:123456789012:repository/ecommerce-frontend"
#     }
# }
```

**Save the `repositoryUri` - you'll need it for GitHub Actions and Kubernetes!**

### Step 3: Create EKS Cluster

#### Option A: Using eksctl (Recommended - Faster & Easier)

```bash
# Create cluster with managed node group
eksctl create cluster \
    --name ecommerce-cluster \
    --region us-east-1 \
    --version 1.28 \
    --nodegroup-name standard-workers \
    --node-type t3.medium \
    --nodes 2 \
    --nodes-min 1 \
    --nodes-max 4 \
    --managed \
    --tags Environment=production,Project=ecommerce

# This takes ~15-20 minutes
# eksctl automatically:
# - Creates VPC and subnets
# - Configures security groups
# - Sets up IAM roles
# - Updates your kubeconfig
```

#### Option B: Using AWS Console (Manual)

1. **Create EKS Cluster:**
   - Go to EKS Console → Create Cluster
   - Cluster name: `ecommerce-cluster`
   - Kubernetes version: 1.28 or later
   - Create cluster service role (or select existing)
   - Configure networking (VPC, subnets - use at least 2 AZs)
   - Wait 10-15 minutes for cluster creation

2. **Create Node Group:**
   - Select your cluster → Compute → Add node group
   - Node group name: `standard-workers`
   - Node IAM role: Create new or select existing
   - AMI type: Amazon Linux 2
   - Instance type: `t3.medium` (2 vCPU, 4GB RAM)
   - Scaling config: Min 1, Max 4, Desired 2
   - Wait 5-10 minutes for nodes to be ready

3. **Update kubeconfig:**
   ```bash
   aws eks update-kubeconfig --region us-east-1 --name ecommerce-cluster
   kubectl get nodes  # Verify connection
   ```

### Step 4: Create IAM User for GitHub Actions

This user will be used by GitHub Actions to push images to ECR and deploy to EKS.

```bash
# Create IAM user
aws iam create-user --user-name github-actions-ecr-eks

# Create and attach ECR policy
cat > ecr-policy.json <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ecr:GetAuthorizationToken",
                "ecr:BatchCheckLayerAvailability",
                "ecr:GetDownloadUrlForLayer",
                "ecr:BatchGetImage",
                "ecr:PutImage",
                "ecr:InitiateLayerUpload",
                "ecr:UploadLayerPart",
                "ecr:CompleteLayerUpload"
            ],
            "Resource": "*"
        }
    ]
}
EOF

aws iam put-user-policy \
    --user-name github-actions-ecr-eks \
    --policy-name ECRPushPull \
    --policy-document file://ecr-policy.json

# Attach EKS access policy
aws iam attach-user-policy \
    --user-name github-actions-ecr-eks \
    --policy-arn arn:aws:iam::aws:policy/AmazonEKSClusterPolicy

# Create access key
aws iam create-access-key --user-name github-actions-ecr-eks

# IMPORTANT: SAVE THE OUTPUT!
# {
#     "AccessKey": {
#         "UserName": "github-actions-ecr-eks",
#         "AccessKeyId": "AKIAIOSFODNN7EXAMPLE",
#         "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
#         "Status": "Active"
#     }
# }
```

### Step 5: Configure kubectl Access

```bash
# Update kubeconfig for EKS cluster
aws eks update-kubeconfig \
    --region us-east-1 \
    --name ecommerce-cluster

# Verify connection
kubectl get nodes
kubectl get namespaces

# Should see:
# NAME               STATUS   ROLES    AGE     VERSION
# ip-192-168-x-x...  Ready    <none>   5m      v1.28.x
# ip-192-168-y-y...  Ready    <none>   5m      v1.28.x
```

---

## 🔐 GitHub Actions Setup

### Step 1: Add GitHub Secrets

Go to your GitHub repository:
1. Click **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Add each secret below:

| Secret Name | Description | Example / How to Get |
|-------------|-------------|----------------------|
| `AWS_ACCESS_KEY_ID` | IAM user access key | From Step 4 output: `AKIAIOSFODNN7EXAMPLE` |
| `AWS_SECRET_ACCESS_KEY` | IAM user secret key | From Step 4 output: `wJalrXUtnFEMI/K7MDENG/...` |
| `AWS_REGION` | AWS region for ECR/EKS | `us-east-1` |
| `AWS_ACCOUNT_ID` | Your AWS account ID | Run: `aws sts get-caller-identity --query Account --output text` |
| `ECR_REPOSITORY` | ECR repository name | `ecommerce-frontend` |
| `EKS_CLUSTER_NAME` | EKS cluster name | `ecommerce-cluster` |
| `REACT_APP_API_URL` | Backend API URL (production) | `https://api.yourdomain.com/api` or `http://your-backend-elb:8000/api` |

**Screenshot reference for adding secrets:**
```
Settings → Secrets and variables → Actions → New repository secret
Name: AWS_ACCESS_KEY_ID
Value: AKIAIOSFODNN7EXAMPLE
[Add secret]
```

### Step 2: Create GitHub Actions Workflow

Create directory structure:
```bash
mkdir -p .github/workflows
```

Create `.github/workflows/deploy-to-eks.yml`:

```yaml
name: Build and Deploy to EKS

on:
  push:
    branches:
      - main        # Deploy on push to main
      - develop     # Deploy on push to develop (optional)
  pull_request:
    branches:
      - main        # Build only (no deploy) on PRs
  workflow_dispatch:  # Allow manual trigger from GitHub UI

env:
  AWS_REGION: ${{ secrets.AWS_REGION }}
  ECR_REPOSITORY: ${{ secrets.ECR_REPOSITORY }}
  EKS_CLUSTER_NAME: ${{ secrets.EKS_CLUSTER_NAME }}
  REACT_APP_API_URL: ${{ secrets.REACT_APP_API_URL }}

jobs:
  build-and-deploy:
    name: Build Docker Image and Deploy to EKS
    runs-on: ubuntu-latest

    # Only deploy on push to main/develop (not on PRs)
    permissions:
      contents: read
      id-token: write  # For OIDC (future enhancement)

    steps:
      # ====================================
      # Step 1: Checkout code from repository
      # ====================================
      - name: Checkout code
        uses: actions/checkout@v4

      # ====================================
      # Step 2: Configure AWS credentials
      # ====================================
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_REGION }}

      # ====================================
      # Step 3: Login to Amazon ECR
      # ====================================
      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v2

      # ====================================
      # Step 4: Build, tag, and push image to ECR
      # ====================================
      - name: Build, tag, and push image to Amazon ECR
        id: build-image
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          IMAGE_TAG: ${{ github.sha }}  # Use git commit SHA as tag
        run: |
          echo "Building Docker image..."

          # Build Docker image with build arguments
          docker build \
            --build-arg REACT_APP_API_URL=${{ env.REACT_APP_API_URL }} \
            --build-arg REACT_APP_ENV=production \
            -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG \
            -t $ECR_REGISTRY/$ECR_REPOSITORY:latest \
            .

          echo "Pushing image to ECR..."
          # Push both tags (commit SHA and latest)
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:latest

          # Output image URI for next steps
          echo "image=$ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG" >> $GITHUB_OUTPUT
          echo "✅ Image pushed: $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG"

      # ====================================
      # Step 5: Install and configure kubectl
      # ====================================
      - name: Install and configure kubectl
        run: |
          echo "Installing kubectl..."
          curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
          chmod +x kubectl
          sudo mv kubectl /usr/local/bin/
          kubectl version --client

          echo "Configuring kubectl for EKS..."
          aws eks update-kubeconfig \
            --region ${{ env.AWS_REGION }} \
            --name ${{ env.EKS_CLUSTER_NAME }}

          kubectl get nodes

      # ====================================
      # Step 6: Deploy to EKS
      # ====================================
      - name: Deploy to EKS
        if: github.event_name == 'push'  # Only deploy on push, not PRs
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          IMAGE_TAG: ${{ github.sha }}
        run: |
          echo "Deploying to EKS cluster..."

          # Update deployment with new image
          kubectl set image deployment/ecommerce-frontend \
            ecommerce-frontend=$ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG \
            --namespace=production \
            --record

          # Wait for rollout to complete (timeout 5 minutes)
          echo "Waiting for rollout to complete..."
          kubectl rollout status deployment/ecommerce-frontend \
            --namespace=production \
            --timeout=5m

          echo "✅ Deployment successful!"

      # ====================================
      # Step 7: Verify deployment
      # ====================================
      - name: Verify deployment
        if: github.event_name == 'push'
        run: |
          echo "Verifying deployment..."

          # Get pod status
          kubectl get pods \
            --namespace=production \
            -l app=ecommerce-frontend \
            -o wide

          # Get service info
          kubectl get services \
            --namespace=production \
            -l app=ecommerce-frontend

          # Get deployment info
          kubectl describe deployment ecommerce-frontend \
            --namespace=production

      # ====================================
      # Step 8: Deployment summary
      # ====================================
      - name: Deployment summary
        if: always()  # Run even if previous steps fail
        run: |
          echo "=========================================="
          echo "📋 Deployment Summary"
          echo "=========================================="
          echo "Status: ${{ job.status }}"
          echo "Image: ${{ steps.build-image.outputs.image }}"
          echo "Cluster: ${{ env.EKS_CLUSTER_NAME }}"
          echo "Region: ${{ env.AWS_REGION }}"
          echo "Commit: ${{ github.sha }}"
          echo "Branch: ${{ github.ref_name }}"
          echo "=========================================="
```

### Step 3: Commit and Push Workflow

```bash
# Add workflow file
git add .github/workflows/deploy-to-eks.yml

# Commit
git commit -m "Add GitHub Actions workflow for EKS deployment"

# Push to trigger the workflow
git push origin main
```

### Step 4: Monitor Workflow Execution

1. Go to your GitHub repository
2. Click **Actions** tab
3. Click on the latest workflow run
4. Watch each step execute in real-time
5. Check for any errors in the logs

---

## 🚀 EKS Deployment

### Step 1: Create Kubernetes Namespace

Create `k8s/namespace.yaml`:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: production
  labels:
    name: production
    environment: production
```

Apply to cluster:
```bash
kubectl apply -f k8s/namespace.yaml

# Verify
kubectl get namespaces
```

### Step 2: Create Kubernetes Deployment

Create `k8s/deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ecommerce-frontend
  namespace: production
  labels:
    app: ecommerce-frontend
    environment: production
    version: v1.0.0
spec:
  replicas: 2  # Run 2 pods for high availability
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1        # Allow 1 extra pod during updates
      maxUnavailable: 0  # No pods can be unavailable (zero downtime)
  selector:
    matchLabels:
      app: ecommerce-frontend
  template:
    metadata:
      labels:
        app: ecommerce-frontend
        environment: production
    spec:
      containers:
      - name: ecommerce-frontend
        # IMPORTANT: Replace with your ECR repository URI
        image: 123456789012.dkr.ecr.us-east-1.amazonaws.com/ecommerce-frontend:latest
        imagePullPolicy: Always  # Always pull latest image
        ports:
        - name: http
          containerPort: 80
          protocol: TCP

        # Resource limits (prevents pod from consuming all node resources)
        resources:
          requests:
            memory: "128Mi"  # Minimum memory required
            cpu: "100m"      # 0.1 CPU cores
          limits:
            memory: "256Mi"  # Maximum memory allowed
            cpu: "200m"      # 0.2 CPU cores

        # Liveness probe (restart pod if unhealthy)
        livenessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 30  # Wait 30s before first check
          periodSeconds: 10        # Check every 10s
          timeoutSeconds: 5        # Timeout after 5s
          failureThreshold: 3      # Restart after 3 failures

        # Readiness probe (remove from service if not ready)
        readinessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 10  # Wait 10s before first check
          periodSeconds: 5         # Check every 5s
          timeoutSeconds: 3        # Timeout after 3s
          failureThreshold: 3      # Mark unready after 3 failures

        # Security context
        securityContext:
          runAsNonRoot: true                # Must not run as root
          runAsUser: 101                    # Run as nginx user (UID 101)
          allowPrivilegeEscalation: false   # Prevent privilege escalation
          readOnlyRootFilesystem: false     # Allow writes to /tmp, /var/cache
          capabilities:
            drop:
              - ALL                         # Drop all capabilities
```

**IMPORTANT:** Update the `image:` line with your actual ECR repository URI from Step 2!

Apply to cluster:
```bash
kubectl apply -f k8s/deployment.yaml

# Verify deployment
kubectl get deployments -n production
kubectl get pods -n production
```

### Step 3: Create Kubernetes Service (LoadBalancer)

Create `k8s/service.yaml`:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: ecommerce-frontend
  namespace: production
  labels:
    app: ecommerce-frontend
  annotations:
    # AWS Load Balancer annotations (optional)
    service.beta.kubernetes.io/aws-load-balancer-type: "nlb"  # Network Load Balancer
    service.beta.kubernetes.io/aws-load-balancer-cross-zone-load-balancing-enabled: "true"
spec:
  type: LoadBalancer  # Creates AWS ELB/NLB automatically
  selector:
    app: ecommerce-frontend  # Route traffic to pods with this label
  ports:
  - name: http
    port: 80          # External port
    targetPort: 80    # Container port
    protocol: TCP
  sessionAffinity: None
```

Apply to cluster:
```bash
kubectl apply -f k8s/service.yaml

# Wait for LoadBalancer to be provisioned (takes 2-3 minutes)
kubectl get service ecommerce-frontend -n production -w

# Get the LoadBalancer URL
kubectl get service ecommerce-frontend -n production
```

Output will look like:
```
NAME                 TYPE           CLUSTER-IP       EXTERNAL-IP
ecommerce-frontend   LoadBalancer   10.100.123.45    a1b2c3d4...us-east-1.elb.amazonaws.com
```

**The EXTERNAL-IP is your frontend URL!**

Test it:
```bash
FRONTEND_URL=$(kubectl get service ecommerce-frontend -n production -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
curl -I http://$FRONTEND_URL
```

### Step 4: (Optional) Create Ingress with AWS Load Balancer Controller

For production with custom domain and SSL, use AWS Load Balancer Controller.

**Install AWS Load Balancer Controller:**

```bash
# Add IAM policy
curl -o iam_policy.json https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/v2.6.0/docs/install/iam_policy.json

aws iam create-policy \
    --policy-name AWSLoadBalancerControllerIAMPolicy \
    --policy-document file://iam_policy.json

# Create service account
eksctl create iamserviceaccount \
    --cluster=ecommerce-cluster \
    --namespace=kube-system \
    --name=aws-load-balancer-controller \
    --attach-policy-arn=arn:aws:iam::YOUR_ACCOUNT_ID:policy/AWSLoadBalancerControllerIAMPolicy \
    --approve

# Install controller
kubectl apply -k "github.com/aws/eks-charts/stable/aws-load-balancer-controller//crds?ref=master"

helm repo add eks https://aws.github.io/eks-charts
helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
    -n kube-system \
    --set clusterName=ecommerce-cluster \
    --set serviceAccount.create=false \
    --set serviceAccount.name=aws-load-balancer-controller
```

**Create Ingress:** `k8s/ingress.yaml`

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ecommerce-frontend
  namespace: production
  annotations:
    kubernetes.io/ingress.class: alb
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/healthcheck-path: /
    alb.ingress.kubernetes.io/listen-ports: '[{"HTTP": 80}, {"HTTPS": 443}]'
    # Add your ACM certificate ARN for HTTPS
    alb.ingress.kubernetes.io/certificate-arn: arn:aws:acm:us-east-1:123456789012:certificate/your-cert-id
    alb.ingress.kubernetes.io/ssl-redirect: '443'
spec:
  rules:
  - host: www.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: ecommerce-frontend
            port:
              number: 80
```

### Step 5: Deploy All Resources

```bash
# Apply all Kubernetes manifests
kubectl apply -f k8s/

# Verify all resources
kubectl get all -n production

# Check pod logs
kubectl logs -f deployment/ecommerce-frontend -n production

# Get service endpoint
kubectl get service ecommerce-frontend -n production -o wide
```

---

## 🔄 Complete Deployment Workflow

### How It All Works Together

1. **Developer pushes code** to `main` branch
   ```bash
   git add .
   git commit -m "Update frontend"
   git push origin main
   ```

2. **GitHub Actions triggers** automatically
   - Workflow file: `.github/workflows/deploy-to-eks.yml`
   - Trigger: Push to `main` branch

3. **Build phase:**
   - Checkout code from repository
   - Configure AWS credentials using GitHub secrets
   - Login to Amazon ECR
   - Build Docker image with `REACT_APP_API_URL` from secrets
   - Tag image with commit SHA (e.g., `abc123def456`)
   - Tag image with `latest`
   - Push both tags to ECR

4. **Deploy phase:**
   - Install kubectl
   - Configure kubectl to connect to EKS cluster
   - Update Kubernetes deployment with new image tag
   - Kubernetes performs rolling update:
     - Creates new pod with new image
     - Waits for new pod to be ready (readiness probe)
     - Routes traffic to new pod
     - Terminates old pod
     - Repeat for all replicas
   - Wait for rollout to complete

5. **Verification:**
   - Check pod status
   - Check service status
   - Display deployment summary

### Zero-Downtime Rolling Updates

```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 1        # Create 1 extra pod during update
    maxUnavailable: 0  # No pods can be unavailable
```

**Example with 2 replicas:**
1. Current state: 2 old pods running
2. Create 1 new pod (maxSurge=1) → Total: 3 pods
3. Wait for new pod to be ready
4. Terminate 1 old pod → Total: 2 pods (1 new, 1 old)
5. Create another new pod → Total: 3 pods (2 new, 1 old)
6. Wait for new pod to be ready
7. Terminate last old pod → Total: 2 new pods
8. Done! Zero downtime.

---

## 🧪 Testing the Deployment

### 1. Check Pod Status

```bash
kubectl get pods -n production -l app=ecommerce-frontend -o wide

# Expected output:
NAME                                  READY   STATUS    RESTARTS   AGE   IP            NODE
ecommerce-frontend-7d8f9c5b6d-abc12   1/1     Running   0          2m    192.168.1.5   ip-192-168-1-100
ecommerce-frontend-7d8f9c5b6d-xyz34   1/1     Running   0          2m    192.168.2.8   ip-192-168-2-200
```

### 2. Check Service and Get Public URL

```bash
kubectl get service ecommerce-frontend -n production

# Expected output:
NAME                 TYPE           CLUSTER-IP       EXTERNAL-IP                          PORT(S)        AGE
ecommerce-frontend   LoadBalancer   10.100.200.123   a1b2c3d4...us-east-1.elb.amazonaws.com   80:30080/TCP   5m

# Get URL
FRONTEND_URL=$(kubectl get service ecommerce-frontend -n production -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
echo "Frontend URL: http://$FRONTEND_URL"
```

### 3. Test the Application

```bash
# Test HTTP endpoint
curl -I http://$FRONTEND_URL

# Should return: HTTP/1.1 200 OK

# Test full response
curl http://$FRONTEND_URL

# Open in browser
echo "Open this URL in your browser:"
echo "http://$FRONTEND_URL"
```

### 4. View Logs

```bash
# All pods logs
kubectl logs -l app=ecommerce-frontend -n production --tail=100

# Specific pod logs
kubectl logs ecommerce-frontend-7d8f9c5b6d-abc12 -n production

# Follow logs in real-time
kubectl logs -f deployment/ecommerce-frontend -n production

# Previous pod logs (if pod crashed)
kubectl logs ecommerce-frontend-7d8f9c5b6d-abc12 -n production --previous
```

### 5. Execute into Pod (Debug)

```bash
# Get shell access to pod
kubectl exec -it deployment/ecommerce-frontend -n production -- /bin/sh

# Inside the pod, you can:
ls -la /usr/share/nginx/html              # Check files
cat /etc/nginx/conf.d/default.conf        # Check nginx config
ps aux                                     # Check processes
wget -O- http://localhost/                # Test locally
exit
```

### 6. Check Resource Usage

```bash
# Pod resource usage
kubectl top pods -n production -l app=ecommerce-frontend

# Node resource usage
kubectl top nodes
```

---

## 🐛 Troubleshooting

### Issue 1: ImagePullBackOff Error

**Symptom:**
```bash
kubectl get pods -n production
# NAME                                  READY   STATUS             RESTARTS   AGE
# ecommerce-frontend-xxx                0/1     ImagePullBackOff   0          2m
```

**Cause:** EKS nodes can't pull image from ECR (permission issue)

**Solution:**
```bash
# 1. Check pod events
kubectl describe pod ecommerce-frontend-xxx -n production

# 2. Find the node IAM role
aws eks describe-nodegroup \
    --cluster-name ecommerce-cluster \
    --nodegroup-name standard-workers \
    --query "nodegroup.nodeRole" --output text

# 3. Attach ECR read policy to node role
aws iam attach-role-policy \
    --role-name eksctl-ecommerce-cluster-nodegro-NodeInstanceRole-XXXXX \
    --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly

# 4. Delete pod to trigger recreation
kubectl delete pod ecommerce-frontend-xxx -n production
```

### Issue 2: Pods Not Starting (CrashLoopBackOff)

**Symptom:**
```bash
kubectl get pods -n production
# NAME                                  READY   STATUS             RESTARTS   AGE
# ecommerce-frontend-xxx                0/1     CrashLoopBackOff   3          5m
```

**Debug:**
```bash
# Check pod logs
kubectl logs ecommerce-frontend-xxx -n production

# Check previous container logs
kubectl logs ecommerce-frontend-xxx -n production --previous

# Describe pod for events
kubectl describe pod ecommerce-frontend-xxx -n production

# Common issues:
# - Nginx config error → Check nginx.conf syntax
# - File permissions → Check USER nginx in Dockerfile
# - Missing files → Check COPY commands in Dockerfile
```

### Issue 3: LoadBalancer Stuck in Pending

**Symptom:**
```bash
kubectl get service ecommerce-frontend -n production
# EXTERNAL-IP shows <pending> for > 5 minutes
```

**Debug:**
```bash
# Check service events
kubectl describe service ecommerce-frontend -n production

# Check AWS Load Balancer creation
aws elbv2 describe-load-balancers \
    --query "LoadBalancers[?contains(LoadBalancerName, 'ecommerce')].LoadBalancerArn" \
    --output text

# Common causes:
# - VPC subnet tags missing
# - Security group issues
# - IAM permissions missing
```

**Solution:**
```bash
# Ensure subnets are tagged correctly
aws ec2 describe-subnets \
    --filters "Name=vpc-id,Values=YOUR_VPC_ID" \
    --query "Subnets[*].[SubnetId,Tags[?Key=='kubernetes.io/role/elb'].Value]"

# Tag subnets if missing
aws ec2 create-tags \
    --resources subnet-xxxxx subnet-yyyyy \
    --tags Key=kubernetes.io/role/elb,Value=1
```

### Issue 4: 502 Bad Gateway from LoadBalancer

**Symptom:**
```bash
curl http://YOUR_LOAD_BALANCER_URL
# Returns: 502 Bad Gateway
```

**Debug:**
```bash
# 1. Check pod health
kubectl get pods -n production -l app=ecommerce-frontend

# 2. Check pod logs
kubectl logs -l app=ecommerce-frontend -n production --tail=50

# 3. Test pod directly (bypass service)
kubectl port-forward pod/ecommerce-frontend-xxx 8080:80 -n production
curl http://localhost:8080  # Test from your machine

# 4. Check readiness probe
kubectl describe pod ecommerce-frontend-xxx -n production | grep -A 10 Readiness

# 5. Check service endpoints
kubectl get endpoints ecommerce-frontend -n production
# Should show pod IPs. If empty, selector mismatch.
```

**Solution:**
```bash
# If readiness probe failing, check:
# - Correct path: /
# - Correct port: 80
# - Container is actually serving on port 80

# Test inside pod
kubectl exec -it ecommerce-frontend-xxx -n production -- wget -O- http://localhost/
```

### Issue 5: Environment Variables Not Working

**Symptom:**
- React app can't connect to backend
- `REACT_APP_API_URL` not set correctly

**Cause:**
React environment variables must be set at **build time**, not runtime!

**Solution:**
```bash
# 1. Verify GitHub Secret is set correctly
# Go to GitHub repo → Settings → Secrets → Check REACT_APP_API_URL

# 2. Verify build args in GitHub Actions workflow
# Check .github/workflows/deploy-to-eks.yml:
#   --build-arg REACT_APP_API_URL=${{ secrets.REACT_APP_API_URL }}

# 3. Rebuild image with correct variable
# Push a commit to trigger rebuild

# 4. Verify environment variable in built image
docker pull YOUR_ECR_URI:latest
docker run --rm YOUR_ECR_URI:latest cat /usr/share/nginx/html/index.html | grep "REACT_APP_API_URL"
# The URL should be in the JavaScript bundle
```

### Issue 6: GitHub Actions Failing

**Symptom:**
```
Error: The security token included in the request is invalid
```

**Solution:**
```bash
# 1. Verify AWS credentials in GitHub Secrets
# Settings → Secrets → Check:
# - AWS_ACCESS_KEY_ID
# - AWS_SECRET_ACCESS_KEY

# 2. Test credentials locally
aws sts get-caller-identity

# 3. Check IAM user permissions
aws iam list-attached-user-policies --user-name github-actions-ecr-eks

# 4. Verify ECR login works
aws ecr get-login-password --region us-east-1 | \
    docker login --username AWS --password-stdin YOUR_ECR_REGISTRY

# 5. Re-create access key if needed
aws iam delete-access-key --user-name github-actions-ecr-eks --access-key-id OLD_KEY
aws iam create-access-key --user-name github-actions-ecr-eks
# Update GitHub secrets with new keys
```

### Common kubectl Commands

```bash
# Get all resources in namespace
kubectl get all -n production

# Describe deployment
kubectl describe deployment ecommerce-frontend -n production

# Check deployment rollout status
kubectl rollout status deployment/ecommerce-frontend -n production

# View rollout history
kubectl rollout history deployment/ecommerce-frontend -n production

# Rollback to previous version
kubectl rollout undo deployment/ecommerce-frontend -n production

# Rollback to specific revision
kubectl rollout undo deployment/ecommerce-frontend --to-revision=2 -n production

# Restart deployment (recreate all pods)
kubectl rollout restart deployment/ecommerce-frontend -n production

# Scale deployment
kubectl scale deployment ecommerce-frontend --replicas=3 -n production

# Edit deployment live
kubectl edit deployment ecommerce-frontend -n production

# Get pod YAML
kubectl get pod ecommerce-frontend-xxx -n production -o yaml

# Port forward to pod
kubectl port-forward pod/ecommerce-frontend-xxx 8080:80 -n production

# Execute command in pod
kubectl exec ecommerce-frontend-xxx -n production -- ls -la /usr/share/nginx/html

# Delete deployment
kubectl delete deployment ecommerce-frontend -n production

# Delete service
kubectl delete service ecommerce-frontend -n production

# Delete everything with label
kubectl delete all -l app=ecommerce-frontend -n production
```

---

## 📊 Monitoring and Logging

### CloudWatch Container Insights

Enable Container Insights for your EKS cluster:

```bash
# Enable control plane logging
aws eks update-cluster-config \
    --region us-east-1 \
    --name ecommerce-cluster \
    --logging '{"clusterLogging":[{"types":["api","audit","authenticator","controllerManager","scheduler"],"enabled":true}]}'

# Install CloudWatch agent
kubectl apply -f https://raw.githubusercontent.com/aws-samples/amazon-cloudwatch-container-insights/latest/k8s-deployment-manifest-templates/deployment-mode/daemonset/container-insights-monitoring/quickstart/cwagent-fluentd-quickstart.yaml
```

### View Logs in CloudWatch

1. Open AWS Console → CloudWatch
2. Navigate to **Log Groups**
3. Find `/aws/eks/ecommerce-cluster/cluster` (control plane logs)
4. Find `/aws/containerinsights/ecommerce-cluster/application` (pod logs)

### Query Logs

```bash
# AWS CLI query
aws logs filter-log-events \
    --log-group-name /aws/eks/ecommerce-cluster/cluster \
    --filter-pattern "error" \
    --start-time $(date -d '1 hour ago' +%s)000
```

### Metrics in CloudWatch

- Container CPU utilization
- Container memory utilization
- Container network traffic
- Pod restart count
- Node resource utilization

---

## 🔒 Security Best Practices

### 1. Use Secrets for Sensitive Data

**Never hardcode credentials!**

Create Kubernetes secret:
```bash
kubectl create secret generic backend-credentials \
    --from-literal=api-key=your-api-key \
    --from-literal=db-password=your-password \
    -n production

# Use in deployment
# env:
# - name: API_KEY
#   valueFrom:
#     secretKeyRef:
#       name: backend-credentials
#       key: api-key
```

### 2. Enable Image Scanning

```bash
# Enable ECR scanning
aws ecr put-image-scanning-configuration \
    --repository-name ecommerce-frontend \
    --image-scanning-configuration scanOnPush=true

# View scan results
aws ecr describe-image-scan-findings \
    --repository-name ecommerce-frontend \
    --image-id imageTag=latest
```

### 3. Network Policies

Restrict pod-to-pod communication:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: frontend-network-policy
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: ecommerce-frontend
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: production
    ports:
    - protocol: TCP
      port: 80
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: ecommerce-backend
    ports:
    - protocol: TCP
      port: 8000
  - to:  # Allow DNS
    - namespaceSelector:
        matchLabels:
          name: kube-system
    ports:
    - protocol: UDP
      port: 53
```

### 4. Pod Security Standards

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: production
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
```

### 5. RBAC (Role-Based Access Control)

Create service account with limited permissions:

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: frontend-sa
  namespace: production
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: frontend-role
  namespace: production
rules:
- apiGroups: [""]
  resources: ["pods", "services"]
  verbs: ["get", "list"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: frontend-rolebinding
  namespace: production
subjects:
- kind: ServiceAccount
  name: frontend-sa
roleRef:
  kind: Role
  name: frontend-role
  apiGroup: rbac.authorization.k8s.io
```

---

## 📈 Scaling

### Horizontal Pod Autoscaler (HPA)

Automatically scale based on CPU/memory usage:

Create `k8s/hpa.yaml`:

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: ecommerce-frontend-hpa
  namespace: production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ecommerce-frontend
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70  # Scale when CPU > 70%
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80  # Scale when memory > 80%
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300  # Wait 5 min before scaling down
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60  # Scale down max 50% per minute
    scaleUp:
      stabilizationWindowSeconds: 0  # Scale up immediately
      policies:
      - type: Percent
        value: 100
        periodSeconds: 60  # Scale up max 100% per minute
```

Apply and monitor:
```bash
kubectl apply -f k8s/hpa.yaml

# Watch autoscaling in action
kubectl get hpa -n production -w

# Generate load to test
kubectl run -it --rm load-generator --image=busybox --restart=Never -- /bin/sh -c "while sleep 0.01; do wget -q -O- http://ecommerce-frontend; done"
```

### Cluster Autoscaler

Automatically add/remove nodes based on pod demand:

```bash
# Deploy cluster autoscaler
kubectl apply -f https://raw.githubusercontent.com/kubernetes/autoscaler/master/cluster-autoscaler/cloudprovider/aws/examples/cluster-autoscaler-autodiscover.yaml

# Edit deployment to add your cluster name
kubectl edit deployment cluster-autoscaler -n kube-system
# Add:
# --node-group-auto-discovery=asg:tag=k8s.io/cluster-autoscaler/enabled,k8s.io/cluster-autoscaler/ecommerce-cluster
# --balance-similar-node-groups
# --skip-nodes-with-system-pods=false
```

---

## 🎯 Production Readiness Checklist

Before going to production:

### Infrastructure
- [ ] EKS cluster created with at least 2 nodes in different AZs
- [ ] ECR repository created with image scanning enabled
- [ ] IAM roles and policies configured correctly
- [ ] VPC and subnets properly configured
- [ ] Security groups allow necessary traffic

### Application
- [ ] Docker image builds successfully
- [ ] All environment variables configured correctly
- [ ] Health checks working (liveness & readiness probes)
- [ ] Resource limits set (CPU & memory)
- [ ] Running as non-root user
- [ ] Image uses specific version tag (not `latest`)

### GitHub Actions
- [ ] All secrets added to GitHub
- [ ] Workflow triggers on correct branches
- [ ] Build and push to ECR succeeds
- [ ] Deployment to EKS succeeds
- [ ] Rollout verification works

### Kubernetes
- [ ] Namespace created
- [ ] Deployment configured with 2+ replicas
- [ ] Service exposes application via LoadBalancer
- [ ] Ingress configured (if using custom domain)
- [ ] SSL certificate configured (if using HTTPS)
- [ ] HPA configured for auto-scaling
- [ ] Network policies configured

### Monitoring & Logging
- [ ] CloudWatch Container Insights enabled
- [ ] Log aggregation working
- [ ] Metrics being collected
- [ ] Alarms configured for critical metrics
- [ ] Dashboard created for monitoring

### Security
- [ ] Secrets stored securely (not in code)
- [ ] Image scanning enabled
- [ ] Network policies configured
- [ ] RBAC configured
- [ ] Pod security standards enforced
- [ ] Regular security updates planned

### Documentation
- [ ] Deployment process documented
- [ ] Rollback procedure documented
- [ ] Troubleshooting guide available
- [ ] Runbook for common issues
- [ ] Architecture diagram created

### Testing
- [ ] Application accessible via LoadBalancer URL
- [ ] Health checks passing
- [ ] Zero-downtime deployment tested
- [ ] Rollback procedure tested
- [ ] Load testing performed
- [ ] Disaster recovery tested

---

## 📚 Additional Resources

### Documentation
- [AWS EKS Documentation](https://docs.aws.amazon.com/eks/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Amazon ECR Documentation](https://docs.aws.amazon.com/ecr/)

### Tools
- [eksctl - EKS CLI](https://eksctl.io/)
- [kubectl - Kubernetes CLI](https://kubernetes.io/docs/reference/kubectl/)
- [k9s - Kubernetes TUI](https://k9scli.io/)
- [stern - Multi-pod log tailing](https://github.com/stern/stern)

### Tutorials
- [EKS Workshop](https://www.eksworkshop.com/)
- [Kubernetes By Example](https://kubernetesbyexample.com/)
- [Docker Curriculum](https://docker-curriculum.com/)

---

## 📝 Summary

**What You've Learned:**
1. **Multi-stage Docker builds** for optimal image size and security
2. **Pushing images to ECR** with proper tagging and versioning
3. **Deploying to EKS** with kubectl and Kubernetes manifests
4. **Automating deployments** with GitHub Actions CI/CD pipeline
5. **Using GitHub Secrets** for sensitive data
6. **Zero-downtime deployments** with rolling updates
7. **Monitoring and troubleshooting** Kubernetes applications

**Your Production Infrastructure:**
```
┌─────────────────┐
│  Developer      │
│  pushes code    │
└────────┬────────┘
         │
         v
┌─────────────────────┐
│  GitHub Actions     │
│  - Build image      │
│  - Push to ECR      │
│  - Deploy to EKS    │
└────────┬────────────┘
         │
         v
┌─────────────────────┐
│  Amazon ECR         │
│  - Store images     │
│  - Scan for vulns   │
└────────┬────────────┘
         │
         v
┌─────────────────────────────────┐
│  Amazon EKS Cluster             │
│  ┌─────────────────────────┐   │
│  │  Deployment             │   │
│  │  ├─ Pod 1 (frontend)    │   │
│  │  └─ Pod 2 (frontend)    │   │
│  └─────────┬───────────────┘   │
│            │                    │
│  ┌─────────v───────────────┐   │
│  │  Service (LoadBalancer) │   │
│  └─────────┬───────────────┘   │
└────────────┼───────────────────┘
             │
             v
┌────────────────────┐
│  AWS Load Balancer │
│  (Public IP)       │
└────────┬───────────┘
         │
         v
   ┌─────────┐
   │  Users  │
   └─────────┘
```

**Next Steps:**
1. ✅ Setup complete - Your app is deployed!
2. [ ] Configure custom domain with Route53
3. [ ] Add SSL certificate from ACM
4. [ ] Set up CloudFront CDN
5. [ ] Configure auto-scaling policies
6. [ ] Set up monitoring dashboards
7. [ ] Implement backup strategy
8. [ ] Plan disaster recovery

---

**Questions or Issues?**
- Check the [Troubleshooting](#troubleshooting) section
- Review pod/deployment logs with `kubectl logs`
- Check AWS CloudWatch for detailed metrics
- Review GitHub Actions logs for CI/CD issues

**Good luck with your deployment! 🚀**
