from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional, Dict
import enum

class JobStatus(str, enum.Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    LOADING = "loading"
    PROCESSING = "processing"
    SEGMENTING = "segmenting"
    EXTRACTING_FEATURES = "extracting_features"
    EXTRACTING_FEATURES_CONNECTIVITY = "extracting_features_connectivity"
    PREDICTING = "predicting"
    FINISHED = "finished"
    FAILED = "failed"


class PredictionProbabilities(BaseModel):
    MCI: float = Field(..., description="Probabilitas Mild Cognitive Impairment")
    Normal: float = Field(..., description="Probabilitas kondisi Normal")
    Alzheimer: float = Field(..., description="Probabilitas kondisi Alzheimer")

class PredictionDetail(BaseModel):
    prediction: str = Field(..., example="Alzheimer")
    probabilities: PredictionProbabilities

class JobsUploadUrlReq(BaseModel):
    filename: str = Field(..., example="data_eeg_pasien_1.edf")

class JobsProcessReq(BaseModel):
    job_file_name: str = Field(..., example="uuid-string_raw.edf")

class JobsUploadUrlRes(BaseModel):
    url: str  
    job_file_name: str

class JobsProcessRes(BaseModel):
    job_id: UUID

class JobsStatusRes(BaseModel):
    job_id: UUID
    status: JobStatus
    progress: int
    
    result: Optional[PredictionDetail] = None

    class Config:
        from_attributes = True