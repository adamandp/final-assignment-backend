from fastapi import APIRouter, Depends, BackgroundTasks, Query
from typing import Annotated
from uuid import UUID

from app.schemas.common_schema import WebResponse
from app.schemas.jobs_schema import (
    JobsUploadUrlRes,
    JobsProcessRes,
    JobsStatusRes,
    JobsUploadUrlReq,
    JobsProcessReq
)
from app.services.jobs.jobs_service import JobService
from app.dependencies import get_job_service_dep

router = APIRouter(
    tags=["Jobs"],
)

JobServiceDep = Annotated[JobService, Depends(get_job_service_dep)]

@router.post("/upload-url", response_model=WebResponse[JobsUploadUrlRes])
def get_presigned_url(
    job_service: JobServiceDep, 
    payload: JobsUploadUrlReq
) -> WebResponse[JobsUploadUrlRes]:
    return job_service.get_upload_url(payload)


@router.post("/process", response_model=WebResponse[JobsProcessRes])
def process_analysis(
    job_service: JobServiceDep, 
    payload: JobsProcessReq, 
    background_tasks: BackgroundTasks
) -> WebResponse[JobsProcessRes]:
    return job_service.process(payload, background_tasks)


@router.get("/status/{job_id}", response_model=WebResponse[JobsStatusRes])
def get_job_status(
    job_service: JobServiceDep, 
    job_id: str
) -> WebResponse[JobsStatusRes]:
    return job_service.get_status(job_id)