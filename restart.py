#!/usr/bin/env python3
"""
Quick restart script for Seven Habits List service on AWS EC2
"""
import subprocess
import sys
import os
import glob

# Configuration
# Automatically find any .pem file in the taskschedule directory
def find_ssh_key():
    for drive in ['C:']:
        key_dir = os.path.join(drive, 'claude_projects', 'taskschedule')
        if os.path.exists(key_dir):
            pem_files = glob.glob(os.path.join(key_dir, '*.pem'))
            if pem_files:
                return pem_files[0]
    return None

SSH_KEY = find_ssh_key()
SERVER_USER = "ec2-user"
SERVER_IP = "100.50.222.238"
SERVICE_NAME = "sevenhabitslist"


def run_ssh_command(command, description):
    """Run SSH command on server."""
    print(f"{'='*60}")
    print(f"📋 {description}")
    print(f"{'='*60}")

    cmd = [
        'ssh',
        '-i', SSH_KEY,
        f'{SERVER_USER}@{SERVER_IP}',
        command
    ]

    try:
        result = subprocess.run(cmd, check=False, text=True, capture_output=True)
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    print("""
╔══════════════════════════════════════════════════════════════╗
║         Seven Habits List - Restart Service                  ║
╚══════════════════════════════════════════════════════════════╝
""")

    print(f"🎯 Target: {SERVER_USER}@{SERVER_IP}")
    print(f"🔧 Service: {SERVICE_NAME}\n")

    # Restart service
    print("🔄 Restarting service...")
    success = run_ssh_command(
        f'sudo systemctl restart {SERVICE_NAME}',
        "Restarting service"
    )

    if not success:
        print("❌ Failed to restart service")
        sys.exit(1)

    # Check status
    print("\n📊 Checking status...")
    run_ssh_command(
        f'sudo systemctl status {SERVICE_NAME}',
        "Service status"
    )

    # Show recent logs
    print("\n📜 Recent logs:")
    run_ssh_command(
        f'sudo journalctl -u {SERVICE_NAME} -n 15 --no-pager',
        "Last 15 log lines"
    )

    print("\n✅ Restart completed!")
    print(f"🌐 App: https://sevenhabitslist.mebbert.com")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Interrupted by user.")
        sys.exit(1)
