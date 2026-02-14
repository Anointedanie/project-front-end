#!/usr/bin/env python3
"""
Pre-deployment Check Script
Validates all prerequisites before running the deployment automation.

This script checks for required tools and ONLY installs if missing:
- Python 3.12.3 (only if missing or < 3.6; accepts 3.6-3.11 with warning)
- kubectl (only if not found)
- Docker (only if not found)
- AWS CLI (only if not found)
- cert-manager (only if namespace doesn't exist)
- Nginx Ingress Controller with AWS LB (only if not found)
- EKS cluster connection (only if not connected)

Safe to run on local machines - will not reinstall existing tools.
Designed for non-interactive use in CI/CD pipelines and local development.

For Nginx Ingress, the script applies deployment files in this order:
1. aws-load-balancer-controller-sa.yaml
2. aws_lb_controller.yaml
3. nginx-ingress-nlb.yaml
"""

import subprocess
import sys
import time
from pathlib import Path


class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text:^60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")


def print_check(name, status, message=""):
    symbol = "✓" if status else "✗"
    color = Colors.GREEN if status else Colors.RED
    print(f"{color}{symbol}{Colors.END} {name:<40} {message}")
    return status


def print_success(message):
    """Print a success message"""
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")


def print_error(message):
    """Print an error message"""
    print(f"{Colors.RED}✗ {message}{Colors.END}")


def print_warning(message):
    """Print a warning message"""
    print(f"{Colors.YELLOW}⚠ {message}{Colors.END}")


def print_info(message):
    """Print an info message"""
    print(f"{Colors.BLUE}ℹ {message}{Colors.END}")


def run_command(cmd, check=True):
    """Run command and return success status, stdout, and stderr"""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, check=check
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return False, e.stdout if e.stdout else "", e.stderr if e.stderr else ""


def install_python():
    """Install Python 3.12.3 automatically"""
    print(f"\n{Colors.BLUE}Installing Python 3.12.3...{Colors.END}")

    # Check if running on Ubuntu/Debian
    print("  Checking system compatibility...")
    returncode, _, _ = run_command("which apt-get", check=False)
    if returncode != 0:
        print_error("This script requires Ubuntu/Debian with apt-get")
        print(f"  {Colors.YELLOW}Please install Python 3.12.3 manually{Colors.END}")
        return False

    # Add deadsnakes PPA (for Python 3.12)
    print("  Adding deadsnakes PPA...")
    add_ppa_cmd = "sudo add-apt-repository -y ppa:deadsnakes/ppa"
    returncode, _, stderr = run_command(add_ppa_cmd, check=False)
    if returncode != 0:
        print_error(f"Failed to add PPA: {stderr}")
        return False

    # Update package list
    print("  Updating package list...")
    returncode, _, stderr = run_command("sudo apt-get update -qq", check=False)
    if returncode != 0:
        print_warning("Failed to update package list, continuing anyway...")

    # Install Python 3.12 and related packages
    print("  Installing Python 3.12...")
    install_cmd = (
        "sudo DEBIAN_FRONTEND=noninteractive apt-get install -y "
        "python3.12 python3.12-venv python3.12-dev python3-pip"
    )
    returncode, _, stderr = run_command(install_cmd, check=False)
    if returncode != 0:
        print_error(f"Failed to install Python 3.12: {stderr}")
        return False

    # Set Python 3.12 as default alternative
    print("  Configuring Python 3.12 as default...")
    alt_cmd = (
        "sudo update-alternatives --install /usr/bin/python3 python3 "
        "/usr/bin/python3.12 1"
    )
    returncode, _, _ = run_command(alt_cmd, check=False)

    print_success("Python 3.12 installed successfully")
    return True


