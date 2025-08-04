"""
Search service for handling semantic search and advanced filtering.
"""

import json
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime

from core.config import config
from database.repository import image_repository
from database.models import ImageEntry
from core.similarity import cosine_similarity
from .ai_service import AIService

class SearchService:
    """Service for searching and filtering images."""
    
    def __init__(self):
        self.ai_service = AIService()
    
    def build_filters_from_params(self, search_params: Dict[str, Any]) -> Dict[str, Any]:
        """Build database filters from search parameters."""
        filters = {}
        
        # Date range filters
        if search_params.get('date_from'):
            filters['date_from'] = datetime.combine(search_params['date_from'], datetime.min.time())
        if search_params.get('date_to'):
            filters['date_to'] = datetime.combine(search_params['date_to'], datetime.max.time())
        
        # Camera filters
        if search_params.get('camera_make'):
            filters['camera_make'] = search_params['camera_make']
        if search_params.get('camera_model'):
            filters['camera_model'] = search_params['camera_model']
        
        # Technical filters
        if search_params.get('iso_min', 50) > 50:
            filters['iso_min'] = search_params['iso_min']
        if search_params.get('iso_max', 6400) < 6400:
            filters['iso_max'] = search_params['iso_max']
        
        if search_params.get('aperture_min', 1.0) > 1.0:
            filters['aperture_min'] = search_params['aperture_min']
        if search_params.get('aperture_max', 22.0) < 22.0:
            filters['aperture_max'] = search_params['aperture_max']
        
        # Dimension filters
        if search_params.get('width_min', 1) > 1:
            filters['width_min'] = search_params['width_min']
        if search_params.get('height_min', 1) > 1:
            filters['height_min'] = search_params['height_min']
        
        # Format filter
        if search_params.get('format'):
            filters['format'] = search_params['format']
        
        # Manual labels filter
        if search_params.get('manual_labels'):
            labels = [label.strip() for label in search_params['manual_labels'].split(",") if label.strip()]
            if labels:
                filters['manual_labels'] = labels
        
        return filters
    
    def calculate_similarity_scores(self, query_embedding: np.ndarray, 
                                  entries: List[ImageEntry]) -> List[Tuple[float, ImageEntry]]:
        """Calculate similarity scores for a list of entries."""
        results_with_scores = []
        
        for entry in entries:
            try:
                # Get embeddings
                ai_emb = np.array(json.loads(entry.ai_embedding or '[]'))
                manual_emb = np.array(json.loads(entry.manual_embedding or '[]'))
                ocr_emb = np.array(json.loads(entry.ocr_embedding or '[]'))
                
                # Calculate similarities
                sim_ai = cosine_similarity(query_embedding, ai_emb) if ai_emb.size > 0 else 0.0
                sim_manual = (cosine_similarity(query_embedding, manual_emb) 
                            if manual_emb.size > 0 and np.any(manual_emb) else 0.0)
                sim_ocr = cosine_similarity(query_embedding, ocr_emb) if ocr_emb.size > 0 else 0.0
                
                # Combined similarity score
                final_sim = (config.AI_WEIGHT * sim_ai + 
                           config.MANUAL_WEIGHT * sim_manual + 
                           config.OCR_WEIGHT * sim_ocr)
                
                results_with_scores.append((final_sim, entry))
                
            except Exception as e:
                print(f"Error calculating similarity for {entry.file_name}: {e}")
                results_with_scores.append((0.0, entry))
        
        # Sort by similarity score
        results_with_scores.sort(key=lambda x: x[0], reverse=True)
        return results_with_scores
    
    def semantic_search(self, query: str, filters: Optional[Dict[str, Any]] = None, 
                       limit: Optional[int] = None) -> List[Tuple[float, ImageEntry]]:
        """Perform semantic search with optional filters."""
        
        # Get filtered entries from database
        if filters:
            entries = image_repository.search_by_filters(filters)
        else:
            entries = image_repository.get_all()
        
        if not entries:
            return []
        
        if not query or not query.strip():
            # No query, return filtered results without scoring
            if limit:
                return [(0.0, entry) for entry in entries[:limit]]
            else:
                return [(0.0, entry) for entry in entries]
        
        # Generate query embedding
        try:
            query_embedding = np.array(self.ai_service.generate_embedding(query))
        except Exception as e:
            print(f"Error generating query embedding: {e}")
            return [(0.0, entry) for entry in entries]
        
        # Calculate similarities
        results_with_scores = self.calculate_similarity_scores(query_embedding, entries)
        
        # Apply limit if specified
        if limit:
            results_with_scores = results_with_scores[:limit]
        
        return results_with_scores
    
    def advanced_search(self, search_params: Dict[str, Any]) -> Dict[str, Any]:
        """Perform advanced search with comprehensive filtering."""
        
        query = search_params.get('query', '').strip()
        filters = self.build_filters_from_params(search_params)
        limit = search_params.get('limit', 100)
        threshold = search_params.get('threshold', config.SIMILARITY_THRESHOLD)
        
        # Perform search
        results = self.semantic_search(query, filters, limit)
        
        # Filter by threshold if query exists
        if query:
            relevant_results = [(score, entry) for score, entry in results if score >= threshold]
            below_threshold = [(score, entry) for score, entry in results if score < threshold]
            
            return {
                'relevant_results': relevant_results,
                'below_threshold_results': below_threshold[:10],  # Max 10 below threshold
                'total_found': len(results),
                'relevant_count': len(relevant_results),
                'query': query,
                'filters_applied': filters,
                'threshold_used': threshold
            }
        else:
            return {
                'relevant_results': results,
                'below_threshold_results': [],
                'total_found': len(results),
                'relevant_count': len(results),
                'query': None,
                'filters_applied': filters,
                'threshold_used': None
            }
    
    def get_similar_images(self, image_id: int, limit: int = 10) -> List[Tuple[float, ImageEntry]]:
        """Find images similar to a given image."""
        
        # Get the reference image
        reference_image = image_repository.get_by_id(image_id)
        if not reference_image:
            return []
        
        # Get reference embedding (use combined embedding)
        try:
            reference_embedding = np.array(json.loads(reference_image.combined_embedding or '[]'))
            if reference_embedding.size == 0:
                return []
        except Exception:
            return []
        
        # Get all other images
        all_images = image_repository.get_all()
        other_images = [img for img in all_images if img.id != image_id]
        
        # Calculate similarities
        results = self.calculate_similarity_scores(reference_embedding, other_images)
        
        # Return top similar images
        return results[:limit]
    
    def search_by_labels(self, labels: List[str], exact_match: bool = False) -> List[ImageEntry]:
        """Search images by labels."""
        
        if exact_match:
            # Use database filtering for exact matches
            filters = {'manual_labels': labels}
            return image_repository.search_by_filters(filters)
        else:
            # Use semantic search for fuzzy label matching
            query = " ".join(labels)
            results = self.semantic_search(query, limit=50)
            return [entry for score, entry in results if score >= 0.3]  # Lower threshold for labels
    
    def get_trending_searches(self, days: int = 30) -> Dict[str, Any]:
        """Get trending search patterns (placeholder for future implementation)."""
        # This could be implemented with search logging
        return {
            'trending_keywords': [],
            'popular_filters': {},
            'common_queries': []
        }

# Global service instance
search_service = SearchService() 