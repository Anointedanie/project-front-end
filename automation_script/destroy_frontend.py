#!/usr/bin/env python3
"""
Kubernetes Cleanup/Destroy Script for E-commerce Frontend
Safely removes all resources created by deploy_frontend.py

This script will:
1. Delete the namespace (removes deployment, service, ingress, certificate, secrets)
2. Optionally delete the ClusterIssuer (cluster-wide resource)

Non-interactive by default - suitable for CI/CD pipelines.
"""

import subprocess
import sys
import time
import argparse
from typing import Tuple


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

    # pylint: disable=too-few-public-methods


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
    returncode, _, stderr = run_command("kubectl version --client 2>/dev/null", check=False)

    if returncode != 0:
        print_error("kubectl is not installed or not in PATH")
        print_error(f"Error: {stderr}")
        sys.exit(1)

    print_success("kubectl found")


def check_cluster_connection():
    """Check if we can connect to the Kubernetes cluster"""
    print_info("Checking cluster connection...")
    returncode, _, stderr = run_command(
        "kubectl cluster-info 2>/dev/null", check=False
    )

    if returncode != 0:
        print_error("Cannot connect to Kubernetes cluster")
        print_error(f"Error: {stderr}")
        sys.exit(1)

    print_success("Connected to Kubernetes cluster")

    # Show current context
    returncode, context, _ = run_command(
        "kubectl config current-context 2>/dev/null", check=False
    )
    if returncode == 0 and context.strip():
        print_info(f"Current context: {context.strip()}")


def namespace_exists(namespace: str) -> bool:
    """Check if a namespace exists"""
    command = f"kubectl get namespace {namespace} 2>/dev/null"
    returncode, _, _ = run_command(command, check=False)
    return returncode == 0


def clusterissuer_exists(issuer_name: str) -> bool:
    """Check if a ClusterIssuer exists"""
    command = f"kubectl get clusterissuer {issuer_name} 2>/dev/null"
    returncode, _, _ = run_command(command, check=False)
    return returncode == 0


def get_namespace_resources(namespace: str):
    """Get a summary of resources in the namespace"""
    print_info(f"Resources in namespace '{namespace}':")

    resource_types = ["deployments", "services", "ingresses", "certificates", "secrets"]

    for resource_type in resource_types:
        command = f"kubectl get {resource_type} -n {namespace} --no-headers 2>/dev/null | wc -l"
        returncode, count, _ = run_command(command, check=False)

        if returncode == 0 and count.strip():
            count_int = int(count.strip())
            if count_int > 0:
                print(f"  • {resource_type}: {count_int}")


def delete_namespace(namespace: str) -> bool:
    """Delete a namespace and all resources within it"""
    print_warning(
        f"Deleting namespace '{namespace}' and ALL resources inside it..."
    )
    print_info(
        "This will remove: deployment, service, ingress, certificate, secrets"
    )

    command = f"kubectl delete namespace {namespace}"
    returncode, _, stderr = run_command(command, check=False, capture_output=False)

    if returncode == 0:
        print_success(f"Namespace '{namespace}' deletion initiated")
        return True

    print_error(f"Failed to delete namespace '{namespace}'")
    print_error(f"Error: {stderr}")
    return False


def wait_for_namespace_deletion(namespace: str, timeout: int = 120):
    """Wait for namespace to be fully deleted"""
    print_info(f"Waiting for namespace '{namespace}' to be fully deleted...")

    start_time = time.time()
    while time.time() - start_time < timeout:
        if not namespace_exists(namespace):
            print_success(f"Namespace '{namespace}' fully deleted")
            return True

        print(".", end="", flush=True)
        time.sleep(5)

    print()
    print_warning(f"Namespace still deleting after {timeout} seconds (may have finalizers)")
    return False


def delete_clusterissuer(issuer_name: str) -> bool:
    """Delete a ClusterIssuer"""
    print_warning(f"Deleting ClusterIssuer '{issuer_name}'...")

    command = f"kubectl delete clusterissuer {issuer_name}"
    returncode, _, stderr = run_command(command, check=False)

    if returncode == 0:
        print_success(f"ClusterIssuer '{issuer_name}' deleted")
        return True

    print_error(f"Failed to delete ClusterIssuer '{issuer_name}'")
    print_error(f"Error: {stderr}")
    return False


def parse_arguments():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description='Destroy E-commerce Frontend Kubernetes resources',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ./destroy_frontend.py                    # Delete namespace only (interactive)
  ./destroy_frontend.py --delete-issuer    # Also delete ClusterIssuer
  ./destroy_frontend.py --interactive      # Require confirmation prompt

