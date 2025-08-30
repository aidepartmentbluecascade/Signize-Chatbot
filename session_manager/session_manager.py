from datetime import datetime
from environment import get_google_credentials, get_hubspot_config, get_dropbox_config,get_flask_config, get_mongodb_uri
from chatbot.chatbot import build_conversation_text
import gspread


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

        if session_id in saved_sessions and update_existing:

            try:

                all_values = worksheet.get_all_values()
                session_row = None

                for i, row_data in enumerate(all_values):
                    if row_data and len(row_data) > 0 and row_data[0] == session_id:
                        session_row = i + 1
                        break

                if session_row:

                    existing_conversation = ""
                    if len(row_data) > 4:
                        existing_conversation = row_data[4] if row_data[4] else ""

                    updated_conversation = existing_conversation
                    if existing_conversation:
                        updated_conversation += "\n\n--- New Messages ---\n"

                    existing_count = int(row_data[3]) if len(row_data) > 3 and row_data[3].isdigit() else 0
                    new_messages = chat_history[existing_count:]

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

                    updated_row = [
                        session_data["session_id"],
                        session_data["email"],
                        session_data["timestamp"],
                        session_data["message_count"],
                        updated_conversation,
                        session_data["status"]
                    ]

                    worksheet.update(f'A{session_row}:F{session_row}', [updated_row])
                    print(
                        f"✅ Session {session_id} updated in Google Sheets (row {session_row}) - {len(new_messages)} new messages added")
                    return True
                else:
                    print(f"⚠️  Session {session_id} not found in sheet, appending new row")

                    worksheet.append_row(row)
                    saved_sessions.add(session_id)
                    print(f"✅ Session {session_id} appended to Google Sheets")
                    return True

            except Exception as update_error:
                print(f"⚠️  Failed to update existing row: {update_error}")

                worksheet.append_row(row)
                saved_sessions.add(session_id)
                print(f"✅ Session {session_id} appended to Google Sheets (fallback)")
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