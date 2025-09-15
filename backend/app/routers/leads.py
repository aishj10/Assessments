# backend/app/routers/leads.py
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from app.database import get_session
from app.models import Lead, ActivityLog, PipelineStage
from app.schemas import LeadCreate, LeadRead, LeadUpdate, QualificationRequest, StageProgressionRequest
from app.grok_client import call_grok, GrokError
from app.prompts import qualification_prompt, outreach_prompt
from app.pipeline_service import PipelineService
from app.search_service import SearchService
import json

router = APIRouter(prefix="/leads", tags=["leads"])

@router.post("/", response_model=LeadRead)
def create_lead(payload: LeadCreate, session=Depends(get_session)):
    lead = Lead(
        company=payload.company,
        name=payload.name,
        title=payload.title,
        email=payload.email,
        phone=payload.phone,
        website=payload.website,
        company_metadata=json.dumps(payload.company_metadata or {}),
    )
    session.add(lead)
    session.commit()
    session.refresh(lead)
    
    # Log the lead creation activity
    PipelineService.log_activity(
        session, lead.id, "system", "lead_created", 
        f"Lead created for {lead.company} - {lead.name or 'No contact name'}"
    )
    
    return lead

@router.get("/", response_model=list[LeadRead])
def list_leads(session=Depends(get_session)):
    leads = session.exec(select(Lead).order_by(Lead.created_at.desc())).all()
    return leads

@router.get("/{lead_id}", response_model=LeadRead)
def get_lead(lead_id: int, session=Depends(get_session)):
    lead = session.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="lead not found")
    return lead

@router.put("/{lead_id}", response_model=LeadRead)
def update_lead(lead_id: int, payload: LeadUpdate, session=Depends(get_session)):
    lead = session.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="lead not found")
    
    # Update only provided fields
    update_data = payload.dict(exclude_unset=True)
    for field, value in update_data.items():
        if field == "company_metadata" and value is not None:
            setattr(lead, field, json.dumps(value))
        else:
            setattr(lead, field, value)
    
    session.add(lead)
    session.add(ActivityLog(lead_id=lead.id, actor="system", action="updated lead", detail=f"Updated fields: {list(update_data.keys())}"))
    session.commit()
    session.refresh(lead)
    return lead

@router.delete("/{lead_id}")
def delete_lead(lead_id: int, session=Depends(get_session)):
    lead = session.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="lead not found")
    
    # Delete associated activity logs first
    activity_logs = session.exec(select(ActivityLog).where(ActivityLog.lead_id == lead_id)).all()
    for log in activity_logs:
        session.delete(log)
    
    session.delete(lead)
    session.commit()
    return {"message": f"Lead {lead_id} deleted successfully"}

@router.post("/qualify", summary="Run Grok qualification")
def qualify(req: QualificationRequest, session=Depends(get_session)):
    lead = session.get(Lead, req.lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="lead not found")

    lead_data = {
        "company": lead.company,
        "name": lead.name,
        "title": lead.title,
        "email": lead.email,
        "website": lead.website,
        "company_metadata": lead.company_metadata
    }

    prompt = qualification_prompt(lead_data, req.scoring_weights)
    try:
        resp = call_grok(prompt)
    except GrokError as e:
        raise HTTPException(status_code=502, detail=str(e))

    text = resp["text"].strip()
    # Validate: expect JSON; robust parsing
    parsed = None
    for attempt in (text,):
        try:
            parsed = json.loads(attempt)
            break
        except Exception:
            # try to extract JSON substring
            import re
            m = re.search(r"(\{.*\})", text, re.S)
            if m:
                try:
                    parsed = json.loads(m.group(1))
                    break
                except Exception:
                    parsed = None
    if parsed is None:
        raise HTTPException(status_code=502, detail=f"Could not parse Grok output: {text[:200]}")

    score = float(parsed.get("score", 0))
    lead.score = float(score)
    
    # Log the qualification activity with clean details
    justification = parsed.get("justification", "No justification provided")
    clean_detail = f"AI qualification completed with score {score}/100. Analysis: {justification[:100]}{'...' if len(justification) > 100 else ''}"
    PipelineService.log_activity(
        session, lead.id, "system", "qualification_completed",
        clean_detail,
        {"score": score, "justification": justification, "breakdown": parsed.get("breakdown", {})}
    )
    
    # Auto-progress based on score using pipeline service
    updated_lead = PipelineService.auto_progress_after_qualification(session, lead.id, score)
    
    return {"lead_id": updated_lead.id, "score": updated_lead.score, "stage": updated_lead.stage, "grok_output": parsed}