By default, the script runs non-interactively (suitable for CI/CD).
        """
    )

    parser.add_argument(
        '--delete-issuer',
        action='store_true',
        help='Also delete the ClusterIssuer (cluster-wide resource)'
    )

    parser.add_argument(
        '--interactive',
        action='store_true',
        help='Require confirmation before deletion (default: auto-approve)'
    )

    return parser.parse_args()


def confirm_deletion() -> bool:
    """Ask user for confirmation before deletion"""
    print(f"\n{Colors.BOLD}{Colors.RED}⚠  WARNING: DESTRUCTIVE OPERATION ⚠"
          f"{Colors.END}")
    print(f"{Colors.YELLOW}This will permanently delete all deployed "
          f"resources.{Colors.END}")
    print(f"{Colors.YELLOW}This action cannot be undone.{Colors.END}\n")

    try:
        response = input(
            f"{Colors.BOLD}Type 'yes' to confirm deletion: {Colors.END}"
        ).strip().lower()
        return response == 'yes'
    except (KeyboardInterrupt, EOFError):
        print()
        return False


# pylint: disable=too-many-statements
def main():
    """Main cleanup function"""

    # Parse command-line arguments
    args = parse_arguments()

    # Configuration (matches deploy_frontend.py)
    namespace = "ecommerce-frontend-ns"
    clusterissuer_name = "letsencrypt-prod"

    print(f"{Colors.BOLD}{Colors.HEADER}")
    print("=" * 70)
    print("  E-COMMERCE FRONTEND CLEANUP / DESTROY")
    print("=" * 70)
    print(f"{Colors.END}")

    if not args.interactive:
        print_info("Running in non-interactive mode (auto-approve)")

    # Pre-flight checks
    check_kubectl()
    check_cluster_connection()

    # ============================================
    # STEP 1: Check if namespace exists
    # ============================================
    print_step(1, f"Checking if namespace '{namespace}' exists...")

    if not namespace_exists(namespace):
        print_info(f"Namespace '{namespace}' does not exist")
        print_success("Nothing to clean up!")

        # Check ClusterIssuer anyway if flag is set
        if args.delete_issuer and clusterissuer_exists(clusterissuer_name):
            print()
            print_info(
                f"ClusterIssuer '{clusterissuer_name}' still exists "
                "(cluster-wide resource)"
            )
            delete_clusterissuer(clusterissuer_name)

        sys.exit(0)

    print_success(f"Namespace '{namespace}' exists")

    # Show what will be deleted
    print()
    get_namespace_resources(namespace)

    # ============================================
    # STEP 2: Confirm deletion (if interactive mode)
    # ============================================
    if args.interactive:
        print_step(2, "Confirming deletion...")

        if not confirm_deletion():
            print()
            print_warning("Deletion cancelled by user")
            sys.exit(0)
    else:
        print_step(2, "Auto-approving deletion (non-interactive mode)...")

    # ============================================
    # STEP 3: Delete namespace
    # ============================================
    print_step(3, f"Deleting namespace '{namespace}'...")

    if not delete_namespace(namespace):
        print_error("Failed to delete namespace. Exiting.")
        sys.exit(1)

    # Wait for deletion to complete
    wait_for_namespace_deletion(namespace, timeout=120)

    # ============================================
    # STEP 4: Handle ClusterIssuer
    # ============================================
    print_step(4, f"Checking ClusterIssuer '{clusterissuer_name}'...")

    if clusterissuer_exists(clusterissuer_name):
        print_info(
            f"ClusterIssuer '{clusterissuer_name}' exists "
            "(cluster-wide resource)"
        )

        if args.delete_issuer:
            print_warning("ClusterIssuer will be deleted (--delete-issuer flag)")
            delete_clusterissuer(clusterissuer_name)
        else:
            print_info(
                "Keeping ClusterIssuer (use --delete-issuer flag to remove it)"
            )
    else:
        print_info(
            f"ClusterIssuer '{clusterissuer_name}' does not exist "
            "(already deleted or never created)"
        )

    # ============================================
    # Summary
    # ============================================
    print(f"\n{Colors.BOLD}{Colors.GREEN}")
    print("=" * 70)
    print("  CLEANUP COMPLETED SUCCESSFULLY! ✓")
    print("=" * 70)
    print(f"{Colors.END}")

    print(f"\n{Colors.BOLD}What was deleted:{Colors.END}")
    print(f"  ✓ Namespace: {namespace}")
    print("  ✓ Deployment: ecommerce-frontend")
    print("  ✓ Service: ecommerce-frontend-service")
    print("  ✓ Ingress: ecommerce-frontend-ingress")
    print("  ✓ Certificate: ecommerce-frontend-tls")
    print("  ✓ Secrets: All secrets in namespace")

    print(f"\n{Colors.BOLD}Next Steps:{Colors.END}")
    print("1. Verify deletion:")
    print(f"   kubectl get namespace {namespace}")
    print("   (Should return: Error from server (NotFound))")
    print("\n2. To redeploy:")
    print("   ./deploy_frontend.py")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Cleanup interrupted by user{Colors.END}")
        sys.exit(1)
    except (OSError, subprocess.SubprocessError) as e:
        print(f"\n{Colors.RED}System error: {e}{Colors.END}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
