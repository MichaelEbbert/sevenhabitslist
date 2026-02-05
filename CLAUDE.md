# Seven Habits List

A web application for managing tasks based on the book "7 Habits of Highly Effective People" by Stephen Covey. Tasks are organized by life roles and scheduled across the upcoming weeks.

---

## Tech Stack

- **Backend:** Python + FastAPI
- **Templates:** Jinja2 (server-rendered HTML)
- **Database:** SQLite single-file (`data/sevenhabits.db`)
- **Server:** Uvicorn

## Project Structure

```
sevenhabitslist/
├── CLAUDE.md              # This file
├── requirements.txt       # Python dependencies
├── main.py               # FastAPI app entry point
├── .gitignore
├── app/
│   ├── __init__.py
│   ├── database.py       # SQLite setup and connection
│   ├── routers/
│   │   ├── roles.py      # Role CRUD endpoints
│   │   ├── tasks.py      # Task CRUD endpoints
│   │   └── schedule.py   # Schedule view endpoints
│   ├── templates/        # Jinja2 templates
│   │   ├── base.html
│   │   ├── index.html
│   │   ├── roles/
│   │   ├── tasks/
│   │   └── schedule/
│   └── static/
│       └── css/style.css
├── data/                 # Created at runtime
│   └── sevenhabits.db    # SQLite database (gitignored)
└── venv/                 # Virtual environment (gitignored)
```

## Running Locally

```bash
# Activate virtual environment
venv\Scripts\activate   # Windows
source venv/bin/activate # Mac/Linux

# Run the server
python main.py
```

Access at http://localhost:3002

---

## Deployment Scripts

**📦 Automated deployment scripts are available!**

For AWS deployment, use the Python scripts in this directory:
- `deploy.py` - Full deployment with file sync and restart
- `restart.py` - Quick service restart
- `status.py` - Health check and status verification
- `logs.py` - View service logs with various options

See **[DEPLOYMENT_SCRIPTS.md](DEPLOYMENT_SCRIPTS.md)** for complete documentation.

**Quick commands:**
```bash
python deploy.py        # Deploy/update application
python status.py        # Check if everything is running
python logs.py -f       # Follow logs in real-time
python restart.py       # Restart the service
```

---

## Project Requirements

### Database
- **SQLite** single-file database for simplicity
- IDs are incremental and **never reused** after deletion
- Database file is gitignored

### Data Model

#### Roles
- Editable list of life roles the user has
- Examples: Father, Son, Husband, AI Programmer
- Fields:
  - `id` (integer, auto-increment, never reused)
  - `name` (text)

#### Tasks
- Each task is linked to a **single Role**
- Fields:
  - `id` (integer, auto-increment, never reused)
  - `role_id` (foreign key to Roles)
  - `name` (text)
  - `effort_level` (enum: Low, Medium, High)
  - `scheduled_date` (date, optional, must be within next 4 weeks from today)
  - `is_complete` (boolean, default false)

### Views

#### Roles View
- List all roles
- Click a role to enter edit mode
- Add/edit/delete roles

#### Tasks View
- List all tasks
- Click a task to enter edit mode
- Edit task details including role assignment
- Assign a day within the next 4 weeks
- Mark task as complete (hides from schedule, keeps in database)
- Delete task (prompt for verification, then permanently remove)

#### Schedule View
- Shows upcoming days starting with **current day**
- Format for each day:
  ```
  Wednesday, 02/05          (10pt font, bold heading)
  -----------------
  Task Name 1
  Task Name 2
  Task Name 3

  Thursday, 02/06
  -----------------
  Task Name 4
  ```
- Tasks listed **alphabetically** under each day
- Space after last task before next day's heading
- **60 line limit** - no partial day crosses this threshold (for single-page printing)
- Only shows **active** tasks (is_complete = false)

#### Print View
- 10pt font
- Basic styling
- Designed to fit on one printed page (60 line limit)

### User Interactions

1. **Create Role**: Add new life role
2. **Edit Role**: Click role to modify name
3. **Delete Role**: Prevent deletion if any tasks are linked; user must reassign/delete tasks first
4. **Create Task**: Add task with name, role, effort level, optional scheduled date
5. **Edit Task**: Click task to modify any field
6. **Schedule Task**: Select a day within the next 4 weeks
7. **Complete Task**: Mark as complete (hidden from schedule but retained)
8. **Delete Task**: Confirmation prompt, then permanent deletion

---

## AWS Deployment Info

- **Subdomain:** https://sevenhabitslist.mebbert.com
- **Internal Port:** 3002
- **Server IP:** 100.50.222.238
- **SSH Key:** `D:\claude_projects\taskschedule\taskschedule-key.pem`
  - **Note:** Path may vary by computer. If not found on D:\ drive, try C:\ drive
- **Deploy Path:** `/home/ec2-user/sevenhabitslist/`

### Quick Commands

