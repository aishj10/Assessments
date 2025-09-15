#!/usr/bin/env python3
"""
Script to clean up duplicate leads in the database.
This script removes duplicate leads based on company name and email combination.
"""

import requests
import json
from collections import defaultdict

BASE_URL = "http://localhost:8000"

def get_all_leads():
    """Get all leads from the API"""
    response = requests.get(f"{BASE_URL}/leads")
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching leads: {response.text}")
        return []

def delete_lead(lead_id):
    """Delete a lead by ID"""
    response = requests.delete(f"{BASE_URL}/leads/{lead_id}")
    if response.status_code == 200:
        return True
    else:
        print(f"Error deleting lead {lead_id}: {response.text}")
        return False

def cleanup_duplicates():
    """Remove duplicate leads, keeping the most recent one"""
    print("🔍 Fetching all leads...")
    leads = get_all_leads()
    
    if not leads:
        print("No leads found.")
        return
    
    print(f"Found {len(leads)} leads total")
    
    # Group leads by company name and email combination
    grouped_leads = defaultdict(list)
    
    for lead in leads:
        # Use company name and email as the key for grouping
        key = (lead['company'], lead.get('email', ''))
        grouped_leads[key].append(lead)
    
    duplicates_found = 0
    duplicates_removed = 0
    
    print("\n🔍 Checking for duplicates...")
    
    for key, lead_group in grouped_leads.items():
        if len(lead_group) > 1:
            company, email = key
            duplicates_found += len(lead_group) - 1  # All but one are duplicates
            
            print(f"\n📋 Found {len(lead_group)} duplicates for: {company} ({email})")
            
            # Sort by created_at (most recent first)
            lead_group.sort(key=lambda x: x['created_at'], reverse=True)
            
            # Keep the most recent one, delete the rest
            keep_lead = lead_group[0]
            delete_leads = lead_group[1:]
            
            print(f"   ✅ Keeping lead ID {keep_lead['id']} (created: {keep_lead['created_at']})")
            
            for lead in delete_leads:
                print(f"   🗑️  Deleting lead ID {lead['id']} (created: {lead['created_at']})")
                if delete_lead(lead['id']):
                    duplicates_removed += 1
                else:
                    print(f"   ❌ Failed to delete lead ID {lead['id']}")
    
    print(f"\n📊 Summary:")
    print(f"   • Total leads found: {len(leads)}")
    print(f"   • Duplicate groups found: {len([g for g in grouped_leads.values() if len(g) > 1])}")
    print(f"   • Duplicates found: {duplicates_found}")
    print(f"   • Duplicates removed: {duplicates_removed}")
    
    if duplicates_removed > 0:
        print(f"\n✅ Successfully cleaned up {duplicates_removed} duplicate leads!")
    else:
        print(f"\n✅ No duplicates found - database is clean!")

if __name__ == "__main__":
    cleanup_duplicates()
