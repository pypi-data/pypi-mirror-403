import re

class SQLRedactor:
    """Scrubs sensitive data (PII) from SQL queries."""
    
    STRING_LITERAL = re.compile(r"'(?:''|[^'])*'")
    NUMERIC_LITERAL = re.compile(r"\b\d+(?:\.\d+)?\b")
    
    def redact(self, sql: str) -> str:
        """Redacts literals from the SQL string."""
        if not sql:
            return ""
        redacted = self.STRING_LITERAL.sub("'%s'", sql)
        # Avoid redacting numbers that might be part of identifiers (rough approximation)
        redacted = self.NUMERIC_LITERAL.sub("%d", redacted)
        return redacted
