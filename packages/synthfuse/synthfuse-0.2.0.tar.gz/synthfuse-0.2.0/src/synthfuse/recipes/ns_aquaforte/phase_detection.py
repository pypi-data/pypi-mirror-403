"""LLM-based phase detection for SAT instances."""

import os
from anthropic import Anthropic

def detect_phase_llm(problem, model: str = "claude-sonnet-4"):
    """Use LLM to predict clause density phase."""
    
    n_vars = problem.nv
    n_clauses = len(problem.clauses)
    density = n_clauses / n_vars
    
    # Analyze clause structure
    clause_lengths = [len(clause) for clause in problem.clauses]
    avg_length = sum(clause_lengths) / len(clause_lengths)
    
    # Build prompt
    prompt = f"""Analyze this SAT instance and predict its clause density phase:

Variables: {n_vars}
Clauses: {n_clauses}
Clause/Variable Ratio (α): {density:.2f}
Average Clause Length: {avg_length:.2f}

Phase definitions:
- "low" (α < 4.0): Under-constrained, many solutions exist
- "critical" (4.0 ≤ α ≤ 4.5): Phase transition region, hardest to solve
- "high" (α > 4.5): Over-constrained, likely unsatisfiable

Respond with only a JSON object:
{{"phase": "low"|"critical"|"high", "confidence": 0.0-1.0}}"""

    # Call Claude API
    client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=100,
        messages=[{"role": "user", "content": prompt}]
    )
    
    # Parse response
    import json
    response_text = message.content[0].text
    result = json.loads(response_text)
    
    return result["phase"], result["confidence"]