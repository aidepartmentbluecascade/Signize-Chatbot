from flask import Flask, render_template, request, jsonify, send_from_directory
import werkzeug
from environment import load_environment
from openai import OpenAI
import json
import os
import uuid
from datetime import datetime
import requests
import time
import gspread
from google.oauth2.service_account import Credentials
from mongodb_operations import mongodb_manager


print("__name__ is:", __name__)

# Load environment variables
openai_key = load_environment()



# Google Sheets configuration
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets'
]



# Initialize Google Sheets client
sheets_client = None
worksheet = None
GOOGLE_SHEETS_ENABLED = False

# Google Service Account credentials will be loaded from environment or credentials.json file

try:
    # Use credentials from environment or file
    from environment import get_google_credentials
    creds = get_google_credentials()
    
    if creds:
        print("✅ Using Google credentials from environment or file")
        # Apply the required scopes to the credentials
        creds = creds.with_scopes(SCOPES)
    else:
        print("⚠️  Google credentials not found. Google Sheets integration disabled.")
        raise FileNotFoundError("Google credentials not found")
    
    sheets_client = gspread.authorize(creds)
    SPREADSHEET_ID = '1qKhBrL2SSuT4iYkH5DExBhSaXyi4l8U1uXAcnWJng7Q'  # Your Google Sheet ID
    worksheet = sheets_client.open_by_key(SPREADSHEET_ID).sheet1
    GOOGLE_SHEETS_ENABLED = True
    print("✅ Google Sheets connected successfully")
    print("📧 Service Account: signize@halogen-chemist-468811-a0.iam.gserviceaccount.com")
    print("📋 Make sure this email has 'Editor' access to your Google Sheet")
    

except Exception as e:
    print(f"⚠️  Google Sheets connection failed: {e}")
    print("   Google Sheets integration disabled - sessions will be saved locally only")
    worksheet = None



# Initialize OpenAI Client
client = OpenAI(api_key=openai_key)

# Flask application setup
app = Flask(__name__, template_folder="templates", static_folder="static")

# Load production configuration
from environment import get_flask_config
flask_config = get_flask_config()
app.config['SECRET_KEY'] = flask_config['FLASK_SECRET_KEY']

# In-memory storage for chat sessions
chat_sessions = {}
# Track which sessions have already been saved to Google Sheets
saved_sessions = set()

