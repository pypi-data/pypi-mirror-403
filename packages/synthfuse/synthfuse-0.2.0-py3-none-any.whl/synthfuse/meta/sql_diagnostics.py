# meta/sql_diagnostics.py
from synthfuse.meta.diagnostics import DiagnosticExtractor

class SQLDiagnosticExtractor(DiagnosticExtractor):
    """
    Extract SQL-specific metrics for meta-alchemist.
    """
    
    def extract_sql_metrics(self, sql_ast: SQLAST, execution_time: float, result_count: int) -> dict:
        """Extract SQL query complexity metrics."""
        
        return {
            "sql_complexity": self._calculate_complexity(sql_ast),
            "execution_time": execution_time,
            "result_count": result_count,
            "query_selectivity": self._calculate_selectivity(sql_ast),
            "join_complexity": self._calculate_join_complexity(sql_ast),
            "where_clause_depth": self._calculate_where_depth(sql_ast),
            "order_by_columns": len(sql_ast.order_by) if sql_ast.order_by else 0,
        }
    
    def _calculate_complexity(self, ast: SQLAST) -> float:
        """Calculate query complexity score (0-1)."""
        complexity = 0.0
        
        # WHERE clause complexity
        if ast.where:
            complexity += 0.3 * self._where_complexity(ast.where)
        
        # JOIN complexity  
        if ast.joins:
            complexity += 0.4 * len(ast.joins) / 10.0
            
        # ORDER BY complexity
        if ast.order_by:
            complexity += 0.2 * len(ast.order_by) / 5.0
            
        # LIMIT complexity (inverse - smaller limits = higher complexity)
        if ast.limit:
            complexity += 0.1 * (1.0 - ast.limit.value / 1000.0)
            
        return min(complexity, 1.0)
