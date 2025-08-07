#!/usr/bin/env python3
"""
Performance testing script for RAG system database operations.
This script will measure:
1. Network latency to external PostgreSQL
2. Vector search query performance
3. Database connection overhead
4. Overall RAG pipeline performance
"""

import time
import asyncio
import statistics
import json
from typing import List, Dict, Any
import psycopg2
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from datetime import datetime

# Import our RAG components
from app.database.rag_database import get_rag_database_url, get_rag_db, rag_engine
from app.services.rag_service import RAGService

class PerformanceProfiler:
    def __init__(self):
        self.results = {}
        self.rag_service = RAGService()
        
    def measure_time(self, operation_name: str):
        """Decorator to measure operation time"""
        def decorator(func):
            async def wrapper(*args, **kwargs):
                start_time = time.time()
                result = await func(*args, **kwargs)
                end_time = time.time()
                elapsed_ms = (end_time - start_time) * 1000
                
                if operation_name not in self.results:
                    self.results[operation_name] = []
                self.results[operation_name].append(elapsed_ms)
                
                print(f"⏱️  {operation_name}: {elapsed_ms:.2f}ms")
                return result
            return wrapper
        return decorator

    async def test_database_connectivity(self, num_tests: int = 10):
        """Test basic database connection performance"""
        print("\n🔌 Testing Database Connectivity...")
        
        connection_times = []
        
        for i in range(num_tests):
            start_time = time.time()
            try:
                # Test PostgreSQL connection
                with rag_engine.connect() as conn:
                    result = conn.execute(text("SELECT 1"))
                    result.fetchone()
                end_time = time.time()
                elapsed_ms = (end_time - start_time) * 1000
                connection_times.append(elapsed_ms)
                print(f"  Connection {i+1}: {elapsed_ms:.2f}ms")
            except Exception as e:
                print(f"  Connection {i+1} failed: {e}")
                connection_times.append(float('inf'))
                
        self.results['db_connection'] = connection_times
        
        if connection_times:
            avg_time = statistics.mean([t for t in connection_times if t != float('inf')])
            print(f"  📊 Average connection time: {avg_time:.2f}ms")

    async def test_network_latency(self, num_tests: int = 20):
        """Test network latency to PostgreSQL server"""
        print("\n🌐 Testing Network Latency...")
        
        # Parse database URL to get host
        db_url = get_rag_database_url()
        host = os.getenv("POSTGRES_RAG_HOST", "localhost")
        port = int(os.getenv("POSTGRES_RAG_PORT", "5432"))
        
        latencies = []
        
        for i in range(num_tests):
            start_time = time.time()
            try:
                # Simple ping-like test using psycopg2
                conn = psycopg2.connect(
                    host=host,
                    port=port,
                    user=os.getenv("POSTGRES_RAG_USER"),
                    password=os.getenv("POSTGRES_RAG_PASSWORD"),
                    database=os.getenv("POSTGRES_RAG_DATABASE"),
                    connect_timeout=5
                )
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                cursor.close()
                conn.close()
                
                end_time = time.time()
                latency_ms = (end_time - start_time) * 1000
                latencies.append(latency_ms)
                print(f"  Ping {i+1}: {latency_ms:.2f}ms")
                
            except Exception as e:
                print(f"  Ping {i+1} failed: {e}")
                latencies.append(float('inf'))
                
        self.results['network_latency'] = latencies
        
        if latencies:
            valid_latencies = [l for l in latencies if l != float('inf')]
            if valid_latencies:
                avg_latency = statistics.mean(valid_latencies)
                min_latency = min(valid_latencies)
                max_latency = max(valid_latencies)
                print(f"  📊 Latency - Avg: {avg_latency:.2f}ms, Min: {min_latency:.2f}ms, Max: {max_latency:.2f}ms")

    async def test_vector_search_performance(self, num_tests: int = 10):
        """Test vector search query performance"""
        print("\n🔍 Testing Vector Search Performance...")
        
        # Create a sample embedding (384 dimensions for all-MiniLM-L6-v2)
        sample_embedding = [0.1] * 384
        
        search_times = []
        
        for i in range(num_tests):
            start_time = time.time()
            try:
                db_session = next(get_rag_db())
                
                # Test direct vector search
                embedding_str = '[' + ','.join(map(str, sample_embedding)) + ']'
                sql_query = """
                    SELECT 
                        document_id,
                        chunk_index,
                        content,
                        (embedding <=> %s::vector) as similarity
                    FROM document_chunks 
                    ORDER BY embedding <=> %s::vector
                    LIMIT 5
                """
                
                raw_connection = db_session.connection().connection
                cursor = raw_connection.cursor()
                cursor.execute(sql_query, (embedding_str, embedding_str))
                results = cursor.fetchall()
                cursor.close()
                db_session.close()
                
                end_time = time.time()
                search_time_ms = (end_time - start_time) * 1000
                search_times.append(search_time_ms)
                print(f"  Vector search {i+1}: {search_time_ms:.2f}ms (found {len(results)} results)")
                
            except Exception as e:
                print(f"  Vector search {i+1} failed: {e}")
                search_times.append(float('inf'))
                
        self.results['vector_search'] = search_times
        
        if search_times:
            valid_searches = [t for t in search_times if t != float('inf')]
            if valid_searches:
                avg_time = statistics.mean(valid_searches)
                print(f"  📊 Average vector search time: {avg_time:.2f}ms")

    async def test_full_rag_pipeline(self, num_tests: int = 5):
        """Test complete RAG pipeline performance"""
        print("\n🤖 Testing Full RAG Pipeline...")
        
        test_questions = [
            "What corruption cases are mentioned?",
            "Tell me about government fraud",
            "What documents discuss police corruption?",
            "Are there any cases from Egypt?",
            "What types of corruption are documented?"
        ]
        
        pipeline_times = []
        
        for i in range(num_tests):
            question = test_questions[i % len(test_questions)]
            print(f"  Testing question {i+1}: '{question}'")
            
            start_time = time.time()
            try:
                # Test full pipeline: embedding generation + vector search + LLM
                db_session = next(get_rag_db())
                response = await self.rag_service.answer_question(
                    question=question,
                    db=db_session
                )
                db_session.close()
                
                end_time = time.time()
                pipeline_time_ms = (end_time - start_time) * 1000
                pipeline_times.append(pipeline_time_ms)
                print(f"  Pipeline {i+1}: {pipeline_time_ms:.2f}ms")
                print(f"    Answer: {response.get('answer', 'No answer')[:100]}...")
                
            except Exception as e:
                print(f"  Pipeline {i+1} failed: {e}")
                pipeline_times.append(float('inf'))
                
        self.results['full_pipeline'] = pipeline_times
        
        if pipeline_times:
            valid_times = [t for t in pipeline_times if t != float('inf')]
            if valid_times:
                avg_time = statistics.mean(valid_times)
                print(f"  📊 Average pipeline time: {avg_time:.2f}ms ({avg_time/1000:.2f}s)")

    async def test_embedding_generation(self, num_tests: int = 10):
        """Test embedding generation performance"""
        print("\n🧠 Testing Embedding Generation...")
        
        test_texts = [
            "What corruption cases are mentioned?",
            "Tell me about government fraud",
            "What documents discuss police corruption?",
            "Are there any cases from Brazil?",
            "What types of corruption are documented?"
        ]
        
        embedding_times = []
        
        for i in range(num_tests):
            text = test_texts[i % len(test_texts)]
            
            start_time = time.time()
            try:
                embedding = await self.rag_service.generate_embedding(text)
                end_time = time.time()
                
                embedding_time_ms = (end_time - start_time) * 1000
                embedding_times.append(embedding_time_ms)
                print(f"  Embedding {i+1}: {embedding_time_ms:.2f}ms (dimensions: {len(embedding)})")
                
            except Exception as e:
                print(f"  Embedding {i+1} failed: {e}")
                embedding_times.append(float('inf'))
                
        self.results['embedding_generation'] = embedding_times
        
        if embedding_times:
            valid_times = [t for t in embedding_times if t != float('inf')]
            if valid_times:
                avg_time = statistics.mean(valid_times)
                print(f"  📊 Average embedding time: {avg_time:.2f}ms")

    def generate_report(self):
        """Generate comprehensive performance report"""
        print("\n" + "="*80)
        print("📊 PERFORMANCE ANALYSIS REPORT")
        print("="*80)
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"Generated: {timestamp}")
        print()
        
        # Calculate statistics for each metric
        for metric_name, times in self.results.items():
            if not times:
                continue
                
            valid_times = [t for t in times if t != float('inf')]
            if not valid_times:
                print(f"❌ {metric_name}: All tests failed")
                continue
                
            avg_time = statistics.mean(valid_times)
            min_time = min(valid_times)
            max_time = max(valid_times)
            median_time = statistics.median(valid_times)
            
            print(f"📈 {metric_name.upper().replace('_', ' ')}")
            print(f"   Average: {avg_time:.2f}ms")
            print(f"   Median:  {median_time:.2f}ms")
            print(f"   Min:     {min_time:.2f}ms")
            print(f"   Max:     {max_time:.2f}ms")
            print(f"   Samples: {len(valid_times)}/{len(times)}")
            print()
        
        # Performance assessment
        print("🎯 PERFORMANCE ASSESSMENT")
        print("-" * 40)
        
        if 'network_latency' in self.results:
            valid_latencies = [l for l in self.results['network_latency'] if l != float('inf')]
            if valid_latencies:
                avg_latency = statistics.mean(valid_latencies)
                if avg_latency > 50:
                    print(f"⚠️  High network latency detected: {avg_latency:.2f}ms")
                    print("   💡 Local database may provide significant speedup")
                elif avg_latency > 20:
                    print(f"⚡ Moderate network latency: {avg_latency:.2f}ms")
                    print("   💡 Local database would provide some speedup")
                else:
                    print(f"✅ Low network latency: {avg_latency:.2f}ms")
                    print("   💡 External DBaaS performance is good")
        
        if 'full_pipeline' in self.results:
            valid_pipeline = [t for t in self.results['full_pipeline'] if t != float('inf')]
            if valid_pipeline:
                avg_pipeline = statistics.mean(valid_pipeline)
                print(f"🤖 Current RAG pipeline speed: {avg_pipeline/1000:.2f}s")
                if avg_pipeline > 5000:
                    print("   ❌ Very slow - optimization needed")
                elif avg_pipeline > 3000:
                    print("   ⚠️  Slow - optimization recommended")
                elif avg_pipeline > 1500:
                    print("   ⚡ Moderate - some optimization possible")
                else:
                    print("   ✅ Good performance")
        
        print("\n💡 OPTIMIZATION RECOMMENDATIONS")
        print("-" * 40)
        
        # Network latency based recommendations
        if 'network_latency' in self.results:
            valid_latencies = [l for l in self.results['network_latency'] if l != float('inf')]
            if valid_latencies:
                avg_latency = statistics.mean(valid_latencies)
                if avg_latency > 30:
                    print("1. 🎯 HIGH PRIORITY: Consider local PostgreSQL")
                    print(f"   Current network latency: {avg_latency:.2f}ms per query")
                    print("   Potential savings: 80-90% of database operation time")
                else:
                    print("1. 💰 Keep external PostgreSQL DBaaS")
                    print("   Network performance is good, DBaaS benefits outweigh costs")
        
        # Caching recommendations
        print("2. 🚀 HIGH PRIORITY: Implement caching")
        print("   - Redis cache for embeddings (24-48h TTL)")
        print("   - Answer cache for identical questions (7d TTL)")
        print("   - Expected improvement: 70-90% for repeat queries")
        
        # Connection pooling
        print("3. 🔧 MEDIUM PRIORITY: Database connection pooling")
        print("   - Reuse connections instead of creating new ones")
        print("   - Expected improvement: 10-20% for frequent queries")
        
        # Model optimization
        print("4. ⚡ LOW PRIORITY: Ollama optimization")
        print("   - Keep models loaded in memory")
        print("   - Faster inference configuration")
        print("   - Expected improvement: 20-30% for LLM generation")

    async def run_all_tests(self):
        """Run comprehensive performance test suite"""
        print("🚀 Starting RAG Performance Analysis...")
        print("This will take about 2-3 minutes to complete.")
        print()
        
        await self.test_database_connectivity(5)
        await self.test_network_latency(10)
        await self.test_embedding_generation(5)
        await self.test_vector_search_performance(5)
        await self.test_full_rag_pipeline(3)
        
        self.generate_report()
        
        # Save results to file
        results_file = f"performance_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\n💾 Detailed results saved to: {results_file}")

async def main():
    """Main function to run performance tests"""
    profiler = PerformanceProfiler()
    await profiler.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())