import enum
import uuid
from sqlalchemy import Column, String, Integer, DateTime, Enum, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.database import Base
from sqlalchemy.dialects.postgresql import JSONB

class JobStatus(enum.Enum):
    processing = "processing"
    finished = "finished"
    failed = "failed"

class Job(Base):
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_name = Column(String(255), nullable=False)
    status = Column(Enum(JobStatus), default=JobStatus.processing, nullable=False)
    progress = Column(Integer, default=0)
    # result_path = Column(Text, nullable=True)
    result_data = Column(JSONB, nullable=True)
    download_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())