from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from openai import OpenAI
import os
from datetime import datetime
import time
import gspread

from mongodb_operations import mongodb_manager
import dropbox
from environment import load_environment, get_google_credentials, get_flask_config

# RAG imports
from chromadb_setup import initialize_chromadb
from documents_processing_responses.document_processing import load_documents_from_directory, preprocess_documents
from embeddings.embedding_generation import generate_embeddings
from db_operations import upsert_documents_into_db

# Dropbox configuration
from dropbox_auth import create_dropbox_client

# Packages
from chatbot.chatbot import generate_sign_nize_response
from validations.validations import validate_email
from session_manager.session_manager import save_session_to_sheets
from chatbot.chatbot import build_conversation_text
from hubspot.hubspot import create_hubspot_contact, hubspot_patch_conversation

# Load environment variables
openai_key = load_environment()

# Initialize OpenAI Client
client = OpenAI(api_key=openai_key)

# Initialize ChromaDB
collection = initialize_chromadb(openai_key)

# Load and preprocess documents
directory_path = "./data"
documents = load_documents_from_directory(directory_path)
chunked_documents = preprocess_documents(documents)

# Generate embeddings
chunked_documents = generate_embeddings(client, chunked_documents)

# Upsert documents into ChromaDB
upsert_documents_into_db(collection, chunked_documents)

# Flask application setup
app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)

flask_config = get_flask_config()
app.config['SECRET_KEY'] = flask_config['FLASK_SECRET_KEY']

# In-memory storage for chat sessions
chat_sessions = {}
saved_sessions = set()

@app.route("/")
def index():
    """Serve the main chatbot page (index.html)."""
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    print(">>> /chat endpoint hit")
    user_message = request.json.get("message")
    session_id = request.json.get("session_id", "default")
    email = request.json.get("email", "")
    print("Message received:", user_message)
    print("Email:", email)

 
    if session_id not in chat_sessions:
        chat_sessions[session_id] = {
            "messages": [],
            "context_history": [],
            "conversation_state": "initial",
            "customer_info": {},
            "email": email
        }
    else:
        
        if email:
            chat_sessions[session_id]["email"] = email
    
    try:
        current_email = chat_sessions[session_id].get("email")
        has_contact_id = chat_sessions[session_id].get("hubspot_contact_id")
        if current_email and not has_contact_id:
            print(f"🔎 No hubspot_contact_id for session {session_id}. Upserting contact for {current_email}...")
            upsert_result = create_hubspot_contact(current_email)
            if upsert_result.get("success") and upsert_result.get("contact_id"):
                contact_id = upsert_result.get("contact_id")
                chat_sessions[session_id]["hubspot_contact_id"] = contact_id
                try:
                    mongodb_manager.update_hubspot_contact_id(session_id, contact_id)
                    print(f"✅ hubspot_contact_id stored for session {session_id}: {contact_id}")
                except Exception as e:
                    print(f"⚠️  Failed to store hubspot_contact_id in DB: {e}")
            else:
                print(f"⚠️  HubSpot upsert failed or no contact_id returned: {upsert_result}")
    except Exception as e:
        print(f"⚠️  Error ensuring HubSpot contact for session: {e}")
  
    chat_sessions[session_id]["messages"].append({
        "role": "user",
        "content": user_message
    })

    try:
        response = generate_sign_nize_response(client, user_message, chat_sessions[session_id])
        quote_form_triggered = "[QUOTE_FORM_TRIGGER]" in response
        if quote_form_triggered:
            response = response.replace("[QUOTE_FORM_TRIGGER]", "")

        chat_sessions[session_id]["messages"].append({
            "role": "assistant",
            "content": response
        })
        
        message_count = len(chat_sessions[session_id]["messages"])
        
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
        
        try:
            db_result = mongodb_manager.save_chat_session(
                session_id, 
                chat_sessions[session_id].get("email", ""), 
                chat_sessions[session_id]["messages"]
            )
            if db_result["success"]:
                print(f"✅ Chat session saved to database: {db_result['action']}")
            else:
                print(f"⚠️  Failed to save chat session to database: {db_result.get('error', 'Unknown error')}")
        except Exception as db_error:
            print(f"❌ Database save error: {db_error}")
        
        print(f"Generated response for session {session_id}:", response)

        try:
            contact_id = None
            if session_id in chat_sessions:
                contact_id = chat_sessions[session_id].get("hubspot_contact_id")
            if not contact_id:
              
                db_session = mongodb_manager.get_chat_session(session_id)
                if db_session.get("success"):
                    contact_id = db_session["session"].get("hubspot_contact_id")

            if contact_id:
              
                last_sync_iso = None
                db_session = mongodb_manager.get_chat_session(session_id)
                if db_session.get("success"):
                    last_sync_iso = db_session["session"].get("hubspot_last_sync_at")

                should_sync = True
                if last_sync_iso:
                    try:
                        last_sync_dt = datetime.fromisoformat(last_sync_iso.replace("Z", "+00:00"))
                     
                        should_sync = (datetime.utcnow() - last_sync_dt).total_seconds() >= 30
                    except Exception:
                        should_sync = True

                if should_sync:
                    conv_text = build_conversation_text(chat_sessions[session_id]["messages"], session_id)
                    patch_result = hubspot_patch_conversation(contact_id, conv_text)
                    if patch_result.get("success"):
                        mongodb_manager.update_hubspot_last_sync(session_id, datetime.utcnow().isoformat() + "Z")
                    else:
                        print(f"⚠️  HubSpot sync skipped/failed: {patch_result.get('error')}")
        except Exception as sync_err:
            print(f"⚠️  HubSpot sync error: {sync_err}")
        return jsonify({
            "message": response,
            "session_id": session_id,
            "message_count": len(chat_sessions[session_id]["messages"]),
            "quote_form_triggered": quote_form_triggered
        })
        
    except Exception as e:
        print("Error in generate_sign_nize_response:", str(e))
        return jsonify({"message": f"Sorry, I encountered an error. Please try again."}), 500

