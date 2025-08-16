from pymongo import MongoClient
from datetime import datetime
import os
import json
from environment import load_environment

class MongoDBManager:
    def __init__(self):
        load_environment()
        mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
        try:
            self.client = MongoClient(mongodb_uri)
            self.client.admin.command('ping')  # Test connection
            self.db = self.client['signize_bot']
            self.quotes_collection = self.db['quotes']
            self.connected = True
            print("✅ MongoDB connected successfully")
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
                    "status": "new"
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

def test_mongodb_connection():
    """Test MongoDB connection for debugging"""
    try:
        load_environment()
        mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
        client = MongoClient(mongodb_uri)
        client.admin.command('ping')
        client.close()
        return True
    except Exception as e:
        print(f"MongoDB connection test failed: {e}")
        return False

# Create global instance
mongodb_manager = MongoDBManager()
