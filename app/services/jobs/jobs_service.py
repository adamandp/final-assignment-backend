import uuid
import os
import logging
from sqlalchemy.orm import Session
from fastapi import BackgroundTasks, HTTPException

from app.schemas.common_schema import WebResponse
from app.schemas.jobs_schema import (
    JobsUploadUrlRes,
    JobsProcessRes,
    JobsStatusRes,
    JobsUploadUrlReq,
    JobsProcessReq
)
from app.model.jobs import Job, JobStatus 
from app.services.jobs.loader import Loader
from app.services.jobs.preprocessor import Preprocessor
from app.services.jobs.segmentor import Segmentor
from app.services.jobs.extractor import Extractor
from app.services.jobs.predictor import predictor
from app.services.storage_service import storage_service
from app.db.database import SessionLocal

logger = logging.getLogger("app")

class JobService:
    def __init__(self, db: Session):
        self.db = db

    def get_upload_url(self, payload: JobsUploadUrlReq) -> WebResponse[JobsUploadUrlRes]:
        filename = payload.filename
        job_id = uuid.uuid4()
        
        ext = os.path.splitext(filename)[1].lower()
        if ext not in [".fif", ".edf", ".set"]:
            raise HTTPException(
                status_code=400, 
                detail="Oops! That file format isn't supported. Please use .fif, .edf, or .set files. 🛑"
            )

        job_file_name = f"{job_id}_raw{ext}"
        url = storage_service.get_presigned_url(object_name=job_file_name)
        
        return WebResponse[JobsUploadUrlRes](
            message="🚀 Your secure upload link is ready! Let's get that EEG data moving. 🛰️",
            data=JobsUploadUrlRes(
                url=url,
                job_file_name=job_file_name
            )
        )

    def process(self, payload: JobsProcessReq, background_tasks: BackgroundTasks) -> WebResponse[JobsProcessRes]:
        job_file_name = payload.job_file_name
        try:
            raw_uuid = job_file_name.replace("_raw", "").split(".")[0]            
            job_id_obj = uuid.UUID(raw_uuid)

            new_job = Job(
                id=job_id_obj,
                file_name=job_file_name,
                status=JobStatus.PROCESSING,
                progress=0
            )

            self.db.add(new_job)
            self.db.commit()
            self.db.refresh(new_job)

            background_tasks.add_task(self.run_heavy_analysis, job_id_obj, job_file_name)
            logger.info(f"🚀 Job {job_id_obj} started processing...")

            return WebResponse[JobsProcessRes](
                message="⚡ Engine started! We're deep-diving into your EEG data as we speak. 🧠",
                data=JobsProcessRes(job_id=job_id_obj)
            )
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to initiate job {job_file_name}: {e}")
            raise HTTPException(
                status_code=500, 
                detail="Something went wrong while firing up the analysis. Please try again! 🛠️"
            )

    def run_heavy_analysis(self, job_id: uuid.UUID, job_file_name: str):
        with SessionLocal() as db:
            local_path = None

            try:
                self._update_job(
                    db,
                    job_id,
                    progress=20,
                    status=JobStatus.DOWNLOADING,
                )
                local_path = storage_service.download_file(job_file_name)
                logger.info(f"💾 Successfully moved file: {job_id}")

                self._update_job(
                    db,
                    job_id,
                    progress=30,
                    status=JobStatus.LOADING,
                )
                raw = Loader.load_raw(local_path)
                logger.info(f"✨ Successfully loaded raw data: {job_id}")

                self._update_job(
                    db,
                    job_id,
                    progress=40,
                    status=JobStatus.PROCESSING,
                )
                raw_preprocessed = Preprocessor.preprocessing(raw)
                logger.info(f"✨ Successfully preprocessed raw data {job_id}")

                self._update_job(
                    db,
                    job_id,
                    progress=50,
                    status=JobStatus.SEGMENTING,
                )
                epochs = Segmentor.segmentor(raw_preprocessed)
                logger.info(f"✨ Successfully segmented raw data {job_id}")

                self._update_job(
                    db,
                    job_id,
                    progress=70,
                    status=JobStatus.EXTRACTING_FEATURES,
                )
                df_features = Extractor.extractor(epochs)
                logger.info(f"✨ Successfully extracted features {job_id}")

                self._update_job(
                    db,
                    job_id,
                    progress=80,
                    status=JobStatus.EXTRACTING_FEATURES_CONNECTIVITY,
                )
                df_con = Extractor.feature_extraction_connectivity(epochs)
                logger.info(f"✨ Successfully extracted connectivity features {job_id}")

                self._update_job(
                    db,
                    job_id,
                    progress=90,
                    status=JobStatus.PREDICTING,
                )
                prediction_result = predictor.predict(df_features, df_con)
                logger.info(f"✨ Successfully predicted {job_id}")

                self._update_job(
                    db,
                    job_id,
                    progress=100,
                    status=JobStatus.FINISHED,
                    result_data=prediction_result,
                )

                logger.info(f"✅ Job {job_id} completed successfully.")

            except Exception as e:
                logger.error(f"❌ Error processing job {job_id}: {str(e)}", exc_info=True)
                self._update_job(db, job_id, progress=0, status=JobStatus.FAILED)
            
            finally:
                if local_path and os.path.exists(local_path):
                    try:
                        os.remove(local_path)
                        storage_service.delete_object(job_file_name)
                    except Exception as cleanup_err:
                        logger.warning(f"Failed to cleanup {local_path}: {cleanup_err}")

    def _update_job(self, db: Session, job_id: uuid.UUID, **kwargs):
        try:
            db.query(Job).filter(Job.id == job_id).update(kwargs)
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update job {job_id}: {e}")

    def get_status(self, job_id: str) -> WebResponse[JobsStatusRes]:
            job_id_obj = uuid.UUID(job_id)
            job = self.db.query(Job).filter(Job.id == job_id_obj).first()

            data_res = JobsStatusRes(
                job_id=job.id,
                status=job.status.value,
                progress=job.progress,
                result=job.result_data 
            )

            return WebResponse[JobsStatusRes](
                message="✨ Insight update! Here is the latest on your brainwave analysis. 📈",
                data=data_res
            )