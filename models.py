# models.py
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field

class SurveySubmission(BaseModel):
    # Incoming payload from the frontend
    name: str = Field(max_length=100)
    email: EmailStr
    age: int
    consent: bool
    rating: int
    comments: Optional[str] = None
    source: Optional[str] = "other"

    # NEW (optional): may be provided by frontend or filled from request headers
    user_agent: Optional[str] = None

    # NEW (optional): if not provided, server will compute
    submission_id: Optional[str] = None


class StoredSurveyRecord(BaseModel):
    # What we persist to disk (NO raw PII)
    submission_id: str

    name: str
    email_sha256: str
    age_sha256: str

    consent: bool
    rating: int
    comments: Optional[str] = None
    source: str

    user_agent: Optional[str] = None
    received_at: datetime
    ip: str