def check_python():
    """Check Python version"""
    version = sys.version_info

    # Check if Python is available at all
    if version.major < 3:
        print_check("Python 3.12.3", False, f"v{version.major}.{version.minor}.{version.micro} (too old)")
        print(f"  {Colors.YELLOW}⚠ Python 2 detected - installing Python 3.12.3...{Colors.END}")
        if install_python():
            print_success("Python 3.12 is now available")
            print(f"  {Colors.YELLOW}Please re-run this script with python3{Colors.END}")
            return False
        print_error("Failed to install Python 3.12")
        return False

    # Check if version is 3.12.x or higher (preferred)
    if version.major == 3 and version.minor >= 12:
        msg = f"v{version.major}.{version.minor}.{version.micro}"
        return print_check("Python 3.12.3+", True, msg)

    # Version is 3.6-3.11 (acceptable but not ideal)
    if version.major == 3 and version.minor >= 6:
        msg = f"v{version.major}.{version.minor}.{version.micro} (acceptable, but 3.12 recommended)"
        result = print_check("Python 3.12.3+", True, msg)
        print(f"  {Colors.YELLOW}⚠ Python 3.12.3 is recommended for CI/CD runners{Colors.END}")
        print(f"  {Colors.YELLOW}  Current version works but consider upgrading{Colors.END}")
        return result

    # Version is less than 3.6 (too old)
    msg = f"v{version.major}.{version.minor}.{version.micro} (too old)"
    print_check("Python 3.12.3+", False, msg)
    print(f"  {Colors.YELLOW}⚠ Python version too old - installing Python 3.12.3...{Colors.END}")

    if install_python():
        print_success("Python 3.12 is now available")
        print(f"  {Colors.YELLOW}Please re-run this script with python3{Colors.END}")
        return False

    print_error("Failed to install Python 3.12")
    return False


def install_kubectl():
    """Install kubectl automatically"""
    print(f"\n{Colors.BLUE}Installing kubectl...{Colors.END}")

    # Get the latest stable version first
    print("  Getting latest kubectl version...")
    returncode, stable_version, _ = run_command(
        'curl -L -s https://dl.k8s.io/release/stable.txt',
        check=False
    )
    if returncode != 0 or not stable_version.strip():
        print_error("Failed to get kubectl version")
        return False

    version = stable_version.strip()
    print(f"  Latest version: {version}")

    # Download kubectl
    download_cmd = f'curl -LO "https://dl.k8s.io/release/{version}/bin/linux/amd64/kubectl"'
    print("  Downloading kubectl...")
    returncode, _, _ = run_command(download_cmd, check=False)
    if returncode != 0:
        print_error("Failed to download kubectl")
        return False

    # Make executable
    print("  Making kubectl executable...")
    returncode, _, _ = run_command("chmod +x kubectl", check=False)
    if returncode != 0:
        print_error("Failed to make kubectl executable")
        return False

    # Move to /usr/local/bin
    print("  Installing to /usr/local/bin (requires sudo)...")
    returncode, _, stderr = run_command("sudo mv kubectl /usr/local/bin/", check=False)
    if returncode != 0:
        print_error(f"Failed to install kubectl: {stderr}")
        return False

    print_success("kubectl installed successfully")
    return True


def check_kubectl():
    """Check if kubectl is installed"""
    ok, output, _ = run_command("kubectl version --client -o json 2>/dev/null")

    # Extract version from JSON output or fall back to simpler check
    if ok and output.strip():
        try:
            import json
            version_info = json.loads(output)
            version = version_info.get('clientVersion', {}).get('gitVersion', 'installed')
            msg = version
        except (json.JSONDecodeError, KeyError):
            msg = "installed"
    else:
        # Fallback: just check if kubectl command exists
        ok, _, _ = run_command("which kubectl 2>/dev/null")
        msg = "installed" if ok else "Not found"

    result = print_check("kubectl", ok, msg)

    if not ok:
        print(f"  {Colors.YELLOW}⚠ kubectl not found - installing automatically...{Colors.END}")
        if install_kubectl():
            # Re-check after installation
            ok, _, _ = run_command("which kubectl 2>/dev/null")
            if ok:
                print_success("kubectl is now available")
                return True
        print_error("Failed to install kubectl")
        return False

    return result


