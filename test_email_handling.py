#!/usr/bin/env python3
"""
Test script to verify email handling logic for sessions without emails.
"""

import requests
import json

def test_session_without_email():
    """Test a session that exists but has no email"""
    
    base_url = "http://localhost:5000"
    
    # Test 1: Create a session without email
    print("🧪 Test 1: Creating session without email")
    
    session_id = f"test_session_{int(__import__('time').time())}"
    
    # Send first message without email
    response = requests.post(f"{base_url}/chat", json={
        "message": "Hi",
        "session_id": session_id,
        "email": ""
    })
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Response: {data['message'][:100]}...")
        
        # Check if it asks for email
        if "email" in data['message'].lower():
            print("✅ Correctly asked for email")
        else:
            print("❌ Did not ask for email")
    else:
        print(f"❌ Request failed: {response.status_code}")
    
    # Test 2: Send another message without email
    print("\n🧪 Test 2: Sending another message without email")
    
    response = requests.post(f"{base_url}/chat", json={
        "message": "I want a quote",
        "session_id": session_id,
        "email": ""
    })
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Response: {data['message'][:100]}...")
        
        # Should still ask for email
        if "email" in data['message'].lower():
            print("✅ Correctly asked for email again")
        else:
            print("❌ Did not ask for email")
    else:
        print(f"❌ Request failed: {response.status_code}")
    
    # Test 3: Provide email
    print("\n🧪 Test 3: Providing email")
    
    response = requests.post(f"{base_url}/chat", json={
        "message": "My email is test@example.com",
        "session_id": session_id,
        "email": "test@example.com"
    })
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Response: {data['message'][:100]}...")
        
        # Should not ask for email anymore
        if "email" in data['message'].lower() and "provide" in data['message'].lower():
            print("❌ Still asking for email")
        else:
            print("✅ No longer asking for email")
    else:
        print(f"❌ Request failed: {response.status_code}")
    
    # Test 4: Send another message with email
    print("\n🧪 Test 4: Sending message with email")
    
    response = requests.post(f"{base_url}/chat", json={
        "message": "I want a quote",
        "session_id": session_id,
        "email": "test@example.com"
    })
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Response: {data['message'][:100]}...")
        
        # Should trigger quote form
        if "[QUOTE_FORM_TRIGGER]" in data['message'] or "quote" in data['message'].lower():
            print("✅ Correctly handled quote request")
        else:
            print("❌ Did not handle quote request properly")
    else:
        print(f"❌ Request failed: {response.status_code}")

if __name__ == "__main__":
    print("🚀 Testing email handling logic...")
    test_session_without_email()
    print("\n✅ Test completed!")
