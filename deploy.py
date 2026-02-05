#!/usr/bin/env python3
"""
Deployment script for Seven Habits List to AWS EC2
"""
import subprocess
import sys
import os
from pathlib import Path

# Configuration
# NOTE: Path may vary by computer. If not found on D:\ drive, try C:\ drive
SSH_KEY = r"D:\claude_projects\taskschedule\taskschedule-key.pem"
SERVER_USER = "ec2-user"
SERVER_IP = "100.50.222.238"
SERVER_PATH = "/home/ec2-user/sevenhabitslist"
SERVICE_NAME = "sevenhabitslist"

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
    print(f"📋 {description}")
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
            print(f"⚠️  {result.stderr}", file=sys.stderr)

        if result.returncode == 0:
            print(f"✅ {description} - Success")
        else:
            print(f"❌ {description} - Failed (exit code: {result.returncode})")

        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        if e.stdout:
            print(f"Output: {e.stdout}")
        if e.stderr:
            print(f"Error: {e.stderr}")
        if check:
            sys.exit(1)
        return None
    except FileNotFoundError as e:
        print(f"❌ Command not found: {e}")
        sys.exit(1)


def check_prerequisites():
    """Check if required tools are available."""
    print("🔍 Checking prerequisites...")

    # Check if SSH key exists
    if not os.path.exists(SSH_KEY):
        print(f"❌ SSH key not found: {SSH_KEY}")
        print(f"Please ensure the SSH key exists at the specified location.")
        sys.exit(1)
    print(f"✅ SSH key found: {SSH_KEY}")

    # Check if rsync is available
    try:
        subprocess.run(['rsync', '--version'], capture_output=True, check=True)
        print("✅ rsync is available")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ rsync not found. Please install rsync.")
        print("   Windows: Install via WSL, Cygwin, or Git Bash")
        sys.exit(1)

    # Check if SSH is available
    try:
        subprocess.run(['ssh', '-V'], capture_output=True, check=False)
        print("✅ SSH is available")
    except FileNotFoundError:
        print("❌ SSH not found. Please install OpenSSH.")
        sys.exit(1)


def test_ssh_connection():
    """Test SSH connection to server."""
    cmd = [
        'ssh',
        '-i', SSH_KEY,
        '-o', 'ConnectTimeout=10',
        '-o', 'BatchMode=yes',
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
        print("❌ Failed to connect to server.")
        print("   Please check your SSH key and server IP.")
        return False


def sync_files():
    """Sync files to server using rsync."""
    # Build exclude arguments
    exclude_args = []
    for pattern in EXCLUDE_PATTERNS:
        exclude_args.extend(['--exclude', pattern])

    cmd = [
        'rsync',
        '-avz',
        '--delete',  # Delete files on server that don't exist locally
        '-e', f'ssh -i {SSH_KEY}',
    ] + exclude_args + [
        './',
        f'{SERVER_USER}@{SERVER_IP}:{SERVER_PATH}/'
    ]

    run_command(cmd, "Syncing files to server")


def install_dependencies():
    """Install Python dependencies on server."""
    cmd = [
        'ssh',
        '-i', SSH_KEY,
        f'{SERVER_USER}@{SERVER_IP}',
        f'cd {SERVER_PATH} && source venv/bin/activate && pip install -r requirements.txt'
    ]

    run_command(cmd, "Installing dependencies on server")


def restart_service():
    """Restart the systemd service."""
    cmd = [
        'ssh',
        '-i', SSH_KEY,
        f'{SERVER_USER}@{SERVER_IP}',
        f'sudo systemctl restart {SERVICE_NAME}'
    ]

    run_command(cmd, f"Restarting {SERVICE_NAME} service")


def check_service_status():
    """Check if the service is running."""
    cmd = [
        'ssh',
        '-i', SSH_KEY,
        f'{SERVER_USER}@{SERVER_IP}',
        f'sudo systemctl is-active {SERVICE_NAME}'
    ]

    result = run_command(
        cmd,
        "Checking service status",
        check=False
    )

    if result and result.returncode == 0 and 'active' in result.stdout:
        print(f"✅ Service {SERVICE_NAME} is active")
        return True
    else:
        print(f"⚠️  Service {SERVICE_NAME} may not be running")
        print(f"   Check logs with: sudo journalctl -u {SERVICE_NAME} -n 50")
        return False


def show_service_logs():
    """Show recent service logs."""
    cmd = [
        'ssh',
        '-i', SSH_KEY,
        f'{SERVER_USER}@{SERVER_IP}',
        f'sudo journalctl -u {SERVICE_NAME} -n 20 --no-pager'
    ]

    run_command(cmd, "Recent service logs", check=False)


def main():
    """Main deployment workflow."""
    print("""
╔══════════════════════════════════════════════════════════════╗
║         Seven Habits List - Deployment Script               ║
║                  AWS EC2 Deployment                          ║
╚══════════════════════════════════════════════════════════════╝
""")

    print(f"🎯 Target: {SERVER_USER}@{SERVER_IP}")
    print(f"📁 Deploy path: {SERVER_PATH}")
    print(f"🔧 Service: {SERVICE_NAME}")

    # Run deployment steps
    check_prerequisites()

    if not test_ssh_connection():
        sys.exit(1)

    # Ask for confirmation
    print("\n" + "="*60)
    response = input("🚀 Ready to deploy. Continue? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("❌ Deployment cancelled.")
        sys.exit(0)

    # Execute deployment
    sync_files()
    install_dependencies()
    restart_service()

    # Check results
    print("\n" + "="*60)
    print("📊 Deployment Summary")
    print("="*60)

    service_ok = check_service_status()

    if service_ok:
        print("\n🎉 Deployment completed successfully!")
        print(f"\n🌐 App should be available at: https://sevenhabitslist.mebbert.com")
    else:
        print("\n⚠️  Deployment completed but service may have issues.")
        show_service_logs()

    print("\n" + "="*60)
    print("📚 Useful commands:")
    print(f"   View logs:    ssh -i {SSH_KEY} {SERVER_USER}@{SERVER_IP} 'sudo journalctl -u {SERVICE_NAME} -f'")
    print(f"   Check status: ssh -i {SSH_KEY} {SERVER_USER}@{SERVER_IP} 'sudo systemctl status {SERVICE_NAME}'")
    print(f"   Restart:      ssh -i {SSH_KEY} {SERVER_USER}@{SERVER_IP} 'sudo systemctl restart {SERVICE_NAME}'")
    print("="*60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Deployment interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
