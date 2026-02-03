from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from datetime import date, timedelta
from collections import defaultdict
import aiosqlite

from app.database import get_db

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

MAX_LINES = 60
LINES_PER_DAY_HEADER = 3  # Heading + separator + blank line after tasks

async def get_scheduled_tasks(db: aiosqlite.Connection):
    """Get all active scheduled tasks grouped by date."""
    today = date.today()
    max_date = today + timedelta(weeks=4)

    cursor = await db.execute("""
        SELECT t.id, t.name, t.effort_level, t.scheduled_date,
               r.name as role_name
        FROM tasks t
        JOIN roles r ON t.role_id = r.id
        WHERE t.is_complete = 0
          AND t.scheduled_date IS NOT NULL
          AND t.scheduled_date >= ?
          AND t.scheduled_date <= ?
        ORDER BY t.scheduled_date, t.name
    """, (today.isoformat(), max_date.isoformat()))

    tasks = await cursor.fetchall()

    # Group tasks by date
    tasks_by_date = defaultdict(list)
    for task in tasks:
        tasks_by_date[task["scheduled_date"]].append(task)

    return tasks_by_date

def build_schedule_days(tasks_by_date: dict, max_lines: int = MAX_LINES):
    """Build schedule days respecting the line limit."""
    today = date.today()
    max_date = today + timedelta(weeks=4)

    schedule_days = []
    current_line = 0
    current_date = today

    while current_date <= max_date:
        date_str = current_date.isoformat()
        tasks = tasks_by_date.get(date_str, [])

        # Calculate lines needed for this day
        # Header (1) + separator (1) + tasks + blank line (1)
        lines_needed = 3 + len(tasks)

        # Check if adding this day would exceed the limit
        if current_line + lines_needed > max_lines:
            break

        schedule_days.append({
            "date": current_date,
            "formatted_date": current_date.strftime("%A, %m/%d"),
            "tasks": tasks
        })

        current_line += lines_needed
        current_date += timedelta(days=1)

    return schedule_days

@router.get("/", response_class=HTMLResponse)
async def view_schedule(request: Request, db: aiosqlite.Connection = Depends(get_db)):
    """View the schedule."""
    tasks_by_date = await get_scheduled_tasks(db)
    schedule_days = build_schedule_days(tasks_by_date)

    return templates.TemplateResponse("schedule/view.html", {
        "request": request,
        "schedule_days": schedule_days
    })

@router.get("/print", response_class=HTMLResponse)
async def print_schedule(request: Request, db: aiosqlite.Connection = Depends(get_db)):
    """Print-friendly schedule view."""
    tasks_by_date = await get_scheduled_tasks(db)
    schedule_days = build_schedule_days(tasks_by_date)

    return templates.TemplateResponse("schedule/print.html", {
        "request": request,
        "schedule_days": schedule_days
    })