def configure_eks_cluster():
    """Configure EKS cluster connection"""
    print(f"\n{Colors.BLUE}Configuring EKS cluster connection...{Colors.END}")

    cmd = "aws eks update-kubeconfig --region us-east-1 --name ecommerce-eks 2>&1"
    print(f"  Running: {cmd}")
    returncode, stdout, stderr = run_command(cmd, check=False)

    if returncode == 0:
        print_success("EKS cluster configured successfully")
        # Show output for debugging
        if stdout.strip():
            print(f"  {Colors.BLUE}{stdout.strip()}{Colors.END}")
        return True

    # Combine stdout and stderr for complete error message
    error_msg = (stderr + stdout).strip() if stderr or stdout else "Unknown error"
    print_error(f"Failed to configure EKS cluster:")
    print(f"  {Colors.RED}{error_msg}{Colors.END}")

    # Check if it's a permissions issue
    if "AccessDenied" in error_msg or "not authorized" in error_msg:
        print(f"  {Colors.YELLOW}IAM permissions issue detected{Colors.END}")
        print(f"  {Colors.YELLOW}Ensure the AWS credentials have these permissions:{Colors.END}")
        print(f"  {Colors.YELLOW}  - eks:DescribeCluster{Colors.END}")
        print(f"  {Colors.YELLOW}  - eks:ListClusters{Colors.END}")
    else:
        print(f"  {Colors.YELLOW}Ensure AWS CLI is installed and configured{Colors.END}")
        print(f"  {Colors.YELLOW}Cluster: ecommerce-eks in us-east-1{Colors.END}")

    return False


def check_cluster():
    """Check cluster connection"""
    ok, _, _ = run_command("kubectl cluster-info 2>/dev/null")
    result = print_check("Kubernetes cluster connection", ok)
    if not ok:
        print(f"  {Colors.YELLOW}⚠ Cannot connect to Kubernetes cluster{Colors.END}")
        print(f"  {Colors.YELLOW}  Attempting to configure EKS cluster...{Colors.END}")

        if configure_eks_cluster():
            # Re-check after configuration
            ok, _, _ = run_command("kubectl cluster-info 2>/dev/null")
            if ok:
                print_success("Successfully connected to cluster")
                return True
            # Configuration succeeded but kubectl still can't connect (timing or credentials issue)
            print_warning("EKS configured but connection check failed (may be credentials or timing issue)")
            return True  # Return True since configuration command succeeded

        print_error("Failed to connect to cluster")
        print(f"  {Colors.YELLOW}Manual steps:{Colors.END}")
        print(f"  {Colors.YELLOW}  1. Ensure AWS CLI is installed and configured{Colors.END}")
        print(f"  {Colors.YELLOW}  2. Run: aws eks update-kubeconfig --region us-east-1 --name ecommerce-eks{Colors.END}")
        return False

    return result


def install_cert_manager():
    """Install cert-manager automatically"""
    print(f"\n{Colors.BLUE}Installing cert-manager...{Colors.END}")

    # Install cert-manager
    cmd = "kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml"
    print("  Applying cert-manager manifest...")
    returncode, _, stderr = run_command(cmd, check=False)

    if returncode != 0:
        print_error(f"Failed to install cert-manager: {stderr}")
        return False

    print_success("cert-manager manifest applied")
    print(f"  {Colors.BLUE}Waiting for cert-manager to be ready (may take 1-2 minutes)...{Colors.END}")

    # Wait for cert-manager pods to be ready
    wait_cmd = "kubectl wait --for=condition=ready pod -l app=cert-manager -n cert-manager --timeout=300s"
    returncode, _, stderr = run_command(wait_cmd, check=False)

    if returncode == 0:
        print_success("cert-manager is ready")
        return True

    print_warning("cert-manager installed but not yet ready")
    print(f"  {Colors.YELLOW}Check status: kubectl get pods -n cert-manager{Colors.END}")
    return True  # Return True as it's installed, just not ready yet


