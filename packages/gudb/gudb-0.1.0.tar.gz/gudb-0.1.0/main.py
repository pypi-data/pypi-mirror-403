from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import List
import socketio
import time
from datetime import datetime
from services.graph import build_sentinel_graph
from utils.config import settings
from utils.db import test_db_connection
from utils.bouncer import Bouncer
from utils.git_tracker import get_git_tracker
from utils.schema_tracker import get_schema_tracker
import traceback
import inspect

# Create Socket.IO server
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
socket_app = socketio.ASGIApp(sio)

app = FastAPI(title="AI-DB-Sentinel", version="1.0.0")
sentinel = build_sentinel_graph()

# Mount Socket.IO
app.mount("/socket.io", socket_app)

# Initialize AI Client for SDK (High Performance)
from google import genai
sdk_ai_client = genai.Client(api_key=settings.gemini_api_key)

# Test database connection on startup
print("\n" + "=" * 50)
print("🚀 AI-DB-Sentinel Starting Up...")
print("=" * 50)
test_db_connection()

# Initialize git tracking
if settings.enable_git_tracking:
    git_tracker = get_git_tracker(settings.git_repo_path)
    if git_tracker.is_available():
        current_commit = git_tracker.get_current_commit()
        if current_commit:
            print(f"📌 Git Tracking: Enabled (commit: {current_commit['short_hash']})")
    else:
        print("⚠️  Git Tracking: Disabled (not a git repository)")
else:
    git_tracker = None
    print("⚠️  Git Tracking: Disabled (via config)")

# Initialize schema tracking
if settings.enable_schema_tracking:
    schema_tracker = get_schema_tracker()
    if settings.auto_capture_schema:
        print("📸 Capturing initial schema snapshot...")
        schema_tracker.capture_schema_snapshot(
            commit_hash=git_tracker.get_current_commit()['hash'] if git_tracker and git_tracker.is_available() else None
        )
    print("✅ Schema Tracking: Enabled")
else:
    schema_tracker = None
    print("⚠️  Schema Tracking: Disabled (via config)")

print("=" * 50)

# In-memory storage for alerts and their analysis
alerts_storage = []
analysis_storage = {}  # Maps alert index to analysis results

# DEDUPLICATION: Track queries currently being analyzed
# Using a set of query strings (or hashes) to prevent duplicate analysis
analyzing_queries = set()


