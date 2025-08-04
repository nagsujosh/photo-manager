"""
Configuration management for the Photo Manager.
Centralizes all configuration settings with environment variable support.
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration class with environment variable support and validation."""
    
    # Database Configuration
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL"
    )
    
    # OCR Configuration
    TESSERACT_CMD: str = os.getenv("TESSERACT_CMD")
    
    # AI Model Configuration
    CAPTION_MODEL_NAME: str = os.getenv("CAPTION_MODEL_NAME")
    CAPTION_MODEL_REVISION: str = os.getenv("CAPTION_MODEL_REVISION")
    EMBEDDING_MODEL_NAME: str = os.getenv("EMBEDDING_MODEL_NAME")
    
    # Search Configuration
    SIMILARITY_THRESHOLD: float = float(os.getenv("SIMILARITY_THRESHOLD"))
    
    # Processing Configuration
    AI_WEIGHT: float = float(os.getenv("AI_WEIGHT"))
    MANUAL_WEIGHT: float = float(os.getenv("MANUAL_WEIGHT"))
    OCR_WEIGHT: float = float(os.getenv("OCR_WEIGHT"))
    
    # Image Processing Configuration
    THUMBNAIL_SIZE: tuple = (256, 256)
    MAX_IMAGE_SIZE: int = int(os.getenv("MAX_IMAGE_SIZE"))  # 10MB
    SUPPORTED_FORMATS: set = {".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp", ".webp"}
    
    # Performance Configuration
    BATCH_SIZE: int = int(os.getenv("BATCH_SIZE"))
    MAX_CONCURRENT_UPLOADS: int = int(os.getenv("MAX_CONCURRENT_UPLOADS"))
    
    # UI Configuration
    PAGE_TITLE: str = "Photo Manager"
    PAGE_ICON: str = "📷"
    LAYOUT: str = "wide"
    
    @classmethod
    def validate(cls) -> bool:
        """Validate configuration settings."""
        errors = []
        
        # Check database URL
        if not cls.DATABASE_URL or cls.DATABASE_URL == "postgresql://...":
            errors.append("DATABASE_URL is not properly configured")
        
        # Check Tesseract path
        if not Path(cls.TESSERACT_CMD).exists():
            errors.append(f"Tesseract not found at: {cls.TESSERACT_CMD}")
        
        # Check weights sum to reasonable value
        total_weight = cls.AI_WEIGHT + cls.MANUAL_WEIGHT + cls.OCR_WEIGHT
        if abs(total_weight - 1.0) > 0.1:
            errors.append(f"Similarity weights don't sum to 1.0 (current: {total_weight})")
        
        # Check similarity threshold
        if not 0.0 <= cls.SIMILARITY_THRESHOLD <= 1.0:
            errors.append("SIMILARITY_THRESHOLD must be between 0.0 and 1.0")
        
        if errors:
            print("Configuration validation errors:")
            for error in errors:
                print(f"   - {error}")
            return False
        
        return True
    
    @classmethod
    def get_model_cache_dir(cls) -> Path:
        """Get directory for caching AI models."""
        cache_dir = Path.home() / ".cache" / "semantic_gallery"
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir
    
    @classmethod
    def get_upload_temp_dir(cls) -> Path:
        """Get directory for temporary upload processing."""
        temp_dir = Path.cwd() / "temp" / "uploads"
        temp_dir.mkdir(parents=True, exist_ok=True)
        return temp_dir

# Global configuration instance
config = Config() 