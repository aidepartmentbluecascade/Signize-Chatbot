#!/usr/bin/env python3
"""
API Service for Signize Chatbot
Single endpoint that handles all functionality with just a session ID
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import uuid
from datetime import datetime
import time
import gspread
from google.oauth2.service_account import Credentials
from openai import OpenAI
import dropbox
from pymongo import MongoClient
import base64
import io

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configuration
OPENAI_API_KEY = "your_openai_api_key_here"
DROPBOX_ACCESS_TOKEN = "your_dropbox_token_here"
MONGODB_URI = "your_mongodb_uri_here"
GOOGLE_SHEETS_ID = "your_google_sheets_id_here"

# Initialize clients
openai_client = OpenAI(api_key=OPENAI_API_KEY)
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
mongo_client = MongoClient(MONGODB_URI)
db = mongo_client['signize_bot']
quotes_collection = db['quotes']

# Google Sheets setup
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
creds = Credentials.from_service_account_file('credentials.json', scopes=SCOPES)
sheets_client = gspread.authorize(creds)
worksheet = sheets_client.open_by_key(GOOGLE_SHEETS_ID).sheet1

# In-memory storage (in production, use Redis or database)
sessions = {}
saved_sessions = set()

# System prompt for the AI
SYSTEM_PROMPT = """You are an AI-powered Customer Support Representative for Signize, a company specializing in custom sign design and production.

Your job is to provide excellent customer support for general signage queries and help customers get quotes/mockups when requested.

Key Rules:
1. ALWAYS ask for email on first message
2. Never ask for email again once collected
3. Trigger quote form when customer wants quote/mockup
4. Handle order tracking requests
5. Be professional and helpful

