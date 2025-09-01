#!/usr/bin/env python3
"""
Migration script to consolidate duplicate sessions for the same email.
This script will merge all sessions with the same email into a single session.
"""

import os
import sys
from datetime import datetime
from pymongo import MongoClient
from environment import load_environment, get_mongodb_uri

def migrate_sessions():
    """Migrate existing sessions to consolidate by email"""
    
    # Load environment
    try:
        load_environment()
        mongodb_uri = get_mongodb_uri()
    except Exception as e:
        print(f"❌ Failed to load environment: {e}")
        return False
    
    try:
        # Connect to MongoDB
        client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=10000)
        client.admin.command('ping')
        db = client['signize_bot']
        quotes_collection = db['quotes']
        
        print("✅ Connected to MongoDB successfully")
        
        # Find all chat sessions
        chat_sessions = list(quotes_collection.find({"type": "chat_session"}))
        print(f"📊 Found {len(chat_sessions)} chat sessions")
        
        # Group sessions by email
        email_groups = {}
        for session in chat_sessions:
            email = session.get("email", "").lower().strip()
            if email:
                if email not in email_groups:
                    email_groups[email] = []
                email_groups[email].append(session)
        
        print(f"📧 Found {len(email_groups)} unique emails")
        
        # Process each email group
        consolidated_count = 0
        for email, sessions in email_groups.items():
            if len(sessions) > 1:
                print(f"🔄 Consolidating {len(sessions)} sessions for email: {email}")
                
                # Sort sessions by creation date
                sessions.sort(key=lambda x: x.get("created_at", datetime.min))
                
                # Use the first session as the base
                base_session = sessions[0]
                base_session_id = base_session["session_id"]
                
                # Merge all messages from all sessions
                all_messages = []
                seen_messages = set()
                
                for session in sessions:
                    messages = session.get("messages", [])
                    for msg in messages:
                        # Create a unique key for each message
                        msg_key = f"{msg.get('role', '')}:{msg.get('content', '')}"
                        if msg_key not in seen_messages:
                            all_messages.append(msg)
                            seen_messages.add(msg_key)
                
                # Update the base session with merged data
                update_data = {
                    "messages": all_messages,
                    "message_count": len(all_messages),
                    "updated_at": datetime.now(),
                    "consolidated_at": datetime.now(),
                    "original_session_count": len(sessions)
                }
                
                # Preserve the earliest HubSpot contact_id if any session has one
                hubspot_contact_ids = [s.get("hubspot_contact_id") for s in sessions if s.get("hubspot_contact_id")]
                if hubspot_contact_ids:
                    update_data["hubspot_contact_id"] = hubspot_contact_ids[0]
                
                # Preserve the latest HubSpot sync time if any session has one
                hubspot_sync_times = [s.get("hubspot_last_sync_at") for s in sessions if s.get("hubspot_last_sync_at")]
                if hubspot_sync_times:
                    # Sort by timestamp and take the latest
                    hubspot_sync_times.sort()
                    update_data["hubspot_last_sync_at"] = hubspot_sync_times[-1]
                
                # Update the base session
                result = quotes_collection.update_one(
                    {"_id": base_session["_id"]},
                    {"$set": update_data}
                )
                
                if result.modified_count > 0:
                    print(f"✅ Updated base session {base_session_id} with {len(all_messages)} messages")
                    
                    # Delete the other sessions
                    other_session_ids = [s["session_id"] for s in sessions[1:]]
                    delete_result = quotes_collection.delete_many({
                        "session_id": {"$in": other_session_ids},
                        "type": "chat_session"
                    })
                    
                    if delete_result.deleted_count > 0:
                        print(f"🗑️  Deleted {delete_result.deleted_count} duplicate sessions")
                        consolidated_count += 1
                    else:
                        print(f"⚠️  Failed to delete duplicate sessions")
                else:
                    print(f"❌ Failed to update base session {base_session_id}")
        
        print(f"✅ Migration completed. Consolidated {consolidated_count} email groups.")
        
        # Verify the migration
        final_sessions = list(quotes_collection.find({"type": "chat_session"}))
        final_email_groups = {}
        for session in final_sessions:
            email = session.get("email", "").lower().strip()
            if email:
                if email not in final_email_groups:
                    final_email_groups[email] = []
                final_email_groups[email].append(session)
        
        duplicate_emails = [email for email, sessions in final_email_groups.items() if len(sessions) > 1]
        
        if duplicate_emails:
            print(f"⚠️  Warning: {len(duplicate_emails)} emails still have multiple sessions:")
            for email in duplicate_emails:
                print(f"   - {email}: {len(final_email_groups[email])} sessions")
        else:
            print("✅ All emails now have single sessions")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting session migration...")
    success = migrate_sessions()
    if success:
        print("✅ Migration completed successfully")
        sys.exit(0)
    else:
        print("❌ Migration failed")
        sys.exit(1)
