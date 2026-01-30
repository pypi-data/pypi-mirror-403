"""
Git Tracker Module

Tracks git commits and correlates database errors with code changes.
Provides insights into which commits introduced schema changes or caused performance issues.
"""

import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pathlib import Path

try:
    from git import Repo, GitCommandError
    GIT_AVAILABLE = True
except ImportError:
    GIT_AVAILABLE = False
    print("⚠️  GitPython not installed. Git tracking features disabled.")


class GitTracker:
    """Tracks git repository changes and correlates them with database errors"""
    
    def __init__(self, repo_path: str = "."):
        """
        Initialize GitTracker
        
        Args:
            repo_path: Path to git repository (default: current directory)
        """
        self.repo_path = repo_path
        self.repo = None
        
        if not GIT_AVAILABLE:
            print("⚠️  Git tracking disabled: GitPython not available")
            return
            
        try:
            self.repo = Repo(repo_path)
            if self.repo.bare:
                print("⚠️  Git tracking disabled: Repository is bare")
                self.repo = None
        except Exception as e:
            print(f"⚠️  Git tracking disabled: {str(e)}")
            self.repo = None
    
    def is_available(self) -> bool:
        """Check if git tracking is available"""
        return self.repo is not None
    
    def get_current_commit(self) -> Optional[Dict[str, Any]]:
        """
        Get current git commit information
        
        Returns:
            Dict with commit hash, author, message, timestamp, or None if unavailable
        """
        if not self.is_available():
            return None
        
        try:
            commit = self.repo.head.commit
            return {
                "hash": commit.hexsha,
                "short_hash": commit.hexsha[:7],
                "author": str(commit.author),
                "email": commit.author.email,
                "message": commit.message.strip(),
                "timestamp": datetime.fromtimestamp(commit.committed_date),
                "files_changed": len(commit.stats.files)
            }
        except Exception as e:
            print(f"❌ Failed to get current commit: {e}")
            return None
    
    def get_recent_commits(
        self, 
        since_hours: int = 24,
        file_patterns: Optional[List[str]] = None,
        max_count: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get recent commits, optionally filtered by file patterns
        
        Args:
            since_hours: Look back this many hours
            file_patterns: List of file patterns to filter (e.g., ['*.sql', 'migrations/*'])
            max_count: Maximum number of commits to return
            
        Returns:
            List of commit dictionaries
        """
        if not self.is_available():
            return []
        
        try:
            since_date = datetime.now() - timedelta(hours=since_hours)
            commits = []
            
            for commit in self.repo.iter_commits(max_count=max_count):
                commit_date = datetime.fromtimestamp(commit.committed_date)
                
                if commit_date < since_date:
                    break
                
                # Filter by file patterns if provided
                if file_patterns:
                    changed_files = list(commit.stats.files.keys())
                    matches = any(
                        any(Path(f).match(pattern) for pattern in file_patterns)
                        for f in changed_files
                    )
                    if not matches:
                        continue
                
                commits.append({
                    "hash": commit.hexsha,
                    "short_hash": commit.hexsha[:7],
                    "author": str(commit.author),
                    "email": commit.author.email,
                    "message": commit.message.strip(),
                    "timestamp": commit_date,
                    "files_changed": list(commit.stats.files.keys())
                })
            
            return commits
        except Exception as e:
            print(f"❌ Failed to get recent commits: {e}")
            return []
    
    def find_schema_changes(self, since_hours: int = 24) -> List[Dict[str, Any]]:
        """
        Find commits that modified database schema files
        
        Args:
            since_hours: Look back this many hours
            
        Returns:
            List of commits with schema changes
        """
        # Common patterns for database-related files
        db_patterns = [
            '*.sql',
            '*migration*',
            '*schema*',
            'models.py',
            'models/*.py',
            'alembic/*',
            'migrations/*'
        ]
        
        return self.get_recent_commits(
            since_hours=since_hours,
            file_patterns=db_patterns
        )
    
    def correlate_error_with_commit(
        self, 
        error_timestamp: datetime,
        lookback_hours: int = 48
    ) -> Optional[Dict[str, Any]]:
        """
        Find the most likely commit that caused an error
        
        Args:
            error_timestamp: When the error occurred
            lookback_hours: How far back to search for commits
            
        Returns:
            Most recent commit before the error, or None
        """
        if not self.is_available():
            return None
        
        try:
            # Get commits before the error
            commits = []
            for commit in self.repo.iter_commits(max_count=100):
                commit_date = datetime.fromtimestamp(commit.committed_date)
                
                # Only consider commits before the error
                if commit_date > error_timestamp:
                    continue
                
                # Don't look too far back
                if (error_timestamp - commit_date).total_seconds() > lookback_hours * 3600:
                    break
                
                commits.append({
                    "hash": commit.hexsha,
                    "short_hash": commit.hexsha[:7],
                    "author": str(commit.author),
                    "message": commit.message.strip(),
                    "timestamp": commit_date,
                    "time_before_error": (error_timestamp - commit_date).total_seconds() / 60,  # minutes
                    "files_changed": list(commit.stats.files.keys())
                })
            
            # Return the most recent commit before the error
            if commits:
                return commits[0]
            
            return None
        except Exception as e:
            print(f"❌ Failed to correlate error with commit: {e}")
            return None
    
    def get_commit_diff(
        self, 
        commit_hash: str,
        file_path: Optional[str] = None
    ) -> Optional[str]:
        """
        Get the diff for a specific commit
        
        Args:
            commit_hash: Commit hash to get diff for
            file_path: Optional specific file to get diff for
            
        Returns:
            Diff text or None
        """
        if not self.is_available():
            return None
        
        try:
            commit = self.repo.commit(commit_hash)
            
            if commit.parents:
                parent = commit.parents[0]
                if file_path:
                    diff = parent.diff(commit, paths=file_path, create_patch=True)
                else:
                    diff = parent.diff(commit, create_patch=True)
                
                return '\n'.join([str(d) for d in diff])
            else:
                # First commit, no parent
                return f"Initial commit: {commit.message}"
        except Exception as e:
            print(f"❌ Failed to get commit diff: {e}")
            return None
    
    def get_file_history(
        self, 
        file_path: str,
        max_commits: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get commit history for a specific file
        
        Args:
            file_path: Path to file
            max_commits: Maximum number of commits to return
            
        Returns:
            List of commits that modified the file
        """
        if not self.is_available():
            return []
        
        try:
            commits = []
            for commit in self.repo.iter_commits(paths=file_path, max_count=max_commits):
                commits.append({
                    "hash": commit.hexsha,
                    "short_hash": commit.hexsha[:7],
                    "author": str(commit.author),
                    "message": commit.message.strip(),
                    "timestamp": datetime.fromtimestamp(commit.committed_date)
                })
            
            return commits
        except Exception as e:
            print(f"❌ Failed to get file history: {e}")
            return []
    
    def detect_migration_in_commit(self, commit_hash: str) -> Dict[str, Any]:
        """
        Detect if a commit contains database migrations
        
        Args:
            commit_hash: Commit to analyze
            
        Returns:
            Dict with migration detection results
        """
        if not self.is_available():
            return {"has_migration": False}
        
        try:
            commit = self.repo.commit(commit_hash)
            changed_files = list(commit.stats.files.keys())
            
            # Detect migration files
            migration_files = []
            schema_changes = []
            
            for file in changed_files:
                file_lower = file.lower()
                if any(pattern in file_lower for pattern in ['migration', 'alembic', 'schema']):
                    migration_files.append(file)
                if file.endswith('.sql'):
                    schema_changes.append(file)
            
            return {
                "has_migration": len(migration_files) > 0 or len(schema_changes) > 0,
                "migration_files": migration_files,
                "schema_files": schema_changes,
                "total_files_changed": len(changed_files)
            }
        except Exception as e:
            print(f"❌ Failed to detect migration: {e}")
            return {"has_migration": False, "error": str(e)}


# Global instance
_git_tracker = None

def get_git_tracker(repo_path: str = ".") -> GitTracker:
    """Get or create global GitTracker instance"""
    global _git_tracker
    if _git_tracker is None:
        _git_tracker = GitTracker(repo_path)
    return _git_tracker
