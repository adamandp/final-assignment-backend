from services.jobs.jobs_service import JobService
from fastapi import Depends, BackgroundTasks
from sqlalchemy.orm import Session
from fastapi import Depends
from sqlalchemy.orm import Session
from db.database import SessionLocal
from typing import Generator

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_job_service_dep(db: Session = Depends(get_db)) -> JobService:
    return JobService(db=db)