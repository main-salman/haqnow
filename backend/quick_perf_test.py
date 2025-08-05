#!/usr/bin/env python3
"""
Quick performance test for RAG database operations.
Run this to get immediate insights into your database performance.
"""

import time
import psycopg2
import os
from sqlalchemy import create_engine, text
from app.database.rag_database import get_rag_database_url, rag_engine

def test_database_performance():
    """Quick test of database performance"""
    print("🔍 Quick RAG Database Performance Test")
    print("="*50)
    
    # Get database connection details
    host = os.getenv("POSTGRES_RAG_HOST", "localhost")
    port = int(os.getenv("POSTGRES_RAG_PORT", "5432"))
    user = os.getenv("POSTGRES_RAG_USER")
    password = os.getenv("POSTGRES_RAG_PASSWORD")
    database = os.getenv("POSTGRES_RAG_DATABASE")
    
    print(f"Testing connection to: {host}:{port}")
    print()
    
    # Test 1: Network latency (10 quick pings)
    print("📡 Testing network latency...")
    latencies = []
    
    for i in range(10):
        start_time = time.time()
        try:
            conn = psycopg2.connect(
                host=host, port=port, user=user, 
                password=password, database=database,
                connect_timeout=5
            )
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            conn.close()
            
            latency_ms = (time.time() - start_time) * 1000
            latencies.append(latency_ms)
            print(f"  Ping {i+1}: {latency_ms:.1f}ms")
            
        except Exception as e:
            print(f"  Ping {i+1}: FAILED - {e}")
    
    if latencies:
        avg_latency = sum(latencies) / len(latencies)
        min_latency = min(latencies)
        max_latency = max(latencies)
        
        print(f"\n📊 Network Performance:")
        print(f"  Average: {avg_latency:.1f}ms")
        print(f"  Range: {min_latency:.1f}ms - {max_latency:.1f}ms")
        
        # Assessment
        if avg_latency > 50:
            print("  🚨 HIGH LATENCY - Local DB would significantly improve speed")
            potential_savings = avg_latency * 0.8  # Assume 80% reduction with local
            print(f"  💡 Potential time savings: ~{potential_savings:.1f}ms per query")
        elif avg_latency > 20:
            print("  ⚠️  MODERATE LATENCY - Local DB would provide some improvement")
            potential_savings = avg_latency * 0.6
            print(f"  💡 Potential time savings: ~{potential_savings:.1f}ms per query")
        else:
            print("  ✅ LOW LATENCY - External DBaaS performance is good")
    
    print()
    
    # Test 2: Vector search query
    print("🔍 Testing vector search performance...")
    
    try:
        # Sample 384-dimensional embedding
        sample_embedding = '[' + ','.join(['0.1'] * 384) + ']'
        
        search_times = []
        for i in range(5):
            start_time = time.time()
            
            with rag_engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT 
                        document_id,
                        content,
                        (embedding <=> :embedding::vector) as similarity
                    FROM document_chunks 
                    ORDER BY embedding <=> :embedding::vector
                    LIMIT 5
                """), embedding=sample_embedding)
                
                rows = result.fetchall()
                search_time_ms = (time.time() - start_time) * 1000
                search_times.append(search_time_ms)
                print(f"  Search {i+1}: {search_time_ms:.1f}ms ({len(rows)} results)")
        
        if search_times:
            avg_search = sum(search_times) / len(search_times)
            print(f"\n📊 Vector Search Performance:")
            print(f"  Average: {avg_search:.1f}ms")
            
            if avg_search > 200:
                print("  🚨 SLOW - Needs optimization")
            elif avg_search > 100:
                print("  ⚠️  MODERATE - Room for improvement")
            else:
                print("  ✅ GOOD - Performing well")
                
    except Exception as e:
        print(f"  ❌ Vector search test failed: {e}")
        print("  💡 This might indicate missing data or configuration issues")
    
    print()
    
    # Test 3: Basic connection overhead
    print("🔌 Testing connection overhead...")
    
    connection_times = []
    for i in range(5):
        start_time = time.time()
        try:
            with rag_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            conn_time_ms = (time.time() - start_time) * 1000
            connection_times.append(conn_time_ms)
            print(f"  Connection {i+1}: {conn_time_ms:.1f}ms")
            
        except Exception as e:
            print(f"  Connection {i+1}: FAILED - {e}")
    
    if connection_times:
        avg_conn = sum(connection_times) / len(connection_times)
        print(f"\n📊 Connection Performance:")
        print(f"  Average: {avg_conn:.1f}ms")
        
        if avg_conn > 100:
            print("  🚨 HIGH OVERHEAD - Connection pooling strongly recommended")
        elif avg_conn > 50:
            print("  ⚠️  MODERATE OVERHEAD - Connection pooling recommended")
        else:
            print("  ✅ LOW OVERHEAD - Good connection performance")
    
    print()
    print("🎯 QUICK RECOMMENDATIONS:")
    print("="*50)
    
    # Generate quick recommendations
    if latencies:
        avg_latency = sum(latencies) / len(latencies)
        if avg_latency > 30:
            print("1. 🏆 HIGHEST IMPACT: Migrate to local PostgreSQL")
            print(f"   Current network overhead: {avg_latency:.1f}ms per database call")
            print("   Expected improvement: 3-5x faster queries")
            print("   Cost reduction: $25-30/month (eliminate external DB)")
        else:
            print("1. 💰 Keep external PostgreSQL DBaaS")
            print("   Network performance is acceptable")
    
    print("2. 🚀 Add Redis caching for embeddings and answers")
    print("   Expected improvement: 70%+ for repeat questions")
    print("   Cost: $0 (use existing server memory)")
    
    if connection_times and sum(connection_times)/len(connection_times) > 50:
        print("3. ⚡ Implement database connection pooling")
        print("   Expected improvement: 20-30% for frequent queries")
    
    print("\n💡 Next step: Run './test_performance.py' for detailed analysis")

if __name__ == "__main__":
    test_database_performance()