# Deployment Scripts

This directory contains Python scripts to simplify deployment and management of the Seven Habits List application on AWS EC2.

## Prerequisites

- Python 3.7+ installed locally
- SSH access to the EC2 server
- `rsync` installed (for deploy.py)
- SSH key at: `C:\claude_projects\taskschedule\taskschedule-key.pem`

## Scripts Overview

### 🚀 deploy.py - Full Deployment

Comprehensive deployment script that handles the complete deployment process.

**Usage:**
```bash
python deploy.py
```

**What it does:**
1. ✅ Checks prerequisites (SSH key, rsync, SSH client)
2. 🔗 Tests SSH connection to server
3. 📦 Syncs all files to server (excludes venv, data, .git)
4. 📥 Installs/updates Python dependencies
5. 🔄 Restarts the systemd service
6. 📊 Checks service status
7. 📜 Shows recent logs

**When to use:**
- Initial deployment
- After code changes
- After updating dependencies
- After modifying configuration

---

### 🔄 restart.py - Quick Restart

Restarts the service without deploying files.

**Usage:**
```bash
python restart.py
```

**What it does:**
1. 🔄 Restarts the systemd service
2. 📊 Shows service status
3. 📜 Shows last 15 log lines

**When to use:**
- After manual file edits on server
- To recover from a crash
- To apply environment changes
- Quick troubleshooting

---

### 📊 status.py - Health Check

Comprehensive status check of the application.

**Usage:**
```bash
python status.py
```

**What it checks:**
- ✅ Systemd service status (active/inactive)
- ✅ Port 3002 listening status
- ✅ Uvicorn process running
- ✅ HTTP endpoint responding (200 OK)
- 📜 Shows last 5 log lines

**When to use:**
- Verify deployment success
- Troubleshoot issues
- Health monitoring
- Before/after changes

---

### 📜 logs.py - View Logs

View service logs with various options.

**Basic usage:**
```bash
python logs.py              # Show last 50 lines
```

**Advanced options:**
```bash
# Follow logs in real-time
python logs.py -f

# Show last 100 lines
python logs.py -n 100

# Show logs since today
python logs.py --since today

# Show logs from last hour
python logs.py --since "1 hour ago"

# Combine options
python logs.py -f --since today
```

**When to use:**
- Debugging errors
- Monitoring in real-time
- Checking startup issues
- Investigating crashes

---

## Common Workflows

### Initial Deployment

```bash
# 1. First, manually SSH and set up directories
ssh -i "C:\claude_projects\taskschedule\taskschedule-key.pem" ec2-user@100.50.222.238

# On server: create directory and venv
mkdir -p /home/ec2-user/sevenhabitslist
cd /home/ec2-user/sevenhabitslist
python3 -m venv venv
mkdir -p data
exit

# 2. Deploy and set up service (see CLAUDE.md for systemd setup)

# 3. Deploy the application
python deploy.py

# 4. Check status
python status.py
```

### Regular Updates

```bash
# 1. Deploy changes
python deploy.py

# 2. Verify everything works
python status.py
```

### Quick Restart

```bash
python restart.py
```

### Debugging Issues

```bash
# 1. Check overall status
python status.py

# 2. View recent logs
python logs.py -n 100

# 3. Follow logs in real-time
python logs.py -f

# 4. If needed, restart
python restart.py
```

---

## Manual Operations

If scripts fail, you can perform operations manually:

### Manual Deployment
```bash
# Sync files
rsync -avz -e "ssh -i C:\claude_projects\taskschedule\taskschedule-key.pem" \
  --exclude='venv/' --exclude='data/' --exclude='__pycache__/' --exclude='.git/' \
  ./ ec2-user@100.50.222.238:/home/ec2-user/sevenhabitslist/

# SSH and restart
ssh -i "C:\claude_projects\taskschedule\taskschedule-key.pem" ec2-user@100.50.222.238
cd /home/ec2-user/sevenhabitslist
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart sevenhabitslist
```

### Manual Status Check
```bash
ssh -i "C:\claude_projects\taskschedule\taskschedule-key.pem" ec2-user@100.50.222.238
sudo systemctl status sevenhabitslist
sudo journalctl -u sevenhabitslist -f
```

---

## Troubleshooting

### "SSH key not found"
- Verify the SSH key path in each script matches your actual key location
- Check the SSH_KEY variable in the scripts

### "Connection refused"
- Verify server IP: `100.50.222.238`
- Check if server is running
- Verify SSH key permissions (should be 400/600)

### "rsync not found"
- Install rsync:
  - Windows: Use Git Bash, WSL, or Cygwin
  - Mac/Linux: `apt-get install rsync` or `brew install rsync`

### "Service failed to start"
- Check logs: `python logs.py -n 50`
- Verify Python dependencies installed
- Check if port 3002 is already in use
- Verify systemd service file exists

### "HTTP check fails"
- Service may be starting (wait 5-10 seconds)
- Check logs for errors: `python logs.py -f`
- Verify app starts: `curl http://localhost:3002`

---

## Configuration

All scripts use these settings:

```python
SSH_KEY = r"C:\claude_projects\taskschedule\taskschedule-key.pem"
SERVER_USER = "ec2-user"
SERVER_IP = "100.50.222.238"
SERVER_PATH = "/home/ec2-user/sevenhabitslist"
SERVICE_NAME = "sevenhabitslist"
PORT = 3002
```

If your setup differs, edit the configuration section at the top of each script.

---

## Tips

- **Test before deploying:** Run `python status.py` to check current state
- **Deploy during low traffic:** If this were production
- **Keep backups:** The database is in `data/sevenhabits.db` on the server
- **Monitor logs:** Use `python logs.py -f` during deployment
- **SSH key security:** Never commit SSH keys to git

---

## Support

For issues with:
- **Scripts:** Check this file and CLAUDE.md
- **AWS/Server:** Check `/home/ec2-user/taskschedule/AWS_DEPLOYMENT.md` on server
- **Application:** Check application logs with `python logs.py`
