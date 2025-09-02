#!/usr/bin/env python3
"""
Debug HubSpot property names to find the exact Chatbot Conversation property
"""

import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from environment import get_hubspot_config
import requests

def debug_property_names():
    """Debug HubSpot property names"""
    
    print("🔍 Debugging HubSpot Property Names")
    print("="*50)
    
    contact_id = "229926588105"
    
    try:
        hubspot_config = get_hubspot_config()
        if not hubspot_config:
            print("❌ HubSpot not configured")
            return

        url = f"https://api.hubapi.com/crm/v3/objects/contacts/{contact_id}"
        headers = {
            "Authorization": f"Bearer {hubspot_config['token']}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        print(f"📋 Getting properties for contact {contact_id}...")
        resp = requests.get(url, headers=headers, timeout=20)
        
        if resp.ok:
            contact_data = resp.json()
            properties = contact_data.get("properties", {})
            
            print(f"✅ Contact found: {contact_data.get('id')}")
            print(f"📧 Email: {properties.get('email', 'N/A')}")
            print(f"📄 All available properties:")
            
            # Print all properties with their values
            for prop_name, prop_value in properties.items():
                print(f"  - '{prop_name}': {prop_value}")
            
            # Look for conversation-related properties
            conversation_props = []
            for prop_name in properties.keys():
                if any(keyword in prop_name.lower() for keyword in ['conversation', 'chat', 'bot', 'chatbot']):
                    conversation_props.append(prop_name)
            
            print(f"\n🔍 Conversation-related properties:")
            if conversation_props:
                for prop in conversation_props:
                    print(f"  - '{prop}': {properties.get(prop)}")
            else:
                print("  - No conversation-related properties found")
            
            # Try to set the Chatbot Conversation property directly
            print(f"\n🧪 Testing Chatbot Conversation property...")
            test_payload = {
                "properties": {
                    "Chatbot Conversation": "Test conversation from debug script"
                }
            }
            
            patch_resp = requests.patch(url, json=test_payload, headers=headers, timeout=20)
            if patch_resp.ok:
                print("✅ Chatbot Conversation property set successful")
                
                # Check if it was actually set
                get_resp = requests.get(url, headers=headers, timeout=20)
                if get_resp.ok:
                    updated_data = get_resp.json()
                    updated_properties = updated_data.get("properties", {})
                    updated_conv = updated_properties.get("Chatbot Conversation")
                    print(f"📄 Updated Chatbot Conversation: {updated_conv}")
                    print(f"📄 Updated length: {len(updated_conv) if updated_conv else 0}")
                    
                    if updated_conv:
                        print("✅ Chatbot Conversation property works!")
                    else:
                        print("⚠️  Chatbot Conversation property was set but returned empty")
                else:
                    print(f"❌ Failed to get updated contact: {get_resp.status_code}")
            else:
                print(f"❌ Chatbot Conversation property set failed: {patch_resp.status_code}")
                print(f"❌ Response: {patch_resp.text}")
                
        else:
            print(f"❌ Failed to get contact: {resp.status_code}")
            print(f"❌ Response: {resp.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_property_names()

