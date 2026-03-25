import logging
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi import Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, NoResultFound
from minio.error import S3Error

from app.schemas.common_schema import WebResponse

logger = logging.getLogger("app.exceptions")

async def app_exception_handler(request: Request, exc: Exception):
    logger.critical(f"🚨 UNHANDLED ERROR: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content=WebResponse(
            message="error",
            errors="An internal server error occurred. Please try зagain later.",
            data=None
        ).model_dump()
    )

async def sqlalchemy_exception_handler(request: Request, exc: Exception):
    message = "Database error occurred"
    errors = str(exc)
    status_code = status.HTTP_400_BAD_REQUEST

    logger.error(
        f"❌ {exc.__class__.__name__}: {errors}",
        exc_info=True
    )

    if isinstance(exc, IntegrityError):
        message = "⚡ Data already exists! No duplicates allowed! 😆"
        status_code = status.HTTP_409_CONFLICT
    
    elif isinstance(exc, NoResultFound):
        message = "🔍 Record not found in another dimension? 🛸"
        status_code = status.HTTP_404_NOT_FOUND

    return JSONResponse(
        status_code=status_code,
        content=WebResponse(
            message="validation error",
            errors=message,
            data=None
        ).model_dump()
    )


async def minio_exception_handler(request: Request, exc: S3Error):
    err = "🔍 Storage issue. Did the bucket teleport to another dimension? 🛸"
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    if exc.code == "NoSuchBucket":
        err = "🪣 Bucket not found! Someone forgot to create the container! 😆"
        status_code = status.HTTP_404_NOT_FOUND
    elif exc.code == "AccessDenied":
        err = "🚫 Access Denied! You don't have the secret key to this vault! 🔐"
        status_code = status.HTTP_403_FORBIDDEN
    elif exc.code == "NoSuchKey":
        err = "📄 File not found. It's gone, reduced to atoms! ⚛️"
        status_code = status.HTTP_404_NOT_FOUND

    logger.error(
        f"❌ MinIO S3 Error: {exc.code} - {err} - {exc.message}", exc_info=True
    )
    logger.error(
        f"❌ MinIO S3 Error: {exc.code} - {exc.message}", exc_info=True
    )

    return JSONResponse(
        status_code=status_code,
        content=WebResponse(
            message="🚨 Server error 🚨",
            errors="🚨 Server error 🚨",
            data=None
        ).model_dump()
    )