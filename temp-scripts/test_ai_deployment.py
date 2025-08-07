#!/usr/bin/env python3
"""Test AI/RAG functionality during deployment"""

import asyncio
import sys
import os
import time
import requests
import json

# Add backend to path
sys.path.append('/opt/foi-archive/backend')

def test_ai_deployment():
    print("🤖 Testing AI/RAG Functionality")
    print("=" * 40)
    
    # 1. Test backend API health
    print("1. Testing backend API...")
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("   ✅ Backend API responding")
        else:
            print(f"   ❌ Backend API error: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Backend API not accessible: {e}")
        return False
    
    # 2. Test RAG status endpoint
    print("2. Testing RAG system status...")
    try:
        response = requests.get("http://localhost:8000/rag/status", timeout=10)
        if response.status_code == 200:
            status_data = response.json()
            print(f"   Status: {status_data.get('status', 'unknown')}")
            print(f"   Ollama: {'✅' if status_data.get('ollama_available') else '❌'}")
            print(f"   Embeddings: {'✅' if status_data.get('embedding_model_loaded') else '❌'}")
            print(f"   Chunks: {status_data.get('total_chunks', 0)}")
            
            if status_data.get('status') == 'operational':
                rag_status_ok = True
            else:
                print("   ⚠️ RAG system not fully operational")
                rag_status_ok = False
        else:
            print(f"   ❌ RAG status error: {response.status_code}")
            rag_status_ok = False
    except Exception as e:
        print(f"   ❌ RAG status check failed: {e}")
        rag_status_ok = False
    
    # 3. Test AI question answering
    print("3. Testing AI question answering...")
    try:
        start_time = time.time()
        
        test_question = "Do you have documents about Egypt?"
        response = requests.post(
            "http://localhost:8000/rag/question",
            json={"question": test_question},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        response_time = int((time.time() - start_time) * 1000)
        
        if response.status_code == 200:
            data = response.json()
            confidence = data.get('confidence', 0)
            sources_count = len(data.get('sources', []))
            
            print(f"   Response time: {response_time}ms")
            print(f"   Confidence: {confidence*100:.1f}%")
            print(f"   Sources: {sources_count}")
            
            if confidence > 0.1:  # At least 10% confidence
                print("   ✅ AI answering working")
                ai_working = True
            elif response_time < 5000:  # Quick response but low confidence
                print("   ⚠️ AI responding but low confidence (vector search issue)")
                ai_working = "partial"
            else:
                print("   ❌ AI not working properly")
                ai_working = False
        else:
            print(f"   ❌ AI question error: {response.status_code}")
            ai_working = False
            
    except Exception as e:
        print(f"   ❌ AI question test failed: {e}")
        ai_working = False
    
    # 4. Overall assessment
    print("4. Overall AI System Assessment:")
    
    if ai_working == True:
        print("   🎉 AI SYSTEM FULLY OPERATIONAL")
        return True
    elif ai_working == "partial" and rag_status_ok:
        print("   ⚠️ AI SYSTEM PARTIALLY WORKING (vector search needs optimization)")
        return True
    else:
        print("   ❌ AI SYSTEM NOT WORKING")
        return False

if __name__ == "__main__":
    success = test_ai_deployment()
    exit(0 if success else 1)