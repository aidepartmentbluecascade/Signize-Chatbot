from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from environment import load_environment
from openai import OpenAI
import json
import os
from datetime import datetime
import time
import gspread
from mongodb_operations import mongodb_manager
import dropbox

# Load environment variables
openai_key = load_environment()

# Google Sheets configuration
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# Initialize Google Sheets client
sheets_client = None
worksheet = None
GOOGLE_SHEETS_ENABLED = False

try:
    from environment import get_google_credentials
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

# Initialize OpenAI Client
client = OpenAI(api_key=openai_key)

# Dropbox configuration
from dropbox_auth import create_dropbox_client

# Flask application setup
app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)

# Load production configuration
from environment import get_flask_config
flask_config = get_flask_config()
app.config['SECRET_KEY'] = flask_config['FLASK_SECRET_KEY']

# In-memory storage for chat sessions
chat_sessions = {}
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
- CRITICAL: When customers ask follow-up questions about signs, materials, or services, answer them directly and continue the conversation naturally.
- CRITICAL: Do NOT fall back to generic greetings like "How can I help you" when customers are asking specific questions about signs.
- CRITICAL: If a customer asks about different sign types (e.g., "2D acrylic will look good"), provide helpful comparison and advice.
- CRITICAL: When customers ask about specific sign types (e.g., "2D sign", "3D metal sign", "acrylic sign"), provide detailed information about those specific types.
- CRITICAL: NEVER respond with generic greetings when customers are asking about signs, materials, or services - always provide helpful, specific information.

Email Collection Process:
- CRITICAL: ALWAYS ask for the customer's email address on their FIRST message, regardless of what they say.
- Say: "Hi there! I'd be happy to help you with your sign needs. First, could you please provide your email address so I can save your information and follow up with you?"
- Do NOT proceed with any other responses until email is collected.
- After email is collected, ask "How can I help you with your sign needs today?"
- CRITICAL: Once email is collected, NEVER ask for it again in the same conversation.
- CRITICAL: If customer says "Hi" or similar greeting and email is already collected, respond with "Hello! How can I help you with your sign needs today?" - DO NOT ask for email again.
- CRITICAL: Even if the conversation seems to restart or customer says "Hi" again, if you already have their email, do NOT ask for it again.
- CRITICAL: Email persists throughout the entire session - if customer says "bye" and then starts talking again, they still have the same email address.
- CRITICAL: Only ask for email again if this is a completely new session or if the email was never collected.

 CRITICAL: Phone number process:
-If customer asks for call or any other related message, ask for their PHONE NUMBER.
-If customer provides their phone number, save it in the session.
-If customer does not provide their phone number, ask for it again.
-If customer says "I need to speak with a sign expert immediately. Can you connect me?" or similar message, ask for their phone number.
-If customer mentions "call me", "call you", "speak to someone", "talk to someone", "human", "representative", "expert", "agent", or similar phrases, ask for their phone number.
-When asking for phone number, say: "I'd be happy to have someone call you! Could you please provide your phone number so I can have a sign expert reach out to you?"
-Only ask for phone number once per session - if already collected, do not ask again.
-CRITICAL: When asking for phone number, ALWAYS include [PHONE_NUMBER_TRIGGER] in your response to trigger the phone number popup.

EXACT PHONE NUMBER TRIGGER PHRASES - ALWAYS ASK FOR PHONE:
- "call me" or "call you"
- "speak to someone" or "talk to someone"
- "human" or "representative" or "expert" or "agent"
- "I need to speak with someone"
- "I want to talk to a person"
- "Can someone call me?"
- "I need help from a human"
- "Connect me with someone"
- "I want to speak with an expert"
- ANY variation of the above phrases

PHONE NUMBER RESPONSE FORMAT:
"I'd be happy to have someone call you! Could you please provide your phone number so I can have a sign expert reach out to you?"

Then include this special marker in your response: [PHONE_NUMBER_TRIGGER]

