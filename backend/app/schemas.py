# backend/app/schemas.py
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.models import PipelineStage

class LeadCreate(BaseModel):
    company: str
    name: Optional[str] = None
    title: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    company_metadata: Optional[dict] = {}

class LeadUpdate(BaseModel):
    company: Optional[str] = None
    name: Optional[str] = None
    title: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    company_metadata: Optional[dict] = None
    stage: Optional[PipelineStage] = None

class LeadRead(BaseModel):
    id: int
    company: str
    name: Optional[str]
    title: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    website: Optional[str]
    company_metadata: Optional[str]  # JSON string
    score: Optional[float]
    stage: PipelineStage
    created_at: datetime

class QualificationRequest(BaseModel):
    lead_id: int
    scoring_weights: Optional[dict] = {}  # user-driven weights, e.g., {"company_size":2,"industry_fit":3}
