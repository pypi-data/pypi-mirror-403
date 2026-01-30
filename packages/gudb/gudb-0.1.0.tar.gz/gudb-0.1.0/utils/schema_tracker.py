"""
Schema Tracker Module

Monitors database schema evolution over time and validates migration safety.
Tracks schema changes, detects unsafe migrations, and predicts production impact.
"""

import json
import psycopg2
from datetime import datetime
from typing import Optional, List, Dict, Any
import sqlparse
from utils.config import settings
from utils.db import get_db_connection


class SchemaTracker:
    """Tracks database schema evolution and validates migrations"""
    
    def __init__(self):
        """Initialize SchemaTracker"""
        self.conn = None
        self._ensure_tracking_tables()
    
    def _ensure_tracking_tables(self):
        """Create schema tracking tables if they don't exist"""
        try:
            conn = get_db_connection()
            if not conn:
                print("⚠️  Schema tracking disabled: No database connection")
                return
            
            cur = conn.cursor()
            
            # Create schema_history table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS schema_history (
                    id SERIAL PRIMARY KEY,
                    table_name VARCHAR(255),
                    schema_snapshot JSONB,
                    commit_hash VARCHAR(40),
                    captured_at TIMESTAMP DEFAULT NOW()
                );
            """)
            
            # Create migration_history table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS migration_history (
                    id SERIAL PRIMARY KEY,
                    migration_file VARCHAR(255),
                    migration_sql TEXT,
                    risk_level VARCHAR(20),
                    applied_at TIMESTAMP,
                    rolled_back_at TIMESTAMP,
                    commit_hash VARCHAR(40),
                    status VARCHAR(20) DEFAULT 'pending'
                );
            """)
            
            # Create query_patterns table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS query_patterns (
                    id SERIAL PRIMARY KEY,
                    query_hash VARCHAR(64) UNIQUE,
                    query_template TEXT,
                    first_seen TIMESTAMP DEFAULT NOW(),
                    last_seen TIMESTAMP DEFAULT NOW(),
                    execution_count INTEGER DEFAULT 1,
                    avg_duration_ms FLOAT DEFAULT 0
                );
            """)
            
            conn.commit()
            cur.close()
            conn.close()
            print("✅ Schema tracking tables initialized")
            
        except Exception as e:
            print(f"⚠️  Failed to create tracking tables: {e}")
    
    def capture_schema_snapshot(
        self, 
        table_name: Optional[str] = None,
        commit_hash: Optional[str] = None
    ) -> bool:
        """
        Capture current schema state
        
        Args:
            table_name: Specific table to snapshot (None for all tables)
            commit_hash: Git commit hash to associate with snapshot
            
        Returns:
            True if successful
        """
        try:
            conn = get_db_connection()
            if not conn:
                return False
            
            cur = conn.cursor()
            
            # Get tables to snapshot
            if table_name:
                tables = [table_name]
            else:
                cur.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_type = 'BASE TABLE'
                    AND table_name NOT IN ('schema_history', 'migration_history', 'query_patterns')
                """)
                tables = [row[0] for row in cur.fetchall()]
            
            # Capture schema for each table
            for tbl in tables:
                # Get columns
                cur.execute("""
                    SELECT 
                        column_name,
                        data_type,
                        is_nullable,
                        column_default,
                        character_maximum_length
                    FROM information_schema.columns
                    WHERE table_name = %s
                    ORDER BY ordinal_position
                """, (tbl,))
                columns = cur.fetchall()
                
                # Get indexes
                cur.execute("""
                    SELECT
                        indexname,
                        indexdef
                    FROM pg_indexes
                    WHERE tablename = %s
                """, (tbl,))
                indexes = cur.fetchall()
                
                # Get constraints
                cur.execute("""
                    SELECT
                        conname,
                        contype,
                        pg_get_constraintdef(oid)
                    FROM pg_constraint
                    WHERE conrelid = %s::regclass
                """, (tbl,))
                constraints = cur.fetchall()
                
                # Build snapshot
                snapshot = {
                    "table": tbl,
                    "columns": [
                        {
                            "name": col[0],
                            "type": col[1],
                            "nullable": col[2],
                            "default": col[3],
                            "max_length": col[4]
                        }
                        for col in columns
                    ],
                    "indexes": [
                        {"name": idx[0], "definition": idx[1]}
                        for idx in indexes
                    ],
                    "constraints": [
                        {"name": con[0], "type": con[1], "definition": con[2]}
                        for con in constraints
                    ]
                }
                
                # Store snapshot
                cur.execute("""
                    INSERT INTO schema_history (table_name, schema_snapshot, commit_hash)
                    VALUES (%s, %s, %s)
                """, (tbl, json.dumps(snapshot), commit_hash))
            
            conn.commit()
            cur.close()
            conn.close()
            print(f"✅ Captured schema snapshot for {len(tables)} table(s)")
            return True
            
        except Exception as e:
            print(f"❌ Failed to capture schema snapshot: {e}")
            return False
    
    def detect_schema_changes(
        self, 
        table_name: str,
        hours_back: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Detect schema changes for a table
        
        Args:
            table_name: Table to check
            hours_back: How far back to look
            
        Returns:
            List of detected changes
        """
        try:
            conn = get_db_connection()
            if not conn:
                return []
            
            cur = conn.cursor()
            
            # Get recent snapshots
            cur.execute("""
                SELECT schema_snapshot, captured_at, commit_hash
                FROM schema_history
                WHERE table_name = %s
                AND captured_at > NOW() - INTERVAL '%s hours'
                ORDER BY captured_at DESC
                LIMIT 10
            """, (table_name, hours_back))
            
            snapshots = cur.fetchall()
            cur.close()
            conn.close()
            
            if len(snapshots) < 2:
                return []
            
            changes = []
            
            # Compare consecutive snapshots
            for i in range(len(snapshots) - 1):
                newer = json.loads(snapshots[i][0])
                older = json.loads(snapshots[i + 1][0])
                
                change = self._compare_schemas(older, newer)
                if change["has_changes"]:
                    change["timestamp"] = snapshots[i][1]
                    change["commit_hash"] = snapshots[i][2]
                    changes.append(change)
            
            return changes
            
        except Exception as e:
            print(f"❌ Failed to detect schema changes: {e}")
            return []
    
    def _compare_schemas(
        self, 
        old_schema: Dict[str, Any],
        new_schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compare two schema snapshots"""
        changes = {
            "has_changes": False,
            "columns_added": [],
            "columns_removed": [],
            "columns_modified": [],
            "indexes_added": [],
            "indexes_removed": [],
            "constraints_added": [],
            "constraints_removed": []
        }
        
        # Compare columns
        old_cols = {col["name"]: col for col in old_schema.get("columns", [])}
        new_cols = {col["name"]: col for col in new_schema.get("columns", [])}
        
        for name in new_cols:
            if name not in old_cols:
                changes["columns_added"].append(name)
                changes["has_changes"] = True
        
        for name in old_cols:
            if name not in new_cols:
                changes["columns_removed"].append(name)
                changes["has_changes"] = True
            elif old_cols[name] != new_cols[name]:
                changes["columns_modified"].append({
                    "name": name,
                    "old": old_cols[name],
                    "new": new_cols[name]
                })
                changes["has_changes"] = True
        
        # Compare indexes
        old_idx = {idx["name"] for idx in old_schema.get("indexes", [])}
        new_idx = {idx["name"] for idx in new_schema.get("indexes", [])}
        
        changes["indexes_added"] = list(new_idx - old_idx)
        changes["indexes_removed"] = list(old_idx - new_idx)
        if changes["indexes_added"] or changes["indexes_removed"]:
            changes["has_changes"] = True
        
        # Compare constraints
        old_con = {con["name"] for con in old_schema.get("constraints", [])}
        new_con = {con["name"] for con in new_schema.get("constraints", [])}
        
        changes["constraints_added"] = list(new_con - old_con)
        changes["constraints_removed"] = list(old_con - new_con)
        if changes["constraints_added"] or changes["constraints_removed"]:
            changes["has_changes"] = True
        
        return changes
    
    def analyze_migration_safety(self, migration_sql: str) -> Dict[str, Any]:
        """
        Analyze migration for safety risks
        
        Args:
            migration_sql: SQL migration to analyze
            
        Returns:
            Risk assessment dict
        """
        risks = []
        risk_level = "low"
        warnings = []
        
        # Parse SQL
        statements = sqlparse.split(migration_sql)
        
        for stmt in statements:
            stmt_upper = stmt.upper().strip()
            
            # High-risk operations
            if "DROP TABLE" in stmt_upper:
                risks.append("DROP TABLE - Data loss risk")
                risk_level = "high"
            
            if "DROP COLUMN" in stmt_upper:
                risks.append("DROP COLUMN - Data loss and query breakage risk")
                risk_level = "high"
            
            if "ALTER COLUMN" in stmt_upper and "NOT NULL" in stmt_upper:
                risks.append("Adding NOT NULL constraint - May fail on existing data")
                risk_level = "high" if risk_level != "high" else "high"
            
            # Medium-risk operations
            if "ADD COLUMN" in stmt_upper and "NOT NULL" in stmt_upper and "DEFAULT" not in stmt_upper:
                risks.append("Adding NOT NULL column without default - Will fail on existing rows")
                risk_level = "high"
            
            if "CREATE INDEX" in stmt_upper and "CONCURRENTLY" not in stmt_upper:
                warnings.append("CREATE INDEX without CONCURRENTLY - Will lock table")
                if risk_level == "low":
                    risk_level = "medium"
            
            if "ALTER TABLE" in stmt_upper and "ADD CONSTRAINT" in stmt_upper:
                warnings.append("Adding constraint - May fail on existing data")
                if risk_level == "low":
                    risk_level = "medium"
            
            # Low-risk but notable
            if "RENAME" in stmt_upper:
                warnings.append("RENAME operation - Update application code")
        
        return {
            "risk_level": risk_level,
            "risks": risks,
            "warnings": warnings,
            "statement_count": len(statements),
            "safe_to_auto_apply": risk_level == "low" and len(risks) == 0
        }
    
    def predict_migration_impact(
        self, 
        migration_sql: str
    ) -> Dict[str, Any]:
        """
        Predict production impact of migration
        
        Args:
            migration_sql: SQL migration to analyze
            
        Returns:
            Impact prediction dict
        """
        safety = self.analyze_migration_safety(migration_sql)
        
        # Estimate affected queries (simplified)
        affected_tables = self._extract_affected_tables(migration_sql)
        
        impact = {
            "risk_level": safety["risk_level"],
            "affected_tables": affected_tables,
            "estimated_downtime": self._estimate_downtime(migration_sql),
            "rollback_difficulty": self._assess_rollback_difficulty(migration_sql),
            "recommendations": []
        }
        
        # Generate recommendations
        if "CREATE INDEX" in migration_sql.upper() and "CONCURRENTLY" not in migration_sql.upper():
            impact["recommendations"].append("Use CREATE INDEX CONCURRENTLY to avoid table locks")
        
        if safety["risk_level"] == "high":
            impact["recommendations"].append("Test in staging environment first")
            impact["recommendations"].append("Create backup before applying")
            impact["recommendations"].append("Plan rollback strategy")
        
        if "DROP" in migration_sql.upper():
            impact["recommendations"].append("Ensure no application code references dropped objects")
        
        return impact
    
    def _extract_affected_tables(self, sql: str) -> List[str]:
        """Extract table names from SQL"""
        tables = set()
        statements = sqlparse.parse(sql)
        
        for stmt in statements:
            for token in stmt.tokens:
                if isinstance(token, sqlparse.sql.Identifier):
                    tables.add(str(token))
        
        return list(tables)
    
    def _estimate_downtime(self, sql: str) -> str:
        """Estimate migration downtime"""
        sql_upper = sql.upper()
        
        if "CREATE INDEX" in sql_upper and "CONCURRENTLY" not in sql_upper:
            return "5-30 minutes (table locked)"
        elif "ALTER TABLE" in sql_upper and "ADD COLUMN" in sql_upper:
            return "< 1 second (metadata only)"
        elif "DROP" in sql_upper:
            return "< 1 second"
        else:
            return "Minimal (< 1 second)"
    
    def _assess_rollback_difficulty(self, sql: str) -> str:
        """Assess how difficult rollback would be"""
        sql_upper = sql.upper()
        
        if "DROP TABLE" in sql_upper or "DROP COLUMN" in sql_upper:
            return "HARD - Data loss, requires backup restore"
        elif "ALTER COLUMN" in sql_upper:
            return "MEDIUM - Requires reverse migration"
        elif "CREATE INDEX" in sql_upper:
            return "EASY - Just DROP INDEX"
        elif "ADD COLUMN" in sql_upper:
            return "EASY - DROP COLUMN"
        else:
            return "MEDIUM - Depends on operation"
    
    def get_schema_history(
        self, 
        table_name: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get schema history for a table
        
        Args:
            table_name: Table name
            limit: Max number of snapshots
            
        Returns:
            List of schema snapshots
        """
        try:
            conn = get_db_connection()
            if not conn:
                return []
            
            cur = conn.cursor()
            cur.execute("""
                SELECT schema_snapshot, captured_at, commit_hash
                FROM schema_history
                WHERE table_name = %s
                ORDER BY captured_at DESC
                LIMIT %s
            """, (table_name, limit))
            
            history = []
            for row in cur.fetchall():
                history.append({
                    "snapshot": json.loads(row[0]),
                    "captured_at": row[1],
                    "commit_hash": row[2]
                })
            
            cur.close()
            conn.close()
            return history
            
        except Exception as e:
            print(f"❌ Failed to get schema history: {e}")
            return []


# Global instance
_schema_tracker = None

def get_schema_tracker() -> SchemaTracker:
    """Get or create global SchemaTracker instance"""
    global _schema_tracker
    if _schema_tracker is None:
        _schema_tracker = SchemaTracker()
    return _schema_tracker
