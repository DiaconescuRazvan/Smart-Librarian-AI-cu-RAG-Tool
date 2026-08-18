from pydantic import BaseModel, Field


class RecommendationRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    conversation_id: str | None = Field(default=None, max_length=64)


class RecommendationResponse(BaseModel):
    conversation_id: str
    recommendation: str
    summary: str
    title: str
    author: str
    themes: list[str]


class ImageRequest(BaseModel):
    title: str = Field(min_length=1, max_length=300)


class AudioRequest(BaseModel):
    recommendation: str = Field(min_length=1)
    summary: str = Field(min_length=1)


class ConversationSummary(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int


class ConversationResponse(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str
    messages: list[dict]
