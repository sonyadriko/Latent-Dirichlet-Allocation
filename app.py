"""
FastAPI application for LDA Topic Modeling
Migrated from Flask to FastAPI for better async support and type safety
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from config import Config
from routers import auth, kdd, search, project

# Database and Error Handling (Phase 2 Backend Improvements)
from core.database import init_database, close_database
from core.error_handlers import register_error_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    """
    # Initialize directories on startup
    Config.init_app()

    # Initialize database tables
    try:
        await init_database()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Warning: Database initialization failed: {e}")
        print("Application will continue with limited functionality")

    # Print startup message
    print("=" * 50)
    print("LDA Business News Trend Application")
    print("FastAPI Framework with persistent database")
    print("=" * 50)

    yield

    # Cleanup on shutdown
    print("Shutting down application...")
    try:
        await close_database()
        print("Database connection closed")
    except Exception as e:
        print(f"Warning: Database close failed: {e}")


# Create FastAPI application
app = FastAPI(
    title="LDA Topic Modeling API",
    description="API untuk LDA Topic Modeling pada berita bisnis Indonesia dengan KDD Pipeline",
    version="2.1.0",  # Bumped for Phase 2 improvements
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Register global error handlers
register_error_handlers(app)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="templates")

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(kdd.router, prefix="/api/kdd", tags=["KDD Pipeline"])
app.include_router(search.router, prefix="/api/search", tags=["Search"])
app.include_router(project.router, prefix="/api/projects", tags=["Projects"])


# Health check endpoint
@app.get("/api/health", tags=["Health"])
async def health():
    """
    Health Check Endpoint

    Returns the current status of the server and database.
    """
    from core.database import _engine
    from sqlalchemy import text

    db_status = "disconnected"
    try:
        if _engine:
            async with _engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            db_status = "connected"
    except Exception:
        pass

    return {
        "status": "ok",
        "message": "Server is running",
        "framework": "FastAPI",
        "version": "2.1.0",
        "database": db_status
    }


# Page routes
@app.get("/")
async def index(request: Request):
    """
    Main page
    """
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/login")
async def login(request: Request):
    """
    Login page
    """
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/register")
async def register(request: Request):
    """
    Register page
    """
    return templates.TemplateResponse("register.html", {"request": request})


@app.get("/admin")
async def admin(request: Request):
    """
    Admin dashboard page
    """
    return templates.TemplateResponse("admin.html", {"request": request})


@app.get("/visualization")
async def visualization(request: Request):
    """
    Visualization page
    """
    return templates.TemplateResponse("visualization.html", {"request": request})


# Entry point for running with uvicorn directly
if __name__ == "__main__":
    import uvicorn

    print("=" * 50)
    print("LDA Business News Trend Application")
    print("FastAPI Framework")
    print("=" * 50)
    print("Server running at: http://localhost:3030")
    print("API Documentation: http://localhost:3030/docs")
    print("=" * 50)

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=3030,
        reload=True
    )
