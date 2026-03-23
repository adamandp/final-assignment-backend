from fastapi import APIRouter
from pydantic import BaseModel


router = APIRouter(tags={"Health Check"})

class HealthCheckResponseModel(BaseModel):
    status: str

@router.get("/", response_model=HealthCheckResponseModel)
async def health_check():
    return HealthCheckResponseModel(status="OK")
