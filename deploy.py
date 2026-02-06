#!/usr/bin/env python3
"""
Deployment script for Seven Habits List to AWS EC2
"""
import subprocess
import sys
import os
from pathlib import Path
import glob

# Configuration
# Automatically find any .pem file in the taskschedule directory
def find_ssh_key():
    # Try both Windows-style and Unix-style paths for compatibility
    search_paths = [
        r'C:\claude_projects\taskschedule',
        r'C:\claude_projects\taskschedule',
        '/c/claude_projects/taskschedule',
        '/c/claude_projects/taskschedule'
    ]

    for key_dir in search_paths:
        if os.path.exists(key_dir):
            pem_files = glob.glob(os.path.join(key_dir, '*.pem'))
            if pem_files:
                return pem_files[0]
    return None

SSH_KEY = find_ssh_key()
SERVER_USER = "ec2-user"
SERVER_IP = "100.50.222.238"
SERVER_PATH = "/home/ec2-user/sevenhabitslist"
SERVICE_NAME = "sevenhabitslist"

# SSH options to skip host key verification
SSH_OPTIONS = ['-o', 'StrictHostKeyChecking=no', '-o', 'UserKnownHostsFile=/dev/null']

# Exclusions for rsync
EXCLUDE_PATTERNS = [
    'venv/',
    'data/',
    '__pycache__/',
    '.git/',
    '*.pyc',
    '.DS_Store',
    'deploy.py',
]


