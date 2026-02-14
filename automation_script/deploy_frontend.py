#!/usr/bin/env python3
"""
Kubernetes Deployment Automation Script for E-commerce Frontend
Automates the deployment process with namespace, secrets, and ingress setup.
"""

import subprocess
import sys
import json
import time
from typing import Tuple, Optional


class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'


def print_step(step_num: int, message: str):
    """Print a formatted step message"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}[STEP {step_num}]{Colors.END} {message}")


def print_success(message: str):
    """Print a success message"""
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")


def print_info(message: str):
    """Print an info message"""
    print(f"{Colors.BLUE}ℹ {message}{Colors.END}")


def print_warning(message: str):
    """Print a warning message"""
    print(f"{Colors.YELLOW}⚠ {message}{Colors.END}")


def print_error(message: str):
    """Print an error message"""
    print(f"{Colors.RED}✗ {message}{Colors.END}")


def run_command(command: str, check: bool = True, capture_output: bool = True) -> Tuple[int, str, str]:
    """
    Run a shell command and return the result

    Args:
        command: Command to execute
        check: Whether to raise exception on non-zero exit
        capture_output: Whether to capture stdout/stderr

    Returns:
        Tuple of (return_code, stdout, stderr)
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=check,
            capture_output=capture_output,
            text=True
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return e.returncode, e.stdout if e.stdout else "", e.stderr if e.stderr else ""


def check_kubectl():
    """Check if kubectl is installed and accessible"""
    print_info("Checking kubectl installation...")
    returncode, stdout, stderr = run_command("kubectl version --client --output=json", check=False)

    if returncode != 0:
        print_error("kubectl is not installed or not in PATH")
        print_error(f"Error: {stderr}")
        sys.exit(1)

    try:
        version_info = json.loads(stdout)
        client_version = version_info.get('clientVersion', {}).get('gitVersion', 'unknown')
        print_success(f"kubectl found (version: {client_version})")
    except json.JSONDecodeError:
        print_success("kubectl found")


def check_cluster_connection():
    """Check if we can connect to the Kubernetes cluster"""
    print_info("Checking cluster connection...")
    returncode, stdout, stderr = run_command("kubectl cluster-info", check=False)

    if returncode != 0:
        print_error("Cannot connect to Kubernetes cluster")
        print_error(f"Error: {stderr}")
        sys.exit(1)

    print_success("Connected to Kubernetes cluster")


def namespace_exists(namespace: str) -> bool:
    """Check if a namespace exists"""
    command = f"kubectl get namespace {namespace} --output=json"
    returncode, stdout, stderr = run_command(command, check=False)
    return returncode == 0


def secret_exists(secret_name: str, namespace: str) -> bool:
    """Check if a secret exists in a namespace"""
    command = f"kubectl get secret {secret_name} -n {namespace} --output=json"
    returncode, stdout, stderr = run_command(command, check=False)
    return returncode == 0


def clusterissuer_exists(issuer_name: str) -> bool:
    """Check if a ClusterIssuer exists"""
    command = f"kubectl get clusterissuer {issuer_name} --output=json"
    returncode, stdout, stderr = run_command(command, check=False)
    return returncode == 0


def delete_secret(secret_name: str, namespace: str) -> bool:
    """Delete a secret from a namespace"""
    command = f"kubectl delete secret {secret_name} -n {namespace}"
    returncode, stdout, stderr = run_command(command, check=False)

    if returncode == 0:
        print_success(f"Deleted secret '{secret_name}'")
        return True
    else:
        print_error(f"Failed to delete secret '{secret_name}': {stderr}")
        return False


def apply_yaml(yaml_file: str, namespace: Optional[str] = None) -> bool:
    """Apply a Kubernetes YAML file"""
    namespace_flag = f"-n {namespace}" if namespace else ""
    command = f"kubectl apply -f {yaml_file} {namespace_flag}".strip()

    print_info(f"Applying {yaml_file}...")
    returncode, stdout, stderr = run_command(command, check=False)

    if returncode == 0:
        print_success(f"Applied {yaml_file}")
        print(f"  {stdout.strip()}")
        return True
    else:
        print_error(f"Failed to apply {yaml_file}")
        print_error(f"  {stderr.strip()}")
        return False


