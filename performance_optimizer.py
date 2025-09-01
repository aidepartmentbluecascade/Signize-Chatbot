#!/usr/bin/env python3
"""
Performance optimization module for millisecond-level responses
"""

import time
import asyncio
import threading
from functools import wraps, lru_cache
from concurrent.futures import ThreadPoolExecutor, as_completed
import redis
import json
from typing import Dict, List, Optional
import hashlib
from redis_config import redis_config

# Global cache and executor
response_cache = {}
ai_response_cache = {}
executor = ThreadPoolExecutor(max_workers=20)
redis_client = None

try:
    # Connect to Redis using configuration
    redis_client = redis.Redis(**redis_config.get_connection_params())
    
    # Test the connection
    redis_client.ping()
    print(f"✅ Redis Cloud connected: {redis_config.host}:{redis_config.port}")
    
except Exception as e:
    print(f"⚠️  Redis Cloud connection failed: {e}")
    print("⚠️  Using in-memory cache as fallback")
    redis_client = None

def timing_decorator(f):
    """Decorator to measure function execution time"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = f(*args, **kwargs)
        end = time.time()
        print(f"⏱️  {f.__name__} took {(end-start)*1000:.1f}ms")
        return result
    return wrapper

def cache_key_generator(session_id: str, message: str, email: str = "") -> str:
    """Generate cache key for responses"""
    content = f"{session_id}:{message}:{email}"
    return hashlib.md5(content.encode()).hexdigest()

@lru_cache(maxsize=1000)
def cached_chroma_query(query: str, n_results: int = 3) -> List[str]:
    """Cache ChromaDB queries for repeated questions"""
    from documents_processing_responses.query_and_response import query_documents
    from chromadb_setup import initialize_chromadb
    from environment import load_environment
    
    try:
        openai_key = load_environment()
        collection = initialize_chromadb(openai_key)
        results = query_documents(collection, [query], n_results)
        return results if results else [""]
    except Exception as e:
        print(f"⚠️  ChromaDB query failed: {e}")
        return [""]

def async_save_to_sheets(session_id: str, email: str, messages: List[Dict]):
    """Save to Google Sheets asynchronously"""
    try:
        from session_manager.session_manager import save_session_to_sheets
        save_session_to_sheets(session_id, email, messages, update_existing=True)
    except Exception as e:
        print(f"⚠️  Async Google Sheets save failed: {e}")

def async_save_to_mongodb(session_id: str, email: str, messages: List[Dict]):
    """Save to MongoDB asynchronously"""
    try:
        from mongodb_operations import mongodb_manager
        mongodb_manager.save_chat_session(session_id, email, messages)
    except Exception as e:
        print(f"⚠️  Async MongoDB save failed: {e}")

def async_hubspot_sync(session_id: str, email: str, messages: List[Dict]):
    """Sync to HubSpot asynchronously"""
    try:
        from hubspot.hubspot import hubspot_patch_conversation
        from mongodb_operations import mongodb_manager
        
        # Get contact_id by email
        db_session = mongodb_manager.get_chat_session_by_email(email)
        if db_session.get("success"):
            contact_id = db_session["session"].get("hubspot_contact_id")
            if contact_id:
                conversation_text = build_conversation_text(messages, session_id)
                hubspot_patch_conversation(contact_id, conversation_text)
    except Exception as e:
        print(f"⚠️  Async HubSpot sync failed: {e}")

def build_conversation_text(messages: List[Dict], session_id: str = None) -> str:
    """Optimized conversation text builder"""
    import re
    
    lines = []
    # Only process last 20 messages for speed
    for m in messages[-20:]:
        role = m.get("role", "")
        content = m.get("content", "")
        
        # Fast HTML tag removal
        content = re.sub(r'<[^>]+>', '', content)
        content = re.sub(r'\*\*([^*]+)\*\*', r'\1', content)
        
        prefix = "User" if role == "user" else "Assistant"
        lines.append(f"{prefix}: {content}")
    
    return "\n".join(lines)

class FastResponseGenerator:
    """Optimized response generator for millisecond responses"""
    
    def __init__(self):
        self.cache = {}
        self.common_responses = {
            "greeting": "Hello! How can I help you with your sign needs today?",
            "email_request": "Hi there! I'd be happy to help you with your sign needs. First, could you please provide your email address so I can save your information and follow up with you?",
            "quote_trigger": "I'd be happy to help you get a quote! Let me gather some details about your sign project. [QUOTE_FORM_TRIGGER]",
            "goodbye": "Thank you for chatting with us! If you have any more questions about signs, feel free to reach out anytime. Have a great day!"
        }
    
    def get_cached_response(self, session_id: str, message: str, email: str = "") -> Optional[str]:
        """Get cached response if available"""
        cache_key = cache_key_generator(session_id, message, email)
        
        if redis_client:
            cached = redis_client.get(f"response:{cache_key}")
            if cached:
                return json.loads(cached)
        else:
            return response_cache.get(cache_key)
        
        return None
    
    def cache_response(self, session_id: str, message: str, email: str, response: str):
        """Cache response for future use"""
        cache_key = cache_key_generator(session_id, message, email)
        
        if redis_client:
            redis_client.setex(f"response:{cache_key}", 3600, json.dumps(response))  # 1 hour TTL
        else:
            response_cache[cache_key] = response
    
    def is_simple_query(self, message: str) -> bool:
        """Check if message is a simple query that can be answered quickly"""
        simple_patterns = [
            r"^hi$|^hello$|^hey$",
            r"^bye$|^goodbye$|^thanks$|^thank you$",
            r"^what materials do you offer\?$",
            r"^how much does.*cost\?$",
            r"^what sizes.*available\?$"
        ]
        
        import re
        message_lower = message.lower().strip()
        return any(re.match(pattern, message_lower) for pattern in simple_patterns)
    
    def get_quick_response(self, message: str, email_collected: bool) -> Optional[str]:
        """Get quick response for simple queries"""
        message_lower = message.lower().strip()
        
        if not email_collected and "hi" in message_lower:
            return self.common_responses["email_request"]
        
        if email_collected:
            if "hi" in message_lower or "hello" in message_lower:
                return self.common_responses["greeting"]
            elif "bye" in message_lower or "goodbye" in message_lower:
                return self.common_responses["goodbye"]
            elif "quote" in message_lower or "pricing" in message_lower:
                return self.common_responses["quote_trigger"]
        
        return None
    
    @timing_decorator
    def generate_response(self, client, user_message: str, session_data: Dict) -> str:
        """Generate optimized response"""
        
        # Check cache first
        session_id = session_data.get("session_id", "default")
        email = session_data.get("email", "")
        
        cached_response = self.get_cached_response(session_id, user_message, email)
        if cached_response:
            print("🚀 Returning cached response")
            return cached_response
        
        # Check for quick response
        email_collected = bool(email)
        quick_response = self.get_quick_response(user_message, email_collected)
        if quick_response:
            print("⚡ Returning quick response")
            self.cache_response(session_id, user_message, email, quick_response)
            return quick_response
        
        # Generate full AI response
        print("🤖 Generating AI response")
        full_response = self._generate_ai_response(client, user_message, session_data)
        
        # Cache the response
        self.cache_response(session_id, user_message, email, full_response)
        
        return full_response
    
    def _generate_ai_response(self, client, user_message: str, session_data: Dict) -> str:
        """Generate full AI response with optimizations"""
        from prompt.prompt import SIGN_NIZE_SYSTEM_PROMPT
        from datetime import datetime
        
        # Optimize context building
        current_date = datetime.now().strftime('%B %d, %Y')
        system_prompt = SIGN_NIZE_SYSTEM_PROMPT.replace('{{date}}', current_date)
        
        # Async ChromaDB query
        knowledge_context = ""
        if hasattr(self, 'chroma_collection') and self.chroma_collection:
            try:
                # Use cached query if available
                knowledge_chunks = cached_chroma_query(user_message, 2)  # Reduced from 3 to 2
                if knowledge_chunks and knowledge_chunks[0]:
                    knowledge_context = "\n\nKNOWLEDGE BASE CONTEXT:\n" + "\n\n".join(knowledge_chunks)
            except Exception as e:
                print(f"⚠️  Knowledge base query failed: {e}")
        
        # Optimize conversation context (only last 10 messages)
        conversation_context = ""
        messages = session_data.get("messages", [])
        if messages:
            conversation_context = "\n\nRECENT CONVERSATION:\n"
            for msg in messages[-10:]:  # Only last 10 messages
                role = "User" if msg["role"] == "user" else "Assistant"
                conversation_context += f"{role}: {msg['content']}\n"
        
        # Simplified email context
        email = session_data.get("email", "")
        email_context = f"CURRENT EMAIL: {email}" if email else "EMAIL: NOT COLLECTED"
        
        # Reduced context instructions
        context_instructions = """
CONTEXT: If email not collected, ask for it. If email collected, help with sign needs. 
Trigger [QUOTE_FORM_TRIGGER] for quote requests. Keep responses helpful and concise.
"""
        
        # Build optimized prompt
        full_prompt = f"{system_prompt}\n{email_context}\n{context_instructions}\n{knowledge_context}\n{conversation_context}\n\nUser: {user_message}"
        
        # Make AI call
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": full_prompt},
                {"role": "user", "content": user_message},
            ],
            max_tokens=800,  # Reduced from 1500
            temperature=0.0
        )
        
        return response.choices[0].message.content

# Global instance
fast_generator = FastResponseGenerator()
