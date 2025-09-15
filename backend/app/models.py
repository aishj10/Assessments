# backend/app/models.py
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
import enum

class PipelineStage(str, enum.Enum):
    NEW = "New"
    QUALIFIED = "Qualified"
    CONTACTED = "Contacted"
    MEETING = "Meeting"
    WON = "Won"
    LOST = "Lost"

class Lead(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    company: str
    name: Optional[str] = None
    title: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    company_metadata: Optional[str] = None  # JSON string w/ company info
    score: Optional[float] = 0.0
    stage: PipelineStage = PipelineStage.NEW
    created_at: datetime = Field(default_factory=datetime.utcnow)
    activities: List["ActivityLog"] = Relationship(back_populates="lead")

class ActivityLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    lead_id: int = Field(foreign_key="lead.id")
    actor: str  # e.g., "system" or user id
    action: str
    detail: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    lead: Optional[Lead] = Relationship(back_populates="activities")