CRITICAL: If phone number is already collected in the session, DO NOT ask for it again. Instead, respond with:
"I'd be happy to have someone call you! I have your phone number on file and will have a sign expert reach out to you shortly. Is there anything else I can help you with regarding your sign needs?"


SESSION MANAGEMENT & EMAIL PERSISTENCE:
- Email addresses are collected once per session and persist throughout the entire conversation
- If a customer says "bye", "goodbye", or similar closing phrases, the email is still remembered
- When the customer starts talking again in the same session, greet them warmly but do NOT ask for email again
- The email address is stored in the session and should be used for all subsequent interactions
- Only reset email collection if the session is completely new or if there's a technical issue
- This prevents the frustrating experience of asking for email multiple times in one session

Quote/Mockup Process:
CRITICAL: When a customer mentions they want a "mockup" or "quote" AND has already provided their email address, ALWAYS trigger the quote form.

EXACT TRIGGER PHRASES - ALWAYS TRIGGER FORM:
- "I want a mockup" or "I want a quote"
- "I need a mockup" or "I need a quote" 
- "get a mockup" or "get a quote"
- "want pricing" or "need pricing"
- "want estimate" or "need estimate"
- "I want to share details" or "I need to provide information"
- ANY variation of the above phrases

RESPONSE FORMAT:
"I'd be happy to help you get a quote and create a mockup! I'll need to collect some specific details from you. Let me open a form for you to fill out with all the necessary information."

Then trigger the quote form by including this special marker in your response: [QUOTE_FORM_TRIGGER]

CRITICAL: If customer says ANYTHING about wanting a mockup, quote, pricing, or estimate - TRIGGER THE FORM IMMEDIATELY.

SPECIFIC EXAMPLES THAT MUST TRIGGER FORM:
- "I want a mockup and quote for a custom sign" → TRIGGER FORM
- "I need pricing" → TRIGGER FORM  
- "I want to get a quote" → TRIGGER FORM
- "I need an estimate" → TRIGGER FORM
- ANY mention of mockup, quote, pricing, or estimate → TRIGGER FORM

QUOTE UPDATE PROCESS:
When customers want to update or modify their existing quote:
- If they say "update", "modify", "change", "edit", "revise", "adjust" their quote
- If they want to "make changes" or "update the form"
- If they need to "fill out the form again" with new details
- ALWAYS trigger the quote form with [QUOTE_FORM_TRIGGER] and say:
"I'd be happy to help you update your quote! Let me open the form again so you can modify your details."

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

SPECIFIC SIGN TYPES - ALWAYS RELEVANT:
- 3D metal signs, 2D metal signs, acrylic signs, vinyl signs, LED signs, neon signs
- Channel letters, backlit signs, illuminated signs, non-illuminated signs
- Wall signs, building signs, storefront signs, directional signs
- Any question about specific sign types, materials, or installation methods

SIGN TYPE QUESTION HANDLING:
- When customers ask about specific sign types (e.g., "2D sign", "3D metal sign", "acrylic sign"), provide detailed information about:
  * What that sign type is and how it works
  * Materials commonly used for that type
  * Typical applications and use cases
  * Advantages and considerations
  * Pricing factors
- Do NOT redirect to generic greetings - provide specific, helpful information
- Use the knowledge base to give comprehensive answers about sign types

EXAMPLES OF PROPER RESPONSES:
- Customer asks "2D sign" → Explain what 2D signs are, materials used, applications, benefits
- Customer asks "3D metal sign" → Explain 3D metal signs, depth, materials, durability, uses
- Customer asks "acrylic sign" → Explain acrylic signs, transparency, indoor/outdoor use, cost
- NEVER respond with "How can I help you" when they're asking about specific sign types

