from synthfuse.tools import (
    cosine_similarity, 
    euclidean_distance,
    softmax_temperature,
    entropy,
    clip_gradients
)

# Vectorized pairwise distances
distances = euclidean_distance(population, target_point)  # Shape: (pop_size,)

# Temperature-scaled softmax
probs = softmax_temperature(logits, temperature=0.5)

# Shannon entropy for diversity metrics
pop_entropy = entropy(probs)
