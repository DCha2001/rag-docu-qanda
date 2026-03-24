from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class ContentBlock(BaseModel):
    type: str
    text: str
    model_config = {"from_attributes": True}


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    session_id: str = Field(..., description="The session this message belongs to")


class QueryResponse(BaseModel):
    response: list[ContentBlock]


class MessageOut(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}


class SessionCreate(BaseModel):
    title: Optional[str] = None


class SessionOut(BaseModel):
    id: str
    title: Optional[str] = None
    created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}
