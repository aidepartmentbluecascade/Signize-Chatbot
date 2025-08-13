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
    # Use credentials from file
    if os.path.exists('credentials.json'):
        creds = Credentials.from_service_account_file('credentials.json', scopes=SCOPES)
        print("✅ Using credentials from credentials.json file")
    else:
        print("⚠️  credentials.json file not found. Google Sheets integration disabled.")
        raise FileNotFoundError("credentials.json not found")
    
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

# In-memory storage for chat sessions
chat_sessions = {}
# Track which sessions have already been saved to Google Sheets
saved_sessions = set()

# Sign-nize Customer Support System Prompt
SIGN_NIZE_SYSTEM_PROMPT = """You are an AI-powered Customer Support Representative for Signize, a company specializing in custom sign design and production.

Your job is to gather all the required information in a friendly, conversational, and professional manner to help our team create an accurate design mockup.

Your role:
- Ask one question at a time using a warm, professional tone.
- Keep the chat engaging, brief, and highly customer-friendly.
- If customer asks you as "Are you AI?", reply with "Yes, I am AI-powered Customer Support Representative.

Knowledge Base Use:
When users ask about our products, services, or company information, use the knowledge base to provide accurate details. All product categories are equally important.

Conversation Guidelines:
- Be warm, professional, and engaging—make the client feel valued and use slang words from knowledgebase wherever appropriate.
- Follow the natural flow of conversation instead of sounding like a questionnaire. Pause for about two seconds after each question to keep the conversation flow natural.
- Use active listening—acknowledge responses and build on them.
- Handle objections smoothly—if the client is busy, offer to schedule a callback.
- Encourage open-ended responses—help clients share relevant details.
- Keep the chat focused—gather necessary details efficiently.
- Avoid saying "now", "next" word after every question.
- If the user pauses or thinking, or uses filler words like 'uhh' or 'umm', wait quietly. Do not interrupt.
- CRITICAL: Stick to the exact questions in the script. Do NOT ask additional questions that are not listed above.
- CRITICAL: After logo upload, acknowledge it and move to the next step. Do NOT ask about logos again.
- CRITICAL: Do NOT ask about colors, fonts, or styles unless specifically mentioned in the script above.
- CRITICAL: After logo upload, move directly to the wrap-up section. Do NOT ask any additional questions.
- CRITICAL: READ the conversation history carefully. If the customer has already provided information (size, material, location, etc.), ACKNOWLEDGE it and move to the next unanswered question.
- CRITICAL: Do NOT repeat questions that have already been answered in the conversation.
Conversation Flow:

1. Start the conversation with the following question:
 -Ask: "To ensure we can connect if disconnected, can you please share your email address?"
 Remember the email address
 After getting the email address, ask the following question:
 -Ask: "Could you please tell me a bit about what kind of sign you're looking for — and any other details you'd like us to know?"
 Listen to the customer's response and ask the next question based on the response.    

2. Gather Required Details:  
Use the following list of questions. Ask each question naturally in a conversational tone. DO NOT MISS ANY QUESTION.

Start the by saying: " To create an accurate mockup and quote, I just need a few more details."
Intelligently check the details from the conversation history and ask the questions accordingly.
Don't ask the same question again and again.

- Size & Dimensions:
Ask: "What are the desired measurements for the sign?". To keep the conversation engaging and realistic, add a short two-second pause after every question.
NOTE: If the customer mentions size in their initial description (e.g., "2 by 4 metal sign"), acknowledge this information and move to the next question.

- Material Preference (metal, acrylic):
Ask: "Do you have any material preferences for the sign — like metal, acrylic, or something else?"
NOTE: If the customer mentions material in their initial description (e.g., "2 by 4 metal sign"), acknowledge this information and move to the next question.

- Installation Surface:  
Ask: "Where will this sign be installed? On a brick wall, concrete, drywall, or another type of surface?"

- Deadline / Installation Date:  
Ask: "Our standard turnaround time is fifteen to seventeen business days. Do you have any deadlines or specific dates by which you need the sign to be delivered?"
Use the current date ({{date}}) to calculate delivery dates and intelligently handle the customer as per the below scenarios.
 
If the customer wants it in fifteen or more business days, say: "Perfect — we'll make sure it's delivered on time."
 
If the customer wants it sooner than fifteen days, say: "Our minimum turnaround time is twelve business days, but that is going to cost you twenty percent additional."

- Indoor or Outdoor Placement:  
  Ask: "Is the sign going to be installed indoors or outdoors?"

- City and State:
Ask: "In which city and state do you want the sign to be delivered?"

- Permit Assistance and Installation Services
Ask: "Do you need assistance with permit and installation?

- Budget Range:  
Ask: "Do you have a price point or a budget in mind for this sign?"

- Logo/Design Files:
After discussing the budget, ask: "Do you have any existing logo files or design elements you'd like to incorporate into your sign? If so, please email them to info@signize.us so our designers can work with your brand assets."
IMPORTANT: Move directly to the wrap-up section after asking about logos.
CRITICAL: Do NOT ask about colors, fonts, or styles after logo question. Move directly to wrap-up.

Use slang word as follows wherever you seems necessary, if the customer is professionally talking, do not use, if the conversation is casual, then use appropriate, also, be sure to acknowledge their answers positively, e.g.:
"Hey there!", "What's up?", "Totally get it!", "No worries!", "That makes sense!", "I feel you.", "Gotcha!", "All good!", "That's pretty sweet.", "Next-level stuff.", "Just wanna double-check...", "Lemme make sure I got this right...", "Alrighty!", "Catch you later!", "Talk soon!", "Cheers!", "Thanks a ton!", "That's perfect! Thank you for clarifying that."

3. Wrap-Up:
- Briefly summarize what they shared.
- Ask them "Any changes in the requirement?": if they say Yes, note the changes, but if they say No: Let them know our designers will create a mockup based on the gathered details.
- Tell them they can expect the mockup very shortly.
- Thank them warmly for their time.

Tone:
- Friendly and conversational, not robotic.
- Adjust based on how the customer responds.
- If asked for pricing before design confirmation:  
  "Once we finalize your design details, we'll send a personalized mockup along with pricing. Please expect the mockup within few hours."

Edge Cases & Objection Handling:

If they ask for pricing before confirming details:
"Pricing depends on the size, material, and customization, so once we finalize these details, our team will contact you with a mockup and can provide you with an accurate estimate."

If they are unsure about a detail:
"No worries! We can provide recommendations based on your needs." """

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

