from fastapi import APIRouter, Request, Form, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
import aiosqlite

from app.database import get_db

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def list_roles(request: Request, db: aiosqlite.Connection = Depends(get_db)):
    """List all roles."""
    cursor = await db.execute("SELECT id, name FROM roles ORDER BY name")
    roles = await cursor.fetchall()
    return templates.TemplateResponse("roles/list.html", {
        "request": request,
        "roles": roles
    })

@router.get("/new", response_class=HTMLResponse)
async def new_role(request: Request):
    """Show form to create a new role."""
    return templates.TemplateResponse("roles/edit.html", {
        "request": request,
        "role": None
    })

@router.post("/new")
async def create_role(
    request: Request,
    name: str = Form(...),
    db: aiosqlite.Connection = Depends(get_db)
):
    """Create a new role."""
    await db.execute("INSERT INTO roles (name) VALUES (?)", (name,))
    await db.commit()
    return RedirectResponse(url="/roles", status_code=303)

@router.get("/{role_id}/edit", response_class=HTMLResponse)
async def edit_role(
    request: Request,
    role_id: int,
    db: aiosqlite.Connection = Depends(get_db)
):
    """Show form to edit a role."""
    cursor = await db.execute("SELECT id, name FROM roles WHERE id = ?", (role_id,))
    role = await cursor.fetchone()
    if not role:
        return RedirectResponse(url="/roles", status_code=303)
    cursor = await db.execute(
        "SELECT id, name, effort_level, scheduled_date, is_complete FROM tasks WHERE role_id = ? ORDER BY name",
        (role_id,)
    )
    tasks = await cursor.fetchall()
    return templates.TemplateResponse("roles/edit.html", {
        "request": request,
        "role": role,
        "tasks": tasks
    })

@router.post("/{role_id}/edit")
async def update_role(
    role_id: int,
    name: str = Form(...),
    db: aiosqlite.Connection = Depends(get_db)
):
    """Update a role."""
    await db.execute("UPDATE roles SET name = ? WHERE id = ?", (name, role_id))
    await db.commit()
    return RedirectResponse(url="/roles", status_code=303)

@router.post("/{role_id}/delete")
async def delete_role(
    request: Request,
    role_id: int,
    db: aiosqlite.Connection = Depends(get_db)
):
    """Delete a role if no tasks are linked."""
    # Check for linked tasks
    cursor = await db.execute(
        "SELECT COUNT(*) as count FROM tasks WHERE role_id = ?", (role_id,)
    )
    result = await cursor.fetchone()

    if result["count"] > 0:
        # Has linked tasks, cannot delete
        cursor = await db.execute("SELECT id, name FROM roles ORDER BY name")
        roles = await cursor.fetchall()
        return templates.TemplateResponse("roles/list.html", {
            "request": request,
            "roles": roles,
            "error": f"Cannot delete role: {result['count']} task(s) are still linked. Reassign or delete them first."
        })

    await db.execute("DELETE FROM roles WHERE id = ?", (role_id,))
    await db.commit()
    return RedirectResponse(url="/roles", status_code=303)
