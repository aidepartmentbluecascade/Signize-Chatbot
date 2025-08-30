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


def hubspot_patch_conversation(contact_id: str, conversation_text: str):
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
        payload = {
            "properties": {
                "chatbot_conversation": conversation_text
            }
        }
        resp = requests.patch(url, json=payload, headers=headers, timeout=20)
        resp.raise_for_status()
        print(f"✅ HubSpot conversation patched for contact {contact_id}")
        return {"success": True}
    except Exception as e:
        print(f"❌ HubSpot PATCH failed: {e}")
        return {"success": False, "error": str(e)}