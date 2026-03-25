from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Annotated

from app.db.database import get_db
from app.schemas.common_schema import WebResponse
from app.schemas.health_schema import HealthCheckRes, ServiceStatus
from app.services.health_service import HealthService

router = APIRouter(
    tags=["System Monitor"],
    prefix="/health"
)

def get_health_service(db: Session = Depends(get_db)):
    return HealthService(db)

HealthServiceDep = Annotated[HealthService, Depends(get_health_service)]

@router.get("", response_model=WebResponse[HealthCheckRes])
def get_overall_health(health_service: HealthServiceDep) -> WebResponse[HealthCheckRes]:
    """
    Get the summary of all system services.
    """
    health_data = health_service.check_system_health()
    message = "All systems go! 🚀" if health_data.overall_status == "fully_functional" else "System issues detected! ⚠️"
    
    return WebResponse[HealthCheckRes](
        message=message,
        data=health_data
    )

@router.get("/database", response_model=WebResponse[ServiceStatus])
def get_database_health(health_service: HealthServiceDep) -> WebResponse[ServiceStatus]:
    """
    Check only the PostgreSQL database connectivity.
    """
    db_data = health_service.check_database()
    message = "Database is breathing fine! 🐘" if db_data.status == "healthy" else "Database is struggling! 🛑"
    
    return WebResponse[ServiceStatus](
        message=message,
        data=db_data
    )

@router.get("/storage", response_model=WebResponse[ServiceStatus])
def get_storage_health(health_service: HealthServiceDep) -> WebResponse[ServiceStatus]:
    """
    Check only the MinIO storage accessibility.
    """
    storage_data = health_service.check_storage()
    message = "Storage is wide open and ready! 📦" if storage_data.status == "healthy" else "Storage is locked down! 🔒"
    
    return WebResponse[ServiceStatus](
        message=message,
        data=storage_data
    )