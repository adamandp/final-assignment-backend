from pydantic_settings import BaseSettings

class MinioSettings(BaseSettings):
    MINIO_ENDPOINT: str
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_BUCKET_NAME: str
    MINIO_SECURE: bool = False

    class Config:
        env_file = ".env"
        extra = "ignore" 

minio_settings = MinioSettings()