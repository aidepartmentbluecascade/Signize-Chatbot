from mongodb_operations import mongodb_manager
from datetime import datetime
from prompt.prompt import SIGN_NIZE_SYSTEM_PROMPT
from documents_processing_responses.query_and_response import query_documents
from chromadb_setup import initialize_chromadb
from environment import load_environment

# Load environment variables
openai_key = load_environment()

def build_conversation_text(messages: list, session_id: str = None) -> str:
    import re

    lines = []
    for m in messages[-100:]:  # cap to last 100 messages to avoid huge payloads
        role = m.get("role", "")
        content = m.get("content", "")

        # Strip HTML tags and asterisks for HubSpot
        # Remove HTML bold tags
        content = re.sub(r'<b>(.*?)</b>', r'\1', content)
        # Remove asterisks
        content = re.sub(r'\*\*(.*?)\*\*', r'\1', content)
        # Remove any remaining HTML tags
        content = re.sub(r'<[^>]+>', '', content)

        prefix = "User" if role == "user" else ("Assistant" if role == "assistant" else role)
        lines.append(f"{prefix}: {content}")

    # Add quote form data if available for this session
    if session_id:
        try:
            quote_result = mongodb_manager.get_quote_data(session_id)
            if quote_result.get("success") and quote_result.get("quote", {}).get("form_data"):
                form_data = quote_result["quote"]["form_data"]
                lines.append("\n--- QUOTE FORM DATA ---")
                lines.append(f"Session ID: {session_id}")

                # Add key form fields
                if form_data.get("sizeDimensions"):
                    lines.append(f"Size: {form_data['sizeDimensions']}")
                elif form_data.get("width") and form_data.get("height"):
                    width_unit = form_data.get("widthUnit", "inches")
                    height_unit = form_data.get("heightUnit", "inches")
                    lines.append(f"Size: {form_data['width']} {width_unit} × {form_data['height']} {height_unit}")

                if form_data.get("materialPreference"):
                    materials = form_data["materialPreference"]
                    if isinstance(materials, list):
                        materials = ", ".join(materials)
                    lines.append(f"Material: {materials}")

                if form_data.get("illumination"):
                    illumination = form_data["illumination"]
                    if isinstance(illumination, list):
                        illumination = ", ".join(illumination)
                    lines.append(f"Illumination: {illumination}")

                if form_data.get("cityState"):
                    lines.append(f"Location: {form_data['cityState']}")

                if form_data.get("budget"):
                    budget = form_data["budget"]
                    if isinstance(budget, list):
                        budget = ", ".join(budget)
                    lines.append(f"Budget: {budget}")

                if form_data.get("placement"):
                    placement = form_data["placement"]
                    if isinstance(placement, list):
                        placement = ", ".join(placement)
                    lines.append(f"Placement: {placement}")

                if form_data.get("deadline"):
                    deadline = form_data["deadline"]
                    if isinstance(deadline, list):
                        deadline = ", ".join(deadline)
                    lines.append(f"Deadline: {deadline}")

                if form_data.get("additionalNotes"):
                    lines.append(f"Notes: {form_data['additionalNotes']}")

                # Add logo information
                if form_data.get("uploadedLogos"):
                    lines.append(f"Logos: {len(form_data['uploadedLogos'])} file(s) uploaded")
                    for i, logo in enumerate(form_data["uploadedLogos"], 1):
                        lines.append(f"  Logo {i}: {logo.get('filename', 'Unknown')}")

                lines.append("--- END QUOTE FORM DATA ---")
        except Exception as e:
            print(f"⚠️  Error adding quote form data to conversation: {e}")

    return "\n".join(lines)

# Initialize RAG system
print("🚀 Initializing RAG system...")
try:
    chroma_collection = initialize_chromadb(openai_key)
    print("✅ ChromaDB collection initialized")
except Exception as e:
    print(f"⚠️  Failed to initialize ChromaDB: {e}")
    chroma_collection = None