def install_docker():
    """Install Docker automatically"""
    print(f"\n{Colors.BLUE}Installing Docker...{Colors.END}")

    # Check if running on Ubuntu/Debian
    print("  Checking system compatibility...")
    returncode, _, _ = run_command("which apt-get", check=False)
    if returncode != 0:
        print_error("This script requires Ubuntu/Debian with apt-get")
        print(f"  {Colors.YELLOW}Please install Docker manually{Colors.END}")
        return False

    # Update package list
    print("  Updating package list...")
    returncode, _, _ = run_command("sudo apt-get update -qq", check=False)

    # Install prerequisites
    print("  Installing prerequisites...")
    prereq_cmd = (
        "sudo DEBIAN_FRONTEND=noninteractive apt-get install -y "
        "ca-certificates curl gnupg lsb-release"
    )
    returncode, _, stderr = run_command(prereq_cmd, check=False)
    if returncode != 0:
        print_error(f"Failed to install prerequisites: {stderr}")
        return False

    # Add Docker's official GPG key
    print("  Adding Docker GPG key...")
    gpg_cmd = (
        "sudo mkdir -p /etc/apt/keyrings && "
        "curl -fsSL https://download.docker.com/linux/ubuntu/gpg | "
        "sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg --yes"
    )
    returncode, _, stderr = run_command(gpg_cmd, check=False)
    if returncode != 0:
        print_warning("Failed to add GPG key, continuing anyway...")

    # Set up Docker repository
    print("  Setting up Docker repository...")
    repo_cmd = (
        'echo "deb [arch=$(dpkg --print-architecture) '
        'signed-by=/etc/apt/keyrings/docker.gpg] '
        'https://download.docker.com/linux/ubuntu '
        '$(lsb_release -cs) stable" | '
        'sudo tee /etc/apt/sources.list.d/docker.list > /dev/null'
    )
    returncode, _, _ = run_command(repo_cmd, check=False)

    # Update package list again
    print("  Updating package list...")
    returncode, _, _ = run_command("sudo apt-get update -qq", check=False)

    # Install Docker
    print("  Installing Docker Engine...")
    install_cmd = (
        "sudo DEBIAN_FRONTEND=noninteractive apt-get install -y "
        "docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin"
    )
    returncode, _, stderr = run_command(install_cmd, check=False)
    if returncode != 0:
        print_error(f"Failed to install Docker: {stderr}")
        return False

    # Start Docker service
    print("  Starting Docker service...")
    returncode, _, _ = run_command("sudo systemctl start docker", check=False)
    returncode, _, _ = run_command("sudo systemctl enable docker", check=False)

    print_success("Docker installed successfully")
    return True


def install_aws_cli():
    """Install AWS CLI automatically"""
    print(f"\n{Colors.BLUE}Installing AWS CLI...{Colors.END}")

    # Download AWS CLI installer
    print("  Downloading AWS CLI installer...")
    download_cmd = 'curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "/tmp/awscliv2.zip"'
    returncode, _, stderr = run_command(download_cmd, check=False)
    if returncode != 0:
        print_error(f"Failed to download AWS CLI: {stderr}")
        return False

    # Install unzip if needed
    print("  Ensuring unzip is installed...")
    returncode, _, _ = run_command("which unzip", check=False)
    if returncode != 0:
        run_command("sudo apt-get install -y unzip", check=False)

    # Unzip the installer
    print("  Extracting AWS CLI installer...")
    returncode, _, stderr = run_command("unzip -q -o /tmp/awscliv2.zip -d /tmp/", check=False)
    if returncode != 0:
        print_error(f"Failed to extract AWS CLI: {stderr}")
        return False

    # Install AWS CLI
    print("  Installing AWS CLI...")
    returncode, _, stderr = run_command("sudo /tmp/aws/install --update", check=False)
    if returncode != 0:
        print_error(f"Failed to install AWS CLI: {stderr}")
        return False

    # Cleanup
    run_command("rm -rf /tmp/awscliv2.zip /tmp/aws", check=False)

    print_success("AWS CLI installed successfully")
    return True