async def run_ai_analysis(alert_index: int, query: str):
    """Background task to run AI analysis and store results"""
    try:
        print(f"🤖 Starting AI analysis for alert {alert_index}...")
        
        # Emit status update: analyzing
        await sio.emit('analysis_status', {
            'alert_id': alert_index,
            'status': 'analyzing',
            'message': 'AI is analyzing the query...'
        })
        
        # Get the alert object to extract forensic trace data
        alert = alerts_storage[alert_index]
        
        # Run synchronous LangGraph in a separate thread to keep Socket.IO reactive
        import asyncio
        result = await asyncio.to_thread(sentinel.invoke, {
            "alert_id": str(alert_index),
            "raw_query": query,
            # PASS THE ALERT HISTORY
            # We copy the list to avoid concurrent modification issues, and only take the last 50
            "history": alerts_storage[-50:],
            # PASS FORENSIC TRACE DATA
            "source_file": alert.get("source_file"),
            "source_line": alert.get("source_line"),
            "function_name": alert.get("function_name"),
            "code_snippet": alert.get("code_snippet"),
            # PASS GIT CONTEXT
            "git_commit": alert.get("git_commit"),
            "error_timestamp": alert.get("timestamp")
        })
        
        # Store comprehensive analysis results
        analysis_storage[alert_index] = {
            "suggested_fix": result.get("suggested_fix", "No fix suggested"),
            "performance_gain": result.get("performance_gain", "Unknown"),
            "explain_plan": result.get("explain_plan", ""),
            "schema_info": result.get("schema_info", ""),
            "reasoning": result.get("reasoning", ""),
            "thought_process": result.get("thought_process", []),
            "business_impact": result.get("business_impact", ""),
            "risk_assessment": result.get("risk_assessment", ""),
            "cost_savings": result.get("cost_savings", ""),
            "rollback_command": result.get("rollback_command", ""),
            # Forensic analysis results (code-level fixes)
            "location": result.get("location"),
            "problem": result.get("problem"),
            "original_code": result.get("original_code"),
            "optimized_code": result.get("optimized_code"),
            "explanation": result.get("explanation"),
            "impact": result.get("impact"),
            # Git correlation results
            "root_cause": result.get("root_cause"),
            "commit_correlation": result.get("commit_correlation"),
            "fix_options": result.get("fix_options", []),
            "what_broke": result.get("what_broke"),
            "how_to_prevent": result.get("how_to_prevent"),
            "sre_warning": result.get("sre_warning", "No SRE warning generated."),
            "impact_analysis": result.get("impact_analysis", {}),
            "status": "completed"
        }
        
        # Update alert with SRE data from result
        if alert_index < len(alerts_storage):
            alerts_storage[alert_index].update({
                "table_stats": result.get("table_stats"),
                "active_blockers": result.get("active_blockers"),
                "db_version": result.get("db_version"),
                "status": "completed"
            })
        
        print(f"✅ Analysis completed for alert {alert_index}")
        
        # Emit status update: completed
        await sio.emit('analysis_status', {
            'alert_id': alert_index,
            'status': 'completed',
            'message': 'Analysis complete! Click to view details.',
            'has_results': True
        })
        
    except Exception as e:
        print(f"❌ Analysis failed for alert {alert_index}: {str(e)}")
        analysis_storage[alert_index] = {
            "error": str(e),
            "status": "failed"
        }
        if alert_index < len(alerts_storage):
            alerts_storage[alert_index]["status"] = "failed"
        
        # Emit status update: failed
        await sio.emit('analysis_status', {
            'alert_id': alert_index,
            'status': 'failed',
            'message': f'Analysis failed: {str(e)}'
        })
    finally:
        # DEDUPLICATION: Remove query from the active set when done or failed
        # Normalize the query string before removing (simple strip for now)
        normalized_query = query.strip()
        if normalized_query in analyzing_queries:
            analyzing_queries.remove(normalized_query)
            print(f"🔓 Removed query from active analysis list. Active: {len(analyzing_queries)}")


