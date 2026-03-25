import time
import logging
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.services.storage_service import storage_service
from app.schemas.health_schema import HealthCheckRes, ServiceStatus

logger = logging.getLogger("app")

class HealthService:
    def __init__(self, db: Session):
        self.db = db

    def check_system_health(self) -> HealthCheckRes:
        db_status = self.check_database()
        storage_status = self.check_storage()

        overall = "fully_functional"
        if db_status.status != "healthy" or storage_status.status != "healthy":
            overall = "degraded"
        
        if db_status.status == "unhealthy" and storage_status.status == "unhealthy":
            overall = "down"

        return HealthCheckRes(
            overall_status=overall,
            database=db_status,
            storage=storage_status
        )

    def check_database(self) -> ServiceStatus:
        start_time = time.time()
        try:
            self.db.execute(text("SELECT 1"))
            latency = (time.time() - start_time) * 1000
            return ServiceStatus(
                status="healthy",
                latency_ms=round(latency, 2),
                details="Database connection is stable and responsive."
            )
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return ServiceStatus(
                status="unhealthy",
                details=f"Database connection error: {str(e)}"
            )

    def check_storage(self) -> ServiceStatus:
        start_time = time.time()
        try:
            storage_service.list_buckets() 
            latency = (time.time() - start_time) * 1000
            return ServiceStatus(
                status="healthy",
                latency_ms=round(latency, 2),
                details="MinIO storage is online and accessible."
            )
        except Exception as e:
            logger.error(f"Storage health check failed: {e}")
            return ServiceStatus(
                status="unhealthy",
                details=f"Storage service error: {str(e)}"
            )