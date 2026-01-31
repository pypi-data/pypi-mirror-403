import inspect
import os
import subprocess
from typing import Dict, Any

class ContextCollector:
    """Captures forensic data from the application environment."""
    
    def get_stack_trace(self, depth: int = 5) -> str:
        """Captures the current calling stack trace."""
        stack = inspect.stack()
        formatted_stack = []
        
        # Skip internal SDK frames
        # Usually offset by 3-4 depending on the call chain (wrapper -> interceptor -> guardian)
        for frame_info in stack[4:4+depth]:
            filename = os.path.basename(frame_info.filename)
            line = frame_info.lineno
            function = frame_info.function
            code_context = frame_info.code_context[0].strip() if frame_info.code_context else ""
            formatted_stack.append(f"  File \"{filename}\", line {line}, in {function}\n    {code_context}")
            
        return "\n".join(formatted_stack)

    def get_git_info(self) -> Dict[str, Any]:
        """Attempts to gather Git metadata."""
        try:
            short_hash = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'], stderr=subprocess.DEVNULL).decode('utf-8').strip()
            author = subprocess.check_output(['git', 'log', '-1', '--format=%an'], stderr=subprocess.DEVNULL).decode('utf-8').strip()
            return {"short_hash": short_hash, "author": author}
        except Exception:
            return {"error": "Git not available"}

    def collect_all(self) -> Dict[str, Any]:
        """Aggregates all context metadata."""
        return {
            "stack_trace": list(reversed(self.get_stack_trace().split("\n\n"))), # Reversed for better logic
            "git_info": self.get_git_info(),
            "pid": os.getpid()
        }
