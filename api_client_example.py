#!/usr/bin/env python3
"""
Example client for the Signize Chatbot API
Shows how to use the API with just a session ID
"""

import requests
import json
import base64
import os

# API Configuration
API_BASE_URL = "http://localhost:5000/api"

class SignizeChatbotClient:
    def __init__(self, session_id=None):
        self.session_id = session_id
        self.api_url = f"{API_BASE_URL}/chatbot"
    
    def chat(self, message, email=None):
        """Send a chat message"""
        payload = {
            "action": "chat",
            "message": message
        }
        
        if self.session_id:
            payload["session_id"] = self.session_id
        
        if email:
            payload["email"] = email
        
        response = requests.post(self.api_url, json=payload)
        data = response.json()
        
        # Store session ID for future use
        if "session_id" in data:
            self.session_id = data["session_id"]
        
        return data
    
    def upload_files(self, file_paths):
        """Upload logo files"""
        if not self.session_id:
            raise ValueError("Session ID required for file upload")
        
        files = []
        for file_path in file_paths:
            if os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    file_data = base64.b64encode(f.read()).decode('utf-8')
                    filename = os.path.basename(file_path)
                    files.append({
                        "filename": filename,
                        "data": file_data
                    })
        
        payload = {
            "action": "upload",
            "session_id": self.session_id,
            "files": files
        }
        
        response = requests.post(self.api_url, json=payload)
        return response.json()
    
    def submit_quote(self, quote_data):
        """Submit quote form data"""
        if not self.session_id:
            raise ValueError("Session ID required for quote submission")
        
        payload = {
            "action": "quote",
            "session_id": self.session_id,
            "quote_data": quote_data
        }
        
        response = requests.post(self.api_url, json=payload)
        return response.json()
    
    def get_quote(self):
        """Get existing quote data"""
        if not self.session_id:
            raise ValueError("Session ID required for getting quote")
        
        payload = {
            "action": "get_quote",
            "session_id": self.session_id
        }
        
        response = requests.post(self.api_url, json=payload)
        return response.json()

def main():
    """Example usage of the API client"""
    
    # Create client (session ID will be generated automatically)
    client = SignizeChatbotClient()
    
    print("🤖 Signize Chatbot API Client Example")
    print("=" * 50)
    
    # Example 1: Start a conversation
    print("\n1️⃣ Starting conversation...")
    response = client.chat("Hi, I need help with a sign")
    print(f"Session ID: {client.session_id}")
    print(f"AI Response: {response['response']}")
    
    # Example 2: Provide email
    print("\n2️⃣ Providing email...")
    response = client.chat("My email is user@example.com", email="user@example.com")
    print(f"AI Response: {response['response']}")
    
    # Example 3: Ask for quote
    print("\n3️⃣ Requesting quote...")
    response = client.chat("I want a mockup and quote for a 3D metal sign")
    print(f"AI Response: {response['response']}")
    print(f"Quote form triggered: {response['quote_form_triggered']}")
    
    # Example 4: Upload logo files (if you have test files)
    print("\n4️⃣ Uploading logo files...")
    try:
        # Create a test file
        test_file = "test_logo.txt"
        with open(test_file, 'w') as f:
            f.write("This is a test logo file")
        
        upload_response = client.upload_files([test_file])
        print(f"Upload response: {upload_response}")
        
        # Clean up test file
        os.remove(test_file)
    except Exception as e:
        print(f"Upload test skipped: {e}")
    
    # Example 5: Submit quote
    print("\n5️⃣ Submitting quote...")
    quote_data = {
        "size": "2x3 feet",
        "material": "3D metal",
        "illumination": "LED backlit",
        "installation": "Brick wall",
        "location": "New York, NY",
        "budget": "$1000-2000",
        "deadline": "Standard (15-17 business days)"
    }
    
    quote_response = client.submit_quote(quote_data)
    print(f"Quote submission: {quote_response}")
    
    # Example 6: Get quote data
    print("\n6️⃣ Getting quote data...")
    get_quote_response = client.get_quote()
    print(f"Quote data: {get_quote_response}")
    
    print(f"\n✅ Session completed! Session ID: {client.session_id}")

if __name__ == "__main__":
    main()