@app.middleware("http")
async def db_monitor_middleware(request: Request, call_next):
    """Monitor query execution time and trigger alerts"""
    start_time = time.perf_counter()
    
    response = await call_next(request)
    
    duration_ms = (time.perf_counter() - start_time) * 1000
    
    # Check if query exceeds threshold
    if duration_ms > settings.slow_query_threshold_ms:
        # In production, capture actual SQL query from request context
        query_to_fix = "SELECT * FROM orders WHERE status = 'pending';"
        
        # Determine severity
        if duration_ms >= settings.critical_threshold_ms:
            severity = "critical"
            severity_emoji = "🚨"
        elif duration_ms >= settings.slow_query_threshold_ms:
            severity = "warning"
            severity_emoji = "⚠️"
        else:
            severity = "info"
            severity_emoji = "ℹ️"
        
        # FORENSIC TRACE: Capture the exact line that triggered this slow request
        source_file = None
        source_line = None
        function_name = None
        code_snippet = None
        
        try:
            # Get the current stack
            stack = traceback.extract_stack()
            
            # Filter out framework/middleware frames to find user code
            # We want frames that are NOT in site-packages, uvicorn, starlette, or this file
            user_frames = [
                frame for frame in stack
                if 'site-packages' not in frame.filename
                and 'uvicorn' not in frame.filename
                and 'starlette' not in frame.filename
                and frame.filename != __file__
                and '/venv/' not in frame.filename
            ]
            
            # The last user frame is likely the one that triggered the request
            if user_frames:
                target_frame = user_frames[-1]
                source_file = target_frame.filename
                source_line = target_frame.lineno
                function_name = target_frame.name
                code_snippet = target_frame.line
                
                print(f"🔍 Forensic Trace: {source_file}:{source_line} in {function_name}()")
        except Exception as trace_error:
            print(f"⚠️  Failed to capture stack trace: {trace_error}")
        
        # Capture git context
        git_commit = None
        if git_tracker and git_tracker.is_available() and settings.include_git_context:
            git_commit = git_tracker.get_current_commit()
            # Try to correlate with recent commits
            error_time = datetime.fromtimestamp(time.time())
            correlated_commit = git_tracker.correlate_error_with_commit(
                error_time,
                lookback_hours=settings.git_lookback_hours
            )
            if correlated_commit:
                print(f"🔗 Correlated with commit: {correlated_commit['short_hash']} ({correlated_commit['time_before_error']:.1f} min ago)")
        
        # Store alert
        alert = {
            "id": len(alerts_storage),
            "query": query_to_fix,
            "duration_ms": duration_ms,
            "endpoint": str(request.url.path),
            "timestamp": time.time(),
            "severity": severity,
            "status": "analyzing",
            # Forensic trace data
            "source_file": source_file,
            "source_line": source_line,
            "function_name": function_name,
            "code_snippet": code_snippet,
            # Git context
            "git_commit": git_commit
        }
        alerts_storage.append(alert)
        alert_index = len(alerts_storage) - 1
        
        # Keep only last 100 alerts
        if len(alerts_storage) > 100:
            removed_alert = alerts_storage.pop(0)
            # Clean up old analysis
            if removed_alert["id"] in analysis_storage:
                del analysis_storage[removed_alert["id"]]
        
        print(f"{severity_emoji} Slow query detected ({duration_ms:.2f}ms) - Alert #{alert_index}")
        
        # Trigger AI analysis in background if enabled
        if settings.enable_auto_analysis:
            # 1. LOW-OVERHEAD CHECK: Only analyze if it's really bad or new
            is_pathological = duration_ms >= 2000
            is_new_pattern = query_to_fix.strip() not in analyzing_queries
            
            # 2. BOUNCER CHECK: Is system healthy?
            if not Bouncer.is_safe_to_operate():
                print(f"🛑 Analysis skipped by Bouncer (System Overload)")
                alerts_storage[alert_index]["status"] = "skipped_overload"
            
            # 3. OVERHEAD FILTER
            elif not (is_pathological or is_new_pattern):
                print(f"🍃 Low-Overhead Mode: Skipping AI analysis for non-critical query")
                alerts_storage[alert_index]["status"] = "skipped_low_impact"
            
            # 4. Proceed with analysis
            else:
                if is_new_pattern:
                    analyzing_queries.add(query_to_fix.strip())
                    print(f"🔒 Locked query for analysis. Active: {len(analyzing_queries)}")
                
                import asyncio
                asyncio.create_task(run_ai_analysis(alert_index, query_to_fix))
    
    return response





@app.get("/api/debug/state")
async def get_debug_state():
    return {
        "analyzing_queries": list(analyzing_queries),
        "alerts_count": len(alerts_storage),
        "analysis_count": len(analysis_storage)
    }

@app.get("/dashboard")
async def dashboard():
    """Serve the dashboard UI"""
    return FileResponse("static/index.html")


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.get("/")
async def read_root():
    return FileResponse('static/index.html')


@app.get("/api/alerts")
async def get_alerts():
    """Get recent alerts"""
    return {"alerts": alerts_storage[-50:]}  # Return last 50 alerts


@app.get("/api/alerts/{alert_id}/analysis")
async def get_alert_analysis(alert_id: int):
    """Get AI analysis for a specific alert"""
    # Find alert by ID
    alert = next((a for a in alerts_storage if a["id"] == alert_id), None)
    
    if not alert:
        return {"error": "Alert not found"}, 404
    
    # Check if analysis exists
    if alert_id in analysis_storage:
        return {
            "alert": alert,
            "analysis": analysis_storage[alert_id]
        }
    else:
        return {
            "alert": alert,
            "analysis": {
                "status": alert.get("status", "analyzing"),
                "message": "Analysis in progress..." if alert.get("status") == "analyzing" else "Analysis not available"
            }
        }


