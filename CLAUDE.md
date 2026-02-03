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
- **Status:** Awaiting deployment

### SSH Access
```bash
ssh -i "C:\claude_projects\taskschedule\taskschedule-key.pem" ec2-user@100.50.222.238
```

### Server Documentation
Full deployment docs on server: `/home/ec2-user/taskschedule/AWS_DEPLOYMENT.md`

### Nginx Config
Already configured in `/etc/nginx/conf.d/subdomains.conf` to proxy to port 3002.

### To Deploy
1. Copy app to `/home/ec2-user/sevenhabitslist/`
2. Run on port 3002
3. Create systemd service (use `/etc/systemd/system/taskschedule.service` as template)
4. Enable and start: `sudo systemctl enable --now sevenhabitslist`

### Nginx Authentication
See `C:\claude_projects\recipeshoppinglist\CLAUDE.md` for instructions on nginx-level auth to protect all deployed apps.
