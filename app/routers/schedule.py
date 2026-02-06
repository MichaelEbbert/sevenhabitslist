from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from datetime import date, timedelta
from collections import defaultdict
import aiosqlite

from app.database import get_db

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

MAX_LINES = 55
LINES_PER_DAY_HEADER = 3  # Heading (1) + 2 blank lines for spacing (2)

async def get_scheduled_tasks(db: aiosqlite.Connection, include_overdue: bool = True, max_future_days: int = 28):
    """Get all active scheduled tasks grouped by date."""
    today = date.today()
    max_date = today + timedelta(days=max_future_days)

    if include_overdue:
        # Get all incomplete tasks up to max_date (includes overdue)
        cursor = await db.execute("""
            SELECT t.id, t.name, t.effort_level, t.scheduled_date,
                   r.name as role_name
            FROM tasks t
            JOIN roles r ON t.role_id = r.id
            WHERE t.is_complete = 0
              AND t.scheduled_date IS NOT NULL
              AND t.scheduled_date <= ?
            ORDER BY t.scheduled_date, t.name
        """, (max_date.isoformat(),))
    else:
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

def get_day_lines(day_tasks: list) -> int:
    """Calculate lines needed for a day: Header (1) + tasks + 2 blank lines (2)."""
    return 3 + len(day_tasks)

def collect_all_days(tasks_by_date: dict, max_future_days: int = 28):
    """Collect all days (overdue + future) in chronological order."""
    today = date.today()
    max_date = today + timedelta(days=max_future_days)

    all_days = []

    # First, collect overdue dates (dates before today that have tasks)
    overdue_dates = sorted([
        date.fromisoformat(d) for d in tasks_by_date.keys()
        if date.fromisoformat(d) < today
    ])

    for overdue_date in overdue_dates:
        date_str = overdue_date.isoformat()
        tasks = tasks_by_date.get(date_str, [])
        if tasks:
            all_days.append({
                "date": overdue_date,
                "formatted_date": overdue_date.strftime("%A, %m/%d"),
                "tasks": tasks,
                "is_overdue": True,
                "lines": get_day_lines(tasks)
            })

    # Then add today and future days
    current_date = today
    while current_date <= max_date:
        date_str = current_date.isoformat()
        tasks = tasks_by_date.get(date_str, [])

        all_days.append({
            "date": current_date,
            "formatted_date": current_date.strftime("%A, %m/%d"),
            "tasks": tasks,
            "is_overdue": False,
            "lines": get_day_lines(tasks)
        })

        current_date += timedelta(days=1)

    return all_days

def build_schedule_days(tasks_by_date: dict, max_lines: int = MAX_LINES, max_future_days: int = 28):
    """Build schedule days respecting the line limit (single column)."""
    all_days = collect_all_days(tasks_by_date, max_future_days=max_future_days)

    schedule_days = []
    current_line = 0

    for day in all_days:
        if current_line + day["lines"] > max_lines:
            break
        schedule_days.append(day)
        current_line += day["lines"]

    return schedule_days

def build_schedule_columns(tasks_by_date: dict, max_lines: int = MAX_LINES, max_future_days: int = 28):
    """Build two columns of schedule days, each respecting the line limit."""
    all_days = collect_all_days(tasks_by_date, max_future_days=max_future_days)

    left_column = []
    right_column = []
    left_lines = 0
    right_lines = 0

    for day in all_days:
        lines_needed = day["lines"]

        # Try to add to left column first
        if left_lines + lines_needed <= max_lines:
            left_column.append(day)
            left_lines += lines_needed
        # Then try right column
        elif right_lines + lines_needed <= max_lines:
            right_column.append(day)
            right_lines += lines_needed
        # Both columns full
        else:
            break

    return left_column, right_column

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
    """Print-friendly schedule view with two columns."""
    tasks_by_date = await get_scheduled_tasks(db, max_future_days=20)
    left_column, right_column = build_schedule_columns(tasks_by_date, max_future_days=20)

    return templates.TemplateResponse("schedule/print.html", {
        "request": request,
        "left_column": left_column,
        "right_column": right_column
    })
