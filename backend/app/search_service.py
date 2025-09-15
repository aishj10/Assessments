# backend/app/search_service.py
from typing import List, Dict, Optional, Any
from sqlmodel import Session, select, or_, and_
from app.models import Lead, ActivityLog
import json
import re
from datetime import datetime

class SearchService:
    """Service for searching leads, activities, and company metadata"""
    
    @staticmethod
    def search_leads(
        session: Session, 
        query: str, 
        search_type: str = "all",
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Search leads by company name, contact info, or metadata
        
        Args:
            session: Database session
            query: Search query string
            search_type: Type of search ("all", "company", "contact", "metadata")
            limit: Maximum number of results
        """
        query_lower = query.lower()
        results = []
        
        # Build search conditions based on type
        conditions = []
        
        if search_type in ["all", "company"]:
            conditions.append(Lead.company.ilike(f"%{query}%"))
        
        if search_type in ["all", "contact"]:
            conditions.append(Lead.name.ilike(f"%{query}%"))
            conditions.append(Lead.title.ilike(f"%{query}%"))
            conditions.append(Lead.email.ilike(f"%{query}%"))
        
        if search_type in ["all", "metadata"]:
            conditions.append(Lead.company_metadata.ilike(f"%{query}%"))
        
        # Execute search
        if conditions:
            leads = session.exec(
                select(Lead)
                .where(or_(*conditions))
                .limit(limit)
            ).all()
            
            for lead in leads:
                # Calculate relevance score
                relevance_score = SearchService._calculate_relevance_score(lead, query_lower)
                
                # Parse company metadata for better display
                metadata = {}
                if lead.company_metadata:
                    try:
                        metadata = json.loads(lead.company_metadata)
                    except:
                        metadata = {}
                
                results.append({
                    "id": lead.id,
                    "company": lead.company,
                    "name": lead.name,
                    "title": lead.title,
                    "email": lead.email,
                    "phone": lead.phone,
                    "website": lead.website,
                    "score": lead.score,
                    "stage": lead.stage,
                    "created_at": lead.created_at.isoformat(),
                    "company_metadata": metadata,
                    "relevance_score": relevance_score,
                    "match_type": SearchService._get_match_type(lead, query_lower)
                })
        
        # Sort by relevance score
        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        return results
    
    @staticmethod
    def search_activities(
        session: Session, 
        query: str, 
        lead_id: Optional[int] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Search through activity logs and conversations
        
        Args:
            session: Database session
            query: Search query string
            lead_id: Optional lead ID to limit search to specific lead
            limit: Maximum number of results
        """
        query_lower = query.lower()
        results = []
        
        # Build search conditions
        conditions = [
            or_(
                ActivityLog.action.ilike(f"%{query}%"),
                ActivityLog.detail.ilike(f"%{query}%"),
                ActivityLog.actor.ilike(f"%{query}%")
            )
        ]
        
        if lead_id:
            conditions.append(ActivityLog.lead_id == lead_id)
        
        # Execute search
        activities = session.exec(
            select(ActivityLog)
            .where(and_(*conditions))
            .order_by(ActivityLog.created_at.desc())
            .limit(limit)
        ).all()
        
        for activity in activities:
            # Get lead info for context
            lead = session.get(Lead, activity.lead_id)
            
            # Calculate relevance score
            relevance_score = SearchService._calculate_activity_relevance(activity, query_lower)
            
            # Parse activity detail if it's JSON
            detail_parsed = activity.detail
            try:
                if activity.detail and activity.detail.startswith('{'):
                    detail_parsed = json.loads(activity.detail)
            except:
                pass
            
            results.append({
                "id": activity.id,
                "lead_id": activity.lead_id,
                "lead_company": lead.company if lead else "Unknown",
                "actor": activity.actor,
                "action": activity.action,
                "detail": detail_parsed,
                "created_at": activity.created_at.isoformat(),
                "relevance_score": relevance_score,
                "match_type": SearchService._get_activity_match_type(activity, query_lower)
            })
        
        # Sort by relevance score
        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        return results
    
    @staticmethod
    def search_company_metadata(
        session: Session, 
        query: str, 
        metadata_field: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Search specifically through company metadata fields
        
        Args:
            session: Database session
            query: Search query string
            metadata_field: Specific metadata field to search (e.g., "industry", "tech_stack")
            limit: Maximum number of results
        """
        query_lower = query.lower()
        results = []
        
        # Get all leads with metadata
        leads = session.exec(select(Lead).where(Lead.company_metadata.isnot(None))).all()
        
        for lead in leads:
            if not lead.company_metadata:
                continue
                
            try:
                metadata = json.loads(lead.company_metadata)
            except:
                continue
            
            # Search in specific field or all fields
            if metadata_field:
                if metadata_field in metadata and query_lower in str(metadata[metadata_field]).lower():
                    results.append({
                        "lead_id": lead.id,
                        "company": lead.company,
                        "field": metadata_field,
                        "value": metadata[metadata_field],
                        "full_metadata": metadata,
                        "relevance_score": 1.0
                    })
            else:
                # Search in all metadata fields
                for field, value in metadata.items():
                    if query_lower in str(value).lower():
                        results.append({
                            "lead_id": lead.id,
                            "company": lead.company,
                            "field": field,
                            "value": value,
                            "full_metadata": metadata,
                            "relevance_score": 1.0
                        })
        
        # Sort by relevance score
        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        return results[:limit]
    
    @staticmethod
    def get_search_suggestions(session: Session, query: str) -> Dict[str, List[str]]:
        """
        Get search suggestions based on partial query
        
        Args:
            session: Database session
            query: Partial search query
        """
        query_lower = query.lower()
        suggestions = {
            "companies": [],
            "contacts": [],
            "industries": [],
            "tech_stacks": []
        }
        
        # Get company suggestions
        companies = session.exec(
            select(Lead.company)
            .where(Lead.company.ilike(f"%{query}%"))
            .limit(10)
        ).all()
        suggestions["companies"] = list(set(companies))
        
        # Get contact suggestions
        contacts = session.exec(
            select(Lead.name)
            .where(Lead.name.ilike(f"%{query}%"))
            .limit(10)
        ).all()
        suggestions["contacts"] = [c for c in contacts if c]
        
        # Get industry suggestions from metadata
        leads_with_metadata = session.exec(
            select(Lead.company_metadata)
            .where(Lead.company_metadata.isnot(None))
        ).all()
        
        industries = set()
        tech_stacks = set()
        
        for metadata_str in leads_with_metadata:
            try:
                metadata = json.loads(metadata_str)
                if "industry" in metadata and query_lower in str(metadata["industry"]).lower():
                    industries.add(metadata["industry"])
                if "tech_stack" in metadata:
                    tech_stack = metadata["tech_stack"]
                    if isinstance(tech_stack, list):
                        for tech in tech_stack:
                            if query_lower in str(tech).lower():
                                tech_stacks.add(tech)
                    elif query_lower in str(tech_stack).lower():
                        tech_stacks.add(tech_stack)
            except:
                continue
        
        suggestions["industries"] = list(industries)
        suggestions["tech_stacks"] = list(tech_stacks)
        
        return suggestions
    
    @staticmethod
    def _calculate_relevance_score(lead: Lead, query: str) -> float:
        """Calculate relevance score for a lead based on search query"""
        score = 0.0
        
        # Company name match (highest weight)
        if query in lead.company.lower():
            score += 10.0
            if lead.company.lower().startswith(query):
                score += 5.0
        
        # Contact name match
        if lead.name and query in lead.name.lower():
            score += 8.0
        
        # Title match
        if lead.title and query in lead.title.lower():
            score += 6.0
        
        # Email match
        if lead.email and query in lead.email.lower():
            score += 7.0
        
        # Metadata match
        if lead.company_metadata and query in lead.company_metadata.lower():
            score += 4.0
        
        return score
    
    @staticmethod
    def _calculate_activity_relevance(activity: ActivityLog, query: str) -> float:
        """Calculate relevance score for an activity based on search query"""
        score = 0.0
        
        # Action match
        if query in activity.action.lower():
            score += 5.0
        
        # Detail match (highest weight)
        if query in activity.detail.lower():
            score += 10.0
        
        # Actor match
        if query in activity.actor.lower():
            score += 3.0
        
        return score
    
    @staticmethod
    def _get_match_type(lead: Lead, query: str) -> str:
        """Determine what type of match was found for a lead"""
        if query in lead.company.lower():
            return "company"
        elif lead.name and query in lead.name.lower():
            return "contact"
        elif lead.title and query in lead.title.lower():
            return "title"
        elif lead.email and query in lead.email.lower():
            return "email"
        elif lead.company_metadata and query in lead.company_metadata.lower():
            return "metadata"
        else:
            return "unknown"
    
    @staticmethod
    def _get_activity_match_type(activity: ActivityLog, query: str) -> str:
        """Determine what type of match was found for an activity"""
        if query in activity.action.lower():
            return "action"
        elif query in activity.detail.lower():
            return "detail"
        elif query in activity.actor.lower():
            return "actor"
        else:
            return "unknown"
