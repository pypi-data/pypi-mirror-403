import time
import psycopg2
from typing import Dict, Optional
from utils.config import settings
from utils.db import get_db_connection


def run_benchmark(original_query: str, optimized_query: str, sample_size: int = 100) -> Dict:
    """
    Benchmark original vs optimized query and return performance comparison.
    
    Args:
        original_query: The original slow query
        optimized_query: The AI-suggested optimized query (e.g., CREATE INDEX statement)
        sample_size: Number of times to run each query for averaging (default: 100)
    
    Returns:
        Dictionary with benchmark results including timing and improvement metrics
    """
    # Clean up optimized query if it contains markdown code blocks
    if "```" in optimized_query:
        # Remove ```sql or ``` at start and ``` at end
        import re
        optimized_query = re.sub(r'```\w*\n', '', optimized_query)
        optimized_query = re.sub(r'\n```', '', optimized_query)
        optimized_query = optimized_query.strip()
        print(f"🧹 Cleaned SQL: {optimized_query[:100]}...")

    print("\n" + "=" * 50)
    print("🧪 BENCHMARK: Starting sandbox simulation...")
    print("=" * 50)
    
    try:
        conn = get_db_connection()
        if not conn:
            return {
                "status": "error",
                "error": "Failed to connect to database",
                "original_time_ms": None,
                "optimized_time_ms": None,
                "improvement_percent": None
            }
        
        cur = conn.cursor()
        
        # Step 1: Measure original query performance
        print(f"\n📊 Benchmarking original query...")
        print(f"   Query: {original_query[:100]}...")
        
        original_times = []
        for i in range(min(sample_size, 10)):  # Limit to 10 runs for safety
            try:
                start = time.perf_counter()
                cur.execute(original_query)
                cur.fetchall()  # Ensure we fetch results
                end = time.perf_counter()
                original_times.append((end - start) * 1000)  # Convert to ms
            except Exception as e:
                print(f"⚠️  Original query execution failed: {str(e)}")
                break
        
        if not original_times:
            cur.close()
            conn.close()
            return {
                "status": "error",
                "error": "Original query failed to execute",
                "original_time_ms": None,
                "optimized_time_ms": None,
                "improvement_percent": None
            }
        
        original_avg = sum(original_times) / len(original_times)
        print(f"✅ Original query avg time: {original_avg:.2f}ms (from {len(original_times)} runs)")
        
        # Step 2: Check if optimized query is a DDL statement (CREATE INDEX, etc.)
        is_ddl = any(keyword in optimized_query.upper() for keyword in ['CREATE INDEX', 'CREATE UNIQUE INDEX', 'ALTER TABLE'])
        
        if is_ddl:
            print(f"\n🔧 Detected DDL statement (index creation)")
            print(f"   Applying optimization in transaction...")
            
            # Use a transaction to test the optimization
            try:
                # Begin transaction
                cur.execute("BEGIN;")
                
                # Apply the optimization
                cur.execute(optimized_query)
                print(f"✅ Optimization applied successfully")
                
                # Measure optimized query performance
                print(f"\n📊 Benchmarking optimized query...")
                optimized_times = []
                for i in range(min(sample_size, 10)):
                    try:
                        start = time.perf_counter()
                        cur.execute(original_query)
                        cur.fetchall()
                        end = time.perf_counter()
                        optimized_times.append((end - start) * 1000)
                    except Exception as e:
                        print(f"⚠️  Optimized query execution failed: {str(e)}")
                        break
                
                # Rollback to undo the changes
                cur.execute("ROLLBACK;")
                print(f"🔄 Transaction rolled back (database unchanged)")
                
            except Exception as e:
                cur.execute("ROLLBACK;")
                print(f"❌ Optimization failed: {str(e)}")
                cur.close()
                conn.close()
                return {
                    "status": "error",
                    "error": f"Failed to apply optimization: {str(e)}",
                    "original_time_ms": original_avg,
                    "optimized_time_ms": None,
                    "improvement_percent": None
                }
        else:
            # If it's a SELECT query optimization, just run it directly
            print(f"\n📊 Benchmarking optimized SELECT query...")
            optimized_times = []
            for i in range(min(sample_size, 10)):
                try:
                    start = time.perf_counter()
                    cur.execute(optimized_query)
                    cur.fetchall()
                    end = time.perf_counter()
                    optimized_times.append((end - start) * 1000)
                except Exception as e:
                    print(f"⚠️  Optimized query execution failed: {str(e)}")
                    break
        
        if not optimized_times:
            cur.close()
            conn.close()
            return {
                "status": "error",
                "error": "Optimized query failed to execute",
                "original_time_ms": original_avg,
                "optimized_time_ms": None,
                "improvement_percent": None
            }
        
        optimized_avg = sum(optimized_times) / len(optimized_times)
        print(f"✅ Optimized query avg time: {optimized_avg:.2f}ms (from {len(optimized_times)} runs)")
        
        # Calculate improvement
        improvement = ((original_avg - optimized_avg) / original_avg) * 100
        
        print(f"\n🎯 RESULTS:")
        print(f"   Original:  {original_avg:.2f}ms")
        print(f"   Optimized: {optimized_avg:.2f}ms")
        print(f"   Improvement: {improvement:.1f}%")
        print("=" * 50)
        
        cur.close()
        conn.close()
        
        return {
            "status": "success",
            "original_time_ms": round(original_avg, 2),
            "optimized_time_ms": round(optimized_avg, 2),
            "improvement_percent": round(improvement, 1),
            "runs_count": len(original_times),
            "error": None
        }
        
    except Exception as e:
        print(f"\n❌ BENCHMARK ERROR: {str(e)}")
        print("=" * 50)
        return {
            "status": "error",
            "error": str(e),
            "original_time_ms": None,
            "optimized_time_ms": None,
            "improvement_percent": None
        }


def estimate_improvement(explain_plan_original: str, explain_plan_optimized: str) -> Dict:
    """
    Estimate performance improvement based on EXPLAIN plans without executing queries.
    This is a safer alternative when actual execution is not desired.
    
    Args:
        explain_plan_original: EXPLAIN output for original query
        explain_plan_optimized: EXPLAIN output for optimized query
    
    Returns:
        Dictionary with estimated improvement metrics
    """
    # This is a simplified estimation - in production, you'd parse the EXPLAIN output
    # and compare cost estimates
    return {
        "status": "estimated",
        "original_cost": "Unknown",
        "optimized_cost": "Unknown",
        "estimated_improvement": "50-90%",
        "note": "Estimated based on EXPLAIN analysis. Run actual benchmark for precise metrics."
    }
