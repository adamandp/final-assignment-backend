from minio import Minio
from core.config_minio import minio_settings
from datetime import timedelta
import os

import logging

logger = logging.getLogger(__name__)

class StorageService:
    def __init__(self):
        self.client = Minio(
            minio_settings.MINIO_ENDPOINT,
            access_key=minio_settings.MINIO_ACCESS_KEY,
            secret_key=minio_settings.MINIO_SECRET_KEY,
            secure=minio_settings.MINIO_SECURE
        )
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        if not self.client.bucket_exists(minio_settings.MINIO_BUCKET_NAME):
            self.client.make_bucket(minio_settings.MINIO_BUCKET_NAME)

    def download_file(self, object_name: str):
        # 1. Gunakan folder /tmp (standar Mac/Linux) biar gak pusing relative path
        # Atau kalau mau tetep di project, pake absolute path
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) 
        temp_dir = os.path.join(base_dir, "temp")
        
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
            
        local_file_path = os.path.join(temp_dir, object_name)

        # 2. WAJIB pake fget_object kalau mau download langsung ke file fisik
        self.client.fget_object(
            minio_settings.MINIO_BUCKET_NAME, 
            object_name,
            local_file_path
        )
        
        logger.info(f"💾 File downloaded to: {local_file_path}")
        return local_file_path
        
    def get_presigned_url(self, object_name: str):
        url = self.client.get_presigned_url(
            method="PUT",
            bucket_name=minio_settings.MINIO_BUCKET_NAME,
            object_name=object_name,
            expires=timedelta(minutes=15),
        )
        if not url:
            return {
                "message": "failed to generate presigned url",
                "error": "MinIO service returned empty URL",
            }
        return url

storage_service = StorageService()