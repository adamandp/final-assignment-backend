import os
import logging
from minio import Minio
from datetime import timedelta
from app.core.config_minio import minio_settings

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
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) 
        temp_dir = os.path.join(base_dir, "temp")
        
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
            
        local_file_path = os.path.join(temp_dir, object_name)

        self.client.fget_object(
            minio_settings.MINIO_BUCKET_NAME, 
            object_name,
            local_file_path
        )
        
        logger.info(f"💾 Successfully moved file to: {local_file_path}")
        return local_file_path
        
    def get_presigned_url(self, object_name: str):
        return self.client.get_presigned_url(
            method="PUT",
            bucket_name=minio_settings.MINIO_BUCKET_NAME,
            object_name=object_name,
            expires=timedelta(minutes=15),
        )

    def list_buckets(self):
        return self.client.list_buckets()
    
    def delete_object(self, object
    _name: str):
        try:
            self.client.remove_object(minio_settings.MINIO_BUCKET_NAME, object_name)
            logger.info(f"🗑️ Successfully deleted object '{object_name}' from bucket.")
        except Exception as e:
            logger.error(f"❌ Error deleting object '{object_name}': {e}")
            raise e

storage_service = StorageService()