# notebook/sql_widgets.py
def sql_query_explorer():
    """Interactive SQL query builder for notebooks."""
    
    @interact(
        query=Textarea(
            value="SELECT * FROM embeddings WHERE similarity > 0.8 ORDER BY distance LIMIT 10",
            description="SQL Query:",
            layout={'width': '800px', 'height': '100px'}
        ),
        beta=FloatSlider(min=0.1, max=2.0, step=0.1, value=0.8),
        sigma=FloatSlider(min=0.1, max=3.0, step=0.1, value=1.2),
        auto_optimize=Checkbox(value=True, description="Auto-optimize SQL")
    )
    def run_sql_query(query, beta, sigma, auto_optimize):
        # Construct spell
        spell = f"(𝕊𝕈𝕃 ⊗ ℤ𝕊𝕍ℝ ⊗ 𝔾ℝ𝔽)(query='{query}', beta={beta}, sigma={sigma})"
        
        if auto_optimize:
            # Let meta-alchemist optimize SQL parameters
            from synthfuse.meta import ZetaAlchemist
            alchemist = ZetaAlchemist()
            
            # Parse SQL complexity
            complexity = alchemist.analyze_sql_complexity(query)
            if complexity > 0.7:
                # Suggest parameter adjustments
                beta_opt = alchemist.optimize_beta_for_complexity(complexity, beta)
                print(f"🧙 Alchemist suggests: beta={beta_opt} (was {beta})")
        
        # Execute spell
        cell, state = run_spell_cell(spell, steps=100, auto_repair=True)
        
        # Display results
        print(f"✨ Executed: {len(state.results)} results")
        print(f"📊 Query complexity: {complexity:.2f}")
        print(f"🔧 Repairs applied: {cell.repair_count}")
        
        return cell, state