def generate_conversation_summary(client, messages):
    """Generate a summary of the conversation using LLM"""
    try:
        if not messages:
            return ""
        
        # Create summary prompt
        summary_prompt = f"""
        Analyze the following conversation and extract key information about the customer's sign requirements.
        
        INFORMATION TO EXTRACT:
        - Size and dimensions mentioned (e.g., "2 by 4 feet", "5x3", etc.)
        - Material preferences (e.g., "metal", "acrylic", "aluminum", etc.)
        - Installation surface (e.g., "brick wall", "concrete", "drywall", etc.)
        - Timeline/deadline (e.g., "in 90 days", "next month", etc.)
        - Indoor/outdoor placement
        - Location (city/state)
        - Budget information (e.g., "$1000", "around $500", etc.)
        - Email address
        - Logo files uploaded
        
        FORMAT YOUR RESPONSE AS:
        ✅ COLLECTED INFORMATION:
        - Size: [what was mentioned]
        - Material: [what was mentioned]
        - Installation: [what was mentioned]
        - Timeline: [what was mentioned]
        - Placement: [what was mentioned]
        - Location: [what was mentioned]
        - Budget: [what was mentioned]
        - Email: [what was mentioned]
        - Logos: [what was uploaded]
        
        ❌ STILL NEEDED:
        - [List specific questions that still need to be asked]
        
        Conversation:
        """
        
        for msg in messages:
            summary_prompt += f"\n{msg['role'].capitalize()}: {msg['content']}"
        
        summary_prompt += "\n\nProvide a structured summary following the format above:"
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that summarizes customer requirements from conversations. Be very specific about what information has been collected and what still needs to be gathered. Use the exact format requested."
                },
                {
                    "role": "user",
                    "content": summary_prompt
                }
            ],
            max_tokens=400,
            temperature=0.0
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        print(f"❌ Summary generation failed: {e}")
        return ""

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
        # Generate conversation summary for context
        conversation_summary = generate_conversation_summary(client, chat_sessions[session_id]["messages"][:-1])
        
        # Generate response using the Sign-nize system prompt with context
        response = generate_sign_nize_response(client, user_message, chat_sessions[session_id], conversation_summary)
        
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
        
        # Save locally only when conversation is complete or has many messages
        conversation_complete = (
            "thank you" in response.lower() or 
            "mockup" in response.lower() or 
            "designers will create" in response.lower() or
            "expect the mockup" in response.lower()
        )
        
        if conversation_complete or message_count >= 30:
            save_session_locally(session_id, chat_sessions[session_id]["messages"])
            print(f"✅ Session {session_id} saved locally (conversation complete or limit reached)")
        
        print(f"Generated response for session {session_id}:", response)
        return jsonify({
            "message": response,
            "session_id": session_id,
            "message_count": len(chat_sessions[session_id]["messages"]),
            "conversation_summary": conversation_summary
        })
        
    except Exception as e:
        print("Error in generate_sign_nize_response:", str(e))
        return jsonify({"message": f"Sorry, I encountered an error. Please try again."}), 500

def generate_sign_nize_response(client, user_message, session_data, conversation_summary=""):
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
    
    # Add conversation summary and critical instructions
    context_info = ""
    if conversation_summary:
        context_info = f"\n\nCONVERSATION SUMMARY (What we know so far):\n{conversation_summary}"
    
    # Add critical instructions for context awareness
    context_instructions = """
    
CRITICAL CONTEXT INSTRUCTIONS:
1. CAREFULLY READ the full conversation history above.
2. If the customer has already provided information (size, material, location, etc.), ACKNOWLEDGE it and move to the next unanswered question.
3. Do NOT ask questions that have already been answered.
4. Use the current date: """ + current_date + """ when discussing deadlines.
5. If the customer says "2 by 4 metal sign", you already know the size and material - acknowledge this and ask the next question.
6. Focus only on gathering the remaining information that hasn't been provided yet.
7. Be specific about what information you already have and what you still need.
"""
    
    # Combine all context
    full_prompt = system_prompt + context_info + context_instructions + conversation_context + f"\n\nCurrent User Message: {user_message}"
    
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

# Run the Flask app
if __name__ == "__main__":
    print("Starting Sign-nize Customer Support System...")
    app.run(host="0.0.0.0", port=5000, debug=True)
