#!/usr/bin/env python3
"""
Script to seed the database with sample leads for demo purposes.
Run this after starting the backend to populate with test data.
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def get_existing_leads():
    """Get all existing leads to check for duplicates"""
    response = requests.get(f"{BASE_URL}/leads")
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching existing leads: {response.text}")
        return []

def lead_exists(lead_data, existing_leads):
    """Check if a lead already exists based on company and email"""
    for existing_lead in existing_leads:
        if (existing_lead['company'] == lead_data['company'] and 
            existing_lead.get('email') == lead_data.get('email')):
            return True
    return False

def create_lead(lead_data, existing_leads):
    """Create a lead via the API if it doesn't already exist"""
    if lead_exists(lead_data, existing_leads):
        print(f"⚠️  Lead already exists: {lead_data['company']} ({lead_data.get('email', 'no email')})")
        return None
    
    response = requests.post(f"{BASE_URL}/leads", json=lead_data)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error creating lead {lead_data['company']}: {response.text}")
        return None

def main():
    """Seed the database with sample leads"""
    
    sample_leads = [
        {
            "company": "Acme AI",
            "name": "Jordan Smith",
            "title": "Head of Product",
            "email": "jordan@acme.ai",
            "website": "https://acme.ai",
            "company_metadata": {
                "company_size": 15,
                "industry": "SaaS",
                "recent_funding": "seed",
                "tech_stack": ["Python", "React", "AWS"]
            }
        },
        {
            "company": "MegaCorp Inc",
            "name": "Taylor Lee",
            "title": "VP Sales",
            "email": "taylor.lee@megacorp.com",
            "website": "https://megacorp.com",
            "company_metadata": {
                "company_size": 5000,
                "industry": "Finance",
                "recent_funding": None,
                "annual_revenue": "500M"
            }
        },
        {
            "company": "TechFlow Solutions",
            "name": "Alex Chen",
            "title": "CTO",
            "email": "alex@techflow.com",
            "website": "https://techflow.com",
            "company_metadata": {
                "company_size": 150,
                "industry": "Technology",
                "recent_funding": "Series A",
                "tech_stack": ["Node.js", "MongoDB", "Docker"]
            }
        },
        {
            "company": "StartupXYZ",
            "name": "Maria Rodriguez",
            "title": "Founder & CEO",
            "email": "maria@startupxyz.com",
            "website": "https://startupxyz.com",
            "company_metadata": {
                "company_size": 8,
                "industry": "E-commerce",
                "recent_funding": "pre-seed",
                "founded": "2023"
            }
        },
        {
            "company": "Enterprise Solutions Ltd",
            "name": "David Kim",
            "title": "Director of Operations",
            "email": "david.kim@enterprise-solutions.com",
            "website": "https://enterprise-solutions.com",
            "company_metadata": {
                "company_size": 2000,
                "industry": "Manufacturing",
                "recent_funding": None,
                "annual_revenue": "200M"
            }
        }
    ]
    
    print("🌱 Seeding database with sample leads...")
    
    # Get existing leads to avoid duplicates
    existing_leads = get_existing_leads()
    print(f"📋 Found {len(existing_leads)} existing leads")
    
    created_leads = []
    for lead_data in sample_leads:
        lead = create_lead(lead_data, existing_leads)
        if lead:
            created_leads.append(lead)
            print(f"✅ Created lead: {lead_data['company']} ({lead['id']})")
        time.sleep(0.5)  # Small delay to avoid overwhelming the API
    
    print(f"\n🎉 Successfully created {len(created_leads)} leads!")
    print("\nYou can now:")
    print("1. Visit http://localhost:3000 to see the frontend")
    print("2. Try the AI qualification feature")
    print("3. Generate personalized outreach messages")
    print("4. Run evaluations: curl http://localhost:8000/evals/run")

if __name__ == "__main__":
    main()
