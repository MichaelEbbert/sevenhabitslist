#!/usr/bin/env python3
"""
View logs for Seven Habits List service on AWS EC2
"""
import subprocess
import sys
import argparse

# Configuration
# NOTE: Path may vary by computer. If not found on D:\ drive, try C:\ drive
SSH_KEY = r"D:\claude_projects\taskschedule\taskschedule-key.pem"
SERVER_USER = "ec2-user"
SERVER_IP = "100.50.222.238"
SERVICE_NAME = "sevenhabitslist"


def view_logs(follow=False, lines=50, since=None):
    """View service logs."""
    print("""
╔══════════════════════════════════════════════════════════════╗
║         Seven Habits List - Service Logs                     ║
╚══════════════════════════════════════════════════════════════╝
""")

    print(f"🎯 Target: {SERVER_USER}@{SERVER_IP}")
    print(f"🔧 Service: {SERVICE_NAME}")

    # Build journalctl command
    cmd_parts = [f'sudo journalctl -u {SERVICE_NAME}']

    if follow:
        cmd_parts.append('-f')
        print(f"📜 Following logs (press Ctrl+C to stop)...\n")
    else:
        cmd_parts.append(f'-n {lines}')
        cmd_parts.append('--no-pager')
        print(f"📜 Showing last {lines} lines...\n")

    if since:
        cmd_parts.append(f'--since "{since}"')

    journalctl_cmd = ' '.join(cmd_parts)

    # SSH command
    ssh_cmd = [
        'ssh',
        '-i', SSH_KEY,
        f'{SERVER_USER}@{SERVER_IP}',
        journalctl_cmd
    ]

    try:
        # Use call instead of run to stream output in real-time
        subprocess.call(ssh_cmd)
    except KeyboardInterrupt:
        print("\n\n✅ Stopped viewing logs.")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description='View Seven Habits List service logs on AWS EC2'
    )
    parser.add_argument(
        '-f', '--follow',
        action='store_true',
        help='Follow logs in real-time'
    )
    parser.add_argument(
        '-n', '--lines',
        type=int,
        default=50,
        help='Number of lines to show (default: 50)'
    )
    parser.add_argument(
        '--since',
        type=str,
        help='Show logs since specific time (e.g., "today", "1 hour ago", "2024-02-05")'
    )

    args = parser.parse_args()

    view_logs(follow=args.follow, lines=args.lines, since=args.since)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n✅ Stopped.")
        sys.exit(0)