def generate_sign_nize_response(client, user_message, session_data):
    """Generate response using the Sign-nize customer support system prompt with context awareness and RAG"""

    current_date = datetime.now().strftime('%B %d, %Y')
    system_prompt = SIGN_NIZE_SYSTEM_PROMPT.replace('{{date}}', current_date)

    knowledge_context = ""
    if chroma_collection:
        try:
            print("🔍 Querying knowledge base for relevant information...")
            relevant_chunks = query_documents(chroma_collection, [user_message], n_results=3)
            if relevant_chunks and relevant_chunks[0]:
                knowledge_context = "\n\nKNOWLEDGE BASE CONTEXT:\n" + "\n\n".join(relevant_chunks)
                print(f"✅ Found {len(relevant_chunks)} relevant knowledge chunks")
            else:
                print("ℹ️  No relevant knowledge base information found")
        except Exception as e:
            print(f"⚠️  Error querying knowledge base: {e}")

    conversation_context = ""
    if session_data["messages"]:
        conversation_context = "\n\nFULL CONVERSATION HISTORY:\n"
        for msg in session_data["messages"]:
            role = "User" if msg["role"] == "user" else "Assistant"
            conversation_context += f"{role}: {msg['content']}\n"

    email_already_collected = False
    email_value = None

    if session_data.get("email"):
        email_already_collected = True
        email_value = session_data.get("email")
    elif session_data.get("customer_info", {}).get("email"):
        email_already_collected = True
        email_value = session_data.get("customer_info", {}).get("email")

    if not email_already_collected and session_data["messages"]:
        for msg in session_data["messages"]:
            if msg["role"] == "user" and "@" in msg["content"]:
                # Extract email from the message
                import re
                email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', msg["content"])
                if email_match:
                    email_already_collected = True
                    email_value = email_match.group(0)

                    session_data["email"] = email_value
                    break

    email_context = ""
    if email_value:
        email_context = f"""
CURRENT SESSION EMAIL: {email_value}
- This email has already been collected and verified
- Do NOT ask for email again in this session
- Use this email for all quote requests and order tracking
- If customer says "bye" and then starts talking again, they still have the same email
"""
        print(f"📧 Email context injected: {email_value}")
    else:
        email_context = """
CURRENT SESSION EMAIL: NOT COLLECTED
- This is a new conversation or email not yet provided
- Follow the email collection process for first message
"""
        print("📧 Email context: NOT COLLECTED")

    print(f"🔍 Email already collected: {email_already_collected}")
    print(f"📧 Email value: {email_value}")

    context_instructions = f"""

CONTEXT INSTRUCTIONS:
1. CAREFULLY READ the full conversation history above.
2. If this is the customer's FIRST message in the conversation, ALWAYS ask for email first.
3. If email is already collected, NEVER ask for it again - this is a CRITICAL rule.
4. After email collection, ask "How can I help you with your sign needs today?"
5. Handle order issues by collecting Order ID and phone number, then tell customer representative will contact them.
6. For general sign questions after order issues, provide helpful information without asking "How can I help you" again.
7. CRITICAL: Trigger quote form with [QUOTE_FORM_TRIGGER] when customer says ANYTHING about wanting mockup, quote, pricing, or estimate - this is a TOP PRIORITY.
8. CRITICAL: Even if customer says "Hi" again after email collection, do NOT ask for email - just say "Hello! How can I help you with your sign needs today?"
9. CRITICAL: When customer wants to update/modify their quote, ALWAYS trigger the form with [QUOTE_FORM_TRIGGER].
10. CRITICAL: For irrelevant questions (weather, politics, etc.), redirect to signage topics professionally.
11. CRITICAL: For goodbye messages, give warm Signize farewell.
12. CRITICAL: Questions about signs, materials, installation, pricing, etc. are ALWAYS relevant - answer them helpfully.
13. CRITICAL: When customers ask about specific sign types (2D, 3D, metal, acrylic, etc.), provide detailed information about those types - NEVER give generic greetings.
14. CRITICAL: Use the knowledge base to provide comprehensive answers about sign types, materials, and applications.
15. CRITICAL: The email {email_value if email_value else 'has not been collected yet'} - use this information to determine if email collection is needed.
16. CRITICAL: Email persists throughout the session - if customer says "bye" and then talks again, they still have the same email.
17. CRITICAL: Only ask for email if this is a completely new session or if email was never collected.
"""

    full_prompt = system_prompt + email_context + context_instructions + knowledge_context + conversation_context + f"\n\nCurrent User Message: {user_message}"

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": full_prompt,
            },
            {
                "role": "user",
                "content": user_message,
            },
        ],
        max_tokens=1500,
        temperature=0.0
    )

    return response.choices[0].message.content
