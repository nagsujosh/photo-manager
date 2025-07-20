"""
Database models for the Photo Manager.
"""

from sqlalchemy import Column, String, Integer, JSON, LargeBinary, DateTime, Float, Text, Index
from sqlalchemy.sql import func
from .connection import Base

class ImageEntry(Base):
    """
    Database model for storing images with comprehensive metadata.
    """
    __tablename__ = "image_information"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Basic file information
    file_name = Column(String, nullable=False, index=True)
    file_size = Column(Integer, nullable=True)
    upload_date = Column(DateTime, default=func.now(), index=True)
    
    # Labels and descriptions
    manual_labels = Column(JSON, nullable=True)  # User provided labels
    ai_labels = Column(JSON, nullable=True)  # AI generated keywords/labels
    short_caption = Column(Text, nullable=True)  # Short AI caption
    detailed_caption = Column(Text, nullable=True)  # Detailed AI caption
    ocr_text = Column(Text, nullable=True)  # Extracted text from image
    
    # Image properties
    width = Column(Integer, nullable=True, index=True)
    height = Column(Integer, nullable=True, index=True)
    format = Column(String, nullable=True, index=True)  # JPEG, PNG, etc.
    mode = Column(String, nullable=True)  # RGB, RGBA, etc.
    
    # EXIF and camera metadata
    exif_metadata = Column(JSON, nullable=True)  # Complete EXIF data
    camera_make = Column(String, nullable=True, index=True)
    camera_model = Column(String, nullable=True, index=True)
    date_taken = Column(DateTime, nullable=True, index=True)
    iso_speed = Column(Integer, nullable=True, index=True)
    aperture = Column(Float, nullable=True, index=True)
    shutter_speed = Column(String, nullable=True)
    focal_length = Column(Float, nullable=True, index=True)
    gps_latitude = Column(Float, nullable=True, index=True)
    gps_longitude = Column(Float, nullable=True, index=True)
    
    # Embeddings for semantic search
    ai_embedding = Column(JSON, nullable=True)  # AI content embedding
    manual_embedding = Column(JSON, nullable=True)  # Manual labels embedding
    ocr_embedding = Column(JSON, nullable=True)  # OCR text embedding
    combined_embedding = Column(JSON, nullable=True)  # Combined metadata embedding
    
    # Binary data
    image_data = Column(LargeBinary, nullable=False)  # Original image data
    thumbnail_data = Column(LargeBinary, nullable=True)  # Thumbnail for faster loading
    
    # Create composite indexes for common queries
    __table_args__ = (
        Index('idx_camera_info', 'camera_make', 'camera_model'),
        Index('idx_date_range', 'date_taken', 'upload_date'),
        Index('idx_dimensions', 'width', 'height'),
        Index('idx_camera_settings', 'iso_speed', 'aperture', 'focal_length'),
    )
    
    def __repr__(self):
        # Basic info
        parts = [f"id={self.id}", f"file='{self.file_name}'"]
        
        # Add dimensions if available
        if self.width and self.height:
            parts.append(f"{self.width}x{self.height}")
        
        # Add format if available
        if self.format:
            parts.append(f"format={self.format}")
        
        # Add camera info if available
        if self.camera_make or self.camera_model:
            camera = f"{self.camera_make or 'Unknown'} {self.camera_model or ''}".strip()
            parts.append(f"camera='{camera}'")
        
        # Add processing status
        processing_status = []
        if self.ai_labels:
            processing_status.append("AI")
        if self.manual_labels:
            processing_status.append("Manual")
        if self.ocr_text:
            processing_status.append("OCR")
        if processing_status:
            parts.append(f"processed=[{', '.join(processing_status)}]")
        
        # Add GPS indicator
        if self.has_gps:
            parts.append("GPS")
        
        return f"<ImageEntry({', '.join(parts)})>"
    
    @property
    def megapixels(self) -> float:
        """Calculate megapixels from width and height."""
        if self.width and self.height:
            return (self.width * self.height) / 1_000_000
        return 0.0
    
    @property
    def aspect_ratio(self) -> str:
        """Calculate aspect ratio string."""
        if not self.width or not self.height:
            return "Unknown"
        
        def gcd(a, b):
            while b:
                a, b = b, a % b
            return a
        
        common_divisor = gcd(self.width, self.height)
        ratio_w = self.width // common_divisor
        ratio_h = self.height // common_divisor
        
        # Check for common ratios
        ratio_value = self.width / self.height
        if abs(ratio_value - 16/9) < 0.1:
            return "16:9"
        elif abs(ratio_value - 4/3) < 0.1:
            return "4:3"
        elif abs(ratio_value - 3/2) < 0.1:
            return "3:2"
        elif abs(ratio_value - 1) < 0.1:
            return "1:1 (Square)"
        else:
            return f"{ratio_w}:{ratio_h}"
    
    @property
    def has_gps(self) -> bool:
        """Check if image has GPS coordinates."""
        return bool(self.gps_latitude and self.gps_longitude)
    
    @property
    def has_ocr_text(self) -> bool:
        """Check if image has OCR text."""
        return bool(self.ocr_text and self.ocr_text.strip()) 