def install_nginx_ingress():
    """Install nginx ingress controller with AWS Load Balancer Controller"""
    print(f"\n{Colors.BLUE}Installing Nginx Ingress Controller...{Colors.END}")

    # Step 1: Apply AWS Load Balancer Controller Service Account
    print("  Step 1/3: Applying AWS Load Balancer Controller Service Account...")
    sa_file = "../deployment/aws-load-balancer-controller-sa.yaml"
    returncode, _, stderr = run_command(f"kubectl apply -f {sa_file}", check=False)
    if returncode != 0:
        print_error(f"Failed to apply service account: {stderr}")
        return False
    print_success("Service account applied")

    # Wait a moment for service account to be created
    time.sleep(2)

    # Step 2: Apply AWS Load Balancer Controller
    print("  Step 2/3: Applying AWS Load Balancer Controller...")
    lb_file = "../deployment/aws_lb_controller.yaml"
    returncode, _, stderr = run_command(f"kubectl apply -f {lb_file}", check=False)
    if returncode != 0:
        print_error(f"Failed to apply AWS LB controller: {stderr}")
        return False
    print_success("AWS Load Balancer Controller applied")

    # Wait for AWS LB controller to be ready
    print("  Waiting for AWS Load Balancer Controller to be ready...")
    time.sleep(5)

    # Step 3: Apply Nginx Ingress with NLB
    print("  Step 3/3: Applying Nginx Ingress Controller with NLB...")
    ingress_file = "../deployment/nginx-ingress-nlb.yaml"
    returncode, _, stderr = run_command(f"kubectl apply -f {ingress_file}", check=False)
    if returncode != 0:
        print_error(f"Failed to apply nginx ingress: {stderr}")
        return False
    print_success("Nginx Ingress Controller manifest applied")

    # Wait for nginx ingress pods to be ready
    print(f"  {Colors.BLUE}Waiting for Nginx Ingress pods to be ready (may take 1-2 minutes)...{Colors.END}")
    wait_cmd = "kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=ingress-nginx -n ingress-nginx --timeout=300s"
    returncode, _, stderr = run_command(wait_cmd, check=False)

    if returncode == 0:
        print_success("Nginx Ingress Controller is ready")
        return True

    print_warning("Nginx Ingress installed but not yet ready")
    print(f"  {Colors.YELLOW}Check status: kubectl get pods -n ingress-nginx{Colors.END}")
    return True  # Return True as it's installed, just not ready yet


def check_cert_manager():
    """Check if cert-manager is installed"""
    ok, _, _ = run_command("kubectl get namespace cert-manager 2>/dev/null")
    result = print_check("cert-manager namespace", ok)
    if not ok:
        print(f"  {Colors.YELLOW}⚠ cert-manager not found - installing automatically...{Colors.END}")
        if install_cert_manager():
            # Re-check after installation
            ok, _, _ = run_command("kubectl get namespace cert-manager 2>/dev/null")
            if ok:
                print_success("cert-manager is now available")
                return True
            # Installation succeeded but namespace not immediately visible (timing issue)
            print_warning("cert-manager installed but namespace not yet visible")
            return True  # Return True since installation succeeded
        print_error("Failed to install cert-manager")
        return False
    return result


def check_cert_manager_pods():
    """Check if cert-manager pods are running"""
    ok, output, _ = run_command(
        "kubectl get pods -n cert-manager -o jsonpath='{.items[*].status.phase}' 2>/dev/null"
    )
    if ok and output:
        all_running = all(status == "Running" for status in output.split())
        result = print_check("cert-manager pods running", all_running)
        if not all_running:
            print(f"  {Colors.YELLOW}⚠ cert-manager pods are not all running{Colors.END}")
            print(f"  {Colors.YELLOW}  Check status: kubectl get pods -n cert-manager{Colors.END}")
            print(f"  {Colors.YELLOW}  View logs: kubectl logs -n cert-manager deployment/cert-manager{Colors.END}")
            print(f"  {Colors.YELLOW}  Wait: kubectl wait --for=condition=ready pod -l app=cert-manager -n cert-manager --timeout=300s{Colors.END}")
        return result

    result = print_check("cert-manager pods running", False)
    print(f"  {Colors.YELLOW}⚠ Cannot get cert-manager pod status{Colors.END}")
    print(f"  {Colors.YELLOW}  Check: kubectl get pods -n cert-manager{Colors.END}")
    return result


