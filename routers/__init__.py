"""
FastAPI routers
"""
from .auth import router as auth_router
from .kdd import router as kdd_router
from .search import router as search_router
from .project import router as project_router

__all__ = [
    "auth_router",
    "kdd_router",
    "search_router",
    "project_router",
]
