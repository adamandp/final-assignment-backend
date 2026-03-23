from pydantic_settings import BaseSettings

class DBSetting(BaseSettings):
    DATABASE_URL: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


db_settings = DBSetting()