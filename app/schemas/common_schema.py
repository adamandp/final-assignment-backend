from pydantic import BaseModel
from typing import TypeVar, Generic, Optional, Any

# T = unknown
T = TypeVar("T")

class WebResponse(BaseModel, Generic[T]):
    message: Optional[str] = None
    errors: Optional[str] = None
    data: Optional[T] = None

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Successfully processed ⚡",
                "data": {
                    "id": "uuid-here", 
                    "status": "active"
                },
                "errors": None
            }
        }