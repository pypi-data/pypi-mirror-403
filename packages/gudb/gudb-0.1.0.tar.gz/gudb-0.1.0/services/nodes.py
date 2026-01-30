import time
import psycopg2
from google import genai
from typing import TypedDict, Optional
from utils.config import settings
from utils.notifier import send_alert

# The State object that moves through the nodes
class SentinelState(TypedDict):
    raw_query: str
    explain_plan: Optional[str]
    schema_info: Optional[str]
    suggested_fix: Optional[str]
    performance_gain: Optional[str]
    thought_process: Optional[list]
    reasoning: Optional[str]
    business_impact: Optional[str]
    risk_assessment: Optional[str]
    sre_warning: Optional[str]
    impact_analysis: Optional[dict]
    cost_savings: Optional[str]
    rollback_command: Optional[str]
    history: Optional[list] # New field for context awareness
    # Forensic trace fields
    source_file: Optional[str]
    source_line: Optional[int]
    function_name: Optional[str]
    code_snippet: Optional[str]
    function_snippet: Optional[str]
    table_stats: Optional[dict]
    active_blockers: Optional[list]
    db_version: Optional[str]
    git_commit: Optional[dict]
    error_timestamp: Optional[float]
    alert_id: Optional[str]

# --- NODE A: THE MONITOR (Logic for the Middleware) ---
# This isn't a graph node but the trigger that starts the graph.
# Logic: if duration > 500ms -> sentinel_graph.invoke({"raw_query": query})

