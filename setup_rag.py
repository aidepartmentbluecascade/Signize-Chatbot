#!/usr/bin/env python3
"""
Setup script to initialize RAG system with existing documents
"""

import os
import sys
from environment import load_environment
from chromadb_setup import initialize_chromadb
from document_processing import load_documents_from_directory, preprocess_documents
from embedding_generation import generate_embeddings
from db_operations import upsert_documents_into_db
from openai import OpenAI

def setup_rag_system():
    """Initialize RAG system with documents from data directory"""
    
    print("🚀 Setting up RAG system...")
    
    # Load environment and initialize OpenAI client
    openai_key = load_environment()
    client = OpenAI(api_key=openai_key)
    
    # Initialize ChromaDB
    print("📚 Initializing ChromaDB...")
    collection = initialize_chromadb(openai_key)
    
    # Check if collection already has data
    try:
        count = collection.count()
        if count > 0:
            print(f"✅ ChromaDB collection already has {count} documents")
            return collection
    except Exception as e:
        print(f"⚠️  Error checking collection count: {e}")
    
    # Load documents from data directory
    data_dir = "data"
    if not os.path.exists(data_dir):
        print(f"❌ Data directory '{data_dir}' not found")
        return None
    
    print(f"📖 Loading documents from {data_dir}...")
    documents = load_documents_from_directory(data_dir)
    
    if not documents:
        print("❌ No documents found in data directory")
        return None
    
    # Preprocess documents into chunks
    print("✂️  Preprocessing documents into chunks...")
    chunked_documents = preprocess_documents(documents, chunk_size=1000, chunk_overlap=200)
    
    # Generate embeddings
    print("🧠 Generating embeddings...")
    chunked_documents_with_embeddings = generate_embeddings(client, chunked_documents)
    
    # Add documents to ChromaDB
    print("💾 Adding documents to ChromaDB...")
    try:
        upsert_documents_into_db(collection, chunked_documents_with_embeddings)
        print(f"✅ Added {len(chunked_documents_with_embeddings)} documents to ChromaDB")
    except Exception as e:
        print(f"⚠️  Error adding documents to ChromaDB: {e}")
        return None
    
    # Verify setup
    try:
        final_count = collection.count()
        print(f"✅ RAG system setup complete! Collection has {final_count} documents")
        return collection
    except Exception as e:
        print(f"❌ Error verifying setup: {e}")
        return None

if __name__ == "__main__":
    print("🧪 Testing RAG system setup...")
    collection = setup_rag_system()
    
    if collection:
        print("\n🎉 RAG system is ready!")
        print("You can now use the chatbot with knowledge base integration.")
    else:
        print("\n💥 RAG system setup failed!")
        sys.exit(1)
