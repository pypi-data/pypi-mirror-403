import sys
import os
from pprint import pprint

# Add src to path for demo
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from ai_db_sentinel import monitor, sentinel, settings
from ai_db_sentinel.exceptions import DisasterBlockedError

def demo_driver_interception():
    print("--- 🛡️ Driver Interception Demo ---")
    
    # Mocking a PEP 249 connection
    class MockCursor:
        def execute(self, q, v=None): print(f"Executing SQL: {q}")
    class MockConn:
        def cursor(self): return MockCursor()
        
    conn = monitor(MockConn())
    cur = conn.cursor()
    
    print("\n1. Testing Safe Query...")
    cur.execute("SELECT * FROM users WHERE id = 1")
    
    print("\n2. Testing Disaster Query (Heuristic Block)...")
    try:
        cur.execute("DELETE FROM orders;")
    except DisasterBlockedError as e:
        print(f"✅ Intercepted Disaster: {e.issue}")
        print(f"💥 Impact: {e.impact}")

def demo_configuration():
    print("\n--- ⚙️ Configuration Demo ---")
    print(f"Default Endpoint: {settings.api_endpoint}")
    print(f"Environment: {settings.environment}")
    print(f"Fail Open: {settings.fail_open}")

if __name__ == "__main__":
    demo_configuration()
    demo_driver_interception()