def get_ingress_endpoints(ingress_name: str, namespace: str) -> list:
    """Get the ingress endpoints (hostnames)"""
    command = f"kubectl get ingress {ingress_name} -n {namespace} -o jsonpath='{{range .spec.rules[*]}}{{.host}}{{\"\\n\"}}{{end}}'"
    returncode, stdout, stderr = run_command(command, check=False)

    if returncode == 0 and stdout.strip():
        return [host.strip() for host in stdout.strip().split('\n') if host.strip()]
    return []


def wait_for_ingress(ingress_name: str, namespace: str, timeout: int = 60):
    """Wait for ingress to be created and get IP/hostname"""
    print_info(f"Waiting for ingress '{ingress_name}' to be ready...")

    start_time = time.time()
    while time.time() - start_time < timeout:
        command = f"kubectl get ingress {ingress_name} -n {namespace} -o jsonpath='{{.status.loadBalancer.ingress[0].ip}}'"
        returncode, stdout, stderr = run_command(command, check=False)

        if returncode == 0 and stdout.strip():
            print_success(f"Ingress IP: {stdout.strip()}")
            return

        # Check for hostname instead of IP (AWS ELB)
        command = f"kubectl get ingress {ingress_name} -n {namespace} -o jsonpath='{{.status.loadBalancer.ingress[0].hostname}}'"
        returncode, stdout, stderr = run_command(command, check=False)

        if returncode == 0 and stdout.strip():
            print_success(f"Ingress Hostname: {stdout.strip()}")
            return

        time.sleep(5)

    print_warning(f"Ingress not ready after {timeout} seconds (this is normal, it may take a few minutes)")


