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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    """
    # Initialize directories on startup
    Config.init_app()

    # Print startup message
    print("=" * 50)
    print("LDA Business News Trend Application")
    print("FastAPI Framework")
    print("=" * 50)

    yield

    # Cleanup on shutdown
    print("Shutting down application...")


# Create FastAPI application
app = FastAPI(
    title="LDA Topic Modeling API",
    description="API untuk LDA Topic Modeling pada berita bisnis Indonesia dengan KDD Pipeline",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

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

    Returns the current status of the server.
    """
    return {
        "status": "ok",
        "message": "Server is running",
        "framework": "FastAPI"
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
