import uuid
import os
import logging

from sqlalchemy.orm import Session
from services.storage_service import storage_service
from schemas.common_schema import WebResponse
from schemas.jobs_schema import (
    JobsUploadUrlRes,
    JobsProcessRes
)
from fastapi import BackgroundTasks
from model.jobs import Job
from services.jobs.loader import Loader
from services.jobs.preprocessor import Preprocessor
from services.jobs.segmentor import Segmentor
from services.jobs.extractor import Extractor
from services.jobs.predictor import predictor
from services.storage_service import storage_service
from db.database import SessionLocal

logger = logging.getLogger("app")

class JobService:
    def __init__(self, db: Session):
        self.db = db

    def get_upload_url(self, filename: str) -> WebResponse[JobsUploadUrlRes]:
        job_id = uuid.uuid4()
        ext = ""

        if filename.endswith((".fif", ".edf", ".set")):
            ext = os.path.splitext(filename)[1]
            print("Format file:", ext)

        job_file_name = f"{job_id}_raw{ext}"

        url = storage_service.get_presigned_url(
            object_name= job_file_name
        )
        return WebResponse[JobsUploadUrlRes](
            message="🎉 upload url created successfully! Welcome aboard! 🚀",
            data=JobsUploadUrlRes(
                url=url,
                job_file_name = job_file_name
            )
        )
    
    def process(self, job_file_name: str, background_tasks: BackgroundTasks) -> WebResponse[JobsProcessRes]:
        try:
            # Ambil UUID string dan ubah ke object UUID asli
            raw_uuid = job_file_name.replace("_raw", "").split(".")[0]            
            job_id_obj = uuid.UUID(raw_uuid) # Pastiin ini valid UUID

            new_job = Job(
                id=job_id_obj, # Pake object UUID
                file_name=job_file_name,
                status="processing",
                progress=0
            )

            self.db.add(new_job)
            self.db.commit()
            self.db.refresh(new_job)

            background_tasks.add_task(self.run_heavy_analysis, job_id_obj, job_file_name)

            return WebResponse[JobsProcessRes](
                message="⚡ Processing started!",
                data=JobsProcessRes(job_id=str(job_id_obj))
            )
        except Exception as e:
            self.db.rollback() # <--- PENTING!
            logger.error(f"Gagal inisiasi job: {e}")
            raise e

    def run_heavy_analysis(self, job_id: str, job_file_name: str):
        with SessionLocal() as db:
            local_path = None

            try:
                # STEP 1: Download (Progress 10)
                self._update_job(
                    db, 
                    job_id, 
                    progress=10, 
                    status="processing"
                )
                local_path = storage_service.download_file(job_file_name)
                
                # STEP 2: Loader (Progress 20)
                self._update_job(
                    db, 
                    job_id, 
                    progress=30, 
                    status="processing"
                )
                raw = Loader.load_raw(local_path)
                
                # STEP 3: Preprocessing (Progress 30)
                self._update_job(
                    db, 
                    job_id, 
                    progress=40, 
                    status="processing"
                )
                raw_preprocessed = Preprocessor.preprocessing(raw)

                # STEP 4: Segmentation (Progress 40)
                self._update_job(
                    db, 
                    job_id, 
                    progress=50, 
                    status="processing"
                )
                epochs = Segmentor.segmentor(raw_preprocessed)
                
                # STEP 5: Feature Extraction (Progress 70)
                self._update_job(
                    db, 
                    job_id, 
                    progress=70, 
                    status="processing"
                )
                df_features = Extractor.extractor(epochs)
                df_con = Extractor.feature_extraction_connectivity(epochs)
                
                # STEP 6: Predict (Progress 90)
                self._update_job(
                    db, 
                    job_id, 
                    progress=90, 
                    status="processing"
                )
                prediction_result = predictor.predict(df_features, df_con)
                
                # STEP 6: Finished (Progress 100)
                self._update_job(
                    db, 
                    job_id, 
                    progress=100, 
                    status="finished", 
                    result_data=prediction_result                
                )
                

                logger.info(f"✅ Job {job_id} completed successfully.")

            except Exception as e:
                logger.error(f"❌ Error processing job {job_id}: {str(e)}", exc_info=True)
                self._update_job(db, job_id, progress=0, status="failed")
            
            finally:
                # Cleanup file sementara di /tmp
                if local_path and os.path.exists(local_path):
                    os.remove(local_path)
                    logger.info(f"Cleaned up local file: {local_path}")

    def _update_job(self, db: Session, job_id: uuid.UUID, **kwargs):
        try:
            db.query(Job).filter(Job.id == job_id).update(kwargs)
            db.commit()
        except Exception as e:
            db.rollback() # <--- BIAR GAK MACET TRANSAKSINYA
            logger.error(f"Gagal update status job {job_id}: {e}")
            raise e

    def get_status(self, job_id: str):
        job = self.db.query(Job).filter(Job.id == job_id).first()
        return WebResponse(
            message="Job status",
            data={
                "status": job.status.value,
                "progress": job.progress,
                "result": job.result_path
            }
        )