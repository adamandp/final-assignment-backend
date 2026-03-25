import enum
import uuid
from sqlalchemy import Column, String, Integer, DateTime, Text
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.db.database import Base


class JobStatus(enum.Enum):
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


class Job(Base):
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_name = Column(String(255), nullable=False)
    status = Column(
        SqlEnum(
            JobStatus,
            name="jobstatus",
            values_callable=lambda x: [e.value for e in x],
        ),
        default=JobStatus.PENDING,
        nullable=False,
    )
    progress = Column(Integer, default=0)
    result_data = Column(JSONB, nullable=True)
    download_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
