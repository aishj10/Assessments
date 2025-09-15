# backend/app/routers/leads.py
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from app.database import get_session
from app.models import Lead, ActivityLog, PipelineStage
from app.schemas import LeadCreate, LeadRead, LeadUpdate, QualificationRequest
from app.grok_client import call_grok, GrokError
from app.prompts import qualification_prompt, outreach_prompt
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
    session.add(ActivityLog(lead_id=lead.id, actor="system", action="created lead", detail="seed"))
    session.commit()
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
        "metadata": lead.company_metadata
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
    # auto-progress stage if score > threshold
    if score >= 70:
        lead.stage = PipelineStage.QUALIFIED
        action = f"auto-advanced to {lead.stage}"
    else:
        action = "remains in pipeline"

    session.add(ActivityLog(lead_id=lead.id, actor="system", action="qualification", detail=json.dumps(parsed)))
    session.add(lead)
    session.commit()
    session.refresh(lead)
    return {"lead_id": lead.id, "score": lead.score, "stage": lead.stage, "grok_output": parsed}

@router.post("/outreach/{lead_id}", summary="Generate outreach message")
def generate_outreach(lead_id: int, tone: str = "friendly", goal: str = "book a meeting", session=Depends(get_session)):
    lead = session.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="lead not found")
    lead_data = {
        "company": lead.company, "name": lead.name, "title": lead.title, "email": lead.email, "website": lead.website, "metadata": lead.company_metadata
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

    # log activity
    session.add(ActivityLog(lead_id=lead.id, actor="system", action="generate_outreach", detail=json.dumps(parsed)))
    session.commit()
    return {"lead_id": lead.id, "outreach": parsed}
