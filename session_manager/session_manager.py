from datetime import datetime
from environment import get_google_credentials, get_hubspot_config, get_dropbox_config,get_flask_config, get_mongodb_uri
from chatbot.chatbot import build_conversation_text
import gspread

# Global variable to track saved sessions
saved_sessions = set()

def set_saved_sessions(sessions_set):
    """Set the global saved_sessions from app.py"""
    global saved_sessions
    saved_sessions = sessions_set

def get_saved_sessions():
    """Get the current saved_sessions set"""
    global saved_sessions
    return saved_sessions

# Google Sheets configuration
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# Initialize Google Sheets client
sheets_client = None
worksheet = None
GOOGLE_SHEETS_ENABLED = False

try:

    creds = get_google_credentials()

    if creds:
        print("✅ Using Google credentials from environment or file")
        creds = creds.with_scopes(SCOPES)
    else:
        print("⚠️  Google credentials not found. Google Sheets integration disabled.")
        raise FileNotFoundError("Google credentials not found")

    sheets_client = gspread.authorize(creds)
    SPREADSHEET_ID = '1qKhBrL2SSuT4iYkH5DExBhSaXyi4l8U1uXAcnWJng7Q'
    worksheet = sheets_client.open_by_key(SPREADSHEET_ID).sheet1
    GOOGLE_SHEETS_ENABLED = True
    print("✅ Google Sheets connected successfully")

except Exception as e:
    print(f"⚠️  Google Sheets connection failed: {e}")
    worksheet = None

def save_session_to_sheets(session_id, email, chat_history, update_existing=False):
    """Save session data to Google Sheets - one row per session with full conversation"""
    if not GOOGLE_SHEETS_ENABLED:
        print("⚠️  Google Sheets integration disabled - skipping Google Sheets save")
        return False

    try:
        if not worksheet:
            print("⚠️  Google Sheets not available - skipping Google Sheets save")
            return False

        conversation_text = build_conversation_text(chat_history, session_id)

        session_data = {
            "session_id": session_id,
            "email": email,
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "message_count": len(chat_history),
            "conversation": conversation_text.strip(),
            "status": "active"
        }

        row = [
            session_data["session_id"],
            session_data["email"],
            session_data["timestamp"],
            session_data["message_count"],
            session_data["conversation"],
            session_data["status"]
        ]

        # Update strategy: consolidate by email (single row per email)
        # If a row exists for this email, update that row irrespective of session_id
        if update_existing or True:

            try:

                all_values = worksheet.get_all_values()
                session_row = None

                # Columns: A=session_id, B=email, C=timestamp, D=message_count, E=conversation, F=status
                # Find existing row by email (column B)
                normalized_target_email = (email or "").strip().lower()
                for i, row_data in enumerate(all_values):
                    try:
                        if not row_data or len(row_data) <= 1:
                            continue
                        sheet_email = (row_data[1] or "").strip().lower()
                        if sheet_email and sheet_email == normalized_target_email:
                            session_row = i + 1
                            break
                    except Exception:
                        continue

                if session_row:

                    existing_conversation = ""
                    if len(row_data) > 4:
                        existing_conversation = row_data[4] if row_data[4] else ""

                    updated_conversation = existing_conversation
                    if existing_conversation:
                        updated_conversation += "\n\n--- New Messages ---\n"

                    # Safely parse existing message count
                    existing_count = 0
                    if len(row_data) > 3:
                        try:
                            existing_count = int(str(row_data[3]).strip())
                        except Exception:
                            existing_count = 0
                    # If the sheet's count is ahead of this session's count (new browser/session),
                    # append the entire current session as new messages to avoid empty diffs.
                    if existing_count >= len(chat_history):
                        new_messages = chat_history
                    else:
                        new_messages = chat_history[existing_count:]
                    # Compute the new total message count to store back in the sheet
                    updated_message_count = existing_count + len(new_messages)

                    # Build new conversation text with quote form data
                    new_conversation_text = build_conversation_text(chat_history, session_id)

                    # If there's existing conversation, append new messages
                    if existing_conversation:
                        updated_conversation = existing_conversation + "\n\n--- New Messages ---\n"
                        # Extract only the new messages part
                        new_messages_text = ""
                        for msg in new_messages:
                            role = msg.get("role", "unknown")
                            content = msg.get("content", "")
                            if role == "user":
                                new_messages_text += f"\n👤 User: {content}"
                            elif role == "assistant":
                                new_messages_text += f"\n🤖 Assistant: {content}"
                        updated_conversation += new_messages_text
                    else:
                        updated_conversation = new_conversation_text

                    # Logo information is now handled in build_conversation_text function

                    # Preserve original session_id in column A for this email
                    original_session_id = row_data[0] if len(row_data) > 0 else session_data["session_id"]

                    # Respect existing sheet schema: if there's a 'Logo Info' column (column F), keep its value
                    has_logo_info_col = len(row_data) >= 6  # columns are 1-indexed in sheet terms
                    existing_logo_info = row_data[5] if has_logo_info_col else ""

                    # Build updated row matching current schema
                    if has_logo_info_col:
                        updated_row = [
                            original_session_id,
                            session_data["email"],
                            session_data["timestamp"],
                            updated_message_count,
                            updated_conversation,
                            existing_logo_info,
                            session_data["status"]
                        ]
                        worksheet.update(f'A{session_row}:G{session_row}', [updated_row])
                    else:
                        updated_row = [
                            original_session_id,
                            session_data["email"],
                            session_data["timestamp"],
                            updated_message_count,
                            updated_conversation,
                            session_data["status"]
                        ]
                        worksheet.update(f'A{session_row}:F{session_row}', [updated_row])
                    print(
                        f"✅ Email {email} updated in Google Sheets (row {session_row}) - {len(new_messages)} new messages added")
                    return True
                else:
                    print(f"⚠️  Email {email} not found in sheet, appending new row")

                    worksheet.append_row(row)
                    saved_sessions.add(session_id)
                    print(f"✅ Email {email} appended to Google Sheets")
                    return True

            except Exception as update_error:
                print(f"⚠️  Failed to update existing row: {update_error}")

                worksheet.append_row(row)
                saved_sessions.add(session_id)
                print(f"✅ Email {email} appended to Google Sheets (fallback)")
                return True
        else:

            try:
                worksheet.append_row(row)
                saved_sessions.add(session_id)
                print(f"✅ Session {session_id} saved to Google Sheets (one row with full conversation)")
                return True
            except Exception as sheet_error:
                print(f"⚠️  Google Sheets append failed: {sheet_error}")
                return False

    except Exception as e:
        print(f"⚠️  Google Sheets save failed: {e}")
        return False