from fastapi import APIRouter, Request, Form, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from datetime import date, timedelta
from typing import Optional
import aiosqlite

from app.database import get_db

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

def get_date_range():
    """Get valid date range (today + 4 weeks)."""
    today = date.today()
    max_date = today + timedelta(weeks=4)
    return today, max_date

@router.get("/", response_class=HTMLResponse)
async def list_tasks(
    request: Request,
    show: str = "active",
    db: aiosqlite.Connection = Depends(get_db)
):
    """List tasks filtered by status."""
    is_complete = 1 if show == "completed" else 0

    cursor = await db.execute("""
        SELECT t.id, t.name, t.effort_level, t.scheduled_date, t.is_complete,
               r.name as role_name, r.id as role_id
        FROM tasks t
        JOIN roles r ON t.role_id = r.id
        WHERE t.is_complete = ?
        ORDER BY
            CASE WHEN t.scheduled_date IS NULL THEN 1 ELSE 0 END,
            t.scheduled_date ASC,
            t.name ASC
    """, (is_complete,))
    tasks = await cursor.fetchall()
    today = date.today().isoformat()
    return templates.TemplateResponse("tasks/list.html", {
        "request": request,
        "tasks": tasks,
        "show": show,
        "today": today
    })

@router.get("/new", response_class=HTMLResponse)
async def new_task(request: Request, db: aiosqlite.Connection = Depends(get_db)):
    """Show form to create a new task."""
    cursor = await db.execute("SELECT id, name FROM roles ORDER BY name")
    roles = await cursor.fetchall()
    today, max_date = get_date_range()
    return templates.TemplateResponse("tasks/edit.html", {
        "request": request,
        "task": None,
        "roles": roles,
        "min_date": today.isoformat(),
        "max_date": max_date.isoformat()
    })

@router.post("/new")
async def create_task(
    request: Request,
    name: str = Form(...),
    role_id: int = Form(...),
    effort_level: str = Form(...),
    scheduled_date: Optional[str] = Form(None),
    db: aiosqlite.Connection = Depends(get_db)
):
    """Create a new task."""
    # Convert empty string to None
    if scheduled_date == "":
        scheduled_date = None

    await db.execute(
        """INSERT INTO tasks (name, role_id, effort_level, scheduled_date, is_complete)
           VALUES (?, ?, ?, ?, 0)""",
        (name, role_id, effort_level, scheduled_date)
    )
    await db.commit()
    return RedirectResponse(url="/tasks", status_code=303)

@router.get("/{task_id}/edit", response_class=HTMLResponse)
async def edit_task(
    request: Request,
    task_id: int,
    db: aiosqlite.Connection = Depends(get_db)
):
    """Show form to edit a task."""
    cursor = await db.execute(
        """SELECT id, name, role_id, effort_level, scheduled_date, is_complete
           FROM tasks WHERE id = ?""",
        (task_id,)
    )
    task = await cursor.fetchone()
    if not task:
        return RedirectResponse(url="/tasks", status_code=303)

    cursor = await db.execute("SELECT id, name FROM roles ORDER BY name")
    roles = await cursor.fetchall()
    today, max_date = get_date_range()

    return templates.TemplateResponse("tasks/edit.html", {
        "request": request,
        "task": task,
        "roles": roles,
        "min_date": today.isoformat(),
        "max_date": max_date.isoformat()
    })

@router.post("/{task_id}/edit")
async def update_task(
    task_id: int,
    name: str = Form(...),
    role_id: int = Form(...),
    effort_level: str = Form(...),
    scheduled_date: Optional[str] = Form(None),
    db: aiosqlite.Connection = Depends(get_db)
):
    """Update a task."""
    if scheduled_date == "":
        scheduled_date = None

    await db.execute(
        """UPDATE tasks SET name = ?, role_id = ?, effort_level = ?, scheduled_date = ?
           WHERE id = ?""",
        (name, role_id, effort_level, scheduled_date, task_id)
    )
    await db.commit()
    return RedirectResponse(url="/tasks", status_code=303)

@router.post("/{task_id}/complete")
async def complete_task(
    task_id: int,
    next: Optional[str] = Form(None),
    db: aiosqlite.Connection = Depends(get_db)
):
    """Mark a task as complete."""
    await db.execute("UPDATE tasks SET is_complete = 1 WHERE id = ?", (task_id,))
    await db.commit()
    return RedirectResponse(url=next or "/tasks", status_code=303)

@router.post("/{task_id}/reactivate")
async def reactivate_task(
    task_id: int,
    db: aiosqlite.Connection = Depends(get_db)
):
    """Reactivate a completed task."""
    await db.execute("UPDATE tasks SET is_complete = 0 WHERE id = ?", (task_id,))
    await db.commit()
    return RedirectResponse(url="/tasks?show=completed", status_code=303)

@router.post("/{task_id}/delete")
async def delete_task(
    task_id: int,
    next: Optional[str] = Form(None),
    db: aiosqlite.Connection = Depends(get_db)
):
    """Delete a task permanently."""
    await db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    await db.commit()
    return RedirectResponse(url=next or "/tasks", status_code=303)
