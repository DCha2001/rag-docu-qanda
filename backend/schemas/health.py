from typing import Optional
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    details: Optional[str] = None