# Sign-nize Customer Support System Prompt
SIGN_NIZE_SYSTEM_PROMPT = """You are an AI-powered Customer Support Representative for Signize, a company specializing in custom sign design and production.

Your job is to provide excellent customer support for general signage queries and help customers get quotes/mockups when requested.

Your role:
- Be warm, professional, and engaging—make the client feel valued.
- Use the knowledge base to answer general signage questions about signs, mountings, materials, etc.
- When customers mention "mockup" or "quote" AND has already provided their email, trigger the quote form process.
- If customer asks you as "Are you AI?", reply with "Yes, I am AI-powered Customer Support Representative."

FIRST MESSAGE HANDLING:
- If this is the customer's FIRST message in the conversation, ALWAYS ask for their email first.
- Do NOT respond to any other questions or requests until email is collected.
- This applies even if they say "Hi", "Hello", or ask about signs, pricing, etc.

Knowledge Base Use:
When users ask about our products, services, or company information, use the knowledge base to provide accurate details about signs, mountings, materials, installation, etc.

Conversation Guidelines:
- Be warm, professional, and engaging—make the client feel valued.
- Use active listening—acknowledge responses and build on them.
- Handle objections smoothly—if the client is busy, offer to schedule a callback.
- Encourage open-ended responses—help clients share relevant details.
- Keep the chat focused and efficient.

Email Collection Process:
- CRITICAL: ALWAYS ask for the customer's email address on their FIRST message, regardless of what they say.
- Say: "Hi there! I'd be happy to help you with your sign needs. First, could you please provide your email address so I can save your information and follow up with you?"
- Do NOT proceed with any other responses until email is collected.
- After email is collected, ask "How can I help you with your sign needs today?"
- CRITICAL: Once email is collected, NEVER ask for it again in the same conversation.
- CRITICAL: If customer says "Hi" or similar greeting and email is already collected, respond with "Hello! How can I help you with your sign needs today?" - DO NOT ask for email again.
- CRITICAL: Even if the conversation seems to restart or customer says "Hi" again, if you already have their email, do NOT ask for it again.

Quote/Mockup Process:
ONLY when a customer mentions they want a "mockup" or "quote" AND has already provided their email address, respond with:
"I'd be happy to help you get a quote and create a mockup! I'll need to collect some specific details from you. Let me open a form for you to fill out with all the necessary information."

Then trigger the quote form by including this special marker in your response: [QUOTE_FORM_TRIGGER]

IMPORTANT: Only trigger the quote form when customers explicitly say they want to:
- "share details", "provide information", "get a quote"
- "want a mockup", "need pricing", "get estimate"
- Use phrases like "I want to share", "Let me tell you", "I need to provide"

After Form Submission:
- If customer says they want changes, acknowledge and let them know they can modify the form.
- If customer says no changes needed, simply say: "Perfect! Please email your logo files to info@signize.us so our designers can work with your brand assets. We'll review your requirements and get back to you with a mockup and quote within a few hours."

The form will collect:
- Size and dimensions
- Material preferences (metal, acrylic, etc.)
- Illumination (with or without lighting)
- Installation surface (brick wall, concrete, etc.)
- City and state
- Budget range
- Placement (indoor/outdoor)
- Deadlines (standard 15-17 business days, rush 12 days with 20% additional cost)

Order/Shipping Issues Process:
When customers mention problems with their order, shipping delays, or order status:
1. Ask for their Order ID
2. Ask for their email address (if not already provided)
3. Ask for their phone number
4. Tell them: "Thank you for providing those details. Our customer service representative will reach out to you within 24 hours with more information about your order. Is there anything else I can help you with today?"

General Signage Support:
For general questions about signs, mountings, materials, installation, etc., provide helpful information using the knowledge base. Be conversational and informative.

After Order Issues:
When customers complete order tracking and then ask about general sign information, provide detailed answers about the specific topics they're asking about. Do not redirect them to ask "how can I help you" again.

CRITICAL: If a customer has completed an order issue (provided Order ID and phone number) and then asks about signs, materials, lighting, or any other general sign-related topics, provide helpful information about those specific topics. Do NOT ask "How can I help you" or redirect them - just answer their question directly.

Tone:
- Friendly and conversational, not robotic.
- Adjust based on how the customer responds.
- Professional but approachable.

Edge Cases & Objection Handling:

If they ask for pricing before getting a quote:
"Pricing depends on the size, material, and customization. Would you like me to help you get a quote? I can collect your requirements and provide you with an accurate estimate."

If they are unsure about details:
"No worries! I can help you figure out what would work best for your needs. Let me know what you're looking for and I'll guide you through the options." """

def save_session_to_sheets(session_id, email, chat_history, update_existing=False):
    """Save session data to Google Sheets - one row per session with full conversation"""
    if not GOOGLE_SHEETS_ENABLED:
        print("⚠️  Google Sheets integration disabled - skipping Google Sheets save")
        return False
        
    try:
        if not worksheet:
            print("⚠️  Google Sheets not available - skipping Google Sheets save")
            return False
        
        # Convert chat history to a readable format
        conversation_text = ""
        for i, message in enumerate(chat_history):
            role = "User" if message["role"] == "user" else "Assistant"
            conversation_text += f"{role}: {message['content']}\n"
        

        
        # Prepare session data - all in one row
        session_data = {
            "session_id": session_id,
            "email": email,
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "message_count": len(chat_history),
            "conversation": conversation_text.strip(),
            "status": "active"
        }
        
        # Add to Google Sheets - one row with all data
        row = [
            session_data["session_id"],
            session_data["email"],
            session_data["timestamp"],
            session_data["message_count"],
            session_data["conversation"],
            session_data["status"]
        ]
        
        # Check if session already exists in the sheet
        if session_id in saved_sessions and update_existing:
            # Find and update existing row
            try:
                # Get all values from the sheet
                all_values = worksheet.get_all_values()
                session_row = None
                
                # Find the row with this session_id
                for i, row_data in enumerate(all_values):
                    if row_data and len(row_data) > 0 and row_data[0] == session_id:
                        session_row = i + 1  # Google Sheets is 1-indexed
                        break
                
                if session_row:
                    # Update the existing row
                    worksheet.update(f'A{session_row}:F{session_row}', [row])
                    print(f"✅ Session {session_id} updated in Google Sheets (row {session_row})")
                    return True
                else:
                    print(f"⚠️  Session {session_id} not found in sheet, appending new row")
                    # Fall back to appending if not found
                    worksheet.append_row(row)
                    saved_sessions.add(session_id)
                    print(f"✅ Session {session_id} appended to Google Sheets")
                    return True
                    
            except Exception as update_error:
                print(f"⚠️  Failed to update existing row: {update_error}")
                # Fall back to appending
                worksheet.append_row(row)
                saved_sessions.add(session_id)
                print(f"✅ Session {session_id} appended to Google Sheets (fallback)")
                return True
        else:
            # First time saving this session
            try:
                worksheet.append_row(row)
                saved_sessions.add(session_id)
                print(f"✅ Session {session_id} saved to Google Sheets (one row with full conversation)")
                return True
            except Exception as sheet_error:
                print(f"⚠️  Google Sheets append failed: {sheet_error}")
                # Try to create a new sheet if the current one doesn't exist
                try:
                    spreadsheet = sheets_client.open_by_key(SPREADSHEET_ID)
                    new_worksheet = spreadsheet.add_worksheet(title=f"Session_{session_id}", rows=100, cols=6)
                    new_worksheet.append_row(["Session ID", "Email", "Timestamp", "Message Count", "Full Conversation", "Status"])
                    new_worksheet.append_row(row)
                    saved_sessions.add(session_id)
                    print(f"✅ Session {session_id} saved to new worksheet")
                    return True
                except Exception as new_sheet_error:
                    print(f"⚠️  Failed to create new worksheet: {new_sheet_error}")
                    print("   Sessions will be saved locally only")
                    return False
        
    except Exception as e:
        print(f"⚠️  Google Sheets save failed: {e}")
        print("   Sessions will be saved locally only")
        return False

