"""
Repository pattern for database operations.
Provides a clean interface for data access with error handling.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy import and_, or_, func
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from .connection import get_db_session
from .models import ImageEntry

class ImageRepository:
    """Repository for image database operations."""
    
    def create(self, image_data: Dict[str, Any]) -> Optional[ImageEntry]:
        """Create a new image entry."""
        try:
            with get_db_session() as session:
                entry = ImageEntry(**image_data)
                session.add(entry)
                session.flush()  # Get the ID
                # Expunge the object to detach it from the session
                session.expunge(entry)
                return entry
        except Exception as e:
            print(f"Error creating image entry: {e}")
            return None
    
    def get_by_id(self, image_id: int) -> Optional[ImageEntry]:
        """Get image by ID."""
        try:
            with get_db_session() as session:
                entry = session.query(ImageEntry).filter(ImageEntry.id == image_id).first()
                if entry:
                    # Expunge the object to detach it from the session
                    session.expunge(entry)
                return entry
        except Exception as e:
            print(f"Error getting image by ID: {e}")
            return None
    
    def get_all(self, limit: Optional[int] = None, offset: int = 0) -> List[ImageEntry]:
        """Get all images with optional pagination."""
        try:
            with get_db_session() as session:
                query = session.query(ImageEntry).order_by(ImageEntry.upload_date.desc())
                if limit:
                    query = query.offset(offset).limit(limit)
                entries = query.all()
                # Expunge all objects to detach them from the session
                session.expunge_all()
                return entries
        except Exception as e:
            print(f"Error getting all images: {e}")
            return []
    
    def search_by_filters(self, filters: Dict[str, Any]) -> List[ImageEntry]:
        """Search images using advanced filters."""
        try:
            with get_db_session() as session:
                query = session.query(ImageEntry)
                
                # Apply filters
                if filters.get('date_from'):
                    query = query.filter(ImageEntry.date_taken >= filters['date_from'])
                
                if filters.get('date_to'):
                    query = query.filter(ImageEntry.date_taken <= filters['date_to'])
                
                if filters.get('camera_make'):
                    query = query.filter(ImageEntry.camera_make.ilike(f"%{filters['camera_make']}%"))
                
                if filters.get('camera_model'):
                    query = query.filter(ImageEntry.camera_model.ilike(f"%{filters['camera_model']}%"))
                
                if filters.get('iso_min'):
                    query = query.filter(ImageEntry.iso_speed >= filters['iso_min'])
                
                if filters.get('iso_max'):
                    query = query.filter(ImageEntry.iso_speed <= filters['iso_max'])
                
                if filters.get('aperture_min'):
                    query = query.filter(ImageEntry.aperture >= filters['aperture_min'])
                
                if filters.get('aperture_max'):
                    query = query.filter(ImageEntry.aperture <= filters['aperture_max'])
                
                if filters.get('width_min'):
                    query = query.filter(ImageEntry.width >= filters['width_min'])
                
                if filters.get('height_min'):
                    query = query.filter(ImageEntry.height >= filters['height_min'])
                
                if filters.get('format'):
                    query = query.filter(ImageEntry.format == filters['format'])
                
                if filters.get('manual_labels'):
                    for label in filters['manual_labels']:
                        query = query.filter(ImageEntry.manual_labels.contains([label]))
                
                entries = query.all()
                # Expunge all objects to detach them from the session
                session.expunge_all()
                return entries
                
        except Exception as e:
            print(f"Error searching images: {e}")
            return []
    
    def update(self, image_id: int, updates: Dict[str, Any]) -> bool:
        """Update an image entry."""
        try:
            with get_db_session() as session:
                entry = session.query(ImageEntry).filter(ImageEntry.id == image_id).first()
                if entry:
                    for key, value in updates.items():
                        if hasattr(entry, key):
                            setattr(entry, key, value)
                    return True
                return False
        except Exception as e:
            print(f"Error updating image: {e}")
            return False
    
    def delete(self, image_id: int) -> bool:
        """Delete an image entry."""
        try:
            with get_db_session() as session:
                entry = session.query(ImageEntry).filter(ImageEntry.id == image_id).first()
                if entry:
                    session.delete(entry)
                    return True
                return False
        except Exception as e:
            print(f"Error deleting image: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics."""
        try:
            with get_db_session() as session:
                total_images = session.query(func.count(ImageEntry.id)).scalar()
                total_size = session.query(func.sum(ImageEntry.file_size)).scalar() or 0
                
                # Format distribution
                format_stats = session.query(
                    ImageEntry.format, 
                    func.count(ImageEntry.id)
                ).group_by(ImageEntry.format).all()
                
                # Camera distribution
                camera_stats = session.query(
                    func.concat(ImageEntry.camera_make, ' ', ImageEntry.camera_model),
                    func.count(ImageEntry.id)
                ).filter(
                    and_(ImageEntry.camera_make.isnot(None), ImageEntry.camera_model.isnot(None))
                ).group_by(ImageEntry.camera_make, ImageEntry.camera_model).all()
                
                # Images with GPS
                gps_count = session.query(func.count(ImageEntry.id)).filter(
                    and_(ImageEntry.gps_latitude.isnot(None), ImageEntry.gps_longitude.isnot(None))
                ).scalar()
                
                # Images with OCR text
                ocr_count = session.query(func.count(ImageEntry.id)).filter(
                    and_(ImageEntry.ocr_text.isnot(None), ImageEntry.ocr_text != '')
                ).scalar()
                
                return {
                    'total_images': total_images,
                    'total_size': total_size,
                    'format_distribution': dict(format_stats),
                    'camera_distribution': dict(camera_stats),
                    'images_with_gps': gps_count,
                    'images_with_ocr': ocr_count
                }
                
        except Exception as e:
            print(f"Error getting statistics: {e}")
            return {}
    
    def get_recent_uploads(self, days: int = 7) -> List[ImageEntry]:
        """Get recently uploaded images."""
        try:
            with get_db_session() as session:
                cutoff_date = datetime.now() - timedelta(days=days)
                entries = session.query(ImageEntry).filter(
                    ImageEntry.upload_date >= cutoff_date
                ).order_by(ImageEntry.upload_date.desc()).all()
                # Expunge all objects to detach them from the session
                session.expunge_all()
                return entries
        except Exception as e:
            print(f"Error getting recent uploads: {e}")
            return []

# Global repository instance
image_repository = ImageRepository() 