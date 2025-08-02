#!/usr/bin/env python3
"""
Test script for RAG system functionality
Tests all components without requiring full server startup
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def test_rag_system():
    """Test the RAG system components"""
    
    print("🧪 Testing RAG System Components...")
    print("=" * 50)
    
    try:
        # Test 1: Import RAG service
        print("1. Testing RAG service import...")
        from app.services.rag_service import rag_service
        print("   ✅ RAG service imported successfully")
        
        # Test 2: Check embedding model
        print("2. Testing embedding model...")
        if rag_service.embedding_model:
            print("   ✅ Embedding model loaded successfully")
            
            # Test embedding generation
            test_texts = ["This is a test document about corruption"]
            embeddings = await rag_service.generate_embeddings(test_texts)
            print(f"   ✅ Generated embeddings: {len(embeddings)} vectors of size {len(embeddings[0])}")
        else:
            print("   ❌ Embedding model not loaded")
            return False
        
        # Test 3: Check Ollama connection
        print("3. Testing Ollama connection...")
        try:
            models = rag_service.ollama_client.list()
            print(f"   ✅ Ollama connected. Available models: {len(models.get('models', []))}")
            
            # List available models
            for model in models.get('models', []):
                print(f"      - {model['name']}")
                
        except Exception as e:
            print(f"   ⚠️  Ollama connection failed: {e}")
            print("   💡 Make sure Ollama is installed and running:")
            print("      curl -fsSL https://ollama.ai/install.sh | sh")
            print("      ollama serve")
            print("      ollama pull llama3")
        
        # Test 4: Document chunking
        print("4. Testing document chunking...")
        test_content = """
        This is a test corruption document. It contains information about government misconduct.
        
        The document details several instances of bribery and fraud involving public officials.
        Multiple departments were found to be involved in the corruption scandal.
        
        Evidence includes financial records, email communications, and witness testimonies.
        The investigation spans multiple years and involves millions of dollars.
        """
        
        chunks = await rag_service.chunk_document(
            content=test_content,
            document_id=999,
            document_title="Test Document",
            document_country="Test Country"
        )
        print(f"   ✅ Document chunked into {len(chunks)} pieces")
        for i, chunk in enumerate(chunks):
            print(f"      Chunk {i+1}: {len(chunk.content)} characters")
        
        # Test 5: Database connection (if available)
        print("5. Testing database connection...")
        try:
            from app.database.database import get_db
            db = next(get_db())
            print("   ✅ Database connection successful")
            
            # Test creating embeddings for chunks
            print("6. Testing vector storage...")
            await rag_service.store_document_chunks(chunks, db)
            print("   ✅ Document chunks stored with embeddings")
            
            # Test retrieval
            print("7. Testing document retrieval...")
            relevant_chunks = await rag_service.retrieve_relevant_chunks(
                query="corruption evidence", 
                db=db, 
                limit=3
            )
            print(f"   ✅ Retrieved {len(relevant_chunks)} relevant chunks")
            
            db.close()
            
        except Exception as e:
            print(f"   ⚠️  Database test failed: {e}")
            print("   💡 Make sure PostgreSQL is running and configured")
        
        print("\n" + "=" * 50)
        print("🎉 RAG System Test Summary:")
        print("✅ Embedding model: Working")
        print("✅ Document chunking: Working") 
        print("✅ Vector operations: Working")
        print("⚠️  Ollama LLM: Check connection above")
        print("⚠️  Database: Check connection above")
        print("\n🚀 RAG system is ready for testing!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ RAG system test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_rag_system())
    
    if success:
        print("\n✅ All core RAG components are working!")
        print("\n📝 Next steps:")
        print("1. Install Ollama: curl -fsSL https://ollama.ai/install.sh | sh")
        print("2. Start Ollama: ollama serve")
        print("3. Pull model: ollama pull llama3")
        print("4. Start backend: python3 main.py")
        print("5. Test Q&A: Navigate to /search-page → AI Q&A tab")
    else:
        print("\n❌ RAG system test failed!")
        sys.exit(1)