@app.post("/api/alerts/{alert_id}/benchmark")
async def benchmark_alert(alert_id: int):
    """Run benchmark comparison between original and optimized query"""
    from utils.benchmark import run_benchmark
    
    # Find alert by ID
    alert = next((a for a in alerts_storage if a["id"] == alert_id), None)
    
    if not alert:
        return {"error": "Alert not found"}, 404
    
    # Check if analysis exists with a suggested fix
    if alert_id not in analysis_storage:
        return {"error": "Analysis not available yet"}, 400
    
    analysis = analysis_storage[alert_id]
    
    if not analysis.get("suggested_fix"):
        return {"error": "No optimization suggestion available"}, 400
    
    # Run the benchmark
    original_query = alert["query"]
    optimized_query = analysis["suggested_fix"]
    
    print(f"\n🧪 Running benchmark for alert #{alert_id}")
    benchmark_results = run_benchmark(original_query, optimized_query)
    
    # Calculate Economic & Carbon Impact
    if benchmark_results["status"] == "success":
        from utils.economics import calculate_savings
        
        impact = calculate_savings(
            original_duration_ms=benchmark_results["original_time_ms"],
            optimized_duration_ms=benchmark_results["optimized_time_ms"]
        )
        
        # Add impact to benchmark results
        benchmark_results["economics"] = impact
        print(f"💰 Economic Impact Calculated: ${impact.get('monthly_usd', 0)}/mo savings")
    
    # Store benchmark results in analysis
    analysis_storage[alert_id]["benchmark"] = benchmark_results
    
    return {
        "alert_id": alert_id,
        "benchmark": benchmark_results
    }


# Test endpoint to simulate slow queries
@app.get("/test/slow")
async def test_slow_query():
    """Test endpoint that simulates a slow query"""
    import time
    time.sleep(0.6)  # Simulate 600ms query
    return {"message": "Slow query executed"}


# ========== NEW ADVANCED FEATURES ENDPOINTS ==========

@app.get("/api/git/recent-commits")
async def get_recent_commits(hours: int = 24):
    """Get recent git commits affecting database files"""
    if not git_tracker or not git_tracker.is_available():
        return {"error": "Git tracking not available", "commits": []}
    
    commits = git_tracker.find_schema_changes(since_hours=hours)
    return {
        "commits": commits,
        "total": len(commits),
        "lookback_hours": hours
    }


@app.get("/api/git/current")
async def get_current_commit():
    """Get current git commit information"""
    if not git_tracker or not git_tracker.is_available():
        return {"error": "Git tracking not available"}
    
    commit = git_tracker.get_current_commit()
    return commit if commit else {"error": "No commit found"}


@app.get("/api/schema/history/{table_name}")
async def get_schema_history(table_name: str, limit: int = 10):
    """Get schema evolution history for a table"""
    if not schema_tracker:
        return {"error": "Schema tracking not available", "history": []}
    
    history = schema_tracker.get_schema_history(table_name, limit=limit)
    return {
        "table": table_name,
        "history": history,
        "total": len(history)
    }


@app.get("/api/schema/changes/{table_name}")
async def get_schema_changes(table_name: str, hours: int = 24):
    """Get recent schema changes for a table"""
    if not schema_tracker:
        return {"error": "Schema tracking not available", "changes": []}
    
    changes = schema_tracker.detect_schema_changes(table_name, hours_back=hours)
    return {
        "table": table_name,
        "changes": changes,
        "total": len(changes),
        "lookback_hours": hours
    }


