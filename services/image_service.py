"""
Image service for handling image upload, processing, and management.
"""

import io
import json
from typing import List, Dict, Any, Optional
from PIL import Image, UnidentifiedImageError
from datetime import datetime
import streamlit as st
import uuid

from core.config import config
from database.repository import image_repository, ImageRepository
from database.models import ImageEntry
from .ai_service import AIService
from core.utils import validate_image_format, format_file_size, extract_exif_data, create_thumbnail, validate_image_file

class ImageService:
    """Service for managing image operations."""
    
    def __init__(self):
        self.repository = ImageRepository()
        self.ai_service = AIService()
    
    def validate_upload(self, file_name: str, file_size: int, file_bytes: bytes) -> tuple[bool, str]:
        """Validate uploaded file."""
        # Check file format
        if not validate_image_format(file_name):
            return False, f"Unsupported file format. Supported: {', '.join(config.SUPPORTED_FORMATS)}"
        
        # Check file size
        if file_size > config.MAX_IMAGE_SIZE:
            max_size_str = format_file_size(config.MAX_IMAGE_SIZE)
            actual_size_str = format_file_size(file_size)
            return False, f"File too large ({actual_size_str}). Maximum size: {max_size_str}"
        
        # Try to open image
        try:
            Image.open(io.BytesIO(file_bytes))
        except UnidentifiedImageError:
            return False, "Invalid image file or corrupted data"
        except Exception as e:
            return False, f"Error validating image: {str(e)}"
        
        return True, "Valid"
    
    def process_single_image(self, file_name: str, file_size: int, 
                           image_bytes: bytes, manual_labels: List[str]) -> Dict[str, Any]:
        """Process a single image with AI analysis."""
        try:
            # Open image
            image = Image.open(io.BytesIO(image_bytes))
            
            # Process with AI
            ai_results = self.ai_service.process_image(image)
            
            # Generate manual embedding if manual labels exist
            manual_text = ", ".join(manual_labels) if manual_labels else ""
            manual_embedding = self.ai_service.generate_embedding(manual_text) if manual_text else [0] * 384
            
            # Prepare data for database
            image_data = {
                'file_name': file_name,
                'file_size': file_size,
                'manual_labels': manual_labels,
                'ai_labels': ai_results.get('ai_labels', []),
                'short_caption': ai_results.get('short_caption', ''),
                'detailed_caption': ai_results.get('detailed_caption', ''),
                'ocr_text': ai_results.get('ocr_text', ''),
                'width': ai_results.get('width'),
                'height': ai_results.get('height'),
                'format': ai_results.get('format'),
                'mode': ai_results.get('mode'),
                'exif_metadata': ai_results.get('exif_metadata', {}),
                'camera_make': ai_results.get('make', ''),
                'camera_model': ai_results.get('model', ''),
                'date_taken': ai_results.get('date_taken'),
                'iso_speed': ai_results.get('iso_speed'),
                'aperture': ai_results.get('aperture'),
                'shutter_speed': ai_results.get('shutter_speed'),
                'focal_length': ai_results.get('focal_length'),
                'gps_latitude': ai_results.get('gps_latitude'),
                'gps_longitude': ai_results.get('gps_longitude'),
                'ai_embedding': json.dumps(ai_results.get('ai_embedding', [])),
                'manual_embedding': json.dumps(manual_embedding),
                'ocr_embedding': json.dumps(ai_results.get('ocr_embedding', [])),
                'combined_embedding': json.dumps(ai_results.get('combined_embedding', [])),
                'image_data': image_bytes,
                'thumbnail_data': ai_results.get('thumbnail_data', b'')
            }
            
            return {
                'success': True,
                'data': image_data,
                'message': f"Successfully processed {file_name}"
            }
            
        except Exception as e:
            return {
                'success': False,
                'data': None,
                'message': f"Error processing {file_name}: {str(e)}"
            }
    
    def upload_images(self, uploaded_files: List[Dict], manual_labels: List[str]) -> Dict[str, Any]:
        """Upload and process multiple images."""
        results = {
            'successful': [],
            'failed': [],
            'total': len(uploaded_files),
            'success_count': 0,
            'error_count': 0
        }
        
        for file_info in uploaded_files:
            file_name = file_info['name']
            file_size = file_info['size']
            file_bytes = file_info['bytes']
            
            # Validate file
            is_valid, validation_message = self.validate_upload(file_name, file_size, file_bytes)
            if not is_valid:
                results['failed'].append({
                    'file_name': file_name,
                    'error': validation_message
                })
                results['error_count'] += 1
                continue
            
            # Process image
            process_result = self.process_single_image(file_name, file_size, file_bytes, manual_labels)
            
            if process_result['success']:
                # Save to database
                entry = image_repository.create(process_result['data'])
                if entry:
                    results['successful'].append({
                        'file_name': file_name,
                        'id': entry.id,
                        'message': process_result['message']
                    })
                    results['success_count'] += 1
                else:
                    results['failed'].append({
                        'file_name': file_name,
                        'error': 'Failed to save to database'
                    })
                    results['error_count'] += 1
            else:
                results['failed'].append({
                    'file_name': file_name,
                    'error': process_result['message']
                })
                results['error_count'] += 1
        
        return results
    
    @st.cache_data(ttl=60)  # Cache for 1 minute
    def get_all_images(_self, limit: Optional[int] = None, offset: int = 0) -> List[ImageEntry]:
        """Get all images with pagination."""
        return _self.repository.get_all(limit=limit, offset=offset)
    
    def get_image_by_id(self, image_id: int) -> Optional[ImageEntry]:
        """Get a specific image by ID."""
        return image_repository.get_by_id(image_id)
    
    def delete_image(self, image_id: int) -> bool:
        """Delete an image."""
        return image_repository.delete(image_id)
    
    def update_image_labels(self, image_id: int, manual_labels: List[str]) -> bool:
        """Update manual labels for an image."""
        # Generate new manual embedding
        manual_text = ", ".join(manual_labels) if manual_labels else ""
        manual_embedding = self.ai_service.generate_embedding(manual_text) if manual_text else [0] * 384
        
        updates = {
            'manual_labels': manual_labels,
            'manual_embedding': json.dumps(manual_embedding)
        }
        
        return image_repository.update(image_id, updates)
    
    @st.cache_data(ttl=60)  # Cache for 1 minute
    def get_image_statistics(_self) -> Dict[str, Any]:
        """Get image collection statistics."""
        return _self.repository.get_statistics()
    
    @st.cache_data(ttl=300)  # Cache for 5 minutes
    def get_recent_uploads(_self, days: int = 7) -> List[ImageEntry]:
        """Get recently uploaded images."""
        return _self.repository.get_recent_uploads(days)

# Global service instance
image_service = ImageService() 