def save_session_locally(session_id, chat_history):
    """Save chat session to local file - one file per session"""
    try:
        # Create data directory if it doesn't exist
        os.makedirs("chat_sessions", exist_ok=True)
        
        # Save session to JSON file - one file per session
        session_data = {
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "messages": chat_history,
            "message_count": len(chat_history)
        }
        
        # Use session_id as filename to ensure one file per session
        filename = f"chat_sessions/session_{session_id}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Local: Session {session_id} saved to {filename}")
        return filename
    except Exception as e:
        print("❌ Local save failed:", str(e))
        return None

# REMOVED: generate_conversation_summary function - not needed

def validate_email(email):
    """Validate email format"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

# Route to serve the chatbot UI
@app.route("/")
def index():
    """
    Serve the main chatbot page (index.html).
    """
    return render_template("index.html")

# Route to handle user messages
@app.route("/chat", methods=["POST"])
def chat():
    print(">>> /chat endpoint hit")
    user_message = request.json.get("message")
    session_id = request.json.get("session_id", "default")
    email = request.json.get("email", "")
    print("Message received:", user_message)
    print("Email:", email)

    # Initialize session if it doesn't exist
    if session_id not in chat_sessions:
        chat_sessions[session_id] = {
            "messages": [],
            "context_history": [],
            "conversation_state": "initial",
            "customer_info": {},
            "email": email
        }
    else:
        # Update email if provided
        if email:
            chat_sessions[session_id]["email"] = email
    
    # Add user message to session history
    chat_sessions[session_id]["messages"].append({
        "role": "user",
        "content": user_message
    })

    try:
        # Generate response using the Sign-nize system prompt with context
        response = generate_sign_nize_response(client, user_message, chat_sessions[session_id])
        
        # Check if response contains quote form trigger
        quote_form_triggered = "[QUOTE_FORM_TRIGGER]" in response
        if quote_form_triggered:
            response = response.replace("[QUOTE_FORM_TRIGGER]", "")
        
        # Quote form triggering is now handled entirely by the system prompt
        # The AI will include [QUOTE_FORM_TRIGGER] when appropriate based on context
        
        # Add assistant response to session history
        chat_sessions[session_id]["messages"].append({
            "role": "assistant",
            "content": response
        })
        
        # Continuously update Google Sheets with each message
        message_count = len(chat_sessions[session_id]["messages"])
        
        # Save to Google Sheets if email is available (update existing or create new)
        if chat_sessions[session_id].get("email"):
            update_existing = session_id in saved_sessions
            success = save_session_to_sheets(session_id, chat_sessions[session_id]["email"], chat_sessions[session_id]["messages"], update_existing)
            if success and session_id not in saved_sessions:
                saved_sessions.add(session_id)
        
        # Order information saving is now handled by the system prompt when appropriate
        
        # Save locally when message count reaches limit
        if message_count >= 30:
            save_session_locally(session_id, chat_sessions[session_id]["messages"])
            print(f"✅ Session {session_id} saved locally (message limit reached)")
        
        print(f"Generated response for session {session_id}:", response)
        return jsonify({
            "message": response,
            "session_id": session_id,
            "message_count": len(chat_sessions[session_id]["messages"]),
            "quote_form_triggered": quote_form_triggered
        })
        
    except Exception as e:
        print("Error in generate_sign_nize_response:", str(e))
        return jsonify({"message": f"Sorry, I encountered an error. Please try again."}), 500

def generate_sign_nize_response(client, user_message, session_data):
    """
    Generate response using the Sign-nize customer support system prompt with context awareness
    """
    # Update system prompt with current date
    current_date = datetime.now().strftime('%B %d, %Y')
    system_prompt = SIGN_NIZE_SYSTEM_PROMPT.replace('{{date}}', current_date)
    
    # Build full conversation context
    conversation_context = ""
    if session_data["messages"]:
        conversation_context = "\n\nFULL CONVERSATION HISTORY:\n"
        for msg in session_data["messages"]:
            role = "User" if msg["role"] == "user" else "Assistant"
            conversation_context += f"{role}: {msg['content']}\n"
    
    # Order issue detection and handling is now managed by the system prompt
    # The AI will understand context and handle order issues appropriately
    
    # All logic is now handled by the system prompt - no hardcoded detection needed
    
    # Check if email has already been collected in this conversation
    email_already_collected = False
    email_value = None
    
    # First check session data
    if session_data.get("email"):
        email_already_collected = True
        email_value = session_data.get("email")
    elif session_data.get("customer_info", {}).get("email"):
        email_already_collected = True
        email_value = session_data.get("customer_info", {}).get("email")
    
    # Then check conversation history for email collection
    if not email_already_collected and session_data["messages"]:
        for msg in session_data["messages"]:
            if msg["role"] == "user" and "@" in msg["content"]:
                # Extract email from the message
                import re
                email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', msg["content"])
                if email_match:
                    email_already_collected = True
                    email_value = email_match.group(0)
                    # Also update session data for future reference
                    session_data["email"] = email_value
                    break
    
        # Add simplified context instructions
    context_instructions = f"""
    