@app.post("/api/schema/snapshot")
async def capture_schema_snapshot(table_name: str = None):
    """Manually capture schema snapshot"""
    if not schema_tracker:
        return {"error": "Schema tracking not available"}
    
    commit_hash = None
    if git_tracker and git_tracker.is_available():
        commit = git_tracker.get_current_commit()
        commit_hash = commit['hash'] if commit else None
    
    success = schema_tracker.capture_schema_snapshot(
        table_name=table_name,
        commit_hash=commit_hash
    )
    
    return {
        "success": success,
        "table": table_name or "all tables",
        "commit_hash": commit_hash
    }


@app.post("/api/preventive/analyze")
async def analyze_migrations(migration_files: List[str] = None):
    """Analyze pending migrations for risks"""
    from services.preventive_analyzer import get_preventive_analyzer
    
    if not migration_files:
        return {"error": "No migration files provided"}
    
    analyzer = get_preventive_analyzer()
    report = await analyzer.generate_risk_report(migration_files)
    
    return report


@app.post("/api/migration/safety")
async def check_migration_safety(migration_sql: str):
    """Check safety of a migration SQL"""
    if not schema_tracker:
        return {"error": "Schema tracking not available"}
    
    safety = schema_tracker.analyze_migration_safety(migration_sql)
    impact = schema_tracker.predict_migration_impact(migration_sql)
    
    return {
        "safety": safety,
        "impact": impact
    }




@app.post("/api/sdk/evaluate")
async def sdk_evaluate(payload: dict):
    """
    SDK Real-time Interception Endpoint (High Performance).
    Calls Gemini directly to avoid DB overhead of the full Graph.
    """
    query = payload.get("query")
    stack_trace = payload.get("stack_trace")
    git_info = payload.get("git_info")
    env = payload.get("env", "development")

    if not query:
        return {"verdict": "GO"}

    print(f"🛡️  SDK Request: {query[:50]}...")

    try:
        from services.prompts import GUARDIAN_SDK_PROMPT
        import json
        
        prompt = GUARDIAN_SDK_PROMPT.format(
            query=query,
            stack_trace=stack_trace,
            git_info=json.dumps(git_info),
            env=env
        )
        
        # Use the global sdk_ai_client
        import asyncio
        response = await asyncio.to_thread(
            sdk_ai_client.models.generate_content,
            model=settings.gemini_model,
            contents=prompt,
            config={'response_mime_type': 'application/json'}
        )
        
        print(f"🤖 Raw AI Response: {response.text}")
        ai_data = json.loads(response.text)
        print(f"🤖 SDK Verdict: {ai_data.get('verdict')} - {ai_data.get('issue')}")
        
        return {
            "verdict": ai_data.get("verdict", "GO"),
            "issue": ai_data.get("issue", "No critical issues detected"),
            "impact": ai_data.get("impact", "Low risk"),
            "fix": ai_data.get("fix", ""),
            "reasoning": ai_data.get("reasoning_short", "")
        }
    except Exception as e:
        print(f"❌ SDK Evaluation Error: {e}")
        return {"verdict": "GO", "error": str(e)}

@app.get("/api/alerts/{alert_id}/root-cause")
async def get_root_cause_analysis(alert_id: int):
    """Get detailed root cause analysis with git correlation"""
    # Find alert by ID
    alert = next((a for a in alerts_storage if a["id"] == alert_id), None)
    
    if not alert:
        return {"error": "Alert not found"}, 404
    
    # Get analysis
    if alert_id not in analysis_storage:
        return {"error": "Analysis not available yet"}, 400
    
    analysis = analysis_storage[alert_id]
    
    # Build root cause response
    root_cause = {
        "alert": alert,
        "git_context": alert.get("git_commit"),
        "root_cause": analysis.get("root_cause"),
        "commit_correlation": analysis.get("commit_correlation"),
        "fix_options": analysis.get("fix_options", []),
        "what_broke": analysis.get("what_broke"),
        "how_to_prevent": analysis.get("how_to_prevent")
    }
    
    return root_cause
# Mount static files at the root AFTER all other routes
from fastapi.staticfiles import StaticFiles
app.mount("/", StaticFiles(directory="static"), name="static_root")
