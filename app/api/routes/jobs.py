from fastapi import APIRouter, Depends, BackgroundTasks
from typing import Annotated
from schemas.common_schema import WebResponse
from schemas.jobs_schema import (
    JobsUploadUrlRes,
    JobsProcessRes
)
from services.jobs.jobs_service import JobService
from dependencies import get_job_service_dep

router = APIRouter(
    tags=["Jobs"]
)

job_dependency = Annotated[JobService, Depends(get_job_service_dep)]

@router.get("/upload-url")
def get_presigned_url(job_service: job_dependency, filename: str) -> WebResponse[JobsUploadUrlRes]:
    return job_service.get_upload_url(filename)


@router.post("/process", response_model=WebResponse[JobsProcessRes])
def process(
    job_service: job_dependency, 
    filename: str, 
    background_tasks: BackgroundTasks
) -> WebResponse[JobsProcessRes]:
    return job_service.process(filename, background_tasks)