"""FastAPI application factory for HomeMortgageInsurance Planner."""
from fastapi import FastAPI

from app.api.routes import router
from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Intelligent home insurance recommendation API",
)

app.include_router(router)
