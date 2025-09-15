# backend/app/pipeline_service.py
from datetime import datetime
from typing import Dict, List, Optional
from sqlmodel import Session, select
from app.models import Lead, ActivityLog, PipelineStage
import json

class PipelineService:
    """Service for managing lead pipeline progression and activity tracking"""
    
    @staticmethod
    def get_pipeline_stages() -> List[Dict[str, str]]:
        """Get all available pipeline stages with descriptions"""
        return [
            {"stage": "New", "description": "Newly added lead, not yet qualified"},
            {"stage": "Qualified", "description": "Lead has been qualified and scored"},
            {"stage": "Contacted", "description": "Initial outreach has been made"},
            {"stage": "Meeting", "description": "Meeting or demo scheduled/completed"},
            {"stage": "Won", "description": "Deal closed successfully"},
            {"stage": "Lost", "description": "Deal lost or disqualified"}
        ]
    
    @staticmethod
    def get_pipeline_stats(session: Session) -> Dict[str, int]:
        """Get pipeline statistics showing lead counts by stage"""
        stats = {}
        for stage in PipelineStage:
            leads = session.exec(select(Lead).where(Lead.stage == stage)).all()
            stats[stage.value] = len(leads)
        return stats
    
    @staticmethod
    def log_activity(
        session: Session, 
        lead_id: int, 
        actor: str, 
        action: str, 
        detail: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> ActivityLog:
        """Log an activity for a lead"""
        # For qualification and outreach activities, store clean detail text with metadata
        if action in ['qualification_completed', 'outreach_generated']:
            if metadata:
                # Store clean text followed by JSON metadata for frontend parsing
                detail_text = f"{detail} {json.dumps(metadata)}"
            else:
                detail_text = detail or "No details provided"
        else:
            # For other activities, append metadata to detail text if provided
            if metadata:
                detail_text = f"{detail} {json.dumps(metadata)}" if detail else json.dumps(metadata)
            else:
                detail_text = detail
            
        activity = ActivityLog(
            lead_id=lead_id,
            actor=actor,
            action=action,
            detail=detail_text
        )
        session.add(activity)
        session.commit()
        session.refresh(activity)
        return activity
    
    @staticmethod
    def progress_lead_stage(
        session: Session, 
        lead_id: int, 
        new_stage: PipelineStage, 
        actor: str = "system",
        reason: Optional[str] = None
    ) -> Lead:
        """Progress a lead to a new stage and log the activity only if stage actually changes"""
        lead = session.get(Lead, lead_id)
        if not lead:
            raise ValueError(f"Lead {lead_id} not found")
        
        old_stage = lead.stage
        
        # Only proceed if the stage is actually changing
        if new_stage == old_stage:
            return lead  # No change needed, return without logging
        
        lead.stage = new_stage
        
        # Log the stage progression only when there's an actual change
        detail = f"Stage changed from {old_stage.value} to {new_stage.value}"
        if reason:
            detail += f" - {reason}"
        
        PipelineService.log_activity(
            session, lead_id, actor, "stage_progression", detail
        )
        
        session.add(lead)
        session.commit()
        session.refresh(lead)
        return lead
    
    @staticmethod
    def auto_progress_after_qualification(
        session: Session, 
        lead_id: int, 
        score: float
    ) -> Lead:
        """Automatically progress lead based on qualification score"""
        lead = session.get(Lead, lead_id)
        if not lead:
            raise ValueError(f"Lead {lead_id} not found")
        
        old_stage = lead.stage
        
        # Auto-progression rules based on score
        if score >= 80:
            new_stage = PipelineStage.QUALIFIED
            reason = f"High qualification score ({score}) - auto-progressed to Qualified"
        elif score >= 60:
            new_stage = PipelineStage.QUALIFIED
            reason = f"Good qualification score ({score}) - auto-progressed to Qualified"
        else:
            new_stage = PipelineStage.NEW
            reason = f"Low qualification score ({score}) - kept at New stage"
        
        # Only log stage progression if the stage actually changes
        if new_stage != old_stage:
            return PipelineService.progress_lead_stage(
                session, lead_id, new_stage, "system", reason
            )
        else:
            # Stage didn't change, just update the lead without logging stage progression
            lead.stage = new_stage
            session.add(lead)
            session.commit()
            session.refresh(lead)
            return lead
    
    @staticmethod
    def get_lead_activities(session: Session, lead_id: int) -> List[ActivityLog]:
        """Get all activities for a lead, ordered by most recent first"""
        activities = session.exec(
            select(ActivityLog)
            .where(ActivityLog.lead_id == lead_id)
            .order_by(ActivityLog.created_at.desc())
        ).all()
        return activities
    
    @staticmethod
    def get_pipeline_analytics(session: Session) -> Dict:
        """Get comprehensive pipeline analytics"""
        all_leads = session.exec(select(Lead)).all()
        total_leads = len(all_leads)
        stats = PipelineService.get_pipeline_stats(session)
        
        # Calculate conversion rates
        won_count = stats.get("Won", 0)
        lost_count = stats.get("Lost", 0)
        total_closed = won_count + lost_count
        
        conversion_rate = (won_count / total_closed * 100) if total_closed > 0 else 0
        
        # Get recent activities (last 10)
        recent_activities = session.exec(
            select(ActivityLog)
            .order_by(ActivityLog.created_at.desc())
            .limit(10)
        ).all()
        
        return {
            "total_leads": total_leads,
            "stage_distribution": stats,
            "conversion_rate": round(conversion_rate, 2),
            "won_count": won_count,
            "lost_count": lost_count,
            "recent_activities": [
                {
                    "id": activity.id,
                    "lead_id": activity.lead_id,
                    "actor": activity.actor,
                    "action": activity.action,
                    "detail": activity.detail,
                    "created_at": activity.created_at.isoformat()
                }
                for activity in recent_activities
            ]
        }
