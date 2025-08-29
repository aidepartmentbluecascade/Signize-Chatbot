#!/usr/bin/env python3
"""
Test script to verify RAG integration with the chatbot
"""

import requests
import json
import time

def test_rag_integration():
    """Test the RAG integration with the chatbot"""
    
    base_url = "http://localhost:5000"
    
    print("🧪 Testing RAG integration...")
    
    # 1. Check RAG status
    print("\n1. Checking RAG system status...")
    try:
        response = requests.get(f"{base_url}/rag-status")
        status_data = response.json()
        print(f"Status: {status_data}")
        
        if not status_data.get("success"):
            print("⚠️  RAG system not ready, attempting setup...")
            
            # 2. Setup RAG system
            print("\n2. Setting up RAG system...")
            setup_response = requests.post(f"{base_url}/setup-rag")
            setup_data = setup_response.json()
            print(f"Setup result: {setup_data}")
            
            if not setup_data.get("success"):
                print("❌ Failed to setup RAG system")
                return False
        else:
            print("✅ RAG system is ready")
            
    except Exception as e:
        print(f"❌ Error checking RAG status: {e}")
        return False
    
    # 3. Test chat with RAG
    print("\n3. Testing chat with RAG...")
    
    # Generate a session ID
    session_id = f"test_session_{int(time.time())}"
    
    # Test message that should trigger knowledge base lookup
    test_message = "What types of signs do you offer?"
    
    try:
        chat_response = requests.post(f"{base_url}/chat", json={
            "message": test_message,
            "session_id": session_id,
            "email": "test@example.com"
        })
        
        chat_data = chat_response.json()
        print(f"Chat response: {chat_data.get('message', 'No message')}")
        
        if chat_data.get("message"):
            print("✅ Chat with RAG working")
            return True
        else:
            print("❌ No response from chat")
            return False
            
    except Exception as e:
        print(f"❌ Error testing chat: {e}")
        return False

def test_knowledge_base_queries():
    """Test specific knowledge base queries"""
    
    print("\n🔍 Testing specific knowledge base queries...")
    
    test_queries = [
        "What are the different types of signs you offer?",
        "How long does it take to make a sign?",
        "What materials do you use for signs?",
        "Do you offer installation services?",
        "What are your pricing options?"
    ]
    
    base_url = "http://localhost:5000"
    session_id = f"test_session_{int(time.time())}"
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        try:
            response = requests.post(f"{base_url}/chat", json={
                "message": query,
                "session_id": session_id,
                "email": "test@example.com"
            })
            
            data = response.json()
            print(f"Response: {data.get('message', 'No response')[:200]}...")
            
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    print("🚀 Starting RAG integration tests...")
    
    success = test_rag_integration()
    
    if success:
        print("\n✅ Basic RAG integration test passed!")
        test_knowledge_base_queries()
    else:
        print("\n❌ RAG integration test failed!")
    
    print("\n🎉 RAG integration testing complete!")