RESTAURANT SIGNAGE GUIDANCE:
- For restaurant signage, consider factors like:
  * 2D acrylic signs: Clean, modern look, great for indoor/outdoor, cost-effective
  * 3D metal signs: Premium appearance, excellent durability, higher cost
  * LED backlit signs: Great visibility at night, energy-efficient
  * Vinyl graphics: Flexible for windows, easy to update, budget-friendly
- Always provide helpful comparisons when customers ask about different materials
- Consider restaurant atmosphere, budget, and location when making recommendations

After Order Issues:
When customers complete order tracking and then ask about general sign information, provide detailed answers about the specific topics they're asking about. Do not redirect them to ask "how can I help you" again.

CRITICAL: If a customer has completed an order issue (provided Order ID and phone number) and then asks about signs, materials, lighting, or any other general sign-related topics, provide helpful information about those specific topics. Do NOT ask "How can I help you" or redirect them - just answer their question directly.

IRRELEVANT QUESTIONS HANDLING:
- If customers ask questions completely unrelated to signs, signage, business, or customer service (e.g., weather, politics, personal advice, sports, entertainment, etc.), respond with:
"I'm sorry, but I'm specifically trained to help with signage-related questions and customer support for Signize. I can't provide information on that topic. Is there something about signs, materials, installation, or our services that I can help you with?"

- IMPORTANT: The following topics are ALWAYS relevant and should be answered helpfully:
  * Any type of sign (3D, 2D, metal, acrylic, vinyl, LED, neon, channel letters, etc.)
  * Sign materials (metal, acrylic, vinyl, wood, etc.)
  * Sign installation and mounting
  * Sign pricing, quotes, and estimates
  * Sign design and customization
  * Sign lighting and illumination
  * Sign maintenance and repair
  * Business signage and branding
  * Any question containing words like "sign", "signs", "3D", "metal", "acrylic", "vinyl", "LED", "neon", "installation", "mounting", "materials", "pricing", "quote", "design", "custom", "lighting", "illumination"

- Keep responses professional but redirect truly irrelevant topics back to signage-related topics.

GOODBYE HANDLING:
- When customers say "bye", "goodbye", "thank you", "that's all", or similar closing phrases, respond with:
"Thank you for choosing Signize! It was a pleasure helping you today. If you have any more questions about signs or need assistance in the future, feel free to reach out. Have a great day!"
- Always end conversations warmly and professionally.

Tone:
- Friendly and conversational, not robotic.
- Adjust based on how the customer responds.
- Professional but approachable.

Edge Cases & Objection Handling:

If they ask for pricing before getting a quote:
"Pricing depends on the size, material, and customization. Would you like me to help you get a quote? I can collect your requirements and provide you with an accurate estimate."

If they are unsure about details:
"No worries! I can help you figure out what would work best for your needs. Let me know what you're looking for and I'll guide you through the options."