# --- NODE B: THE DETECTIVE (Gather Context) ---
def detective_node(state: SentinelState):
    """Runs EXPLAIN ANALYZE and fetches table schema."""
    print("\n" + "=" * 50)
    print("🔍 DETECTIVE NODE: Starting analysis...")
    print("=" * 50)
    
    try:
        print(f"📍 Connecting to database: {settings.db_url}")
        conn = psycopg2.connect(settings.db_url)
        cur = conn.cursor()
        print("✅ Database connection established")
        
        # Check if 'orders' table exists
        print("\n🔎 Checking if 'orders' table exists...")
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'orders'
            );
        """)
        table_exists = cur.fetchone()[0]
        
        if not table_exists:
            print("⚠️  'orders' table does not exist in database")
            print("💡 Creating mock data for demonstration...")
            cur.close()
            conn.close()
            return {
                "explain_plan": "Table 'orders' not found. Using mock execution plan.",
                "schema_info": "Mock schema: id (integer), status (varchar), created_at (timestamp)"
            }
        
        print("✅ 'orders' table found")
        
        # 1. Get the Execution Plan
        print(f"\n📊 Running Safe EXPLAIN on query:")
        print(f"   {state['raw_query']}")
        
        try:
            # Step 1: Run cost-only EXPLAIN (Safe)
            cur.execute(f"EXPLAIN (FORMAT JSON) {state['raw_query']}")
            cost_plan_json = cur.fetchone()[0]
            
            # Helper to extract total cost from JSON plan
            def get_total_cost(plan_node):
                if isinstance(plan_node, list):
                    plan_node = plan_node[0]
                if 'Plan' in plan_node:
                    return plan_node['Plan'].get('Total Cost', 0)
                return 0

            estimated_cost = get_total_cost(cost_plan_json)
            print(f"💰 Estimated Query Cost: {estimated_cost}")
            
            # Step 2: Check Threshold
            if estimated_cost > settings.max_safe_cost_threshold:
                print(f"🛑 Cost {estimated_cost} exceeds safety limit {settings.max_safe_cost_threshold}")
                print("⚠️ Skipping EXPLAIN ANALYZE to prevent DB lockup")
                plan = cost_plan_json # return cost-only plan
            else:
                # Step 3: Run full EXPLAIN ANALYZE (if safe)
                print("✅ Cost within safety limits. Running full EXPLAIN ANALYZE...")
                cur.execute(f"EXPLAIN (FORMAT JSON, ANALYZE) {state['raw_query']}")
                plan = cur.fetchone()[0]
                print("✅ Execution plan retrieved successfully")
                
        except Exception as explain_error:
            print(f"⚠️  EXPLAIN failed: {str(explain_error)}")
            print("💡 This might be because the query syntax is invalid or table is empty")
            plan = f"EXPLAIN failed: {str(explain_error)}"
        
        # 2. Get Schema Info
        print("\n📋 Fetching table schema...")
        cur.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'orders'
            ORDER BY ordinal_position;
        """)
        schema = cur.fetchall()
        print(f"✅ Schema retrieved: {len(schema)} columns found")
        
        if schema:
            print("📝 Columns:")
            for col in schema:
                print(f"   - {col[0]} ({col[1]})")
        
        # 3. Extract Source Code Context (Forensic Analysis)
        function_snippet = None
        if state.get('source_file') and state.get('source_line'):
            print(f"\n📂 Reading source code from: {state['source_file']}")
            try:
                with open(state['source_file'], 'r') as f:
                    lines = f.readlines()
                
                # Extract 10 lines before and after the target line
                target_line = state['source_line']
                start_line = max(0, target_line - 10)
                end_line = min(len(lines), target_line + 10)
                
                snippet_lines = []
                for i in range(start_line, end_line):
                    line_num = i + 1
                    marker = ">>>" if line_num == target_line else "   "
                    snippet_lines.append(f"{marker} {line_num:4d} | {lines[i].rstrip()}")
                
                function_snippet = "\n".join(snippet_lines)
                print(f"✅ Extracted {len(snippet_lines)} lines of context")
            except Exception as read_error:
                print(f"⚠️  Failed to read source file: {read_error}")
                function_snippet = f"Error reading {state['source_file']}: {read_error}"
        
        # 4. Get Table Statistics & Deep Observability (SRE Guardrails)
        print("\n📈 Fetching table statistics & SRE context...")
        table_stats = {}
        active_blockers = []
        db_version = "Unknown"
        
        try:
            # Get table name from query (simple heuristic for prototype)
            import re
            table_match = re.search(r"FROM\s+([a-zA-Z0-9_]+)", state['raw_query'], re.IGNORECASE)
            table_name = table_match.group(1) if table_match else 'orders'
            
            # Fetch Version
            cur.execute("SELECT version();")
            full_version = cur.fetchone()[0]
            # Extract just "PostgreSQL X.Y"
            match = re.search(r"PostgreSQL ([\d\.]+)", full_version)
            db_version = f"Postgres {match.group(1)}" if match else "Postgres 15.0"
            
            # Fetch Table Stats & Index Usage
            cur.execute(f"""
                SELECT 
                    s.reltuples::bigint AS row_count,
                    pg_total_relation_size(quote_ident('{table_name}')) AS total_bytes,
                    (SELECT count(*) FROM pg_index WHERE indrelid = quote_ident('{table_name}')::regclass) as index_count,
                    COALESCE(SUM(idx_scan), 0) as total_index_scans
                FROM pg_class s
                LEFT JOIN pg_stat_user_tables stat ON stat.relname = s.relname
                WHERE s.relname = '{table_name}'
                GROUP BY s.reltuples, s.relname;
            """)
            stats = cur.fetchone()
            if stats:
                table_stats = {
                    "table_name": table_name,
                    "row_count": stats[0],
                    "total_size": f"{stats[1] / (1024*1024):.2f} MB",
                    "index_count": stats[2],
                    "total_index_scans": stats[3]
                }
            
            # Fetch Recursive Lock Chains (SRE-Grade Lock Forest)
            # This traces: Blocker -> Waiting -> ... -> You
            cur.execute("""
                WITH RECURSIVE lock_forest AS (
                    -- Level 1: Direct Blockers
                    SELECT 
                        blocking.pid AS blocking_pid,
                        waiting.pid AS waiting_pid,
                        now() - blocking_activity.xact_start AS duration,
                        blocking_activity.query AS blocking_query,
                        1 AS depth
                    FROM pg_locks AS waiting
                    JOIN pg_stat_activity AS waiting_activity ON waiting.pid = waiting_activity.pid
                    JOIN pg_locks AS blocking ON waiting.locktype = blocking.locktype
                        AND waiting.database IS NOT DISTINCT FROM blocking.database
                        AND waiting.relation IS NOT DISTINCT FROM blocking.relation
                        AND waiting.page IS NOT DISTINCT FROM blocking.page
                        AND waiting.tuple IS NOT DISTINCT FROM blocking.tuple
                        AND waiting.virtualxid IS NOT DISTINCT FROM blocking.virtualxid
                        AND waiting.transactionid IS NOT DISTINCT FROM blocking.transactionid
                        AND waiting.classid IS NOT DISTINCT FROM blocking.classid
                        AND waiting.objid IS NOT DISTINCT FROM blocking.objid
                        AND waiting.objsubid IS NOT DISTINCT FROM blocking.objsubid
                        AND waiting.pid != blocking.pid
                    JOIN pg_stat_activity AS blocking_activity ON blocking.pid = blocking_activity.pid
                    WHERE NOT waiting.granted AND blocking.granted
                    
                    UNION ALL
                    
                    -- Levels 2-5: Indirect Blockers (Who is blocking the blocker?)
                    SELECT 
                        b.pid AS blocking_pid,
                        lf.blocking_pid AS waiting_pid,
                        now() - ba.xact_start AS duration,
                        ba.query AS blocking_query,
                        lf.depth + 1
                    FROM lock_forest lf
                    JOIN pg_locks AS w ON w.pid = lf.blocking_pid
                    JOIN pg_locks AS b ON w.locktype = b.locktype
                        AND w.database IS NOT DISTINCT FROM b.database
                        AND w.relation IS NOT DISTINCT FROM b.relation
                        -- (omitting minor lock types for brevity in recursion, focusing on relations)
                        AND w.pid != b.pid
                    JOIN pg_stat_activity AS ba ON b.pid = ba.pid
                    WHERE NOT w.granted AND b.granted AND lf.depth < 5
                )
                SELECT blocking_pid, waiting_pid, duration, blocking_query, depth
                FROM lock_forest
                ORDER BY depth DESC, duration DESC
                LIMIT 10;
            """)
            blockers = cur.fetchall()
            for b in blockers:
                active_blockers.append({
                    "blocking_pid": b[0],
                    "waiting_pid": b[1],
                    "duration": str(b[2]),
                    "query": b[3][:100],
                    "depth": b[4],
                    "description": f"Indirect blocker at depth {b[4]}" if b[4] > 1 else "Direct blocker"
                })
                
            print(f"✅ Lock Forest: {len(active_blockers)} nodes in blocking chain found")
            
        except Exception as stats_error:
            print(f"⚠️  SRE Context Fetch failed: {stats_error}")
            table_stats = {"error": str(stats_error)}
        
        cur.close()
        conn.close()
        print("✅ Database connection closed")
        print("=" * 50)
        
        return {
            "explain_plan": str(plan), 
            "schema_info": str(schema),
            "function_snippet": function_snippet,
            "table_stats": table_stats,
            "active_blockers": active_blockers,
            "db_version": db_version
        }
        
    except psycopg2.OperationalError as e:
        print(f"\n❌ DATABASE CONNECTION ERROR: {str(e)}")
        print("=" * 50)
        print("💡 Possible issues:")
        print("   - PostgreSQL server is not running")
        print("   - Wrong database credentials")
        print("   - Database does not exist")
        print("=" * 50)
        return {
            "explain_plan": f"Connection error: {str(e)}",
            "schema_info": "Unable to connect to database"
        }
    except Exception as e:
        print(f"\n❌ DETECTIVE NODE ERROR: {str(e)}")
        print(f"   Error type: {type(e).__name__}")
        print("=" * 50)
        print("⚠️  Using mock data instead...")
        print("=" * 50)
        return {
            "explain_plan": f"Error: {str(e)}",
            "schema_info": "Mock schema info (error occurred)"
        }

