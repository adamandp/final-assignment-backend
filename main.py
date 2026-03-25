import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError
from minio.error import S3Error

from app.api.init_routes import init_routes
from app.exceptions.handlers import (
    app_exception_handler, 
    sqlalchemy_exception_handler,
    minio_exception_handler
)

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)-8s | %(asctime)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

app = FastAPI(
    title="FastAPI",
    description="FastAPI",
    version="0.0.1"
)

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(Exception, app_exception_handler)
app.add_exception_handler(S3Error, minio_exception_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)


init_routes(app)
