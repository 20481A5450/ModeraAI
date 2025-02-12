from pydantic import BaseModel

class TextModerationRequest(BaseModel):
    text: str

class TextModerationResponse(BaseModel):
    id: int
    text: str
    flagged: bool
    categories: dict
