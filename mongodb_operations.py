from pymongo import MongoClient
from datetime import datetime
import os
import json
from environment import load_environment

class MongoDBManager:
    def __init__(self):
        # Load environment variables
        load_environment()
        
        # Get MongoDB connection string from environment or use default
        from environment import get_mongodb_uri
        mongodb_uri = get_mongodb_uri()
        
        print(f"🔍 Attempting to connect to MongoDB with URI: {mongodb_uri[:50]}...")
        
        # Check if this is Atlas or local
        is_atlas = "mongodb+srv://" in mongodb_uri or "cluster" in mongodb_uri
        print(f"📍 Connection type: {'MongoDB Atlas' if is_atlas else 'Local MongoDB'}")
        
        try:
            self.client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=10000)
            # Test the connection
            self.client.admin.command('ping')
            self.db = self.client['signize_bot']
            self.quotes_collection = self.db['quotes']
            self.connected = True
            print("✅ MongoDB connected successfully")
            print(f"📊 Database: {self.db.name}")
            print(f"📋 Collection: {self.quotes_collection.name}")
            print(f"🌐 Connection: {'Atlas' if is_atlas else 'Local'}")
            
            # Test write access
            test_doc = {"test": "connection", "timestamp": datetime.now(), "connection_type": "atlas" if is_atlas else "local"}
            result = self.quotes_collection.insert_one(test_doc)
            print(f"✅ Write test successful - inserted document ID: {result.inserted_id}")
            # Clean up test document
            self.quotes_collection.delete_one({"_id": result.inserted_id})
            print("✅ Test document cleaned up")
            
        except Exception as e:
            print(f"⚠️  MongoDB connection failed: {e}")
            print("   Quote data will be stored locally only")
            self.connected = False
            self.client = None
            self.db = None
            self.quotes_collection = None

    def save_quote_data(self, session_id, email, form_data):
        """Save quote data to MongoDB or local file as fallback"""
        if not self.connected:
            return self._save_quote_data_locally(session_id, email, form_data)
        
        try:
            # Check if quote already exists
            existing_quote = self.quotes_collection.find_one({"session_id": session_id})
            
            if existing_quote:
                # Update existing quote
                result = self.quotes_collection.update_one(
                    {"session_id": session_id},
                    {
                        "$set": {
                            "email": email,
                            "form_data": form_data,
                            "updated_at": datetime.now(),
                            "status": "updated"
                        }
                    }
                )
                if result.modified_count > 0:
                    print(f"✅ Quote data updated for session {session_id}")
                    return {"success": True, "action": "updated", "quote_id": str(existing_quote["_id"])}
                else:
                    print(f"⚠️  No changes made to quote for session {session_id}")
                    return {"success": False, "error": "No changes made"}
            else:
                # Create new quote
                quote_doc = {
                    "session_id": session_id,
                    "email": email,
                    "form_data": form_data,
                    "created_at": datetime.now(),
                    "updated_at": datetime.now(),
                    "status": "new",
                    "type": "quote_data"
                }
                result = self.quotes_collection.insert_one(quote_doc)
                if result.inserted_id:
                    print(f"✅ Quote data saved for session {session_id}")
                    return {"success": True, "action": "created", "quote_id": str(result.inserted_id)}
                else:
                    print(f"❌ Failed to save quote data for session {session_id}")
                    return {"success": False, "error": "Failed to insert quote"}
                    
        except Exception as e:
            print(f"❌ Error saving quote data to MongoDB: {e}")
            print("   Falling back to local storage")
            return self._save_quote_data_locally(session_id, email, form_data)

    def get_quote_data(self, session_id):
        """Get quote data from MongoDB or local file as fallback"""
        if not self.connected:
            return self._get_quote_data_locally(session_id)
        
        try:
            quote = self.quotes_collection.find_one({"session_id": session_id})
            if quote:
                # Convert ObjectId to string for JSON serialization
                quote["_id"] = str(quote["_id"])
                return {"success": True, "quote": quote}
            else:
                return {"success": False, "error": "Quote not found"}
                
        except Exception as e:
            print(f"❌ Error retrieving quote data from MongoDB: {e}")
            print("   Falling back to local storage")
            return self._get_quote_data_locally(session_id)

    def update_quote_status(self, session_id, status):
        """Update quote status in MongoDB or local file as fallback"""
        if not self.connected:
            return self._update_quote_status_locally(session_id, status)
        
        try:
            result = self.quotes_collection.update_one(
                {"session_id": session_id},
                {
                    "$set": {
                        "status": status,
                        "updated_at": datetime.now()
                    }
                }
            )
            if result.modified_count > 0:
                print(f"✅ Quote status updated to '{status}' for session {session_id}")
                return {"success": True, "message": f"Status updated to {status}"}
            else:
                print(f"⚠️  No quote found to update status for session {session_id}")
                return {"success": False, "error": "Quote not found"}
                
        except Exception as e:
            print(f"❌ Error updating quote status in MongoDB: {e}")
            print("   Falling back to local storage")
            return self._update_quote_status_locally(session_id, status)

    def get_all_quotes(self):
        """Get all quotes from MongoDB or local files as fallback"""
        if not self.connected:
            return self._get_all_quotes_locally()
        
        try:
            quotes = list(self.quotes_collection.find())
            # Convert ObjectIds to strings for JSON serialization
            for quote in quotes:
                quote["_id"] = str(quote["_id"])
            return {"success": True, "quotes": quotes}
            
        except Exception as e:
            print(f"❌ Error retrieving all quotes from MongoDB: {e}")
            print("   Falling back to local storage")
            return self._get_all_quotes_locally()

    def _save_quote_data_locally(self, session_id, email, form_data):
        """Save quote data to local JSON file"""
        try:
            # Create quotes directory if it doesn't exist
            os.makedirs("quotes", exist_ok=True)
            
            quote_data = {
                "session_id": session_id,
                "email": email,
                "form_data": form_data,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "status": "new"
            }
            
            filename = f"quotes/quote_{session_id}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(quote_data, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"✅ Quote data saved locally to {filename}")
            return {"success": True, "action": "created", "filename": filename}
            
        except Exception as e:
            print(f"❌ Error saving quote data locally: {e}")
            return {"success": False, "error": str(e)}

    def _get_quote_data_locally(self, session_id):
        """Get quote data from local JSON file"""
        try:
            filename = f"quotes/quote_{session_id}.json"
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    quote_data = json.load(f)
                return {"success": True, "quote": quote_data}
            else:
                return {"success": False, "error": "Quote not found"}
                
        except Exception as e:
            print(f"❌ Error reading quote data locally: {e}")
            return {"success": False, "error": str(e)}

    def _update_quote_status_locally(self, session_id, status):
        """Update quote status in local JSON file"""
        try:
            filename = f"quotes/quote_{session_id}.json"
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    quote_data = json.load(f)
                
                quote_data["status"] = status
                quote_data["updated_at"] = datetime.now().isoformat()
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(quote_data, f, indent=2, ensure_ascii=False, default=str)
                
                print(f"✅ Quote status updated locally to '{status}' for session {session_id}")
                return {"success": True, "message": f"Status updated to {status}"}
            else:
                return {"success": False, "error": "Quote not found"}
                
        except Exception as e:
            print(f"❌ Error updating quote status locally: {e}")
            return {"success": False, "error": str(e)}

    def _get_all_quotes_locally(self):
        """Get all quotes from local JSON files"""
        try:
            if not os.path.exists("quotes"):
                return {"success": True, "quotes": []}
            
            quotes = []
            for filename in os.listdir("quotes"):
                if filename.endswith('.json'):
                    filepath = os.path.join("quotes", filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            quote_data = json.load(f)
                            quotes.append(quote_data)
                    except Exception as e:
                        print(f"⚠️  Error reading {filename}: {e}")
                        continue
            
            return {"success": True, "quotes": quotes}
            
        except Exception as e:
            print(f"❌ Error reading all quotes locally: {e}")
            return {"success": False, "error": str(e)}

    def update_hubspot_contact_id(self, session_id, contact_id: str):
        """Persist HubSpot contact_id for a session (Atlas or local fallback)"""
        if not self.connected:
            return self._update_hubspot_contact_id_locally(session_id, contact_id)
        try:
            result = self.quotes_collection.update_one(
                {"session_id": session_id},
                {"$set": {"hubspot_contact_id": contact_id, "updated_at": datetime.now()}},
                upsert=True
            )
            if result.matched_count > 0 or result.upserted_id:
                print(f"✅ HubSpot contact_id saved for session {session_id}")
                return {"success": True}
            return {"success": False, "error": "No document matched or upsert failed"}
        except Exception as e:
            print(f"❌ Error saving HubSpot contact_id to MongoDB: {e}")
            return {"success": False, "error": str(e)}

    def _update_hubspot_contact_id_locally(self, session_id, contact_id: str):
        """Persist HubSpot contact_id locally in chat_sessions file"""
        try:
            os.makedirs("chat_sessions", exist_ok=True)
            filename = f"chat_sessions/session_{session_id}.json"
            data = {"session_id": session_id}
            if os.path.exists(filename):
                try:
                    with open(filename, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                except Exception:
                    data = {"session_id": session_id}
            data["hubspot_contact_id"] = contact_id
            data["updated_at"] = datetime.now().isoformat()
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            print(f"✅ HubSpot contact_id saved locally for session {session_id}")
            return {"success": True}
        except Exception as e:
            print(f"❌ Error saving HubSpot contact_id locally: {e}")
            return {"success": False, "error": str(e)}

    def update_hubspot_last_sync(self, session_id, iso_timestamp: str):
        """Record last HubSpot sync time for a session"""
        if not self.connected:
            return self._update_hubspot_last_sync_locally(session_id, iso_timestamp)
        try:
            result = self.quotes_collection.update_one(
                {"session_id": session_id},
                {"$set": {"hubspot_last_sync_at": iso_timestamp, "updated_at": datetime.now()}},
                upsert=True
            )
            if result.matched_count > 0 or result.upserted_id:
                print(f"✅ HubSpot last sync time saved for session {session_id}")
                return {"success": True}
            return {"success": False, "error": "Update failed"}
        except Exception as e:
            print(f"❌ Error saving HubSpot last sync time: {e}")
            return {"success": False, "error": str(e)}

    def _update_hubspot_last_sync_locally(self, session_id, iso_timestamp: str):
        try:
            os.makedirs("chat_sessions", exist_ok=True)
            filename = f"chat_sessions/session_{session_id}.json"
            data = {"session_id": session_id}
            if os.path.exists(filename):
                try:
                    with open(filename, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                except Exception:
                    data = {"session_id": session_id}
            data["hubspot_last_sync_at"] = iso_timestamp
            data["updated_at"] = datetime.now().isoformat()
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            print(f"✅ HubSpot last sync time saved locally for session {session_id}")
            return {"success": True}
        except Exception as e:
            print(f"❌ Error saving HubSpot last sync time locally: {e}")
            return {"success": False, "error": str(e)}

    def save_chat_session(self, session_id, email, messages, phone_number=None):
        """Save chat session to MongoDB quotes collection or local file as fallback"""
        if not self.connected:
            return self._save_chat_session_locally(session_id, email, messages, phone_number)
        
        try:
            # First, check if a session already exists for this email
            existing_session_by_email = self.quotes_collection.find_one({"email": email, "type": "chat_session"})
            
            if existing_session_by_email:
                # Update existing session for this email
                existing_session_id = existing_session_by_email.get("session_id")
                
                # Merge messages from both sessions (avoid duplicates)
                existing_messages = existing_session_by_email.get("messages", [])
                new_messages = messages
                
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
                
                # ✅ IMPORTANT: Keep the existing session_id to maintain consistency
                # Only update if the existing session_id is None or empty
                update_session_id = existing_session_id if existing_session_id else session_id
                
                # Update with merged data
                update_data = {
                    "session_id": update_session_id,  # ✅ Keep existing session_id if available
                    "email": email,
                    "messages": merged_messages,
                    "updated_at": datetime.now(),
                    "message_count": len(merged_messages),
                    "type": "chat_session"
                }
                
                # Only update phone number if provided
                if phone_number:
                    update_data["phone_number"] = phone_number
                
                result = self.quotes_collection.update_one(
                    {"email": email, "type": "chat_session"},
                    {"$set": update_data}
                )
                if result.modified_count > 0:
                    print(f"✅ Chat session updated for email {email} (merged with existing session {existing_session_id})")
                    return {"success": True, "action": "updated", "session_id": update_session_id, "email": email}
                else:
                    print(f"⚠️  No changes made to chat session for email {email}")
                    return {"success": False, "error": "No changes made"}
            else:
                # Check if session already exists by session_id (fallback)
                existing_session = self.quotes_collection.find_one({"session_id": session_id})
                
                if existing_session:
                    # Update existing session with messages and phone number
                    update_data = {
                        "email": email,
                        "messages": messages,
                        "updated_at": datetime.now(),
                        "message_count": len(messages),
                        "type": "chat_session"
                    }
                    
                    # Only update phone number if provided
                    if phone_number:
                        update_data["phone_number"] = phone_number
                    
                    result = self.quotes_collection.update_one(
                        {"session_id": session_id},
                        {"$set": update_data}
                    )
                    if result.modified_count > 0:
                        print(f"✅ Chat session updated in quotes collection for session {session_id}")
                        return {"success": True, "action": "updated", "session_id": session_id}
                    else:
                        print(f"⚠️  No changes made to chat session for session {session_id}")
                        return {"success": False, "error": "No changes made"}
                else:
                    # Create new session in quotes collection
                    session_doc = {
                        "session_id": session_id,
                        "email": email,
                        "messages": messages,
                        "created_at": datetime.now(),
                        "updated_at": datetime.now(),
                        "message_count": len(messages),
                        "type": "chat_session"
                    }
                    
                    # Add phone number if provided
                    if phone_number:
                        session_doc["phone_number"] = phone_number
                    
                    result = self.quotes_collection.insert_one(session_doc)
                    if result.inserted_id:
                        print(f"✅ Chat session saved in quotes collection for session {session_id}")
                        return {"success": True, "action": "created", "session_id": session_id}
                    else:
                        print(f"❌ Failed to save chat session for session {session_id}")
                        return {"success": False, "error": "Failed to insert session"}
                    
        except Exception as e:
            print(f"❌ Error saving chat session to MongoDB: {e}")
            print("   Falling back to local storage")
            return self._save_chat_session_locally(session_id, email, messages, phone_number)

    def update_phone_number(self, session_id, phone_number):
        """Update phone number for a session"""
        if not self.connected:
            return self._update_phone_number_locally(session_id, phone_number)
        
        try:
            result = self.quotes_collection.update_one(
                {"session_id": session_id},
                {
                    "$set": {
                        "phone_number": phone_number,
                        "updated_at": datetime.now()
                    }
                }
            )
            if result.modified_count > 0:
                print(f"✅ Phone number updated for session {session_id}")
                return {"success": True, "message": "Phone number updated"}
            else:
                print(f"⚠️  No session found to update phone number for session {session_id}")
                return {"success": False, "error": "Session not found"}
                
        except Exception as e:
            print(f"❌ Error updating phone number in MongoDB: {e}")
            print("   Falling back to local storage")
            return self._update_phone_number_locally(session_id, phone_number)

    def get_phone_number(self, session_id):
        """Get phone number for a session"""
        if not self.connected:
            return self._get_phone_number_locally(session_id)
        
        try:
            session_data = self.quotes_collection.find_one({"session_id": session_id})
            if session_data and "phone_number" in session_data:
                return {"success": True, "phone_number": session_data["phone_number"]}
            else:
                return {"success": False, "phone_number": None}
                
        except Exception as e:
            print(f"❌ Error getting phone number from MongoDB: {e}")
            print("   Falling back to local storage")
            return self._get_phone_number_locally(session_id)

    def get_chat_session(self, session_id):
        """Get chat session from MongoDB quotes collection or local file as fallback"""
        if not self.connected:
            return self._get_chat_session_locally(session_id)
        
        try:
            session_data = self.quotes_collection.find_one({"session_id": session_id})
            if session_data:
                # Convert ObjectId to string for JSON serialization
                session_data["_id"] = str(session_data["_id"])
                return {"success": True, "session": session_data}
            else:
                return {"success": False, "error": "Session not found"}
                
        except Exception as e:
            print(f"❌ Error getting chat session from MongoDB: {e}")
            print("   Falling back to local storage")
            return self._get_chat_session_locally(session_id)

    def get_chat_session_by_email(self, email):
        """Get chat session from MongoDB by email"""
        if not self.connected:
            return self._get_chat_session_by_email_locally(email)
        
        try:
            session_data = self.quotes_collection.find_one({"email": email, "type": "chat_session"})
            if session_data:
                # Convert ObjectId to string for JSON serialization
                session_data["_id"] = str(session_data["_id"])
                return {"success": True, "session": session_data}
            else:
                return {"success": False, "error": "Session not found"}
                
        except Exception as e:
            print(f"❌ Error getting chat session by email from MongoDB: {e}")
            print("   Falling back to local storage")
            return self._get_chat_session_by_email_locally(email)

    def _get_chat_session_by_email_locally(self, email):
        """Get chat session from local JSON file by email"""
        try:
            if not os.path.exists("chat_sessions"):
                return {"success": False, "error": "Session not found"}
            
            for filename in os.listdir("chat_sessions"):
                if filename.endswith('.json'):
                    filepath = os.path.join("chat_sessions", filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            session_data = json.load(f)
                            if session_data.get("email") == email:
                                return {"success": True, "session": session_data}
                    except Exception as e:
                        print(f"⚠️  Error reading {filename}: {e}")
                        continue
            
            return {"success": False, "error": "Session not found"}
                
        except Exception as e:
            print(f"❌ Error reading chat session by email locally: {e}")
            return {"success": False, "error": str(e)}

    def update_hubspot_contact_id_by_email(self, email, contact_id: str):
        """Persist HubSpot contact_id for an email (Atlas or local fallback)"""
        if not self.connected:
            return self._update_hubspot_contact_id_by_email_locally(email, contact_id)
        try:
            result = self.quotes_collection.update_one(
                {"email": email, "type": "chat_session"},
                {"$set": {"hubspot_contact_id": contact_id, "updated_at": datetime.now()}},
                upsert=True
            )
            if result.matched_count > 0 or result.upserted_id:
                print(f"✅ HubSpot contact_id saved for email {email}")
                return {"success": True}
            return {"success": False, "error": "No document matched or upsert failed"}
        except Exception as e:
            print(f"❌ Error saving HubSpot contact_id to MongoDB: {e}")
            return {"success": False, "error": str(e)}

    def _update_hubspot_contact_id_by_email_locally(self, email, contact_id: str):
        """Persist HubSpot contact_id locally by email"""
        try:
            os.makedirs("chat_sessions", exist_ok=True)
            
            # Find existing session file for this email
            session_filename = None
            for filename in os.listdir("chat_sessions"):
                if filename.endswith('.json'):
                    filepath = os.path.join("chat_sessions", filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            if data.get("email") == email:
                                session_filename = filename
                                break
                    except Exception:
                        continue
            
            if session_filename:
                filepath = os.path.join("chat_sessions", session_filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                data["hubspot_contact_id"] = contact_id
                data["updated_at"] = datetime.now().isoformat()
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False, default=str)
                print(f"✅ HubSpot contact_id saved locally for email {email}")
                return {"success": True}
            else:
                # Create new session file for this email
                filename = f"chat_sessions/session_email_{email.replace('@', '_at_').replace('.', '_')}.json"
                data = {
                    "email": email,
                    "hubspot_contact_id": contact_id,
                    "updated_at": datetime.now().isoformat()
                }
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False, default=str)
                print(f"✅ HubSpot contact_id saved locally for email {email}")
                return {"success": True}
        except Exception as e:
            print(f"❌ Error saving HubSpot contact_id locally: {e}")
            return {"success": False, "error": str(e)}

    def update_hubspot_last_sync_by_email(self, email, iso_timestamp: str):
        """Record last HubSpot sync time for an email"""
        if not self.connected:
            return self._update_hubspot_last_sync_by_email_locally(email, iso_timestamp)
        try:
            result = self.quotes_collection.update_one(
                {"email": email, "type": "chat_session"},
                {"$set": {"hubspot_last_sync_at": iso_timestamp, "updated_at": datetime.now()}},
                upsert=True
            )
            if result.matched_count > 0 or result.upserted_id:
                print(f"✅ HubSpot last sync time saved for email {email}")
                return {"success": True}
            return {"success": False, "error": "Update failed"}
        except Exception as e:
            print(f"❌ Error saving HubSpot last sync time: {e}")
            return {"success": False, "error": str(e)}

    def _update_hubspot_last_sync_by_email_locally(self, email, iso_timestamp: str):
        try:
            os.makedirs("chat_sessions", exist_ok=True)
            
            # Find existing session file for this email
            session_filename = None
            for filename in os.listdir("chat_sessions"):
                if filename.endswith('.json'):
                    filepath = os.path.join("chat_sessions", filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            if data.get("email") == email:
                                session_filename = filename
                                break
                    except Exception:
                        continue
            
            if session_filename:
                filepath = os.path.join("chat_sessions", session_filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                data["hubspot_last_sync_at"] = iso_timestamp
                data["updated_at"] = datetime.now().isoformat()
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False, default=str)
                print(f"✅ HubSpot last sync time saved locally for email {email}")
                return {"success": True}
            else:
                # Create new session file for this email
                filename = f"chat_sessions/session_email_{email.replace('@', '_at_').replace('.', '_')}.json"
                data = {
                    "email": email,
                    "hubspot_last_sync_at": iso_timestamp,
                    "updated_at": datetime.now().isoformat()
                }
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False, default=str)
                print(f"✅ HubSpot last sync time saved locally for email {email}")
                return {"success": True}
        except Exception as e:
            print(f"❌ Error saving HubSpot last sync time locally: {e}")
            return {"success": False, "error": str(e)}

    def _save_chat_session_locally(self, session_id, email, messages, phone_number=None):
        """Save chat session to local JSON file"""
        try:
            os.makedirs("chat_sessions", exist_ok=True)
            
            session_data = {
                "session_id": session_id,
                "email": email,
                "messages": messages,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "message_count": len(messages)
            }
            
            # Add phone number if provided
            if phone_number:
                session_data["phone_number"] = phone_number
            
            filename = f"chat_sessions/session_{session_id}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"✅ Chat session saved locally to {filename}")
            return {"success": True, "action": "created", "filename": filename}
            
        except Exception as e:
            print(f"❌ Error saving chat session locally: {e}")
            return {"success": False, "error": str(e)}

    def _get_chat_session_locally(self, session_id):
        """Get chat session from local JSON file"""
        try:
            filename = f"chat_sessions/session_{session_id}.json"
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                return {"success": True, "session": session_data}
            else:
                return {"success": False, "error": "Session not found"}
                
        except Exception as e:
            print(f"❌ Error reading chat session locally: {e}")
            return {"success": False, "error": str(e)}

    def _update_phone_number_locally(self, session_id, phone_number):
        """Update phone number in local JSON file"""
        try:
            filename = f"chat_sessions/session_{session_id}.json"
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                
                session_data["phone_number"] = phone_number
                session_data["updated_at"] = datetime.now().isoformat()
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(session_data, f, indent=2, ensure_ascii=False, default=str)
                
                print(f"✅ Phone number updated locally for session {session_id}")
                return {"success": True, "message": "Phone number updated"}
            else:
                return {"success": False, "error": "Session not found"}
                
        except Exception as e:
            print(f"❌ Error updating phone number locally: {e}")
            return {"success": False, "error": str(e)}

    def _get_phone_number_locally(self, session_id):
        """Get phone number from local JSON file"""
        try:
            filename = f"chat_sessions/session_{session_id}.json"
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                return {"success": True, "phone_number": session_data.get("phone_number")}
            else:
                return {"success": False, "phone_number": None}
                
        except Exception as e:
            print(f"❌ Error reading phone number locally: {e}")
            return {"success": False, "error": str(e)}


def test_mongodb_connection():
    """Test MongoDB connection for debugging"""
    try:
        from environment import get_mongodb_uri
        mongodb_uri = get_mongodb_uri()
        client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        client.close()
        return True
    except Exception as e:
        print(f"MongoDB connection test failed: {e}")
        return False


# Create global instance
mongodb_manager = MongoDBManager()
