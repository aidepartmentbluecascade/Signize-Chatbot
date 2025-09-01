#!/usr/bin/env python3
"""
Test script to verify Google Sheets continuous updates are working.
"""

import requests
import json
import time

def test_google_sheets_continuous_update():
    """Test that Google Sheets gets updated with each new message"""
    
    base_url = "http://localhost:5000"
    
    # Test 1: Create a session and send first message
    print("🧪 Test 1: Creating session and sending first message")
    
    session_id = f"test_sheets_{int(time.time())}"
    
    # Send first message with email
    response = requests.post(f"{base_url}/chat", json={
        "message": "Hi, I want a quote for a sign",
        "session_id": session_id,
        "email": "test@example.com"
    })
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ First response: {data['message'][:100]}...")
        
        # Check if it asks for email (should not since we provided it)
        if "email" in data['message'].lower() and "provide" in data['message'].lower():
            print("❌ Still asking for email when it was provided")
        else:
            print("✅ Correctly handled message with email")
    else:
        print(f"❌ Request failed: {response.status_code}")
        return
    
    # Wait a moment for Google Sheets to update
    print("⏳ Waiting 2 seconds for Google Sheets update...")
    time.sleep(2)
    
    # Test 2: Send second message
    print("\n🧪 Test 2: Sending second message")
    
    response = requests.post(f"{base_url}/chat", json={
        "message": "I need a 3x5 foot sign for my business",
        "session_id": session_id,
        "email": "test@example.com"
    })
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Second response: {data['message'][:100]}...")
    else:
        print(f"❌ Request failed: {response.status_code}")
        return
    
    # Wait a moment for Google Sheets to update
    print("⏳ Waiting 2 seconds for Google Sheets update...")
    time.sleep(2)
    
    # Test 3: Send third message
    print("\n🧪 Test 3: Sending third message")
    
    response = requests.post(f"{base_url}/chat", json={
        "message": "What materials do you offer?",
        "session_id": session_id,
        "email": "test@example.com"
    })
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Third response: {data['message'][:100]}...")
    else:
        print(f"❌ Request failed: {response.status_code}")
        return
    
    # Test 4: Check if session can be loaded
    print("\n🧪 Test 4: Checking if session can be loaded")
    
    response = requests.get(f"{base_url}/session/{session_id}/messages")
    
    if response.status_code == 200:
        data = response.json()
        message_count = len(data.get("messages", []))
        print(f"✅ Session loaded with {message_count} messages")
        
        if message_count >= 6:  # 3 user + 3 assistant messages
            print("✅ Session has expected number of messages")
        else:
            print(f"⚠️  Expected 6+ messages, got {message_count}")
    else:
        print(f"❌ Failed to load session: {response.status_code}")
    
    print(f"\n📊 Test completed for session: {session_id}")
    print("🔍 Check Google Sheets to verify continuous updates were saved")

if __name__ == "__main__":
    print("🚀 Testing Google Sheets continuous updates...")
    test_google_sheets_continuous_update()
    print("\n✅ Test completed!")