CONTEXT INSTRUCTIONS:
1. CAREFULLY READ the full conversation history above.
2. If this is the FIRST message in the conversation, ALWAYS ask for email first.
3. If email is already collected, NEVER ask for it again - this is a CRITICAL rule.
4. After email collection, ask "How can I help you with your sign needs today?"
5. Handle order issues by collecting Order ID and phone number, then tell customer representative will contact them.
6. For general sign questions after order issues, provide helpful information without asking "How can I help you" again.
7. Trigger quote form with [QUOTE_FORM_TRIGGER] when customer explicitly wants quotes/mockups.
8. CRITICAL: Even if customer says "Hi" again after email collection, do NOT ask for email - just say "Hello! How can I help you with your sign needs today?"
"""
    
    # Order issue handling is now managed by the system prompt
    
    # Combine all context
    full_prompt = system_prompt + context_instructions + conversation_context + f"\n\nCurrent User Message: {user_message}"
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": full_prompt,
            },
            {
                "role": "user",
                "content": user_message,
            },
        ],
        max_tokens=300,
        temperature=0.0
    )

    return response.choices[0].message.content

# Route to get session history
@app.route("/chat/<session_id>/history", methods=["GET"])
def get_session_history(session_id):
    print(f">>> Getting history for session {session_id}")
    
    if session_id not in chat_sessions:
        return jsonify({"error": "Session not found"}), 404
    
    return jsonify({
        "session_id": session_id,
        "messages": chat_sessions[session_id]["messages"],
        "message_count": len(chat_sessions[session_id]["messages"])
    })

# Route to clear session history
@app.route("/chat/<session_id>/clear", methods=["DELETE"])
def clear_session(session_id):
    print(f">>> Clearing session {session_id}")
    
    if session_id in chat_sessions:
        del chat_sessions[session_id]
        return jsonify({"message": f"Session {session_id} cleared successfully"})
    else:
        return jsonify({"error": "Session not found"}), 404

# Route to list all active sessions
@app.route("/sessions", methods=["GET"])
def list_sessions():
    print(">>> Listing all active sessions")
    
    sessions_info = {}
    for session_id, session_data in chat_sessions.items():
        sessions_info[session_id] = {
            "message_count": len(session_data["messages"]),
            "last_message": session_data["messages"][-1]["content"] if session_data["messages"] else None
        }
    
    return jsonify({
        "active_sessions": list(chat_sessions.keys()),
        "session_count": len(chat_sessions),
        "sessions_info": sessions_info
    })

# Route to validate email
@app.route("/validate-email", methods=["POST"])
def validate_email_endpoint():
    print(">>> Email validation endpoint hit")
    data = request.json
    email = data.get("email", "")
    
    if not email:
        return jsonify({"valid": False, "message": "Email is required"})
    
    is_valid = validate_email(email)
    return jsonify({
        "valid": is_valid,
        "message": "Valid email format" if is_valid else "Invalid email format"
    })



# Route to save session to Google Sheets
@app.route("/chat/<session_id>/save-sheets", methods=["POST"])
def save_session_sheets(session_id):
    print(f">>> Manually saving session {session_id} to Google Sheets")
    
    if session_id not in chat_sessions:
        return jsonify({"error": "Session not found"}), 404
    
    email = chat_sessions[session_id].get("email")
    if not email:
        return jsonify({"error": "No email associated with this session"}), 400
    
    try:
        update_existing = session_id in saved_sessions
        success = save_session_to_sheets(session_id, email, chat_sessions[session_id]["messages"], update_existing)
        if success:
            return jsonify({
                "message": f"Session {session_id} {'updated' if update_existing else 'saved'} to Google Sheets",
                "session_id": session_id,
                "email": email,
                "message_count": len(chat_sessions[session_id]["messages"]),
                "already_saved": session_id in saved_sessions,
                "action": "updated" if update_existing else "saved"
            })
        else:
            return jsonify({"error": "Failed to save to Google Sheets"}), 500
    except Exception as e:
        return jsonify({"error": f"Failed to save to sheets: {str(e)}"}), 500

# Route to force save session to Google Sheets (bypass duplicate check)
@app.route("/chat/<session_id>/force-save-sheets", methods=["POST"])
def force_save_session_sheets(session_id):
    print(f">>> Force saving session {session_id} to Google Sheets")
    
    if session_id not in chat_sessions:
        return jsonify({"error": "Session not found"}), 404
    
    email = chat_sessions[session_id].get("email")
    if not email:
        return jsonify({"error": "No email associated with this session"}), 400
    
    try:
        # Temporarily remove from saved_sessions to force save
        if session_id in saved_sessions:
            saved_sessions.remove(session_id)
        
        success = save_session_to_sheets(session_id, email, chat_sessions[session_id]["messages"], True)
        if success:
            return jsonify({
                "message": f"Session {session_id} force saved to Google Sheets",
                "session_id": session_id,
                "email": email,
                "message_count": len(chat_sessions[session_id]["messages"])
            })
        else:
            return jsonify({"error": "Failed to save to Google Sheets"}), 500
    except Exception as e:
        return jsonify({"error": f"Failed to save to sheets: {str(e)}"}), 500

# Route to save session locally
@app.route("/chat/<session_id>/save-local", methods=["POST"])
def save_session_local(session_id):
    print(f">>> Saving session {session_id} locally")
    
    if session_id not in chat_sessions:
        return jsonify({"error": "Session not found"}), 404
    
    try:
        filename = save_session_locally(session_id, chat_sessions[session_id]["messages"])
        if filename:
            return jsonify({
                "message": f"Session {session_id} saved locally",
                "filename": filename,
                "session_id": session_id,
                "message_count": len(chat_sessions[session_id]["messages"])
            })
        else:
            return jsonify({"error": "Failed to save session locally"}), 500
    except Exception as e:
        return jsonify({"error": f"Failed to save locally: {str(e)}"}), 500

# Route to list locally saved sessions
@app.route("/saved-sessions", methods=["GET"])
def list_saved_sessions():
    print(">>> Listing locally saved sessions")
    
    try:
        if not os.path.exists("chat_sessions"):
            return jsonify({"saved_sessions": [], "count": 0})
        
        sessions = []
        for filename in os.listdir("chat_sessions"):
            if filename.endswith('.json'):
                filepath = os.path.join("chat_sessions", filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        session_data = json.load(f)
                        session_id = session_data.get("session_id")
                        sessions.append({
                            "filename": filename,
                            "session_id": session_id,
                            "timestamp": session_data.get("timestamp"),
                            "message_count": session_data.get("message_count", 0),
                            "saved_to_sheets": session_id in saved_sessions
                        })
                except Exception as e:
                    print(f"Error reading {filename}: {e}")
        
        return jsonify({
            "saved_sessions": sessions,
            "count": len(sessions),
            "sheets_saved_count": len(saved_sessions)
        })
    except Exception as e:
        return jsonify({"error": f"Failed to list saved sessions: {str(e)}"}), 500

# Route to view saved sessions tracking
@app.route("/sheets-saved-sessions", methods=["GET"])
def list_sheets_saved_sessions():
    print(">>> Listing sessions saved to Google Sheets")
    
    return jsonify({
        "saved_to_sheets": list(saved_sessions),
        "count": len(saved_sessions)
    })

# Route to test MongoDB connection
@app.route("/test-mongodb", methods=["GET"])
def test_mongodb():
    print(">>> Testing MongoDB connection")
    
    try:
        from mongodb_operations import test_mongodb_connection
        success = test_mongodb_connection()
        
        if success:
            return jsonify({
                "success": True,
                "message": "MongoDB connection test successful",
                "status": "connected"
            })
        else:
            return jsonify({
                "success": False,
                "message": "MongoDB connection test failed",
                "status": "disconnected"
            })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"MongoDB test error: {str(e)}",
            "status": "error"
        })

# Route to manually test MongoDB save
@app.route("/test-mongodb-save", methods=["POST"])
def test_mongodb_save():
    print(">>> Testing MongoDB save operation")
    
    try:
        test_data = {
            "session_id": "test_session_123",
            "email": "test@example.com",
            "form_data": {
                "test": "data",
                "timestamp": datetime.now().isoformat()
            }
        }
        
        result = mongodb_manager.save_quote_data(
            test_data["session_id"],
            test_data["email"],
            test_data["form_data"]
        )
        
        if result["success"]:
            return jsonify({
                "success": True,
                "message": f"Test data saved successfully: {result['action']}",
                "result": result
            })
        else:
            return jsonify({
                "success": False,
                "message": f"Test data save failed: {result.get('error', 'Unknown error')}",
                "result": result
            })
            
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Test save error: {str(e)}",
            "status": "error"
        })

# Tool call function for chat session management
def manage_chat_session(session_id, action="get", data=None):
    """
    Tool call function for managing chat sessions
    Available actions: get, save_local, save_sheets, clear, list_all
    """
    try:
        if action == "get":
            if session_id in chat_sessions:
                return {
                    "success": True,
                    "session_id": session_id,
                    "messages": chat_sessions[session_id]["messages"],
                    "email": chat_sessions[session_id].get("email"),
                    "message_count": len(chat_sessions[session_id]["messages"])
                }
            else:
                return {"success": False, "error": "Session not found"}
        
        elif action == "save_local":
            if session_id in chat_sessions:
                filename = save_session_locally(session_id, chat_sessions[session_id]["messages"])
                return {"success": True, "filename": filename}
            else:
                return {"success": False, "error": "Session not found"}
        
        elif action == "save_sheets":
            if session_id in chat_sessions:
                email = chat_sessions[session_id].get("email")
                if email:
                    update_existing = session_id in saved_sessions
                    success = save_session_to_sheets(session_id, email, chat_sessions[session_id]["messages"], update_existing)
                    return {"success": success, "email": email, "action": "updated" if update_existing else "saved"}
                else:
                    return {"success": False, "error": "No email associated with session"}
            else:
                return {"success": False, "error": "Session not found"}
        
        elif action == "clear":
            if session_id in chat_sessions:
                del chat_sessions[session_id]
                return {"success": True, "message": "Session cleared"}
            else:
                return {"success": False, "error": "Session not found"}
        
        elif action == "list_all":
            sessions_info = {}
            for sid, session_data in chat_sessions.items():
                sessions_info[sid] = {
                    "message_count": len(session_data["messages"]),
                    "email": session_data.get("email"),
                    "last_message": session_data["messages"][-1]["content"] if session_data["messages"] else None
                }
            return {"success": True, "sessions": sessions_info}
        
        else:
            return {"success": False, "error": "Invalid action"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

# Route to use the tool call function
@app.route("/tool/chat-session", methods=["POST"])
def chat_session_tool():
    print(">>> Chat session tool endpoint hit")
    data = request.json
    session_id = data.get("session_id")
    action = data.get("action", "get")
    
    if not session_id:
        return jsonify({"error": "Session ID is required"}), 400
    
    result = manage_chat_session(session_id, action, data.get("data"))
    return jsonify(result)

# Route to save quote form data
@app.route("/save-quote", methods=["POST"])
def save_quote():
    print(">>> Save quote endpoint hit")
    data = request.json
    session_id = data.get("session_id")
    email = data.get("email")
    form_data = data.get("form_data")
    
    if not session_id or not email or not form_data:
        return jsonify({"error": "Session ID, email, and form data are required"}), 400
    
    try:
        result = mongodb_manager.save_quote_data(session_id, email, form_data)
        if result["success"]:
            return jsonify({
                "success": True,
                "message": f"Quote data {result['action']} successfully",
                "quote_id": result.get("quote_id")
            })
        else:
            return jsonify({"error": result["error"]}), 500
    except Exception as e:
        return jsonify({"error": f"Failed to save quote: {str(e)}"}), 500

# Route to get quote data for a session
@app.route("/get-quote/<session_id>", methods=["GET"])
def get_quote(session_id):
    print(f">>> Get quote endpoint hit for session {session_id}")
    
    try:
        result = mongodb_manager.get_quote_data(session_id)
        if result["success"]:
            return jsonify(result["quote"])
        else:
            # Return empty data instead of 404 when no quote exists yet
            return jsonify({"form_data": {}})
    except Exception as e:
        return jsonify({"error": f"Failed to get quote: {str(e)}"}), 500

# Route to get all quotes (admin)
@app.route("/admin/quotes", methods=["GET"])
def get_all_quotes():
    print(">>> Get all quotes endpoint hit")
    
    try:
        result = mongodb_manager.get_all_quotes()
        if result["success"]:
            return jsonify({"quotes": result["quotes"]})
        else:
            return jsonify({"error": result["error"]}), 500
    except Exception as e:
        return jsonify({"error": f"Failed to get quotes: {str(e)}"}), 500

# Route to upload logo files
@app.route("/upload-logo", methods=["POST"])
def upload_logo():
    print(">>> Upload logo endpoint hit")
    
    if 'logo' not in request.files:
        return jsonify({"success": False, "message": "No logo file provided"}), 400
    
    file = request.files['logo']
    session_id = request.form.get('session_id')
    
    if file.filename == '':
        return jsonify({"success": False, "message": "No file selected"}), 400
    
    if not session_id:
        return jsonify({"success": False, "message": "Session ID required"}), 400
    
    try:
        # Create logos directory if it doesn't exist
        logos_dir = os.path.join('data', 'logos', session_id)
        os.makedirs(logos_dir, exist_ok=True)
        
        # Save the file
        filename = f"logo_{int(time.time())}_{file.filename}"
        file_path = os.path.join(logos_dir, filename)
        file.save(file_path)
        
        # For now, just return success (in a real app, you'd store this in a database)
        return jsonify({
            "success": True,
            "message": f"Logo uploaded successfully: {filename}",
            "logo_count": 1  # This would be dynamic in a real implementation
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Upload failed: {str(e)}"}), 500

# Route to get logos for a session
@app.route("/session/<session_id>/logos", methods=["GET"])
def get_session_logos(session_id):
    print(f">>> Get logos endpoint hit for session {session_id}")
    
    try:
        logos_dir = os.path.join('data', 'logos', session_id)
        if os.path.exists(logos_dir):
            logos = []
            for filename in os.listdir(logos_dir):
                if filename.startswith('logo_'):
                    logos.append({
                        "filename": filename,
                        "public_url": f"/logos/{session_id}/{filename}"
                    })
            return jsonify({"logos": logos})
        else:
            return jsonify({"logos": []})
    except Exception as e:
        return jsonify({"error": f"Failed to get logos: {str(e)}"}), 500

# Route to serve uploaded logo files
@app.route("/logos/<session_id>/<filename>")
def serve_logo(session_id, filename):
    logos_dir = os.path.join('data', 'logos', session_id)
    return send_from_directory(logos_dir, filename)

# Run the Flask app
if __name__ == "__main__":
    print("Starting Sign-nize Customer Support System...")
    # Use environment variables for production settings
    debug_mode = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(host="0.0.0.0", port=5000, debug=debug_mode)
