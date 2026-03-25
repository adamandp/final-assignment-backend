from fastapi import FastAPI

from app.api.routes import (
    health_check,
    jobs
)

def init_routes(app: FastAPI):
    app.include_router(health_check.router, prefix="/health-check")
    app.include_router(jobs.router, prefix="/jobs")