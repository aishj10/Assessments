# backend/app/routers/leads.py
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select, Session
from app.database import get_session
from app.models import Lead, ActivityLog, PipelineStage
from app.schemas import LeadCreate, LeadRead, LeadUpdate, QualificationRequest, StageProgressionRequest
from app.grok_client import call_grok, GrokError
from app.prompts import qualification_prompt, outreach_prompt
from app.pipeline_service import PipelineService
from app.search_service import SearchService
import json
import logging
from typing import Optional

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/leads", tags=["leads"])

@router.post("/", response_model=LeadRead)
def create_lead(payload: LeadCreate, session: Session = Depends(get_session)):
    """Create a new lead with proper error handling"""
    try:
        # Validate required fields
        if not payload.company or not payload.company.strip():
            raise HTTPException(status_code=400, detail="Company name is required")
        
        # Check for duplicate company names
        existing_lead = session.exec(
            select(Lead).where(Lead.company.ilike(payload.company.strip()))
        ).first()
        
        if existing_lead:
            raise HTTPException(
                status_code=409, 
                detail=f"Lead with company '{payload.company}' already exists"
            )
        
        # Create lead with proper metadata handling
        try:
            metadata_json = json.dumps(payload.company_metadata or {})
        except (TypeError, ValueError) as e:
            logger.error(f"Invalid company metadata: {e}")
            raise HTTPException(status_code=400, detail="Invalid company metadata format")
        
        lead = Lead(
            company=payload.company.strip(),
            name=payload.name.strip() if payload.name else None,
            title=payload.title.strip() if payload.title else None,
            email=payload.email.strip() if payload.email else None,
            phone=payload.phone.strip() if payload.phone else None,
            website=payload.website.strip() if payload.website else None,
            company_metadata=metadata_json,
        )
        
        session.add(lead)
        session.commit()
        session.refresh(lead)
        
        # Log the lead creation activity
        try:
            PipelineService.log_activity(
                session, lead.id, "system", "lead_created", 
                f"Lead created for {lead.company} - {lead.name or 'No contact name'}"
            )
        except Exception as e:
            logger.error(f"Failed to log lead creation activity: {e}")
            # Don't fail the request if logging fails
        
        logger.info(f"Successfully created lead {lead.id} for company {lead.company}")
        return lead
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error creating lead: {e}")
        session.rollback()
        raise HTTPException(status_code=500, detail="Internal server error creating lead")

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
def qualify(req: QualificationRequest, session: Session = Depends(get_session)):
    """Run AI qualification on a lead with comprehensive error handling"""
    try:
        # Validate request
        if not req.lead_id or req.lead_id <= 0:
            raise HTTPException(status_code=400, detail="Valid lead_id is required")
        
        # Get lead with error handling
        lead = session.get(Lead, req.lead_id)
        if not lead:
            raise HTTPException(status_code=404, detail=f"Lead with ID {req.lead_id} not found")

        # Validate scoring weights if provided
        if req.scoring_weights:
            for key, value in req.scoring_weights.items():
                if not isinstance(value, (int, float)) or value < 1 or value > 10:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Scoring weight for '{key}' must be a number between 1 and 10"
                    )

        # Prepare lead data
        try:
            lead_data = {
                "company": lead.company,
                "name": lead.name,
                "title": lead.title,
                "email": lead.email,
                "website": lead.website,
                "company_metadata": lead.company_metadata
            }
        except Exception as e:
            logger.error(f"Error preparing lead data: {e}")
            raise HTTPException(status_code=500, detail="Error preparing lead data")

        # Generate prompt and call Grok
        try:
            prompt = qualification_prompt(lead_data, req.scoring_weights)
            logger.info(f"Calling Grok for lead {lead.id} qualification")
            resp = call_grok(prompt)
        except GrokError as e:
            logger.error(f"Grok API error for lead {lead.id}: {e}")
            raise HTTPException(status_code=502, detail=f"AI qualification service error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error calling Grok for lead {lead.id}: {e}")
            raise HTTPException(status_code=500, detail="Internal error calling AI service")

        # Parse Grok response with robust error handling
        text = resp["text"].strip()
        parsed = None
        
        # Try direct JSON parsing first
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            # Try to extract JSON from text
            import re
            json_match = re.search(r"(\{.*\})", text, re.S)
            if json_match:
                try:
                    parsed = json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    pass
        
        if parsed is None:
            logger.error(f"Could not parse Grok response for lead {lead.id}: {text[:200]}")
            raise HTTPException(
                status_code=502, 
                detail=f"AI returned invalid response format. Response preview: {text[:200]}"
            )

        # Validate parsed response
        if "score" not in parsed:
            logger.error(f"Grok response missing score for lead {lead.id}: {parsed}")
            raise HTTPException(status_code=502, detail="AI response missing required score field")
        
        try:
            score = float(parsed.get("score", 0))
            if not (0 <= score <= 100):
                logger.warning(f"Grok returned unusual score {score} for lead {lead.id}")
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid score format for lead {lead.id}: {parsed.get('score')}")
            raise HTTPException(status_code=502, detail="AI returned invalid score format")

        # Update lead score
        try:
            lead.score = score
            session.add(lead)
            session.commit()
        except Exception as e:
            logger.error(f"Error updating lead score for lead {lead.id}: {e}")
            session.rollback()
            raise HTTPException(status_code=500, detail="Error updating lead score")
        
        # Log the qualification activity
        try:
            justification = parsed.get("justification", "No justification provided")
            clean_detail = f"AI qualification completed with score {score}/100. Analysis: {justification[:100]}{'...' if len(justification) > 100 else ''}"
            PipelineService.log_activity(
                session, lead.id, "system", "qualification_completed",
                clean_detail,
                {"score": score, "justification": justification, "breakdown": parsed.get("breakdown", {})}
            )
        except Exception as e:
            logger.error(f"Failed to log qualification activity for lead {lead.id}: {e}")
            # Don't fail the request if logging fails
        
        # Auto-progress based on score
        try:
            updated_lead = PipelineService.auto_progress_after_qualification(session, lead.id, score)
        except Exception as e:
            logger.error(f"Error auto-progressing lead {lead.id}: {e}")
            # Return the lead even if auto-progression fails
            updated_lead = lead
        
        logger.info(f"Successfully qualified lead {lead.id} with score {score}")
        return {
            "lead_id": updated_lead.id, 
            "score": updated_lead.score, 
            "stage": updated_lead.stage, 
            "grok_output": parsed
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in qualification for lead {req.lead_id}: {e}")
        session.rollback()
        raise HTTPException(status_code=500, detail="Internal server error during qualification")

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
