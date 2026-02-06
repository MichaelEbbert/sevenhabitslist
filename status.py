#!/usr/bin/env python3
"""
Check status of Seven Habits List service on AWS EC2
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
PORT = 3002
SUBDOMAIN = "https://sevenhabitslist.mebbert.com"


def run_ssh_command(command):
    """Run SSH command and return output."""
    cmd = [
        'ssh',
        '-i', SSH_KEY,
        f'{SERVER_USER}@{SERVER_IP}',
        command
    ]

    try:
        result = subprocess.run(cmd, check=False, text=True, capture_output=True)
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except Exception as e:
        return None, str(e), 1


def check_service_status():
    """Check if systemd service is running."""
    stdout, stderr, returncode = run_ssh_command(
        f'systemctl is-active {SERVICE_NAME}'
    )

    is_active = stdout == 'active'
    return is_active, stdout


def check_port():
    """Check if port is listening."""
    stdout, stderr, returncode = run_ssh_command(
        f'sudo ss -tlnp | grep ":{PORT}"'
    )

    is_listening = bool(stdout)
    return is_listening, stdout


def check_process():
    """Check if uvicorn process is running."""
    stdout, stderr, returncode = run_ssh_command(
        'ps aux | grep "[u]vicorn main:app"'
    )

    is_running = bool(stdout)
    return is_running, stdout


def get_recent_logs():
    """Get last 5 log lines."""
    stdout, stderr, returncode = run_ssh_command(
        f'sudo journalctl -u {SERVICE_NAME} -n 5 --no-pager'
    )

    return stdout


def test_http():
    """Test HTTP endpoint."""
    stdout, stderr, returncode = run_ssh_command(
        f'curl -s -o /dev/null -w "%{{http_code}}" http://localhost:{PORT}/'
    )

    if stdout:
        status_code = stdout.strip()
        return status_code == '200', status_code
    return False, None


def main():
    print("""
╔══════════════════════════════════════════════════════════════╗
║         Seven Habits List - Status Check                     ║
╚══════════════════════════════════════════════════════════════╝
""")

    print(f"🎯 Server: {SERVER_USER}@{SERVER_IP}")
    print(f"🔧 Service: {SERVICE_NAME}")
    print(f"🌐 URL: {SUBDOMAIN}")
    print(f"🔌 Port: {PORT}\n")

    print("="*60)
    print("📊 Status Checks")
    print("="*60)

    all_ok = True

    # Check service status
    is_active, status = check_service_status()
    if is_active:
        print("✅ Systemd service: ACTIVE")
    else:
        print(f"❌ Systemd service: {status.upper()}")
        all_ok = False

    # Check port
    is_listening, output = check_port()
    if is_listening:
        print(f"✅ Port {PORT}: LISTENING")
    else:
        print(f"❌ Port {PORT}: NOT LISTENING")
        all_ok = False

    # Check process
    is_running, output = check_process()
    if is_running:
        print("✅ Uvicorn process: RUNNING")
    else:
        print("❌ Uvicorn process: NOT FOUND")
        all_ok = False

    # Test HTTP
    is_ok, status_code = test_http()
    if is_ok:
        print(f"✅ HTTP response: {status_code} OK")
    else:
        print(f"❌ HTTP response: {status_code if status_code else 'FAILED'}")
        all_ok = False

    print("\n" + "="*60)
    print("📜 Recent Logs (last 5 lines)")
    print("="*60)
    logs = get_recent_logs()
    if logs:
        print(logs)
    else:
        print("(No logs available)")

    print("\n" + "="*60)
    if all_ok:
        print("✅ All checks passed! Service is healthy.")
        print(f"🌐 Access at: {SUBDOMAIN}")
    else:
        print("⚠️  Some checks failed. Service may have issues.")
        print("\nTroubleshooting:")
        print(f"  - View full logs: python logs.py -f")
        print(f"  - Restart service: python restart.py")
        print(f"  - SSH to server: ssh -i {SSH_KEY} {SERVER_USER}@{SERVER_IP}")
    print("="*60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        sys.exit(1)
