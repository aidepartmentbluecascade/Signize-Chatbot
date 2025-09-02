import requests

# HubSpot integration functions
def create_hubspot_contact(email, phone_number=None, first_name=None, last_name=None, company=None):
    """Create or update a contact in HubSpot"""
    try:
        from environment import get_hubspot_config

        hubspot_config = get_hubspot_config()

        if not hubspot_config:
            print("⚠️  HubSpot configuration not available - skipping contact creation")
            return {"success": False, "error": "HubSpot not configured"}

        import requests

        # Prepare contact properties
        properties = {
            "email": email
        }

        if phone_number:
            properties["phone"] = phone_number
        if first_name:
            properties["firstname"] = first_name
        if last_name:
            properties["lastname"] = last_name
        if company:
            properties["company"] = company

        # 1. Search for existing contact by email
        search_url = "https://api.hubapi.com/crm/v3/objects/contacts/search"
        search_payload = {
            "filterGroups": [{
                "filters": [{
                    "propertyName": "email",
                    "operator": "EQ",
                    "value": email
                }]
            }],
            "properties": ["email"],
            "limit": 1
        }

        headers = {
            "Authorization": f"Bearer {hubspot_config['token']}",
            "Content-Type": "application/json"
        }

        search_response = requests.post(search_url, json=search_payload, headers=headers)
        search_response.raise_for_status()

        existing_contacts = search_response.json().get("results", [])

        if existing_contacts:
            # 2. Update existing contact
            contact_id = existing_contacts[0]["id"]
            update_url = f"https://api.hubapi.com/crm/v3/objects/contacts/{contact_id}"

            update_payload = {"properties": properties}
            update_response = requests.patch(update_url, json=update_payload, headers=headers)
            update_response.raise_for_status()

            print(f"✅ HubSpot contact updated: {email}")
            return {
                "success": True,
                "action": "updated",
                "contact_id": contact_id,
                "message": "Contact already existed — updated instead"
            }
        else:
            # 3. Create new contact
            create_url = "https://api.hubapi.com/crm/v3/objects/contacts"
            create_payload = {"properties": properties}

            create_response = requests.post(create_url, json=create_payload, headers=headers)
            create_response.raise_for_status()

            new_contact = create_response.json()
            print(f"✅ HubSpot contact created: {email}")
            return {
                "success": True,
                "action": "created",
                "contact_id": new_contact.get("id"),
                "message": "New contact created"
            }

    except requests.exceptions.RequestException as e:
        # Handle 409 conflict: contact already exists -> extract ID or search by email
        try:
            if hasattr(e, 'response') and e.response is not None and e.response.status_code == 409:
                resp_text = e.response.text or ""
                # Try to extract Existing ID from error text
                import re as _re
                m = _re.search(r"Existing ID:\s*(\d+)", resp_text)
                if m:
                    existing_id = m.group(1)
                    print(f"ℹ️  Conflict received; using existing HubSpot contact ID: {existing_id}")
                    return {
                        "success": True,
                        "action": "existing",
                        "contact_id": existing_id,
                        "message": "Contact already existed — using existing ID"
                    }
                # Fallback: run a search by email to fetch the ID
                from environment import get_hubspot_config
                hubspot_config = get_hubspot_config()
                if hubspot_config:
                    import requests as _rq
                    headers = {
                        "Authorization": f"Bearer {hubspot_config['token']}",
                        "Content-Type": "application/json"
                    }
                    search_url = "https://api.hubapi.com/crm/v3/objects/contacts/search"
                    search_payload = {
                        "filterGroups": [{
                            "filters": [{
                                "propertyName": "email",
                                "operator": "EQ",
                                "value": email
                            }]
                        }],
                        "limit": 1
                    }
                    s_resp = _rq.post(search_url, json=search_payload, headers=headers, timeout=20)
                    if s_resp.ok:
                        results = s_resp.json().get("results", [])
                        if results:
                            existing_id = results[0].get("id")
                            print(f"ℹ️  Conflict; found existing contact via search: {existing_id}")
                            return {
                                "success": True,
                                "action": "existing",
                                "contact_id": existing_id,
                                "message": "Contact already existed — resolved via search"
                            }
        except Exception as parse_err:
            print(f"⚠️  Failed handling 409 fallback: {parse_err}")
        error_msg = f"HubSpot API request failed: {str(e)}"
        if hasattr(e, 'response') and e.response is not None:
            error_msg += f" - Status: {e.response.status_code}, Response: {e.response.text}"
        print(f"❌ {error_msg}")
        return {"success": False, "error": error_msg}
    except Exception as e:
        error_msg = f"HubSpot contact creation failed: {str(e)}"
        print(f"❌ {error_msg}")
        return {"success": False, "error": error_msg}


