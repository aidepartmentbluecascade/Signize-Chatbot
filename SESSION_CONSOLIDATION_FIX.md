# Session Consolidation Fix

## Problem Description

The chatbot was creating multiple database documents for the same email address when users had different session IDs, and HubSpot conversations were not being synced properly across different sessions for the same email.

### Issues Identified:

1. **Database Duplication**: Each new session (even for the same email) created a new document in MongoDB
2. **HubSpot Fragmentation**: HubSpot contact_id was tied to session_id instead of email, causing conversation history to be fragmented
3. **Conversation Loss**: Users returning with different session IDs couldn't see their previous conversations

## Solution Implemented

### 1. Email-Based Session Management

Modified `mongodb_operations.py` to use email as the primary key for session management:

- **`save_chat_session()`**: Now checks for existing sessions by email first, then merges messages
- **`get_chat_session_by_email()`**: New method to retrieve sessions by email
- **`update_hubspot_contact_id_by_email()`**: New method to store HubSpot contact_id by email
- **`update_hubspot_last_sync_by_email()`**: New method to track sync times by email

### 2. Message Deduplication

Implemented intelligent message merging to prevent duplicates:

```python
# Create a set of message content to avoid duplicates
existing_content = set()
for msg in existing_messages:
    content_key = f"{msg.get('role', '')}:{msg.get('content', '')}"
    existing_content.add(content_key)

# Add only new messages that don't already exist
merged_messages = existing_messages.copy()
for msg in new_messages:
    content_key = f"{msg.get('role', '')}:{msg.get('content', '')}"
    if content_key not in existing_content:
        merged_messages.append(msg)
        existing_content.add(content_key)
```

### 3. HubSpot Integration Fix

Updated HubSpot contact management to be email-based:

- Contact IDs are now stored and retrieved by email instead of session_id
- Conversations are synced to the same HubSpot contact regardless of session
- Sync timing is tracked per email to prevent excessive API calls

### 4. Session Loading Enhancement

Enhanced session loading to handle email-based consolidation:

- If session_id lookup fails, tries to load by email
- Merges conversation history from previous sessions
- Maintains backward compatibility with existing session-based lookups

## Files Modified

1. **`mongodb_operations.py`**
   - Updated `save_chat_session()` method
   - Added `get_chat_session_by_email()` method
   - Added `update_hubspot_contact_id_by_email()` method
   - Added `update_hubspot_last_sync_by_email()` method

2. **`app.py`**
   - Updated HubSpot contact creation to use email-based storage
   - Modified HubSpot sync logic to retrieve contact_id by email
   - Enhanced session loading to handle email-based sessions

3. **`migrate_sessions.py`** (New)
   - Migration script to consolidate existing duplicate sessions
   - Merges messages from multiple sessions for the same email
   - Preserves HubSpot contact_id and sync timing

## Migration Process

### Step 1: Run Migration Script

```bash
cd Signize-Chatbot
python migrate_sessions.py
```

This script will:
- Find all chat sessions in the database
- Group them by email address
- Merge sessions with the same email
- Delete duplicate sessions
- Preserve HubSpot contact information

### Step 2: Verify Migration

The migration script will output:
- Number of sessions found
- Number of unique emails
- Number of email groups consolidated
- Verification that no duplicates remain

### Step 3: Test the Fix

1. Start a chat session with an email
2. Close the browser/tab
3. Start a new session with the same email
4. Verify that previous conversation history is loaded
5. Check that HubSpot sync works correctly

## Benefits

1. **No More Duplicates**: Each email will have only one session document
2. **Complete Conversation History**: Users can see all their previous conversations
3. **Proper HubSpot Integration**: All conversations sync to the same HubSpot contact
4. **Better User Experience**: Seamless experience across different sessions
5. **Data Integrity**: Consistent data structure and relationships

## Backward Compatibility

The changes maintain backward compatibility:
- Existing session-based lookups still work
- Fallback mechanisms ensure graceful degradation
- No breaking changes to existing functionality

## Monitoring

After deployment, monitor:
- Database document count (should decrease)
- HubSpot sync success rates (should improve)
- User session continuity (should be seamless)
- Error logs for any issues

## Rollback Plan

If issues arise, the system can be rolled back by:
1. Restoring the original `mongodb_operations.py` methods
2. Reverting the HubSpot integration changes in `app.py`
3. The migration script changes are permanent but can be reverted by restoring from backup
