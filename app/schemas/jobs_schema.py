from pydantic import BaseModel
from uuid import UUID

class JobsUploadUrlRes(BaseModel):
    url: str
    job_file_name: str

class JobsProcessRes(BaseModel):
    job_id: UUID