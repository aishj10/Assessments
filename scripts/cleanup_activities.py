#!/usr/bin/env python3
"""
Script to clean up old activities from the database.
This script removes old activity logs while keeping recent ones.
"""

import os
import sys
from datetime import datetime, timedelta
from sqlmodel import Session, select, delete
from app.database import engine
from app.models import ActivityLog, Lead

def cleanup_old_activities(days_to_keep=7, dry_run=True):
    """
    Clean up old activities from the database.
    
    Args:
        days_to_keep: Number of days of activities to keep (default: 7)
        dry_run: If True, only show what would be deleted without actually deleting
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
    
    with Session(engine) as session:
        # Get all activities older than cutoff date
        old_activities = session.exec(
            select(ActivityLog)
            .where(ActivityLog.created_at < cutoff_date)
        ).all()
        
        print(f"Found {len(old_activities)} activities older than {cutoff_date}")
        
        if dry_run:
            print("\n=== DRY RUN - No activities will be deleted ===")
            for activity in old_activities[:10]:  # Show first 10
                print(f"  - Activity {activity.id}: {activity.action} on {activity.created_at}")
            if len(old_activities) > 10:
                print(f"  ... and {len(old_activities) - 10} more")
        else:
            # Actually delete the old activities
            deleted_count = 0
            for activity in old_activities:
                session.delete(activity)
                deleted_count += 1
            
            session.commit()
            print(f"\n✅ Deleted {deleted_count} old activities")
        
        # Show remaining activity count
        remaining_activities = session.exec(select(ActivityLog)).all()
        print(f"Remaining activities: {len(remaining_activities)}")

def cleanup_activities_by_lead(lead_id=None, keep_recent=5, dry_run=True):
    """
    Clean up old activities for a specific lead, keeping only the most recent ones.
    
    Args:
        lead_id: ID of the lead to clean up (if None, cleans all leads)
        keep_recent: Number of recent activities to keep per lead
        dry_run: If True, only show what would be deleted
    """
    with Session(engine) as session:
        if lead_id:
            # Clean up activities for specific lead
            activities = session.exec(
                select(ActivityLog)
                .where(ActivityLog.lead_id == lead_id)
                .order_by(ActivityLog.created_at.desc())
            ).all()
            
            if len(activities) <= keep_recent:
                print(f"Lead {lead_id} has only {len(activities)} activities, no cleanup needed")
                return
            
            activities_to_delete = activities[keep_recent:]
            print(f"Lead {lead_id}: Found {len(activities_to_delete)} old activities to delete")
            
            if dry_run:
                print(f"  Would keep {keep_recent} most recent activities")
                for activity in activities_to_delete[:5]:
                    print(f"  - Would delete: {activity.action} on {activity.created_at}")
            else:
                for activity in activities_to_delete:
                    session.delete(activity)
                session.commit()
                print(f"✅ Deleted {len(activities_to_delete)} old activities for lead {lead_id}")
        else:
            # Clean up activities for all leads
            leads = session.exec(select(Lead)).all()
            total_deleted = 0
            
            for lead in leads:
                activities = session.exec(
                    select(ActivityLog)
                    .where(ActivityLog.lead_id == lead.id)
                    .order_by(ActivityLog.created_at.desc())
                ).all()
                
                if len(activities) <= keep_recent:
                    continue
                
                activities_to_delete = activities[keep_recent:]
                total_deleted += len(activities_to_delete)
                
                if dry_run:
                    print(f"Lead {lead.id} ({lead.company}): {len(activities_to_delete)} old activities")
                else:
                    for activity in activities_to_delete:
                        session.delete(activity)
            
            if not dry_run:
                session.commit()
                print(f"✅ Deleted {total_deleted} old activities across all leads")
            else:
                print(f"Would delete {total_deleted} old activities across all leads")

def show_activity_summary():
    """Show a summary of current activities in the database."""
    with Session(engine) as session:
        # Get total activity count
        total_activities = session.exec(select(ActivityLog)).all()
        print(f"Total activities in database: {len(total_activities)}")
        
        # Get activities by lead
        leads = session.exec(select(Lead)).all()
        print(f"\nActivities per lead:")
        for lead in leads:
            activities = session.exec(
                select(ActivityLog).where(ActivityLog.lead_id == lead.id)
            ).all()
            print(f"  Lead {lead.id} ({lead.company}): {len(activities)} activities")
        
        # Get activities by type
        print(f"\nActivities by type:")
        activity_types = {}
        for activity in total_activities:
            activity_types[activity.action] = activity_types.get(activity.action, 0) + 1
        
        for action, count in sorted(activity_types.items()):
            print(f"  {action}: {count}")

if __name__ == "__main__":
    print("🧹 Activity Cleanup Script")
    print("=" * 50)
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python cleanup_activities.py summary                    # Show activity summary")
        print("  python cleanup_activities.py cleanup-days [days]       # Clean by date (default: 7 days)")
        print("  python cleanup_activities.py cleanup-recent [count]    # Keep only recent activities (default: 5)")
        print("  python cleanup_activities.py cleanup-lead [lead_id]    # Clean specific lead")
        print("  Add --execute to actually perform the cleanup (default is dry run)")
        sys.exit(1)
    
    command = sys.argv[1]
    dry_run = "--execute" not in sys.argv
    
    if command == "summary":
        show_activity_summary()
    elif command == "cleanup-days":
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
        cleanup_old_activities(days_to_keep=days, dry_run=dry_run)
    elif command == "cleanup-recent":
        count = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        cleanup_activities_by_lead(keep_recent=count, dry_run=dry_run)
    elif command == "cleanup-lead":
        if len(sys.argv) < 3:
            print("Error: Please provide a lead ID")
            sys.exit(1)
        lead_id = int(sys.argv[2])
        cleanup_activities_by_lead(lead_id=lead_id, dry_run=dry_run)
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