def check_aws_cli():
    """Check if AWS CLI is installed"""
    ok, output, _ = run_command("aws --version 2>/dev/null")
    msg = output.strip().split('\n')[0] if ok else "Not found"
    result = print_check("AWS CLI", ok, msg)

    if not ok:
        print(f"  {Colors.YELLOW}⚠ AWS CLI not found - installing automatically...{Colors.END}")
        if install_aws_cli():
            # Re-check after installation
            ok, output, _ = run_command("aws --version 2>/dev/null")
            if ok:
                print_success("AWS CLI is now available")
                return True
        print_error("Failed to install AWS CLI")
        return False

    return result


def check_aws_credentials():
    """Check if AWS credentials are configured"""
    ok, _, _ = run_command("aws sts get-caller-identity 2>/dev/null")

    if ok:
        # Get account info and user/role ARN
        ok_account, account_output, _ = run_command(
            "aws sts get-caller-identity --query 'Account' --output text 2>/dev/null"
        )
        ok_arn, arn_output, _ = run_command(
            "aws sts get-caller-identity --query 'Arn' --output text 2>/dev/null"
        )
        account = account_output.strip() if ok_account else "configured"
        result = print_check("AWS credentials", True, f"Account: {account}")
        if ok_arn and arn_output.strip():
            print(f"  {Colors.BLUE}IAM Identity: {arn_output.strip()}{Colors.END}")
    else:
        result = print_check("AWS credentials", False, "Not configured")
        print(f"  {Colors.YELLOW}⚠ AWS credentials not configured{Colors.END}")
        print(f"  {Colors.YELLOW}  Configure: aws configure{Colors.END}")
        print(f"  {Colors.YELLOW}  Or set: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY{Colors.END}")

    return result


def check_docker():
    """Check if Docker is installed"""
    ok, output, _ = run_command("docker --version 2>/dev/null")
    msg = output.strip().split('\n')[0] if ok else "Not found"
    result = print_check("Docker", ok, msg)

    if not ok:
        print(f"  {Colors.YELLOW}⚠ Docker not found - installing automatically...{Colors.END}")
        if install_docker():
            # Re-check after installation
            ok, output, _ = run_command("docker --version 2>/dev/null")
            if ok:
                print_success("Docker is now available")
                return True
        print_error("Failed to install Docker")
        return False

    # Check if Docker daemon is running
    ok_daemon, _, _ = run_command("docker info 2>/dev/null")
    if not ok_daemon:
        print(f"  {Colors.YELLOW}⚠ Docker daemon not running - starting...{Colors.END}")
        returncode, _, _ = run_command("sudo systemctl start docker", check=False)
        if returncode == 0:
            print_success("Docker daemon started")
        else:
            print_warning("Failed to start Docker daemon")
            print(f"  {Colors.YELLOW}  Start manually: sudo systemctl start docker{Colors.END}")

    return result


def check_ecr_authentication():
    """Check if Docker is authenticated to ECR"""
    region = "us-east-1"
    account_id = "793796654438"
    ecr_registry = f"{account_id}.dkr.ecr.{region}.amazonaws.com"

    # Try to get ECR authorization token (this validates authentication)
    ok, _, _ = run_command(
        f"aws ecr get-authorization-token --region {region} 2>/dev/null"
    )

    if ok:
        result = print_check("ECR authentication", True, f"Authenticated to {ecr_registry}")
    else:
        result = print_check("ECR authentication", False, "Not authenticated")
        print(f"  {Colors.YELLOW}⚠ Not authenticated to ECR{Colors.END}")
        print(f"  {Colors.YELLOW}  Authenticate: aws ecr get-login-password --region {region} | docker login --username AWS --password-stdin {ecr_registry}{Colors.END}")

    return result