MATERIAL COMPARISON HANDLING:
- When customers ask about different materials (e.g., "2D acrylic vs 3D metal"), provide helpful comparisons
- Consider factors like cost, durability, appearance, and suitability for their specific use case
- Always answer material questions directly - do NOT redirect to generic responses
- Provide specific advice based on their needs (restaurant, office, retail, etc.) """

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
        
        # Get logo URLs from session data and add to conversation
        logo_urls = []
        if session_id in chat_sessions and "logos" in chat_sessions[session_id]:
            for logo in chat_sessions[session_id]["logos"]:
                if "dropbox_url" in logo:
                    logo_urls.append(logo["dropbox_url"])
        
        # Add logo URLs to conversation if available
        if logo_urls:
            conversation_text += "\n\n--- LOGO FILES ---\n"
            for i, url in enumerate(logo_urls, 1):
                conversation_text += f"Logo {i}: {url}\n"
        
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
                    # Get existing conversation and append new messages
                    existing_conversation = ""
                    if len(row_data) > 4:  # Make sure conversation column exists
                        existing_conversation = row_data[4] if row_data[4] else ""
                    
                    # Append new messages to existing conversation
                    updated_conversation = existing_conversation
                    if existing_conversation:
                        updated_conversation += "\n\n--- New Messages ---\n"
                    
                    # Add only the new messages (messages after the existing count)
                    existing_count = int(row_data[3]) if len(row_data) > 3 and row_data[3].isdigit() else 0
                    new_messages = chat_history[existing_count:]
                    
                    for msg in new_messages:
                        role = msg.get("role", "unknown")
                        content = msg.get("content", "")
                        if role == "user":
                            updated_conversation += f"\n👤 User: {content}"
                        elif role == "assistant":
                            updated_conversation += f"\n🤖 Assistant: {content}"
                    
                    # Get logo URLs and add to conversation if not already present
                    logo_urls = []
                    if session_id in chat_sessions and "logos" in chat_sessions[session_id]:
                        for logo in chat_sessions[session_id]["logos"]:
                            if "dropbox_url" in logo:
                                logo_urls.append(logo["dropbox_url"])
                    
                    # Add logo URLs if available and not already in conversation
                    if logo_urls and "--- LOGO FILES ---" not in updated_conversation:
                        updated_conversation += "\n\n--- LOGO FILES ---\n"
                        for i, url in enumerate(logo_urls, 1):
                            updated_conversation += f"Logo {i}: {url}\n"
                    
                    # Update the row with new conversation and message count
                    updated_row = [
                        session_data["session_id"],
                        session_data["email"],
                        session_data["timestamp"],
                        session_data["message_count"],
                        updated_conversation,
                        session_data["status"]
                    ]
                    
                    worksheet.update(f'A{session_row}:F{session_row}', [updated_row])
                    print(f"✅ Session {session_id} updated in Google Sheets (row {session_row}) - {len(new_messages)} new messages added")
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
                return False
        
    except Exception as e:
        print(f"⚠️  Google Sheets save failed: {e}")
        return False

def validate_email(email):
    """Validate email format"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def send_to_n8n_webhook(session_id, email, phone_number):
    """Send user data to n8n webhook after phone number collection"""
    import requests
    from requests.auth import HTTPBasicAuth
    
    webhook_url = "https://arslanalvi.app.n8n.cloud/webhook/signize-ic"
    username = "info@signize.us"
    password = "Bluecascade.org786"
    
    # Prepare webhook data
    webhook_data = {
        "session_id": session_id,
        "email": email,
        "phone_number": phone_number,
        "timestamp": datetime.now().isoformat(),
        "source": "chromabot_phone_collection",
        "event_type": "phone_number_collected"
    }
    
    try:
        print(f"📡 Sending webhook to n8n: {webhook_url}")
        print(f"📊 Webhook data: {webhook_data}")
        print(f"🔐 Using auth: {username}")
        
        response = requests.post(
            webhook_url,
            json=webhook_data,
            auth=HTTPBasicAuth(username, password),
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'ChromaBot/1.0',
                'Accept': 'application/json'
            },
            timeout=30
        )
        
        print(f"📡 Webhook response status: {response.status_code}")
        print(f"📡 Webhook response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print(f"✅ Webhook sent successfully to n8n: {response.status_code}")
            try:
                response_data = response.json()
                print(f"📊 Webhook response data: {response_data}")
            except:
                print(f"📊 Webhook response text: {response.text}")
            return True
        else:
            print(f"⚠️  Webhook failed with status {response.status_code}")
            print(f"📄 Response text: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"⏰ Webhook request timed out after 30 seconds")
        return False
    except requests.exceptions.ConnectionError:
        print(f"🔌 Webhook connection error - network or DNS issue")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Webhook request failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected webhook error: {e}")
        return False

# Route to serve the chatbot UI
@app.route("/")
def index():
    """Serve the main chatbot page (index.html)."""
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
            "email": email,
            "phone_number": ""
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
        
        # Check if response contains phone number trigger
        phone_number_triggered = "[PHONE_NUMBER_TRIGGER]" in response
        if phone_number_triggered:
            response = response.replace("[PHONE_NUMBER_TRIGGER]", "")
            
            # Trigger webhook for every call request (not just first collection)
            # This ensures the webhook fires on every call request, even if phone number already exists
            if chat_sessions[session_id].get("email") and chat_sessions[session_id].get("phone_number"):
                print(f"📱 Call request detected - triggering webhook for existing phone number")
                webhook_result = send_to_n8n_webhook(
                    session_id, 
                    chat_sessions[session_id].get("email", ""), 
                    chat_sessions[session_id].get("phone_number", "")
                )
                print(f"📱 Webhook result for call request: {webhook_result}")
            else:
                print(f"📱 Call request detected but missing email or phone number - webhook will be triggered when phone is collected")
        
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
            print(f"📊 Updating Google Sheets for session {session_id}: {message_count} messages, update_existing={update_existing}")
            success = save_session_to_sheets(session_id, chat_sessions[session_id]["email"], chat_sessions[session_id]["messages"], update_existing)
            if success and session_id not in saved_sessions:
                saved_sessions.add(session_id)
                print(f"✅ Session {session_id} added to saved_sessions")
            elif success:
                print(f"✅ Session {session_id} updated in Google Sheets")
        else:
            print(f"⚠️  No email available for session {session_id}, skipping Google Sheets update")
        
        # Save chat session to database
        try:
            db_result = mongodb_manager.save_chat_session(
                session_id, 
                chat_sessions[session_id].get("email", ""), 
                chat_sessions[session_id]["messages"],
                chat_sessions[session_id].get("phone_number", "")
            )
            if db_result["success"]:
                print(f"✅ Chat session saved to database: {db_result['action']}")
            else:
                print(f"⚠️  Failed to save chat session to database: {db_result.get('error', 'Unknown error')}")
        except Exception as db_error:
            print(f"❌ Database save error: {db_error}")
        
        print(f"Generated response for session {session_id}:", response)
        return jsonify({
            "message": response,
            "session_id": session_id,
            "message_count": len(chat_sessions[session_id]["messages"]),
            "quote_form_triggered": quote_form_triggered,
            "phone_number_triggered": phone_number_triggered
        })
        
    except Exception as e:
        print("Error in generate_sign_nize_response:", str(e))
        return jsonify({"message": f"Sorry, I encountered an error. Please try again."}), 500

def generate_sign_nize_response(client, user_message, session_data):
    """Generate response using the Sign-nize customer support system prompt with context awareness"""
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
    
    # Add email information to the system prompt
    email_context = ""
    if email_value:
        email_context = f"""
CURRENT SESSION EMAIL: {email_value}
- This email has already been collected and verified
- Do NOT ask for email again in this session
- Use this email for all quote requests and order tracking
- If customer says "bye" and then starts talking again, they still have the same email
"""
        print(f"📧 Email context injected: {email_value}")
    else:
        email_context = """
CURRENT SESSION EMAIL: NOT COLLECTED
- This is a new conversation or email not yet provided
- Follow the email collection process for first message
"""
        print("📧 Email context: NOT COLLECTED")
    
    # Add phone number information to the system prompt
    phone_context = ""
    if session_data.get("phone_number"):
        phone_context = f"""
CURRENT SESSION PHONE: {session_data.get("phone_number")}
- This phone number has already been collected
- Do NOT ask for phone number again in this session
- Use this phone number for call requests and order tracking
"""
        print(f"📱 Phone context injected: {session_data.get('phone_number')}")
    else:
        phone_context = """
CURRENT SESSION PHONE: NOT COLLECTED
- Phone number not yet provided
- Ask for phone number when customer wants to speak with someone or get a call
"""
        print("📱 Phone context: NOT COLLECTED")
    
    print(f"🔍 Email already collected: {email_already_collected}")
    print(f"📧 Email value: {email_value}")
    
    # Add simplified context instructions
    context_instructions = f"""
    
CONTEXT INSTRUCTIONS:
1. CAREFULLY READ the full conversation history above.
2. If this is the customer's FIRST message in the conversation, ALWAYS ask for email first.
3. If email is already collected, NEVER ask for it again - this is a CRITICAL rule.
4. After email collection, ask "How can I help you with your sign needs today?"
5. Handle order issues by collecting Order ID and phone number, then tell customer representative will contact them.
6. For general sign questions after order issues, provide helpful information without asking "How can I help you" again.
7. CRITICAL: Trigger quote form with [QUOTE_FORM_TRIGGER] when customer says ANYTHING about wanting mockup, quote, pricing, or estimate - this is a TOP PRIORITY.
8. CRITICAL: Even if customer says "Hi" again after email collection, do NOT ask for email - just say "Hello! How can I help you with your sign needs today?"
9. CRITICAL: When customer wants to update/modify their quote, ALWAYS trigger the form with [QUOTE_FORM_TRIGGER].
10. CRITICAL: For irrelevant questions (weather, politics, etc.), redirect to signage topics professionally.
11. CRITICAL: For goodbye messages, give warm Signize farewell.
12. CRITICAL: Questions about signs, materials, installation, pricing, etc. are ALWAYS relevant - answer them helpfully.
13. CRITICAL: When customers ask about specific sign types (2D, 3D, metal, acrylic, etc.), provide detailed information about those types - NEVER give generic greetings.
14. CRITICAL: Use the knowledge base to provide comprehensive answers about sign types, materials, and applications.
15. CRITICAL: The email {email_value if email_value else 'has not been collected yet'} - use this information to determine if email collection is needed.
16. CRITICAL: Email persists throughout the session - if customer says "bye" and then talks again, they still have the same email.
17. CRITICAL: Only ask for email if this is a completely new session or if email was never collected.
18. CRITICAL: When customer mentions wanting to speak with someone, get a call, or talk to a human/expert, ask for their phone number and include [PHONE_NUMBER_TRIGGER] in your response.
19. CRITICAL: Phone number collection is triggered by phrases like "call me", "speak to someone", "human", "representative", "expert", "agent", etc.
20. CRITICAL: Only ask for phone number once per session - if already collected, do NOT ask again.
21. CRITICAL: If phone number already exists in session, acknowledge the request and confirm you'll have someone call them using their existing number.
22. CRITICAL: NEVER ask for phone number again if it's already been collected in the current session.
"""
    
    # Combine all context
    full_prompt = system_prompt + email_context + phone_context + context_instructions + conversation_context + f"\n\nCurrent User Message: {user_message}"
    
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
        # Save to MongoDB
        result = mongodb_manager.save_quote_data(session_id, email, form_data)
        
        # Update Google Sheets with the latest session data (including logo URLs)
        if result["success"] and session_id in chat_sessions:
            try:
                # Force update Google Sheets with current session data
                update_existing = session_id in saved_sessions
                save_session_to_sheets(session_id, email, chat_sessions[session_id]["messages"], update_existing)
                print(f"✅ Google Sheets updated with latest session data for {session_id}")
            except Exception as sheet_error:
                print(f"⚠️  Failed to update Google Sheets: {sheet_error}")
        
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

# Route to upload logo files
@app.route("/upload-logo", methods=["POST"])
def upload_logo():
    print(">>> Upload logo endpoint hit")
    
    try:
        if 'logo' not in request.files:
            return jsonify({"success": False, "message": "No logo file provided"}), 400
        
        file = request.files['logo']
        session_id = request.form.get('session_id')
        
        if file.filename == '':
            return jsonify({"success": False, "message": "No file selected"}), 400
        
        if not session_id:
            return jsonify({"success": False, "message": "Session ID required"}), 400
        
        # Validate file type
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'svg', 'pdf'}
        file_extension = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        
        if file_extension not in allowed_extensions:
            return jsonify({"success": False, "message": f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}"}), 400
        
        # Upload directly to Dropbox without saving locally
        try:
            filename = f"logo_{int(time.time())}_{file.filename}"
            dropbox_path = f"/logos/{session_id}/{filename}"
            
            # Create Dropbox client with proper authentication
            dbx = create_dropbox_client()
            if not dbx:
                print("❌ Failed to create Dropbox client")
                return jsonify({"success": False, "message": "Failed to connect to Dropbox"}), 500
            
            # Upload file directly from memory
            file_content = file.read()
            dbx.files_upload(file_content, dropbox_path, mode=dropbox.files.WriteMode.overwrite)
            print(f"✅ Uploaded to Dropbox: {dropbox_path}")
            
            # Create a shared link
            try:
                link_metadata = dbx.sharing_create_shared_link_with_settings(dropbox_path)
            except dropbox.exceptions.ApiError as e:
                # If link already exists, fetch it
                if isinstance(e.error, dropbox.sharing.CreateSharedLinkWithSettingsError):
                    links = dbx.sharing_list_shared_links(dropbox_path).links
                    if links:
                        link_metadata = links[0]
                    else:
                        raise
                else:
                    raise
            
            # Modify link to make it direct-download
            dropbox_url = link_metadata.url.replace("?dl=0", "?dl=1")
            print(f"✅ Created shared link: {dropbox_url}")
            
            # Store logo info in session
            logo_info = {
                "filename": filename,
                "dropbox_url": dropbox_url,
                "upload_time": datetime.now().isoformat()
            }
            
            # Store in session
            if session_id not in chat_sessions:
                chat_sessions[session_id] = {"logos": []}
            elif "logos" not in chat_sessions[session_id]:
                chat_sessions[session_id]["logos"] = []
            
            chat_sessions[session_id]["logos"].append(logo_info)
            
            return jsonify({
                "success": True,
                "message": f"Logo uploaded successfully: {filename}",
                "dropbox_url": dropbox_url,
                "logo_count": len(chat_sessions[session_id]["logos"])
            })
            
        except Exception as dropbox_error:
            print(f"❌ Dropbox upload failed: {dropbox_error}")
            return jsonify({"success": False, "message": f"Failed to upload to Dropbox: {str(dropbox_error)}"}), 500
        
    except Exception as e:
        print(f"❌ Upload logo error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": f"Upload failed: {str(e)}"}), 500

# Route to save phone number
@app.route("/save-phone", methods=["POST"])
def save_phone():
    print(">>> Save phone endpoint hit")
    data = request.json
    session_id = data.get("session_id")
    phone_number = data.get("phone_number")
    
    if not session_id or not phone_number:
        return jsonify({"error": "Session ID and phone number are required"}), 400
    
    try:
        # Save phone number to database
        result = mongodb_manager.update_phone_number(session_id, phone_number)
        
        if result["success"]:
            # Also update in-memory session
            if session_id in chat_sessions:
                chat_sessions[session_id]["phone_number"] = phone_number
            
            # Send webhook to n8n
            webhook_result = send_to_n8n_webhook(session_id, chat_sessions[session_id].get("email", ""), phone_number)
            
            return jsonify({
                "success": True,
                "message": "Phone number saved successfully",
                "webhook_sent": webhook_result
            })
        else:
            return jsonify({"error": result["error"]}), 500
    except Exception as e:
        return jsonify({"error": f"Failed to save phone number: {str(e)}"}), 500

# Route to get phone number for a session
@app.route("/get-phone/<session_id>", methods=["GET"])
def get_phone(session_id):
    print(f">>> Get phone endpoint hit for session {session_id}")
    
    try:
        result = mongodb_manager.get_phone_number(session_id)
        if result["success"]:
            return jsonify({"phone_number": result["phone_number"]})
        else:
            return jsonify({"phone_number": None})
    except Exception as e:
        return jsonify({"error": f"Failed to get phone number: {str(e)}"}), 500

# Route to get session messages
@app.route("/session/<session_id>/messages", methods=["GET"])
def get_session_messages(session_id):
    print(f">>> Get session messages endpoint hit for session {session_id}")
    
    try:
        # First try to get from database
        result = mongodb_manager.get_chat_session(session_id)
        
        if result["success"]:
            session_data = result["session"]
            messages = session_data.get("messages", [])
            email = session_data.get("email", "")
            
            # Also update in-memory session for consistency
            if session_id not in chat_sessions:
                chat_sessions[session_id] = {
                    "messages": messages,
                    "email": email,
                    "context_history": [],
                    "conversation_state": "initial",
                    "customer_info": {},
                    "phone_number": session_data.get("phone_number", "")
                }
            else:
                chat_sessions[session_id]["messages"] = messages
                chat_sessions[session_id]["email"] = email
                chat_sessions[session_id]["phone_number"] = session_data.get("phone_number", "")
            
            return jsonify({
                "success": True,
                "messages": messages,
                "email": email,
                "phone_number": session_data.get("phone_number", ""),
                "message_count": len(messages)
            })
        else:
            # Fallback to in-memory session
            if session_id in chat_sessions and "messages" in chat_sessions[session_id]:
                messages = chat_sessions[session_id]["messages"]
                email = chat_sessions[session_id].get("email", "")
                phone_number = chat_sessions[session_id].get("phone_number", "")
                return jsonify({
                    "success": True,
                    "messages": messages,
                    "email": email,
                    "phone_number": phone_number,
                    "message_count": len(messages)
                })
            else:
                # No session found
                return jsonify({
                    "success": False,
                    "messages": [],
                    "email": "",
                    "message_count": 0,
                    "message": "Session not found"
                })
    except Exception as e:
        print(f"❌ Error getting session messages: {str(e)}")
        return jsonify({"error": f"Failed to get session messages: {str(e)}"}), 500

# Route to get logos for a session
@app.route("/session/<session_id>/logos", methods=["GET"])
def get_session_logos(session_id):
    print(f">>> Get logos endpoint hit for session {session_id}")
    
    try:
        # Get logos from session data (which includes Dropbox URLs)
        if session_id in chat_sessions and "logos" in chat_sessions[session_id]:
            logos = chat_sessions[session_id]["logos"]
            return jsonify({"logos": logos})
        else:
            # No local files - only Dropbox URLs are stored
            return jsonify({"logos": []})
    except Exception as e:
        return jsonify({"error": f"Failed to get logos: {str(e)}"}), 500

# Route to test n8n webhook connection
@app.route("/test-webhook", methods=["GET"])
def test_webhook():
    """Test the n8n webhook connection"""
    print(">>> Test webhook endpoint hit")
    
    try:
        # Test webhook with sample data
        test_result = send_to_n8n_webhook(
            "test_session_123", 
            "test@example.com", 
            "+1234567890"
        )
        
        if test_result:
            return jsonify({
                "success": True,
                "message": "Webhook test successful",
                "webhook_url": "https://arslanalvi.app.n8n.cloud/webhook/signize-ic",
                "status": "connected"
            })
        else:
            return jsonify({
                "success": False,
                "message": "Webhook test failed",
                "webhook_url": "https://arslanalvi.app.n8n.cloud/webhook/signize-ic",
                "status": "failed"
            })
            
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Webhook test error: {str(e)}",
            "webhook_url": "https://arslanalvi.app.n8n.cloud/webhook/signize-ic",
            "status": "error"
        }), 500

# Run the Flask app
if __name__ == "__main__":
    print("Starting Sign-nize Customer Support System...")
    # Use environment variables for production settings
    debug_mode = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(host="0.0.0.0", port=5000, debug=debug_mode)