@router.post("/outreach/{lead_id}", summary="Generate outreach message")
def generate_outreach(lead_id: int, tone: str = "friendly", goal: str = "book a meeting", session=Depends(get_session)):
    lead = session.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="lead not found")
    lead_data = {
        "company": lead.company, "name": lead.name, "title": lead.title, "email": lead.email, "website": lead.website, "company_metadata": lead.company_metadata
    }
    prompt = outreach_prompt(lead_data, tone=tone, goal=goal)
    try:
        resp = call_grok(prompt)
    except GrokError as e:
        raise HTTPException(status_code=502, detail=str(e))

    text = resp["text"]
    # parse JSON similarly to qualification
    import json, re
    parsed = None
    try:
        parsed = json.loads(text)
    except Exception:
        m = re.search(r"(\{.*\})", text, re.S)
        if m:
            try:
                parsed = json.loads(m.group(1))
            except Exception:
                parsed = {"subject": "Hey", "body": text[:500], "tags": []}
        else:
            parsed = {"subject": "Hey", "body": text[:500], "tags": []}

    # Log the outreach generation activity with clean details
    subject = parsed.get("subject", "No subject")
    body_preview = parsed.get("body", "No message content")[:100]
    tags = parsed.get("tags", [])
    tags_text = ", ".join(tags) if tags else "No tags"
    clean_detail = f"AI-generated outreach message created. Subject: '{subject}'. Tags: {tags_text}"
    
    PipelineService.log_activity(
        session, lead.id, "system", "outreach_generated",
        clean_detail,
        {"subject": subject, "body": parsed.get("body", ""), "tags": tags}
    )
    
    return {"lead_id": lead.id, "outreach": parsed}

# Pipeline Management Endpoints

@router.get("/pipeline/stages", summary="Get all pipeline stages")
def get_pipeline_stages():
    """Get all available pipeline stages with descriptions"""
    return PipelineService.get_pipeline_stages()

@router.get("/pipeline/stats", summary="Get pipeline statistics")
def get_pipeline_stats(session=Depends(get_session)):
    """Get pipeline statistics showing lead counts by stage"""
    return PipelineService.get_pipeline_stats(session)

@router.get("/pipeline/analytics", summary="Get comprehensive pipeline analytics")
def get_pipeline_analytics(session=Depends(get_session)):
    """Get comprehensive pipeline analytics including conversion rates and recent activities"""
    return PipelineService.get_pipeline_analytics(session)

@router.post("/{lead_id}/progress", summary="Manually progress lead to next stage")
def progress_lead_stage(
    lead_id: int, 
    request: StageProgressionRequest,
    session=Depends(get_session)
):
    """Manually progress a lead to a new stage"""
    try:
        updated_lead = PipelineService.progress_lead_stage(
            session, lead_id, request.new_stage, "user", request.reason
        )
        return {"lead_id": updated_lead.id, "stage": updated_lead.stage, "message": "Lead progressed successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid request: {str(e)}")

@router.get("/{lead_id}/activities", summary="Get activity history for a lead")
def get_lead_activities(lead_id: int, session=Depends(get_session)):
    """Get all activities for a specific lead"""
    activities = PipelineService.get_lead_activities(session, lead_id)
    return [
        {
            "id": activity.id,
            "actor": activity.actor,
            "action": activity.action,
            "detail": activity.detail,
            "created_at": activity.created_at.isoformat()
        }
        for activity in activities
    ]

# Search Endpoints

@router.get("/search/all", summary="Search leads and activities")
def search_all(
    q: str,
    search_type: str = "all",
    limit: int = 50,
    session=Depends(get_session)
):
    """Search through leads, activities, and company metadata"""
    if not q.strip():
        return {"leads": [], "activities": [], "metadata": []}
    
    leads = SearchService.search_leads(session, q, search_type, limit)
    activities = SearchService.search_activities(session, q, None, limit)
    metadata = SearchService.search_company_metadata(session, q, None, limit)
    
    return {
        "query": q,
        "search_type": search_type,
        "leads": leads,
        "activities": activities,
        "metadata": metadata,
        "total_results": len(leads) + len(activities) + len(metadata)
    }

@router.get("/search/leads-only", summary="Search leads only")
def search_leads_only(
    q: str,
    search_type: str = "all",
    limit: int = 50,
    session=Depends(get_session)
):
    """Search through leads by company, contact, or metadata"""
    if not q.strip():
        return {"leads": []}
    
    leads = SearchService.search_leads(session, q, search_type, limit)
    return {
        "query": q,
        "search_type": search_type,
        "leads": leads,
        "total_results": len(leads)
    }

@router.get("/search/activities-only", summary="Search activities only")
def search_activities_only(
    q: str,
    lead_id: int = None,
    limit: int = 50,
    session=Depends(get_session)
):
    """Search through activity logs and conversations"""
    if not q.strip():
        return {"activities": []}
    
    activities = SearchService.search_activities(session, q, lead_id, limit)
    return {
        "query": q,
        "lead_id": lead_id,
        "activities": activities,
        "total_results": len(activities)
    }

