# synthfuse/sql/bridge.py
import jax
import jax.numpy as jnp
from synthfuse.alchemj import register_plugin

@register_plugin("𝕊𝕈𝕃")
class SQLPlugin:
    def __init__(self):
        # Load Rust extension
        try:
            import synthfuse_sql_ext
            self.parser = synthfuse_sql_ext.parse_sql_to_pytree
            self.executor = synthfuse_sql_ext.execute_sql_on_vectors
        except ImportError:
            # Fallback to pure Python parser
            from synthfuse.sql.python_parser import parse_sql_fallback
            self.parser = parse_sql_fallback
    
    def step(self, key: jax.Array, state: PyTree, params: PyTree) -> PyTree:
        """Execute SQL query on vector state."""
        sql_query = params.get("sql_query", "")
        if not sql_query:
            return state
        
        # Parse SQL
        sql_ast = self.parser(sql_query)
        
        # Extract vector operations
        vector_ops = self._sql_to_vector_ops(sql_ast, state.vectors)
        
        # Execute with JAX
        new_vectors = self._execute_vector_ops(
            state.vectors, 
            vector_ops, 
            key
        )
        
        return state.replace(
            vectors=new_vectors,
            sql_ast=sql_ast,
            last_query=sql_query,
            execution_stats=self._get_execution_stats()
        )
