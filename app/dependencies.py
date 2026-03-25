from sqlalchemy.orm import Session
from fastapi import Depends
from typing import Generator

from app.services.jobs.jobs_service import JobService
from app.db.database import SessionLocal

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_job_service_dep(db: Session = Depends(get_db)) -> JobService:
    return JobService(db=db)