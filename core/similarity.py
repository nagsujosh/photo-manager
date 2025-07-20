"""
Similarity calculation utilities.
"""

import numpy as np

def cosine_similarity(vec1, vec2):
    """
    Calculate cosine similarity between two vectors.
    
    Args:
        vec1: First vector (numpy array)
        vec2: Second vector (numpy array)
        
    Returns:
        float: Cosine similarity score between 0 and 1
    """
    # Ensure inputs are numpy arrays
    if not isinstance(vec1, np.ndarray):
        vec1 = np.array(vec1)
    if not isinstance(vec2, np.ndarray):
        vec2 = np.array(vec2)
        
    # Calculate dot product and magnitudes
    dot_product = np.dot(vec1, vec2)
    norm_vec1 = np.linalg.norm(vec1)
    norm_vec2 = np.linalg.norm(vec2)
    
    # Avoid division by zero
    if norm_vec1 == 0 or norm_vec2 == 0:
        return 0.0
        
    # Return cosine similarity
    return dot_product / (norm_vec1 * norm_vec2) 