Quote Form Trigger: Include [QUOTE_FORM_TRIGGER] in response when customer wants quote."""

def generate_session_id():
    """Generate unique session ID"""
    return f"session_{int(time.time())}_{uuid.uuid4().hex[:8]}"

def save_to_google_sheets(session_id, email, messages, logos=None):
    """Save session data to Google Sheets"""
    try:
        # Format conversation
        conversation = ""
        for msg in messages:
            role = "👤 User" if msg["role"] == "user" else "🤖 Assistant"
            conversation += f"{role}: {msg['content']}\n"
        
        # Add logo URLs if available
        if logos:
            conversation += "\n--- LOGO FILES ---\n"
            for i, logo in enumerate(logos, 1):
                conversation += f"Logo {i}: {logo['url']}\n"
        
        # Prepare row data
        row = [
            session_id,
            email,
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            len(messages),
            conversation,
            "active"
        ]
        
        # Check if session exists
        all_values = worksheet.get_all_values()
        session_row = None
        
        for i, row_data in enumerate(all_values):
            if row_data and len(row_data) > 0 and row_data[0] == session_id:
                session_row = i + 1
                break
        
        if session_row:
            # Update existing row
            worksheet.update(f'A{session_row}:F{session_row}', [row])
        else:
            # Add new row
            worksheet.append_row(row)
            saved_sessions.add(session_id)
        
        return True
    except Exception as e:
        print(f"Google Sheets error: {e}")
        return False

def save_quote_to_mongodb(session_id, email, quote_data):
    """Save quote data to MongoDB"""
    try:
        quote_doc = {
            "session_id": session_id,
            "email": email,
            "form_data": quote_data,
            "created_at": datetime.now(),
            "status": "new"
        }
        
        # Check if quote exists
        existing = quotes_collection.find_one({"session_id": session_id})
        if existing:
            quotes_collection.update_one(
                {"session_id": session_id},
                {"$set": {"form_data": quote_data, "updated_at": datetime.now()}}
            )
        else:
            quotes_collection.insert_one(quote_doc)
        
        return True
    except Exception as e:
        print(f"MongoDB error: {e}")
        return False

def upload_file_to_dropbox(file_data, filename, session_id):
    """Upload file to Dropbox and return public URL"""
    try:
        # Decode base64 file data
        file_bytes = base64.b64decode(file_data)
        
        # Upload to Dropbox
        dropbox_path = f"/logos/{session_id}/{filename}"
        dbx.files_upload(file_bytes, dropbox_path, mode=dropbox.files.WriteMode.overwrite)
        
        # Create shared link
        try:
            link_metadata = dbx.sharing_create_shared_link_with_settings(dropbox_path)
        except:
            links = dbx.sharing_list_shared_links(dropbox_path).links
            link_metadata = links[0] if links else None
        
        if link_metadata:
            url = link_metadata.url.replace("?dl=0", "?dl=1")
            return url
        return None
    except Exception as e:
        print(f"Dropbox upload error: {e}")
        return None

def generate_ai_response(messages, email=None):
    """Generate AI response using OpenAI"""
    try:
        # Build conversation context
        conversation_context = ""
        for msg in messages:
            role = "User" if msg["role"] == "user" else "Assistant"
            conversation_context += f"{role}: {msg['content']}\n"
        
        # Add email context
        email_context = f"\nCurrent Email: {email}" if email else "\nEmail: Not collected"
        
        # Create full prompt
        full_prompt = SYSTEM_PROMPT + email_context + "\n\nConversation:\n" + conversation_context
        
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": full_prompt},
                {"role": "user", "content": messages[-1]["content"]}
            ],
            max_tokens=300,
            temperature=0.0
        )
        
        return response.choices[0].message.content
    except Exception as e:
        print(f"OpenAI error: {e}")
        return "Sorry, I encountered an error. Please try again."

@app.route('/api/chatbot', methods=['POST'])
def chatbot_api():
    """
    Main API endpoint for all chatbot functionality
    
    Expected JSON payload:
    {
        "session_id": "optional_session_id",  // If not provided, new session created
        "action": "chat|upload|quote|get_quote",  // Required action
        "message": "user message",  // Required for chat action
        "email": "user@example.com",  // Optional, can be collected during chat
        "files": [  // Required for upload action
            {
                "filename": "logo.png",
                "data": "base64_encoded_file_data"
            }
        ],
        "quote_data": {  // Required for quote action
            "size": "2x3 feet",
            "material": "3D metal",
            // ... other quote fields
        }
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        action = data.get("action")
        if not action:
            return jsonify({"error": "Action is required"}), 400
        
        # Get or create session
        session_id = data.get("session_id")
        if not session_id:
            session_id = generate_session_id()
            sessions[session_id] = {
                "messages": [],
                "email": None,
                "logos": []
            }
        
        # Initialize session if not exists
        if session_id not in sessions:
            sessions[session_id] = {
                "messages": [],
                "email": None,
                "logos": []
            }
        
        session = sessions[session_id]
        
        # Handle different actions
        if action == "chat":
            return handle_chat_action(data, session_id, session)
        elif action == "upload":
            return handle_upload_action(data, session_id, session)
        elif action == "quote":
            return handle_quote_action(data, session_id, session)
        elif action == "get_quote":
            return handle_get_quote_action(session_id)
        else:
            return jsonify({"error": "Invalid action"}), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def handle_chat_action(data, session_id, session):
    """Handle chat messages"""
    message = data.get("message")
    if not message:
        return jsonify({"error": "Message is required for chat action"}), 400
    
    # Update email if provided
    email = data.get("email")
    if email:
        session["email"] = email
    
    # Add user message
    session["messages"].append({"role": "user", "content": message})
    
    # Generate AI response
    ai_response = generate_ai_response(session["messages"], session["email"])
    
    # Add AI response
    session["messages"].append({"role": "assistant", "content": ai_response})
    
    # Save to Google Sheets
    save_to_google_sheets(session_id, session["email"], session["messages"], session["logos"])
    
    # Check if quote form should be triggered
    quote_form_triggered = "[QUOTE_FORM_TRIGGER]" in ai_response
    if quote_form_triggered:
        ai_response = ai_response.replace("[QUOTE_FORM_TRIGGER]", "")
    
    return jsonify({
        "session_id": session_id,
        "response": ai_response,
        "quote_form_triggered": quote_form_triggered,
        "message_count": len(session["messages"]),
        "email": session["email"]
    })

def handle_upload_action(data, session_id, session):
    """Handle file uploads"""
    files = data.get("files")
    if not files:
        return jsonify({"error": "Files are required for upload action"}), 400
    
    uploaded_files = []
    
    for file_info in files:
        filename = file_info.get("filename")
        file_data = file_info.get("data")
        
        if not filename or not file_data:
            continue
        
        # Upload to Dropbox
        dropbox_url = upload_file_to_dropbox(file_data, filename, session_id)
        
        if dropbox_url:
            logo_info = {
                "filename": filename,
                "url": dropbox_url,
                "upload_time": datetime.now().isoformat()
            }
            session["logos"].append(logo_info)
            uploaded_files.append(logo_info)
    
    # Update Google Sheets with new logos
    save_to_google_sheets(session_id, session["email"], session["messages"], session["logos"])
    
    return jsonify({
        "session_id": session_id,
        "uploaded_files": uploaded_files,
        "total_logos": len(session["logos"])
    })

def handle_quote_action(data, session_id, session):
    """Handle quote form submission"""
    quote_data = data.get("quote_data")
    if not quote_data:
        return jsonify({"error": "Quote data is required for quote action"}), 400
    
    # Save to MongoDB
    success = save_quote_to_mongodb(session_id, session["email"], quote_data)
    
    if success:
        # Update Google Sheets
        save_to_google_sheets(session_id, session["email"], session["messages"], session["logos"])
        
        return jsonify({
            "session_id": session_id,
            "message": "Quote saved successfully",
            "quote_id": session_id
        })
    else:
        return jsonify({"error": "Failed to save quote"}), 500

def handle_get_quote_action(session_id):
    """Get existing quote data"""
    try:
        quote = quotes_collection.find_one({"session_id": session_id})
        if quote:
            return jsonify({
                "session_id": session_id,
                "quote_data": quote.get("form_data", {}),
                "status": quote.get("status", "unknown")
            })
        else:
            return jsonify({
                "session_id": session_id,
                "quote_data": {},
                "status": "not_found"
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_sessions": len(sessions)
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
