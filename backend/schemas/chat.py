from pydantic import BaseModel, Field


class ContentBlock(BaseModel):
    type: str
    text: str

    model_config = {"from_attributes": True}


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)


class QueryResponse(BaseModel):
    response: list[ContentBlock]
