# meta/sql_constitution.py
from synthfuse.meta.constitution import Constitution

class SQLConstitution(Constitution):
    """
    Extended constitution for SQL-driven operations.
    """
    
    def validate_sql_query(self, sql_query: str, complexity_threshold: float = 0.8) -> bool:
        """Validate SQL query against constitutional constraints."""
        
        # Check query complexity
        complexity = self.calculate_sql_complexity(sql_query)
        if complexity > complexity_threshold:
            self.logger.warning(
                "SQL query too complex",
                complexity=complexity,
                threshold=complexity_threshold,
                query=sql_query[:100]
            )
            return False
        
        # Check for dangerous operations
        if self.contains_dangerous_operations(sql_query):
            self.logger.error("SQL query contains dangerous operations")
            return False
            
        # Check vector operation safety
        if not self.validate_vector_operations(sql_query):
            self.logger.error("SQL query has unsafe vector operations")
            return False
        
        return True
    
    def contains_dangerous_operations(self, sql: str) -> bool:
        """Check for SQL injection or dangerous patterns."""
        dangerous_patterns = [
            "DROP", "DELETE", "UPDATE", "INSERT",
            "EXEC", "SCRIPT", "ALTER", "CREATE"
        ]
        return any(pattern in sql.upper() for pattern in dangerous_patterns)