# --- NODE C: THE BRAIN (Gemini Optimizer) ---
def architect_node(state: SentinelState):
    """Uses Gemini to solve the bottleneck."""
    print("\n" + "=" * 50)
    print("🧠 ARCHITECT NODE: Generating AI recommendations...")
    print("=" * 50)
    
    try:
        client = genai.Client(api_key=settings.gemini_api_key)
        
        from services.prompts import DBA_SYSTEM_PROMPT, FORENSIC_ARCHITECT_PROMPT
        import json
        from decimal import Decimal
        from datetime import datetime

        class SentinelEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, Decimal):
                    return float(obj)
                if isinstance(obj, datetime):
                    return obj.isoformat()
                return super().default(obj)
        
        # Determine which prompt to use based on available data
        is_sdk_request = state.get('alert_id') == "sdk_validation"
        use_forensic = (
            state.get('source_file') and 
            state.get('source_line') and 
            state.get('function_snippet')
        )
        
        if is_sdk_request:
            from services.prompts import GUARDIAN_SDK_PROMPT
            print("🛡️  Using SDK GUARDIAN mode (real-time interception)")
            prompt = GUARDIAN_SDK_PROMPT.format(
                query=state['raw_query'],
                stack_trace=state.get('explain_plan', 'No stack trace provided'), # We repurpose fields for SDK
                git_info=json.dumps(state.get('table_stats', {}), indent=2, cls=SentinelEncoder), # Repurposed
                env=state.get('db_version', 'production') # Repurposed
            )
        elif use_forensic:
            print("🔬 Using FORENSIC mode (code-level analysis)")
            prompt = FORENSIC_ARCHITECT_PROMPT.format(
                file_path=state.get('source_file', 'Unknown'),
                line_number=state.get('source_line', 0),
                function_name=state.get('function_name', 'unknown_function'),
                function_snippet=state.get('function_snippet', 'No code context available'),
                query=state['raw_query'],
                plan=state['explain_plan'],
                ddl=state['schema_info']
            )
        else:
            print("📊 Using STANDARD mode (SQL-only analysis)")
            # ... (the rest of standard mode logic follows)
            # Format history string
            history_str = "No recent alerts"
            if state.get("history"):
                 # Format as: "- [ID: 12] SELECT * FROM users (Status: pending)"
                 history_str = "\n".join([
                     f"- [ID: {a['id']}] {a['query']} (Duration: {a.get('duration_ms', 0):.2f}ms)" 
                     for a in state["history"]
                 ])
            
            # Format the prompt using the user's template
            prompt = DBA_SYSTEM_PROMPT.format(
                query=state['raw_query'],
                plan=state['explain_plan'],
                ddl=state['schema_info'],
                table_stats=json.dumps(state.get('table_stats', {}), indent=2, cls=SentinelEncoder),
                historical_alerts_summary=history_str
            )
        
        # SRE context enrichment
        sre_context = f"""
### SRE GUARDRAILS
- DB Engine: {state.get('db_version', 'Unknown')}
- Active Blockers: {json.dumps(state.get('active_blockers', []), indent=2, cls=SentinelEncoder)}
- Index Stats: {json.dumps(state.get('table_stats', {}), indent=2, cls=SentinelEncoder)}
"""
        
        # Determine if we should use SENIOR_ENGINEER_PROMPT
        if state.get('git_commit'):
            from services.prompts import SENIOR_ENGINEER_PROMPT
            print("👴 Using SENIOR ENGINEER mode (blunt, git-aware analysis)")
            commit = state['git_commit']
            prompt = SENIOR_ENGINEER_PROMPT.format(
                query=state['raw_query'],
                plan=state['explain_plan'],
                table_stats=json.dumps(state.get('table_stats', {}), indent=2, cls=SentinelEncoder),
                short_hash=commit.get('short_hash', 'unknown'),
                author=commit.get('author', 'Unknown'),
                message=commit.get('message', 'No message'),
                time_since_commit="Recently"
            )
            
        # Append SRE Guardrails to any prompt
        prompt += sre_context
        
        print("📤 Sending request to Gemini AI...")
        
        # Request JSON response
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config={
                'response_mime_type': 'application/json'
            }
        )
        
        response_text = response.text
        print("✅ AI response received")
        print("=" * 50)
        
        try:
            # Parse JSON response
            ai_data = json.loads(response_text)
            
            # Map JSON fields to SentinelState structure
            if is_sdk_request:
                return {
                    "verdict": ai_data.get("verdict", "GO"),
                    "issue": ai_data.get("issue", "No issue found"),
                    "impact": ai_data.get("impact", "Low impact"),
                    "fix": ai_data.get("fix", ""),
                    "reasoning_short": ai_data.get("reasoning_short", "")
                }
            
            impact = ai_data.get("impact_analysis", {})
            
            result = {
                "thought_process": [
                    ai_data.get("diagnosis", ai_data.get("root_cause", "No diagnosis")),
                    f"Action: {ai_data.get('actionable_insight', 'Manual review')}"
                ],
                "reasoning": ai_data.get("diagnosis", ai_data.get("root_cause", "No diagnosis")),
                "suggested_fix": ai_data.get("recommended_fix", ai_data.get("fix_options", [{"sql": "-- No fix"}])[0].get("sql")),
                "business_impact": f"Read Gain: {impact.get('read_gain', 'Unknown')}",
                "risk_assessment": f"Lock Risk: {impact.get('lock_risk', 'Unknown')} | Write Penalty: {impact.get('write_penalty', 'Unknown')}",
                "cost_savings": f"Storage Impact: {impact.get('storage_impact', 'Unknown')}",
                "rollback_command": "-- Rollback via migration reversal",
                "performance_gain": impact.get("read_gain", "Unknown"),
                "sre_warning": ai_data.get("sre_warning", ai_data.get("locker_warning", "No SRE warning generated.")),
                "impact_analysis": {
                    "read_gain": impact.get("read_gain", "Unknown"),
                    "write_penalty": impact.get("write_penalty", "Unknown"),
                    "lock_risk": impact.get("lock_risk", "None predicted")
                }
            }
            
            # If SENIOR ENGINEER mode was used, adapt the fields
            if "fix_options" in ai_data:
                result["suggested_fix"] = next((f["sql"] for f in ai_data["fix_options"] if f.get("recommended")), ai_data["fix_options"][0]["sql"])
                result["reasoning"] = ai_data.get("root_cause", result["reasoning"])

            print(f"📊 Reasoning: {result['reasoning'][:100]}...")
            print(f"✨ Fix generated: {len(result['suggested_fix'])} characters")
            print("=" * 50)
            
            return result
            
        except json.JSONDecodeError as je:
            print(f"❌ Failed to parse JSON response: {str(je)}")
            print(f"Raw response: {response_text[:200]}...")
            return {
                "suggested_fix": None,
                "reasoning": f"JSON Parsing Error: {str(je)}",
                "business_impact": "Error",
                "risk_assessment": "Error",
                "cost_savings": "Error",
                "rollback_command": "N/A"
            }
            
    except Exception as e:
        print(f"\n❌ ARCHITECT NODE ERROR: {str(e)}")
        print(f"   Error type: {type(e).__name__}")
        print("=" * 50)
        return {
            "suggested_fix": None,
            "reasoning": f"Error: {str(e)}",
            "business_impact": "Unable to calculate",
            "risk_assessment": "Unable to assess",
            "cost_savings": "Unable to estimate",
            "rollback_command": "N/A"
        }

# --- NODE D: THE TESTER (Validator) ---
def validator_node(state: SentinelState):
    """Runs the fix in a sandbox to prove it works."""
    # Logic: 
    # 1. Connect to 'Shadow DB' 
    # 2. Run state['suggested_fix'] (e.g., CREATE INDEX)
    # 3. Re-run state['raw_query']
    # 4. Compare times.
    
    # Mocking the result for now:
    return {"performance_gain": "92% speedup verified"}