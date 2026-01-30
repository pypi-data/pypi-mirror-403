"""
Preventive Analyzer Module

Analyzes pending migrations and code changes before deployment.
Predicts production failures and generates risk reports.
"""

from typing import List, Dict, Any, Optional
import sqlparse
from datetime import datetime
from utils.schema_tracker import get_schema_tracker
from utils.git_tracker import get_git_tracker


class PreventiveAnalyzer:
    """Analyzes pending changes to prevent production failures"""
    
    def __init__(self):
        """Initialize PreventiveAnalyzer"""
        self.schema_tracker = get_schema_tracker()
        self.git_tracker = get_git_tracker()
    
    async def analyze_pending_migrations(
        self, 
        migration_files: List[str],
        use_ai: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze pending migration files for risks
        """
        results = {
            "total_migrations": len(migration_files),
            "overall_risk": "low",
            "migrations": [],
            "critical_warnings": [],
            "recommendations": [],
            "estimated_total_downtime": "< 1 minute"
        }
        
        high_risk_count = 0
        
        for migration_file in migration_files:
            try:
                with open(migration_file, 'r') as f:
                    sql = f.read()
                
                # Basic Rule-Based Analysis
                safety = self.schema_tracker.analyze_migration_safety(sql)
                impact = self.schema_tracker.predict_migration_impact(sql)
                
                # Fetch SRE Context (Blockers, Version)
                from utils.db import get_db_connection
                sre_context = {"stats": {}, "blockers": [], "version": "Unknown"}
                tables = impact.get("affected_tables", [])
                try:
                    conn = get_db_connection()
                    cur = conn.cursor()
                    # Version
                    cur.execute("SELECT version();")
                    sre_context["version"] = cur.fetchone()[0]
                    # Stats
                    if tables:
                        cur.execute(f"SELECT reltuples::bigint FROM pg_class WHERE relname = '{tables[0]}';")
                        sre_context["stats"] = {"row_count": cur.fetchone()[0]}
                    # Active Blockers (Lock Starvation Check)
                    cur.execute("""
                        SELECT pid, now() - xact_start as duration, query 
                        FROM pg_stat_activity 
                        WHERE state != 'idle' AND now() - xact_start > interval '5 seconds'
                        LIMIT 5;
                    """)
                    sre_context["blockers"] = [{"pid": b[0], "duration": str(b[1]), "query": b[2][:50]} for b in cur.fetchall()]
                    cur.close()
                    conn.close()
                except: pass

                # AI-Driven Deep Analysis (The "SRE Auditor" Verdict)
                ai_verdict = None
                if use_ai:
                    from google import genai
                    from services.prompts import MIGRATION_SAFETY_PROMPT
                    import json
                    from utils.config import settings
                    
                    try:
                        client = genai.Client(api_key=settings.gemini_api_key)
                        prompt = MIGRATION_SAFETY_PROMPT.format(
                            migration_sql=sql,
                            table_stats=json.dumps(sre_context["stats"], indent=2),
                            active_blockers=json.dumps(sre_context["blockers"], indent=2),
                            db_version=sre_context["version"]
                        )
                        response = client.models.generate_content(
                            model=settings.gemini_model,
                            contents=prompt,
                            config={'response_mime_type': 'application/json'}
                        )
                        ai_verdict = json.loads(response.text)
                    except Exception as ai_err:
                        print(f"⚠️ AI Migration Analysis failed: {ai_err}")

                migration_result = {
                    "file": migration_file,
                    "risk_level": ai_verdict.get("risk_score") if ai_verdict else safety["risk_level"],
                    "lock_prediction": ai_verdict.get("lock_prediction") if ai_verdict else "Unknown",
                    "rewrite_risk": ai_verdict.get("rewrite_risk") if ai_verdict else "Unknown",
                    "verdict": ai_verdict.get("verdict") if ai_verdict else "Pending Manual Review"
                }
                
                results["migrations"].append(migration_result)
                
                if (ai_verdict and int(str(ai_verdict.get("risk_score", 0))) >= 7) or safety["risk_level"] == "high":
                    high_risk_count += 1
                
            except Exception as e:
                results["migrations"].append({"file": migration_file, "error": str(e)})
        
        results["overall_risk"] = "high" if high_risk_count > 0 else "low"
        return results
    
    def simulate_query_impact(
        self, 
        queries: List[str],
        schema_changes: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Simulate impact of schema changes on existing queries
        
        Args:
            queries: List of SQL queries to test
            schema_changes: Dict describing schema changes
            
        Returns:
            Impact analysis
        """
        results = {
            "total_queries": len(queries),
            "affected_queries": [],
            "broken_queries": [],
            "warnings": []
        }
        
        for query in queries:
            impact = self._analyze_query_compatibility(query, schema_changes)
            if impact["is_broken"]:
                results["broken_queries"].append({
                    "query": query,
                    "reason": impact["reason"],
                    "severity": "critical"
                })
            elif impact["is_affected"]:
                results["affected_queries"].append({
                    "query": query,
                    "impact": impact["impact"],
                    "severity": "warning"
                })
        
        # Generate warnings
        if results["broken_queries"]:
            results["warnings"].append(
                f"🚨 {len(results['broken_queries'])} queries will FAIL after deployment"
            )
        
        if results["affected_queries"]:
            results["warnings"].append(
                f"⚠️  {len(results['affected_queries'])} queries will be affected"
            )
        
        return results
    
    def _analyze_query_compatibility(
        self, 
        query: str,
        schema_changes: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze if a query is compatible with schema changes"""
        result = {
            "is_broken": False,
            "is_affected": False,
            "reason": None,
            "impact": None
        }
        
        query_upper = query.upper()
        
        # Check for dropped columns
        if "columns_removed" in schema_changes:
            for col in schema_changes["columns_removed"]:
                if col.upper() in query_upper:
                    result["is_broken"] = True
                    result["reason"] = f"References dropped column: {col}"
                    return result
        
        # Check for dropped tables
        if "tables_removed" in schema_changes:
            for table in schema_changes["tables_removed"]:
                if table.upper() in query_upper:
                    result["is_broken"] = True
                    result["reason"] = f"References dropped table: {table}"
                    return result
        
        # Check for renamed columns/tables
        if "columns_renamed" in schema_changes:
            for old_name, new_name in schema_changes["columns_renamed"].items():
                if old_name.upper() in query_upper:
                    result["is_affected"] = True
                    result["impact"] = f"Column {old_name} renamed to {new_name}"
                    return result
        
        # Check for new NOT NULL constraints
        if "constraints_added" in schema_changes:
            for constraint in schema_changes["constraints_added"]:
                if "NOT NULL" in constraint.upper():
                    result["is_affected"] = True
                    result["impact"] = "New NOT NULL constraint may cause INSERT failures"
        
        return result
    
    async def generate_risk_report(
        self, 
        migrations: List[str],
        recent_queries: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive deployment risk report
        """
        report = {
            "generated_at": datetime.now().isoformat(),
            "migration_analysis": None,
            "query_impact": None,
            "git_context": None,
            "overall_assessment": None,
            "deployment_strategy": None
        }
        
        # Analyze migrations
        if migrations:
            report["migration_analysis"] = await self.analyze_pending_migrations(migrations)
        
        # Simulate query impact if queries provided
        if recent_queries and migrations:
            # Extract schema changes from migrations
            schema_changes = self._extract_schema_changes_from_migrations(migrations)
            report["query_impact"] = self.simulate_query_impact(recent_queries, schema_changes)
        
        # Get git context
        if self.git_tracker.is_available():
            recent_commits = self.git_tracker.find_schema_changes(since_hours=48)
            report["git_context"] = {
                "recent_schema_commits": len(recent_commits),
                "commits": recent_commits[:5]  # Last 5
            }
        
        # Overall assessment
        report["overall_assessment"] = self._generate_overall_assessment(report)
        
        # Deployment strategy
        report["deployment_strategy"] = self._suggest_deployment_strategy(report)
        
        return report
    
    def _extract_schema_changes_from_migrations(
        self, 
        migration_files: List[str]
    ) -> Dict[str, Any]:
        """Extract schema changes from migration files"""
        changes = {
            "columns_removed": [],
            "columns_added": [],
            "tables_removed": [],
            "constraints_added": []
        }
        
        for migration_file in migration_files:
            try:
                with open(migration_file, 'r') as f:
                    sql = f.read()
                
                sql_upper = sql.upper()
                
                # Simple pattern matching (could be enhanced with proper SQL parsing)
                if "DROP COLUMN" in sql_upper:
                    # Extract column names (simplified)
                    changes["columns_removed"].append("unknown_column")
                
                if "DROP TABLE" in sql_upper:
                    changes["tables_removed"].append("unknown_table")
                
                if "ADD CONSTRAINT" in sql_upper and "NOT NULL" in sql_upper:
                    changes["constraints_added"].append("NOT NULL constraint")
                
            except Exception as e:
                print(f"⚠️  Failed to parse {migration_file}: {e}")
        
        return changes
    
    def _generate_overall_assessment(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """Generate overall deployment assessment"""
        assessment = {
            "safe_to_deploy": True,
            "risk_level": "low",
            "blocking_issues": [],
            "warnings": []
        }
        
        # Check migration risks
        if report.get("migration_analysis"):
            migration_risk = report["migration_analysis"]["overall_risk"]
            if migration_risk == "high":
                assessment["safe_to_deploy"] = False
                assessment["risk_level"] = "high"
                assessment["blocking_issues"].extend(
                    report["migration_analysis"]["critical_warnings"]
                )
            elif migration_risk == "medium":
                assessment["risk_level"] = "medium"
                assessment["warnings"].extend(
                    report["migration_analysis"].get("recommendations", [])
                )
        
        # Check query impact
        if report.get("query_impact"):
            if report["query_impact"]["broken_queries"]:
                assessment["safe_to_deploy"] = False
                assessment["risk_level"] = "high"
                assessment["blocking_issues"].append(
                    f"{len(report['query_impact']['broken_queries'])} queries will fail"
                )
        
        return assessment
    
    def _suggest_deployment_strategy(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """Suggest deployment strategy based on risk"""
        assessment = report.get("overall_assessment", {})
        risk_level = assessment.get("risk_level", "low")
        
        strategies = {
            "high": {
                "approach": "Staged Rollout with Rollback Plan",
                "steps": [
                    "1. Create full database backup",
                    "2. Deploy to staging and run full test suite",
                    "3. Deploy to single production instance (canary)",
                    "4. Monitor for 1 hour",
                    "5. If stable, gradually roll out to remaining instances",
                    "6. Keep rollback scripts ready"
                ],
                "monitoring": [
                    "Watch error rates closely",
                    "Monitor query performance",
                    "Check application logs",
                    "Track user-reported issues"
                ],
                "rollback_trigger": "Any increase in error rate or user complaints"
            },
            "medium": {
                "approach": "Careful Deployment with Monitoring",
                "steps": [
                    "1. Test in staging environment",
                    "2. Deploy during low-traffic window",
                    "3. Monitor for 30 minutes",
                    "4. Verify key functionality"
                ],
                "monitoring": [
                    "Monitor error rates",
                    "Check query performance"
                ],
                "rollback_trigger": "Significant increase in errors"
            },
            "low": {
                "approach": "Standard Deployment",
                "steps": [
                    "1. Deploy to production",
                    "2. Basic smoke testing",
                    "3. Monitor for anomalies"
                ],
                "monitoring": [
                    "Standard monitoring"
                ],
                "rollback_trigger": "Critical errors only"
            }
        }
        
        return strategies.get(risk_level, strategies["low"])
    
    def suggest_deployment_strategy(self, risk_level: str) -> Dict[str, Any]:
        """
        Suggest deployment strategy based on risk level
        
        Args:
            risk_level: "low", "medium", or "high"
            
        Returns:
            Deployment strategy dict
        """
        return self._suggest_deployment_strategy({"overall_assessment": {"risk_level": risk_level}})


# Global instance
_preventive_analyzer = None

def get_preventive_analyzer() -> PreventiveAnalyzer:
    """Get or create global PreventiveAnalyzer instance"""
    global _preventive_analyzer
    if _preventive_analyzer is None:
        _preventive_analyzer = PreventiveAnalyzer()
    return _preventive_analyzer
