from pydantic import BaseModel, Field
from typing import Optional

class ServiceStatus(BaseModel):
    status: str = Field(..., example="healthy")
    latency_ms: Optional[float] = Field(None, example=12.5)
    details: Optional[str] = Field(None, example="Connected to PostgreSQL 15.3")

class HealthCheckRes(BaseModel):
    overall_status: str = Field(..., example="fully_functional")
    database: ServiceStatus
    storage: ServiceStatus