def run_command(cmd, description, check=True, shell=False):
    """Run a command and handle errors."""
    print(f"\n{'='*60}")
    print(f"{description}")
    print(f"{'='*60}")
    print(f"Command: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    print()

    try:
        if shell:
            result = subprocess.run(
                cmd,
                shell=True,
                check=check,
                text=True,
                capture_output=True
            )
        else:
            result = subprocess.run(
                cmd,
                check=check,
                text=True,
                capture_output=True
            )

        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(f"Warning: {result.stderr}", file=sys.stderr)

        if result.returncode == 0:
            print(f"[OK] {description} - Success")
        else:
            print(f"[FAIL] {description} - Failed (exit code: {result.returncode})")

        return result
    except subprocess.CalledProcessError as e:
        print(f"ERROR: {e}")
        if e.stdout:
            print(f"Output: {e.stdout}")
        if e.stderr:
            print(f"Error: {e.stderr}")
        if check:
            sys.exit(1)
        return None
    except FileNotFoundError as e:
        print(f"ERROR: Command not found: {e}")
        sys.exit(1)


def check_prerequisites():
    """Check if required tools are available."""
    print("Checking prerequisites...")

    # Check if SSH key exists
    if not SSH_KEY or not os.path.exists(SSH_KEY):
        print(f"ERROR: SSH key not found")
        print(f"Please ensure a .pem file exists in C:\\claude_projects\\taskschedule\\")
        sys.exit(1)
    print(f"[OK] SSH key found: {SSH_KEY}")

    # Check if rsync or scp is available
    has_rsync = False
    has_scp = False

    try:
        subprocess.run(['rsync', '--version'], capture_output=True, check=True)
        print("[OK] rsync is available")
        has_rsync = True
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    try:
        subprocess.run(['scp', '-V'], capture_output=True, check=False)
        if not has_rsync:
            print("[OK] scp is available (will use instead of rsync)")
        has_scp = True
    except FileNotFoundError:
        pass

    if not has_rsync and not has_scp:
        print("ERROR: Neither rsync nor scp found. Please install OpenSSH.")
        sys.exit(1)

    # Check if SSH is available
    try:
        subprocess.run(['ssh', '-V'], capture_output=True, check=False)
        print("[OK] SSH is available")
    except FileNotFoundError:
        print("ERROR: SSH not found. Please install OpenSSH.")
        sys.exit(1)


def test_ssh_connection():
    """Test SSH connection to server."""
    cmd = [
        'ssh',
        '-i', SSH_KEY,
        '-o', 'ConnectTimeout=10',
        '-o', 'BatchMode=yes',
        '-o', 'StrictHostKeyChecking=no',
        '-o', 'UserKnownHostsFile=/dev/null',
        f'{SERVER_USER}@{SERVER_IP}',
        'echo "Connection successful"'
    ]

    result = run_command(
        cmd,
        "Testing SSH connection",
        check=False
    )

    if result and result.returncode == 0:
        return True
    else:
        print("ERROR: Failed to connect to server.")
        print("   Please check your SSH key and server IP.")
        return False


def sync_files():
    """Sync files to server using rsync or scp."""
    # Check if rsync is available
    try:
        subprocess.run(['rsync', '--version'], capture_output=True, check=True)
        use_rsync = True
    except (subprocess.CalledProcessError, FileNotFoundError):
        use_rsync = False
        print("Note: rsync not available, using scp instead")

    if use_rsync:
        # Build exclude arguments
        exclude_args = []
        for pattern in EXCLUDE_PATTERNS:
            exclude_args.extend(['--exclude', pattern])

        ssh_cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null'
        cmd = [
            'rsync',
            '-avz',
            '--delete',  # Delete files on server that don't exist locally
            '-e', ssh_cmd,
        ] + exclude_args + [
            './',
            f'{SERVER_USER}@{SERVER_IP}:{SERVER_PATH}/'
        ]

        run_command(cmd, "Syncing files to server")
    else:
        # Use scp as fallback
        print("Using scp to copy files...")

        # Create a tar archive excluding certain patterns
        import tempfile
        import tarfile

        with tempfile.NamedTemporaryFile(suffix='.tar.gz', delete=False) as tmp_file:
            tar_path = tmp_file.name

        with tarfile.open(tar_path, 'w:gz') as tar:
            def filter_func(tarinfo):
                for pattern in EXCLUDE_PATTERNS:
                    if pattern.rstrip('/') in tarinfo.name:
                        return None
                return tarinfo

            tar.add('.', filter=filter_func)

        # Copy tar to server
        cmd = [
            'scp',
            '-i', SSH_KEY,
        ] + SSH_OPTIONS + [
            tar_path,
            f'{SERVER_USER}@{SERVER_IP}:/tmp/deploy.tar.gz'
        ]
        run_command(cmd, "Copying files to server")

        # Extract on server
        cmd = [
            'ssh',
            '-i', SSH_KEY,
        ] + SSH_OPTIONS + [
            f'{SERVER_USER}@{SERVER_IP}',
            f'cd {SERVER_PATH} && tar -xzf /tmp/deploy.tar.gz && rm /tmp/deploy.tar.gz'
        ]
        run_command(cmd, "Extracting files on server")

        # Clean up local tar file
        os.unlink(tar_path)


def install_dependencies():
    """Install Python dependencies on server."""
    cmd = [
        'ssh',
        '-i', SSH_KEY,
    ] + SSH_OPTIONS + [
        f'{SERVER_USER}@{SERVER_IP}',
        f'cd {SERVER_PATH} && source venv/bin/activate && pip install -r requirements.txt'
    ]

    run_command(cmd, "Installing dependencies on server")


def restart_service():
    """Restart the systemd service."""
    cmd = [
        'ssh',
        '-i', SSH_KEY,
    ] + SSH_OPTIONS + [
        f'{SERVER_USER}@{SERVER_IP}',
        f'sudo systemctl restart {SERVICE_NAME}'
    ]

    run_command(cmd, f"Restarting {SERVICE_NAME} service")


def check_service_status():
    """Check if the service is running."""
    cmd = [
        'ssh',
        '-i', SSH_KEY,
    ] + SSH_OPTIONS + [
        f'{SERVER_USER}@{SERVER_IP}',
        f'sudo systemctl is-active {SERVICE_NAME}'
    ]

    result = run_command(
        cmd,
        "Checking service status",
        check=False
    )

    if result and result.returncode == 0 and 'active' in result.stdout:
        print(f"[OK] Service {SERVICE_NAME} is active")
        return True
    else:
        print(f"WARNING: Service {SERVICE_NAME} may not be running")
        print(f"   Check logs with: sudo journalctl -u {SERVICE_NAME} -n 50")
        return False


def show_service_logs():
    """Show recent service logs."""
    cmd = [
        'ssh',
        '-i', SSH_KEY,
    ] + SSH_OPTIONS + [
        f'{SERVER_USER}@{SERVER_IP}',
        f'sudo journalctl -u {SERVICE_NAME} -n 20 --no-pager'
    ]

    run_command(cmd, "Recent service logs", check=False)


def main():
    """Main deployment workflow."""
    print("""
================================================================
         Seven Habits List - Deployment Script
                  AWS EC2 Deployment
================================================================
""")

    print(f"Target: {SERVER_USER}@{SERVER_IP}")
    print(f"Deploy path: {SERVER_PATH}")
    print(f"Service: {SERVICE_NAME}")

    # Run deployment steps
    check_prerequisites()

    if not test_ssh_connection():
        sys.exit(1)

    # Ask for confirmation
    print("\n" + "="*60)
    response = input("Ready to deploy. Continue? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("Deployment cancelled.")
        sys.exit(0)

    # Execute deployment
    sync_files()
    install_dependencies()
    restart_service()

    # Check results
    print("\n" + "="*60)
    print("Deployment Summary")
    print("="*60)

    service_ok = check_service_status()

    if service_ok:
        print("\nDeployment completed successfully!")
        print(f"\nApp should be available at: https://sevenhabitslist.mebbert.com")
    else:
        print("\nWARNING: Deployment completed but service may have issues.")
        show_service_logs()

    print("\n" + "="*60)
    print("Useful commands:")
    print(f"   View logs:    ssh -i {SSH_KEY} {SERVER_USER}@{SERVER_IP} 'sudo journalctl -u {SERVICE_NAME} -f'")
    print(f"   Check status: ssh -i {SSH_KEY} {SERVER_USER}@{SERVER_IP} 'sudo systemctl status {SERVICE_NAME}'")
    print(f"   Restart:      ssh -i {SSH_KEY} {SERVER_USER}@{SERVER_IP} 'sudo systemctl restart {SERVICE_NAME}'")
    print("="*60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDeployment interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nERROR: Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
