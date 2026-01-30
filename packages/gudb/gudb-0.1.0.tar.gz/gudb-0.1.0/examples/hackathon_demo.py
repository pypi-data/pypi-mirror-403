import sys
import os
import time
from typing import Any

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from gudb import monitor, settings
from gudb.exceptions import DisasterBlockedError

# ANSI Visuals
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RED = "\033[91m"
RESET = "\033[0m"

def print_header(text):
    print(f"\n{BOLD}{BLUE}{'='*60}{RESET}")
    print(f"{BOLD}{BLUE} 🛡️  {text}{RESET}")
    print(f"{BOLD}{BLUE}{'='*60}{RESET}\n")

def simulate_typing(text, delay=0.03):
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()

def print_pipeline():
    pipeline = f"""
{BOLD}{CYAN}   The gudb Pipeline{RESET}
   ┌──────────────┐
   │ Incoming SQL │
   └──────┬───────┘
          │
          ▼
   ┌────────────────────┐
   │  {RED}Heuristic Guard{RESET}   │  (<1ms)
   │  (DELETE, DROP)    │
   └──────┬─────────────┘
          │ safe
          ▼
   ┌────────────────────┐
   │ {YELLOW}Time Guard (⏱️){RESET}     │  (runtime)
   │ Max execution time │
   └──────┬─────────────┘
          │ safe
          ▼
   ┌────────────────────┐
   │ {GREEN}AI Advisor (async){RESET} │
   └────────────────────┘
    """
    print(pipeline)

def run_demo():
    # 1. Setup Mock Connection
    class MockCursor:
        def execute(self, q, v=None):
            if "SLEEP" in q:
                # Simulate a DB timeout
                raise Exception("statement_timeout: query took too long")
            pass
    class MockConn:
        def cursor(self): return MockCursor()
        
    print_header("GUDB: THE DATABASE SEATBELT")
    print_pipeline()
    
    # Configuration for Demo
    settings.enable_local_heuristics = True
    settings.api_endpoint = "https://ai-db-sentinel.onrender.com/api/sdk/evaluate"
    settings.service_name = "payments-api"
    settings.environment = "production"
    settings.max_execution_time_ms = 2000 # 2 seconds
    
    conn = monitor(MockConn())
    cur = conn.cursor()

    # --- SCENARIO 1: SAFE QUERY ---
    print(f"{BOLD}[SCENARIO 1] Standard Analytical Query{RESET}")
    sql = "SELECT order_id, total FROM orders WHERE status = 'shipped' LIMIT 10;"
    simulate_typing(f"💻 Developer: {sql}")
    print(f"📡 {GREEN}Status: MONITORING...{RESET}")
    cur.execute(sql)
    print(f"✅ {GREEN}Query Passed (Latency: 0.12ms){RESET}")

    # --- SCENARIO 2: THE CAREER-ENDER ---
    print(f"\n{BOLD}[SCENARIO 2] The 'Accidental' Disaster{RESET}")
    sql = "DELETE FROM users;"
    simulate_typing(f"💻 Developer: {sql}", delay=0.05)
    print(f"📡 {BOLD}Status: INTERCEPTING (Tier 1)...{RESET}")
    
    try:
        cur.execute(sql)
    except Exception as e:
        print(e)

    # --- SCENARIO 3: TIME GUARD (PERFORMANCE SEATBELT) ---
    print(f"\n{BOLD}[SCENARIO 3] The Performance Guard (Tier 2){RESET}")
    print(f"💡 {BOLD}Test: A query that hangs or is unoptimised.{RESET}")
    sql = "SELECT * FROM large_table t1 CROSS JOIN large_table t2; -- OOPS"
    simulate_typing(f"💻 Developer: {sql}")
    print(f"📡 {YELLOW}Status: MONITORING EXECUTION...{RESET}")
    
    # We use a special keyword "SLEEP" in our mock to trigger the timeout
    try:
        cur.execute("SELECT SLEEP(5); -- Heavy cross join simulation")
    except Exception as e:
        print(e)
        print(f"📊 {CYAN}{BOLD}[gudb] PERFORMANCE INCIDENT LOGGED:{RESET}")
        print(f"   {CYAN}service={settings.service_name}{RESET}")
        print(f"   {CYAN}outcome=TERMINATED_BY_TIME_GUARD{RESET}")

    # --- SCENARIO 4: FAIL-OPEN (PRODUCTION THINKING) ---
    print(f"\n{BOLD}[SCENARIO 4] Fail-Open (Infrastructure Resilience){RESET}")
    print(f"💡 {BOLD}Test: What if the AI backend is OFFLINE?{RESET}")
    
    # Simulate AI Backend Down
    original_endpoint = settings.api_endpoint
    settings.api_endpoint = "http://invalid-internal-service:9999/evaluate"
    settings.fail_open = True
    
    sql = "UPDATE products SET price = price * 1.1 WHERE category = 'electronics';"
    simulate_typing(f"💻 Developer: {sql}")
    print(f"📡 {YELLOW}Status: AI OFFLINE! ACTIVATING FAIL-OPEN...{RESET}")
    
    cur.execute(sql)
    
    print(f"✅ {GREEN}Query Allowed (Fail-Open Mode){RESET}")
    print(f"🛡️  {BOLD}Note: Standard operation continues even if security backend is unreachable.{RESET}")
    
    # Restore configuration
    settings.api_endpoint = original_endpoint

    # --- SCENARIO 5: THE AI ADVISOR ---
    print(f"\n{BOLD}[SCENARIO 5] Complex Performance Advice (Tier 3){RESET}")
    sql = "SELECT * FROM logs l JOIN users u ON l.user_id = u.id WHERE l.level = 'ERROR';"
    simulate_typing(f"💻 Developer: {sql}")
    print(f"📡 {BOLD}Status: CONSULTING SENIOR DRE (AI MODE)...{RESET}")
    
    # Mock realistic AI Advisory Verdict for Demo Impact
    print(f"\n💡 {CYAN}{BOLD}ADVISOR FEEDBACK:{RESET}")
    print(f"   {BOLD}AI Verdict:{RESET} {YELLOW}WARNING{RESET}")
    print(f"   {BOLD}Reason:{RESET} Mass join detected on unindexed columns. Potential for table-scan lock.")
    print(f"   {BOLD}Confidence:{RESET} High (92%)")
    print(f"   {BOLD}Advice:{RESET} Add index on logs(user_id) to prevent full table scans.")

    print_header("DEMO COMPLETE: THE SEATBELT IS ALWAYS ON")

if __name__ == "__main__":
    try:
        run_demo()
    except KeyboardInterrupt:
        print("\nDemo aborted.")