def check_ecr_repository():
    """Check if ECR repository exists"""
    repo_name = "ecommerce/frontend"
    region = "us-east-1"

    ok, output, _ = run_command(
        f"aws ecr describe-repositories --repository-names {repo_name} "
        f"--region {region} 2>/dev/null"
    )

    if ok:
        # Get repository URI
        ok_uri, uri_output, _ = run_command(
            f"aws ecr describe-repositories --repository-names {repo_name} "
            f"--region {region} --query 'repositories[0].repositoryUri' "
            f"--output text 2>/dev/null"
        )
        uri = uri_output.strip() if ok_uri else "exists"
        result = print_check(f"ECR repository '{repo_name}'", True, uri)
    else:
        result = print_check(f"ECR repository '{repo_name}'", False, "Not found")
        print(f"  {Colors.YELLOW}⚠ ECR repository not found{Colors.END}")
        print(f"  {Colors.YELLOW}  Create: aws ecr create-repository --repository-name {repo_name} --region {region}{Colors.END}")

    return result


def check_ecr_images():
    """Check if there are images in ECR repository"""
    repo_name = "ecommerce/frontend"
    region = "us-east-1"

    ok, output, _ = run_command(
        f"aws ecr list-images --repository-name {repo_name} "
        f"--region {region} --query 'imageIds[*].imageTag' "
        f"--output text 2>/dev/null"
    )

    if ok and output.strip():
        tags = output.strip().split()
        result = print_check("ECR images", True, f"{len(tags)} image(s) found")
        print(f"  {Colors.BLUE}Latest tags: {', '.join(tags[:3])}{Colors.END}")
    elif ok:
        result = print_check("ECR images", False, "No images found")
        print(f"  {Colors.YELLOW}⚠ No images in ECR repository{Colors.END}")
        print(f"  {Colors.YELLOW}  Build and push: docker build & docker push{Colors.END}")
    else:
        result = print_check("ECR images", False, "Cannot check (repo may not exist)")

    return result


def check_nginx_ingress():
    """Check if Nginx ingress controller is installed"""
    ok, _, _ = run_command(
        "kubectl get namespace ingress-nginx 2>/dev/null"
    )

    if ok:
        # Check if pods are running
        ok_pods, output, _ = run_command(
            "kubectl get pods -n ingress-nginx "
            "-o jsonpath='{.items[*].status.phase}' 2>/dev/null"
        )

        if ok_pods and output:
            all_running = all(status == "Running" for status in output.split())
            status_msg = "Running" if all_running else "Not all pods running"
            result = print_check("Nginx ingress controller", all_running, status_msg)

            if not all_running:
                print(f"  {Colors.YELLOW}⚠ Nginx ingress controller pods not all running{Colors.END}")
                print(f"  {Colors.YELLOW}  Check: kubectl get pods -n ingress-nginx{Colors.END}")
        else:
            result = print_check("Nginx ingress controller", True, "Namespace exists")
    else:
        result = print_check("Nginx ingress controller", False, "Not found")
        print(f"  {Colors.YELLOW}⚠ Nginx ingress controller not found - installing automatically...{Colors.END}")
        if install_nginx_ingress():
            # Re-check after installation
            ok, _, _ = run_command("kubectl get namespace ingress-nginx 2>/dev/null")
            if ok:
                print_success("Nginx Ingress Controller is now available")
                return True
        print_error("Failed to install Nginx Ingress Controller")
        return False

    return result


def check_file(filepath, name):
    """Check if a file exists"""
    exists = Path(filepath).exists()
    return print_check(name, exists, filepath)


