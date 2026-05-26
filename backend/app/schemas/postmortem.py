"""
Pydantic schemas for PostMortem.
"""
from datetime import datetime
from pydantic import BaseModel, Field


class PostMortemCreate(BaseModel):
    title: str = Field(..., max_length=500)
    summary: str
    root_cause: str
    impact: str
    timeline: str
    action_items: str
    lessons_learned: str | None = None


class PostMortemResponse(BaseModel):
    id: int
    incident_id: int
    title: str
    summary: str
    root_cause: str
    impact: str
    timeline: str
    action_items: str
    lessons_learned: str | None
    generated_by_ai: bool
    ai_model: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
