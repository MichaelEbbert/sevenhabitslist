import uvicorn
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager

from app.database import init_db
from app.routers import roles, tasks, schedule

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    await init_db()
    yield

app = FastAPI(title="Seven Habits List", lifespan=lifespan)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Templates
templates = Jinja2Templates(directory="app/templates")

# Include routers
app.include_router(roles.router, prefix="/roles", tags=["roles"])
app.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
app.include_router(schedule.router, prefix="/schedule", tags=["schedule"])

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page with navigation."""
    return templates.TemplateResponse("index.html", {"request": request})

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=3002, reload=True)