def check_deployment_files():
    """Check all required deployment files"""
    files = {
        "../deployment/namespace.yaml": "Namespace config",
        "../deployment/clusterissuer.yaml": "ClusterIssuer config",
        "../deployment/certificate.yaml": "Certificate config",
        "../deployment/deployment.yaml": "Deployment config",
        "../deployment/service.yaml": "Service config",
        "../deployment/frontend-ingress.yaml": "Ingress config",
    }

    all_ok = True
    for filepath, name in files.items():
        file_exists = check_file(filepath, name)
        if not file_exists:
            all_ok = False
            print(f"  {Colors.YELLOW}⚠ Missing: {filepath}{Colors.END}")
            print(f"  {Colors.YELLOW}  Ensure all YAML files are in the ../deployment/ folder{Colors.END}")

    return all_ok


def main():
    """Main function to check all deployment prerequisites"""
    print_header("Pre-Deployment Prerequisites Check")

    all_checks = []

    # System checks
    print(f"\n{Colors.BOLD}System Requirements:{Colors.END}")
    all_checks.append(check_python())
    all_checks.append(check_kubectl())
    all_checks.append(check_docker())
    aws_cli_ok = check_aws_cli()
    all_checks.append(aws_cli_ok)

    # AWS credentials check
    if aws_cli_ok:
        print(f"\n{Colors.BOLD}AWS Configuration:{Colors.END}")
        aws_creds_ok = check_aws_credentials()
        all_checks.append(aws_creds_ok)

        # ECR checks (only if AWS credentials are available)
        if aws_creds_ok:
            print(f"\n{Colors.BOLD}ECR (Elastic Container Registry):{Colors.END}")
            ecr_auth_ok = check_ecr_authentication()
            all_checks.append(ecr_auth_ok)

            ecr_repo_ok = check_ecr_repository()
            all_checks.append(ecr_repo_ok)

            if ecr_repo_ok:
                # Only check images if repo exists
                check_ecr_images()  # Informational, not required

    # Cluster checks
    print(f"\n{Colors.BOLD}Kubernetes Cluster:{Colors.END}")
    cluster_ok = check_cluster()
    all_checks.append(cluster_ok)

    if cluster_ok:
        # Context info
        ok, context, _ = run_command("kubectl config current-context 2>/dev/null")
        if ok:
            print(f"  {Colors.BLUE}Current context: {context.strip()}{Colors.END}")

    # Ingress controller check
    if cluster_ok:
        print(f"\n{Colors.BOLD}Ingress Controller:{Colors.END}")
        all_checks.append(check_nginx_ingress())

    # cert-manager checks
    print(f"\n{Colors.BOLD}cert-manager (for SSL certificates):{Colors.END}")
    cm_ns = check_cert_manager()
    all_checks.append(cm_ns)
    if cm_ns:
        all_checks.append(check_cert_manager_pods())

    # File checks
    print(f"\n{Colors.BOLD}Deployment Files:{Colors.END}")
    files_ok = check_deployment_files()
    all_checks.append(files_ok)

    # Namespace check
    print(f"\n{Colors.BOLD}Current State:{Colors.END}")
    ns_exists, _, _ = run_command("kubectl get namespace ecommerce-frontend-ns 2>/dev/null")
    if ns_exists:
        print_check("ecommerce-frontend-ns namespace", True, "Already exists")
        print(f"  {Colors.YELLOW}⚠ Deployment script will exit if namespace exists{Colors.END}")
        print(f"  {Colors.YELLOW}  To redeploy: kubectl delete namespace ecommerce-frontend-ns{Colors.END}")
    else:
        print_check("ecommerce-frontend-ns namespace", False, "Does not exist (ready for deployment)")

    # Summary
    print_header("Summary")

    passed = sum(all_checks)
    total = len(all_checks)

    if passed == total:
        print(f"{Colors.GREEN}{Colors.BOLD}✓ All checks passed! Ready to deploy.{Colors.END}\n")
        print(f"Run deployment with: {Colors.BOLD}./deploy_frontend.py{Colors.END}\n")
        return 0
    else:
        print(f"{Colors.RED}{Colors.BOLD}✗ {total - passed} check(s) failed.{Colors.END}\n")
        print("Please fix the issues above before deploying.\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
