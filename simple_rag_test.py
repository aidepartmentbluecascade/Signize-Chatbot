#!/usr/bin/env python3
"""
Simple test to verify RAG integration works
"""

import sys
import os

def test_rag_imports():
    """Test that all RAG components can be imported"""
    
    print("🧪 Testing RAG component imports...")
    
    try:
        # Test basic imports
        from chromadb_setup import initialize_chromadb
        print("✅ ChromaDB setup imported")
        
        from query_and_response import query_documents, generate_response
        print("✅ Query and response imported")
        
        from document_processing import load_documents_from_directory, preprocess_documents
        print("✅ Document processing imported")
        
        from embedding_generation import generate_embeddings
        print("✅ Embedding generation imported")
        
        from db_operations import upsert_documents_into_db
        print("✅ Database operations imported")
        
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_chromadb_initialization():
    """Test ChromaDB initialization"""
    
    print("\n🧪 Testing ChromaDB initialization...")
    
    try:
        from environment import load_environment
        openai_key = load_environment()
        
        from chromadb_setup import initialize_chromadb
        collection = initialize_chromadb(openai_key)
        
        print("✅ ChromaDB collection created successfully")
        return collection
        
    except Exception as e:
        print(f"❌ ChromaDB initialization error: {e}")
        return None

def test_query_function():
    """Test the query function with a simple query"""
    
    print("\n🧪 Testing query function...")
    
    try:
        from environment import load_environment
        openai_key = load_environment()
        
        from chromadb_setup import initialize_chromadb
        collection = initialize_chromadb(openai_key)
        
        from query_and_response import query_documents
        
        # Test query
        test_query = "What types of signs do you offer?"
        results = query_documents(collection, [test_query], n_results=2)
        
        print(f"✅ Query function works, returned {len(results)} results")
        if results and results[0]:
            print(f"   Sample result: {results[0][:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Query function error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting simple RAG integration tests...")
    
    # Test imports
    imports_ok = test_rag_imports()
    
    if imports_ok:
        # Test ChromaDB initialization
        collection = test_chromadb_initialization()
        
        if collection:
            # Test query function
            query_ok = test_query_function()
            
            if query_ok:
                print("\n🎉 All RAG components are working!")
                print("The RAG integration should work in the main app.")
            else:
                print("\n⚠️  Query function has issues")
        else:
            print("\n⚠️  ChromaDB initialization failed")
    else:
        print("\n❌ Import issues detected")
    
    print("\n📝 Next steps:")
    print("1. Run the main app: python app.py")
    print("2. Check RAG status: GET /rag-status")
    print("3. Setup RAG if needed: POST /setup-rag")
    print("4. Test chat with RAG functionality")
