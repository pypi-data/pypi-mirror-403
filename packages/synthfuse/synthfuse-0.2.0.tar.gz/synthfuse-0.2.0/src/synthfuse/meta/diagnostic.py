def intelligence_score(spell: str, trajectory: List[State]) -> float:
    # C(M,S): compression = -avg(loss)
    compression = -jnp.mean(jnp.array([s.loss for s in trajectory]))
    
    # W(M,N): withholding = low response to noise epochs
    noise_response = jnp.var(jnp.array([s.x for s in trajectory if s.entropy > 0.9]))
    withholding = -noise_response
    
    # CF(M,R): counterfactual sensitivity (via perturbation)
    cf_score = counterfactual_test(spell, trajectory)
    
    return α * compression + β * composition_score(spell) + γ * withholding