**SSH into server:**
```bash
ssh -i "D:\claude_projects\taskschedule\taskschedule-key.pem" ec2-user@100.50.222.238
```

**Deploy/Update (from local machine):**
```bash
# Run the deployment script
python deploy.py
```

**Restart app (on server):**
```bash
sudo systemctl restart sevenhabitslist
sudo systemctl status sevenhabitslist
```

**View logs (on server):**
```bash
sudo journalctl -u sevenhabitslist -f
```

---

## Deployment Guide

### First-Time Deployment

#### Step 1: Prepare Server
SSH into the server and set up the application directory:

```bash
ssh -i "D:\claude_projects\taskschedule\taskschedule-key.pem" ec2-user@100.50.222.238

# Create directory
mkdir -p /home/ec2-user/sevenhabitslist
cd /home/ec2-user/sevenhabitslist

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Create data directory
mkdir -p data
```

#### Step 2: Copy Files to Server
From your local machine, use the deployment script:

```bash
python deploy.py
```

Or manually with rsync:

```bash
rsync -avz -e "ssh -i D:\claude_projects\taskschedule\taskschedule-key.pem" \
  --exclude='venv/' \
  --exclude='data/' \
  --exclude='__pycache__/' \
  --exclude='.git/' \
  ./ ec2-user@100.50.222.238:/home/ec2-user/sevenhabitslist/
```

#### Step 3: Install Dependencies on Server
```bash
# SSH into server
ssh -i "D:\claude_projects\taskschedule\taskschedule-key.pem" ec2-user@100.50.222.238

cd /home/ec2-user/sevenhabitslist
source venv/bin/activate
pip install -r requirements.txt
```

#### Step 4: Create Systemd Service
Create `/etc/systemd/system/sevenhabitslist.service`:

```bash
sudo nano /etc/systemd/system/sevenhabitslist.service
```

Paste this content:

```ini
[Unit]
Description=Seven Habits List FastAPI Application
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/home/ec2-user/sevenhabitslist
Environment="PATH=/home/ec2-user/sevenhabitslist/venv/bin"
ExecStart=/home/ec2-user/sevenhabitslist/venv/bin/uvicorn main:app --host 0.0.0.0 --port 3002
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### Step 5: Enable and Start Service
```bash
sudo systemctl daemon-reload
sudo systemctl enable sevenhabitslist
sudo systemctl start sevenhabitslist
sudo systemctl status sevenhabitslist
```

#### Step 6: Verify Nginx Configuration
Nginx should already be configured in `/etc/nginx/conf.d/subdomains.conf` to proxy port 3002:

```bash
# Check nginx config
sudo nginx -t

# Restart nginx if needed
sudo systemctl restart nginx
```

### Updating the App

**Option 1: Use deployment script (recommended)**
```bash
python deploy.py
```

**Option 2: Manual update**
```bash
# 1. Copy files to server
rsync -avz -e "ssh -i D:\claude_projects\taskschedule\taskschedule-key.pem" \
  --exclude='venv/' --exclude='data/' --exclude='__pycache__/' --exclude='.git/' \
  ./ ec2-user@100.50.222.238:/home/ec2-user/sevenhabitslist/

# 2. SSH into server
ssh -i "D:\claude_projects\taskschedule\taskschedule-key.pem" ec2-user@100.50.222.238

# 3. Update dependencies if needed
cd /home/ec2-user/sevenhabitslist
source venv/bin/activate
pip install -r requirements.txt

# 4. Restart service
sudo systemctl restart sevenhabitslist
sudo systemctl status sevenhabitslist
```

### Restarting the App

**Restart service:**
```bash
sudo systemctl restart sevenhabitslist
```

**Check status:**
```bash
sudo systemctl status sevenhabitslist
```

**View logs:**
```bash
# Follow logs in real-time
sudo journalctl -u sevenhabitslist -f

# View last 100 lines
sudo journalctl -u sevenhabitslist -n 100

# View logs since today
sudo journalctl -u sevenhabitslist --since today
```

**Stop/Start service:**
```bash
sudo systemctl stop sevenhabitslist
sudo systemctl start sevenhabitslist
```

### Troubleshooting

**Check if app is running:**
```bash
ps aux | grep uvicorn
```

**Check if port 3002 is listening:**
```bash
sudo netstat -tlnp | grep 3002
# or
sudo ss -tlnp | grep 3002
```

**Test app directly:**
```bash
curl http://localhost:3002
```

**Check nginx status:**
```bash
sudo systemctl status nginx
sudo nginx -t
```

**Check database file:**
```bash
ls -la /home/ec2-user/sevenhabitslist/data/
```

### References

- Full deployment docs on server: `/home/ec2-user/taskschedule/AWS_DEPLOYMENT.md`
- Nginx config: `/etc/nginx/conf.d/subdomains.conf`
- Service template: `/etc/systemd/system/taskschedule.service`
- For nginx authentication: `C:\claude_projects\recipeshoppinglist\CLAUDE.md`