def main():
    """Main deployment automation function"""

    # Configuration
    NAMESPACE = "ecommerce-frontend-ns"
    SECRET_NAME = "ecommerce-frontend-tls-secret"
    # PRODUCTION configuration (trusted SSL certificates)
    CLUSTERISSUER_NAME = "letsencrypt-prod"
    # For testing (unlimited requests), use: "letsencrypt-staging"
    INGRESS_NAME = "ecommerce-frontend-ingress"

    # YAML files (relative to script location in automation_script/)
    NAMESPACE_YAML = "../deployment/namespace.yaml"
    # PRODUCTION issuer (limited to 5 certs/week)
    CLUSTERISSUER_YAML = "../deployment/clusterissuer.yaml"
    CERTIFICATE_YAML = "../deployment/certificate.yaml"
    # For testing (unlimited requests), use:
    # CLUSTERISSUER_YAML = "../deployment/clusterissuer-staging.yaml"
    # CERTIFICATE_YAML = "../deployment/certificate-staging.yaml"
    DEPLOYMENT_YAML = "../deployment/deployment.yaml"
    SERVICE_YAML = "../deployment/service.yaml"
    INGRESS_YAML = "../deployment/frontend-ingress.yaml"

    print(f"{Colors.BOLD}{Colors.HEADER}")
    print("=" * 70)
    print("  E-COMMERCE FRONTEND DEPLOYMENT AUTOMATION")
    print("=" * 70)
    print(f"{Colors.END}")

    # Pre-flight checks
    check_kubectl()
    check_cluster_connection()

    # ============================================
    # STEP 1: Check if namespace exists
    # ============================================
    print_step(1, f"Checking if namespace '{NAMESPACE}' exists...")

    if namespace_exists(NAMESPACE):
        print_success(f"Namespace '{NAMESPACE}' already exists")
        print_warning("Skipping remaining deployment steps as namespace exists")
        print_info("To redeploy, delete the namespace first with:")
        print_info(f"  kubectl delete namespace {NAMESPACE}")
        sys.exit(0)
    else:
        print_info(f"Namespace '{NAMESPACE}' does not exist")

    # ============================================
    # STEP 2: Create namespace
    # ============================================
    print_step(2, f"Creating namespace '{NAMESPACE}'...")

    if not apply_yaml(NAMESPACE_YAML):
        print_error("Failed to create namespace. Exiting.")
        sys.exit(1)

    # Wait a moment for namespace to be ready
    time.sleep(2)

    # ============================================
    # STEP 3: Check and delete secret if exists
    # ============================================
    print_step(3, f"Checking if secret '{SECRET_NAME}' exists...")

    if secret_exists(SECRET_NAME, NAMESPACE):
        print_warning(f"Secret '{SECRET_NAME}' already exists")
        delete_secret(SECRET_NAME, NAMESPACE)
    else:
        print_info(f"Secret '{SECRET_NAME}' does not exist (this is expected)")

    # ============================================
    # STEP 4: Check and create ClusterIssuer
    # ============================================
    print_step(4, f"Checking if ClusterIssuer '{CLUSTERISSUER_NAME}' exists...")

    if clusterissuer_exists(CLUSTERISSUER_NAME):
        print_success(f"ClusterIssuer '{CLUSTERISSUER_NAME}' already exists")
        print_info("Skipping ClusterIssuer creation")
    else:
        print_info(f"ClusterIssuer '{CLUSTERISSUER_NAME}' does not exist")
        if not apply_yaml(CLUSTERISSUER_YAML):
            print_error("Failed to create ClusterIssuer. Exiting.")
            sys.exit(1)

    # ============================================
    # STEP 5: Create Certificate
    # ============================================
    print_step(5, "Creating Let's Encrypt certificate...")

    if not apply_yaml(CERTIFICATE_YAML):
        print_error("Failed to create certificate. Continuing anyway...")

    # Wait for certificate to be processed
    time.sleep(3)

    # ============================================
    # STEP 6: Apply deployment, service, and ingress
    # ============================================
    print_step(6, "Deploying application resources...")

    yaml_files = [
        DEPLOYMENT_YAML,
        SERVICE_YAML,
        INGRESS_YAML
    ]

    success = True
    for yaml_file in yaml_files:
        if not apply_yaml(yaml_file):
            success = False
            break

    if not success:
        print_error("Deployment failed. Please check the errors above.")
        sys.exit(1)

    # Wait for resources to be created
    time.sleep(5)

    # ============================================
    # STEP 7: Get ingress endpoints
    # ============================================
    print_step(7, "Retrieving ingress endpoints...")

    endpoints = get_ingress_endpoints(INGRESS_NAME, NAMESPACE)

    if endpoints:
        print_success("Ingress configured with the following hosts:")
        for endpoint in endpoints:
            print(f"  {Colors.BOLD}{Colors.GREEN}→ https://{endpoint}{Colors.END}")
    else:
        print_warning("No ingress hosts found. Check your ingress configuration.")

    # Wait for ingress to get IP/hostname
    wait_for_ingress(INGRESS_NAME, NAMESPACE, timeout=60)

    # ============================================
    # Summary
    # ============================================
    print(f"\n{Colors.BOLD}{Colors.GREEN}")
    print("=" * 70)
    print("  DEPLOYMENT COMPLETED SUCCESSFULLY! 🎉")
    print("=" * 70)
    print(f"{Colors.END}")

    print(f"\n{Colors.BOLD}Next Steps:{Colors.END}")
    print("1. Check pod status:")
    print(f"   kubectl get pods -n {NAMESPACE}")
    print("\n2. Check service status:")
    print(f"   kubectl get svc -n {NAMESPACE}")
    print("\n3. Check ingress status:")
    print(f"   kubectl get ingress -n {NAMESPACE}")
    print("\n4. View pod logs:")
    print(f"   kubectl logs -f deployment/ecommerce-frontend -n {NAMESPACE}")
    print("\n5. Check certificate status:")
    print(f"   kubectl get certificate -n {NAMESPACE}")
    print(f"   kubectl describe certificate -n {NAMESPACE}")

    if endpoints:
        print(f"\n{Colors.BOLD}Access your application at:{Colors.END}")
        for endpoint in endpoints:
            print(f"  {Colors.CYAN}https://{endpoint}{Colors.END}")

    print(f"\n{Colors.YELLOW}Note: SSL certificate may take a few minutes to be issued by Let's Encrypt{Colors.END}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Deployment interrupted by user{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Unexpected error: {e}{Colors.END}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