@app.route("/validate-email", methods=["POST"])
def validate_email_endpoint():
    print(">>> Email validation endpoint hit")
    data = request.json
    email = data.get("email", "")
    session_id = data.get("session_id")
    
    if not email:
        return jsonify({"valid": False, "message": "Email is required"})
    
    is_valid = validate_email(email)
    
    if is_valid:
        
        print(f"📧 Valid email detected - creating/updating HubSpot contact: {email}")
        hubspot_result = create_hubspot_contact(email)

        contact_id = None
        if hubspot_result.get("success"):
            print(f"✅ HubSpot contact {hubspot_result['action']}: {email}")
            contact_id = hubspot_result.get("contact_id")
         
            if session_id and contact_id:
                if session_id not in chat_sessions:
                    chat_sessions[session_id] = {"messages": [], "context_history": [], "conversation_state": "initial", "customer_info": {}, "email": email}
                chat_sessions[session_id]["email"] = email
                chat_sessions[session_id]["hubspot_contact_id"] = contact_id
                try:
                    mongodb_manager.update_hubspot_contact_id(session_id, contact_id)
                    print(f"✅ Saved hubspot_contact_id to MongoDB for session {session_id}")
                except Exception as db_err:
                    print(f"⚠️  Failed saving hubspot_contact_id to MongoDB: {db_err}")

            return jsonify({
                "valid": True,
                "message": "Valid email format",
                "hubspot_contact": {
                    "action": hubspot_result.get("action"),
                    "contact_id": contact_id,
                    "message": hubspot_result.get("message")
                }
            })
        else:
            print(f"⚠️  HubSpot contact creation failed: {hubspot_result.get('error', 'Unknown error')}")
       
            return jsonify({
                "valid": True,
                "message": "Valid email format (HubSpot sync failed)",
                "hubspot_error": hubspot_result.get("error")
            })
    
    return jsonify({
        "valid": False,
        "message": "Invalid email format"
    })

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
       
        if result["success"] and session_id in chat_sessions:
            try:
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

@app.route("/get-quote/<session_id>", methods=["GET"])
def get_quote(session_id):
    print(f">>> Get quote endpoint hit for session {session_id}")
    
    try:
        result = mongodb_manager.get_quote_data(session_id)
        if result["success"]:
            return jsonify(result["quote"])
        else:
            
            return jsonify({"form_data": {}})
    except Exception as e:
        return jsonify({"error": f"Failed to get quote: {str(e)}"}), 500

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
   
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'svg', 'pdf'}
        file_extension = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        
        if file_extension not in allowed_extensions:
            return jsonify({"success": False, "message": f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}"}), 400
        
        try:
            filename = f"logo_{int(time.time())}_{file.filename}"
            dropbox_path = f"/logos/{session_id}/{filename}"
            
            dbx = create_dropbox_client()
            if not dbx:
                print("❌ Failed to create Dropbox client")
                return jsonify({"success": False, "message": "Failed to connect to Dropbox"}), 500
            
            file_content = file.read()
            dbx.files_upload(file_content, dropbox_path, mode=dropbox.files.WriteMode.overwrite)
            print(f"✅ Uploaded to Dropbox: {dropbox_path}")
            
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
            
            dropbox_url = link_metadata.url.replace("?dl=0", "?dl=1")
            print(f"✅ Created shared link: {dropbox_url}")

            logo_info = {
                "filename": filename,
                "dropbox_url": dropbox_url,
                "upload_time": datetime.now().isoformat()
            }
            
          
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

@app.route("/session/<session_id>/messages", methods=["GET"])
def get_session_messages(session_id):
    print(f">>> Get session messages endpoint hit for session {session_id}")
    
    try:
        
        result = mongodb_manager.get_chat_session(session_id)
        
        if result["success"]:
            session_data = result["session"]
            messages = session_data.get("messages", [])
            email = session_data.get("email", "")
            
            if session_id not in chat_sessions:
                chat_sessions[session_id] = {
                    "messages": messages,
                    "email": email,
                    "context_history": [],
                    "conversation_state": "initial",
                    "customer_info": {}
                }
            else:
                chat_sessions[session_id]["messages"] = messages
                chat_sessions[session_id]["email"] = email
            
            return jsonify({
                "success": True,
                "messages": messages,
                "email": email,
                "message_count": len(messages)
            })
        else:
            # Fallback to in-memory session
            if session_id in chat_sessions and "messages" in chat_sessions[session_id]:
                messages = chat_sessions[session_id]["messages"]
                email = chat_sessions[session_id].get("email", "")
                return jsonify({
                    "success": True,
                    "messages": messages,
                    "email": email,
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

@app.route("/session/<session_id>/logos", methods=["GET"])
def get_session_logos(session_id):
    print(f">>> Get logos endpoint hit for session {session_id}")
    
    try:
        if session_id in chat_sessions and "logos" in chat_sessions[session_id]:
            logos = chat_sessions[session_id]["logos"]
            return jsonify({"logos": logos})
        else:
          
            return jsonify({"logos": []})
    except Exception as e:
        return jsonify({"error": f"Failed to get logos: {str(e)}"}), 500

if __name__ == "__main__":
    debug_mode = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(host="0.0.0.0", port=5000, debug=debug_mode)