def hubspot_patch_conversation(contact_id: str, conversation_text: str, append_mode: bool = False):
    """Patch chatbot_conversation property for a HubSpot contact"""
    try:
        from environment import get_hubspot_config
        hubspot_config = get_hubspot_config()
        if not hubspot_config:
            return {"success": False, "error": "HubSpot not configured"}

        import requests
        url = f"https://api.hubapi.com/crm/v3/objects/contacts/{contact_id}"
        headers = {
            "Authorization": f"Bearer {hubspot_config['token']}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Always try chatbot_conversation first (we know it exists in schema)
        property_name = "chatbot_conversation"
        
        if append_mode:
            # First, get the existing conversation (explicitly request chatbot_conversation)
            print(f"🔍 Getting existing conversation for contact {contact_id}...")
            get_url = f"{url}?properties=chatbot_conversation,notes,email"
            get_resp = requests.get(get_url, headers=headers, timeout=20)
            if get_resp.ok:
                existing_data = get_resp.json()
                existing_conversation = existing_data.get("properties", {}).get(property_name)
                
                # If chatbot_conversation is not in response (empty/null), try notes as fallback
                if existing_conversation is None:
                    property_name = "notes"
                    existing_conversation = existing_data.get("properties", {}).get(property_name)
                    print(f"📄 Using {property_name} property instead of chatbot_conversation")
                
                # Handle None values
                if existing_conversation is None:
                    existing_conversation = ""
                
                print(f"📄 Existing conversation length: {len(existing_conversation)} characters")
                print(f"📄 Existing conversation type: {type(existing_conversation)}")
                
                # Append new conversation to existing one
                if existing_conversation:
                    combined_conversation = f"{existing_conversation}\n\n--- NEW SESSION ---\n{conversation_text}"
                    print(f"📄 Appending to existing conversation (total: {len(combined_conversation)} chars)")
                else:
                    combined_conversation = conversation_text
                    print(f"📄 No existing conversation, using new one (total: {len(combined_conversation)} chars)")
                
                payload = {
                    "properties": {
                        property_name: combined_conversation
                    }
                }
            else:
                print(f"⚠️  Failed to get existing conversation: {get_resp.status_code}")
                # If we can't get existing conversation, just use the new one
                payload = {
                    "properties": {
                        property_name: conversation_text
                    }
                }
        else:
            # Overwrite mode (original behavior)
            payload = {
                "properties": {
                    property_name: conversation_text
                }
            }
        
        print(f"📤 Sending PATCH request to HubSpot using {property_name}...")
        resp = requests.patch(url, json=payload, headers=headers, timeout=20)
        
        # Check if the property doesn't exist
        if resp.status_code == 400:
            error_data = resp.json()
            if "PROPERTY_DOESNT_EXIST" in str(error_data):
                # If chatbot_conversation doesn't exist, try notes as fallback
                if property_name == "chatbot_conversation":
                    print(f"⚠️  chatbot_conversation property doesn't exist, trying notes...")
                    property_name = "notes"
                    payload["properties"] = {property_name: conversation_text}
                    
                    # Retry with notes property
                    resp = requests.patch(url, json=payload, headers=headers, timeout=20)
                    if resp.ok:
                        action = "appended" if append_mode else "updated"
                        print(f"✅ HubSpot conversation {action} for contact {contact_id} using {property_name}")
                        return {"success": True, "action": action, "property_used": property_name}
                    else:
                        print(f"❌ Notes property also failed: {resp.status_code}")
                        return {"success": False, "error": f"Both chatbot_conversation and notes properties failed"}
                else:
                    error_msg = f"HubSpot property '{property_name}' does not exist. Please create this custom property in HubSpot Settings → Properties."
                    print(f"❌ {error_msg}")
                    return {"success": False, "error": error_msg, "property_missing": property_name}
        
        resp.raise_for_status()
        
        action = "appended" if append_mode else "updated"
        print(f"✅ HubSpot conversation {action} for contact {contact_id} using {property_name}")
        return {"success": True, "action": action, "property_used": property_name}
        
    except Exception as e:
        print(f"❌ HubSpot PATCH failed: {e}")
        return {"success": False, "error": str(e)}


def hubspot_get_conversation(contact_id: str):
    """Get existing chatbot_conversation property for a HubSpot contact"""
    try:
        from environment import get_hubspot_config
        hubspot_config = get_hubspot_config()
        if not hubspot_config:
            return {"success": False, "error": "HubSpot not configured"}

        import requests
        # Explicitly request chatbot_conversation property
        url = f"https://api.hubapi.com/crm/v3/objects/contacts/{contact_id}?properties=chatbot_conversation,notes,email"
        headers = {
            "Authorization": f"Bearer {hubspot_config['token']}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        resp = requests.get(url, headers=headers, timeout=20)
        if resp.ok:
            contact_data = resp.json()
            properties = contact_data.get("properties", {})
            
            # Try chatbot_conversation first (we explicitly requested it)
            conversation = properties.get("chatbot_conversation")
            property_used = "chatbot_conversation"
            
            # If chatbot_conversation is not in response (empty/null), try notes as fallback
            if conversation is None:
                conversation = properties.get("notes")
                property_used = "notes"
                print(f"📄 Using {property_used} property instead of chatbot_conversation")
            
            # Handle None values
            if conversation is None:
                conversation = ""
            
            print(f"📄 Retrieved conversation length: {len(conversation)} characters")
            print(f"📄 Retrieved conversation type: {type(conversation)}")
            print(f"📄 Property used: {property_used}")
            
            return {"success": True, "conversation": conversation, "property_used": property_used}
        else:
            print(f"❌ Failed to get contact: {resp.status_code}")
            print(f"❌ Response: {resp.text}")
            return {"success": False, "error": f"Failed to get contact: {resp.status_code}"}
            
    except Exception as e:
        print(f"❌ HubSpot GET failed: {e}")
        return {"success": False, "error": str(e)}


def hubspot_append_conversation(contact_id: str, conversation_text: str):
    """Append to existing chatbot_conversation property for a HubSpot contact"""
    return hubspot_patch_conversation(contact_id, conversation_text, append_mode=True)