@router.get("/search/metadata-only", summary="Search company metadata")
def search_metadata_only(
    q: str,
    field: str = None,
    limit: int = 50,
    session=Depends(get_session)
):
    """Search through company metadata fields"""
    if not q.strip():
        return {"metadata": []}
    
    metadata = SearchService.search_company_metadata(session, q, field, limit)
    return {
        "query": q,
        "field": field,
        "metadata": metadata,
        "total_results": len(metadata)
    }

@router.get("/search/suggestions", summary="Get search suggestions")
def get_search_suggestions(
    q: str,
    session=Depends(get_session)
):
    """Get search suggestions based on partial query"""
    if not q.strip():
        return {"suggestions": {}}
    
    suggestions = SearchService.get_search_suggestions(session, q)
    return {
        "query": q,
        "suggestions": suggestions
    }

# Cleanup Endpoints

@router.delete("/activities/cleanup", summary="Clean up old activities")
def cleanup_old_activities(
    days_to_keep: int = 7,
    keep_recent_per_lead: int = 5,
    dry_run: bool = True,
    session=Depends(get_session)
):
    """Clean up old activities from the database"""
    from datetime import datetime, timedelta
    
    cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
    
    # Get old activities by date
    old_activities_by_date = session.exec(
        select(ActivityLog).where(ActivityLog.created_at < cutoff_date)
    ).all()
    
    # Get old activities by count per lead
    leads = session.exec(select(Lead)).all()
    old_activities_by_count = []
    
    for lead in leads:
        activities = session.exec(
            select(ActivityLog)
            .where(ActivityLog.lead_id == lead.id)
            .order_by(ActivityLog.created_at.desc())
        ).all()
        
        if len(activities) > keep_recent_per_lead:
            old_activities_by_count.extend(activities[keep_recent_per_lead:])
    
    # Combine and deduplicate by ID
    all_old_activity_ids = set()
    all_old_activities = []
    
    for activity in old_activities_by_date + old_activities_by_count:
        if activity.id not in all_old_activity_ids:
            all_old_activity_ids.add(activity.id)
            all_old_activities.append(activity)
    
    if dry_run:
        return {
            "message": "Dry run - no activities deleted",
            "old_activities_by_date": len(old_activities_by_date),
            "old_activities_by_count": len(old_activities_by_count),
            "total_to_delete": len(all_old_activities),
            "activities_preview": [
                {
                    "id": activity.id,
                    "lead_id": activity.lead_id,
                    "action": activity.action,
                    "created_at": activity.created_at.isoformat()
                }
                for activity in all_old_activities[:10]
            ]
        }
    else:
        # Actually delete the activities
        deleted_count = 0
        for activity in all_old_activities:
            session.delete(activity)
            deleted_count += 1
        
        session.commit()
        
        return {
            "message": f"Successfully deleted {deleted_count} old activities",
            "deleted_count": deleted_count
        }

@router.get("/activities/summary", summary="Get activity summary")
def get_activity_summary(session=Depends(get_session)):
    """Get a summary of current activities in the database"""
    # Get total activity count
    total_activities = session.exec(select(ActivityLog)).all()
    
    # Get activities by lead
    leads = session.exec(select(Lead)).all()
    activities_by_lead = []
    
    for lead in leads:
        activities = session.exec(
            select(ActivityLog).where(ActivityLog.lead_id == lead.id)
        ).all()
        activities_by_lead.append({
            "lead_id": lead.id,
            "company": lead.company,
            "activity_count": len(activities)
        })
    
    # Get activities by type
    activity_types = {}
    for activity in total_activities:
        activity_types[activity.action] = activity_types.get(activity.action, 0) + 1
    
    return {
        "total_activities": len(total_activities),
        "activities_by_lead": activities_by_lead,
        "activities_by_type": activity_types
    }

@router.delete("/activities/clear-all", summary="Remove all activities from all leads")
def clear_all_activities(
    dry_run: bool = True,
    session=Depends(get_session)
):
    """Remove all activities from all leads"""
    # Get all activities
    all_activities = session.exec(select(ActivityLog)).all()
    
    if dry_run:
        return {
            "message": "Dry run - no activities deleted",
            "total_activities": len(all_activities),
            "activities_preview": [
                {
                    "id": activity.id,
                    "lead_id": activity.lead_id,
                    "action": activity.action,
                    "created_at": activity.created_at.isoformat()
                }
                for activity in all_activities[:10]
            ]
        }
    else:
        # Actually delete all activities
        deleted_count = 0
        for activity in all_activities:
            session.delete(activity)
            deleted_count += 1
        
        session.commit()
        
        return {
            "message": f"Successfully deleted all {deleted_count} activities from all leads",
            "deleted_count": deleted_count
        }
