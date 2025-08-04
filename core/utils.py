"""
Utility functions for the Photo Manager.
Enhanced with additional helper functions for metadata processing.
"""

import re
import io
import os
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from PIL import Image, ExifTags, UnidentifiedImageError
import json

def clean_text_string(text: str) -> str:
    """
    Cleans the given text string by:
    - Removing leading/trailing whitespace
    - Removing non-alphanumeric characters (except spaces and common punctuation)
    - Converting text to lowercase for consistency
    - Removing extra spaces
    """
    if not text:
        return ""
    
    text = text.strip()
    # Keep letters, numbers, spaces, and basic punctuation
    text = re.sub(r'[^\w\s\.\,\!\?\-\:\;]', '', text)
    text = text.lower()
    text = re.sub(r'\s+', ' ', text)
    
    return text

def extract_keywords(text: str, min_length: int = 3, max_keywords: int = 20) -> List[str]:
    """
    Extract meaningful keywords from text by filtering out common stop words
    """
    if not text:
        return []
    
    # Common stop words to filter out
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
        'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
        'will', 'would', 'could', 'should', 'this', 'that', 'these', 'those', 'there', 'here',
        'when', 'where', 'why', 'how', 'what', 'who', 'which', 'can', 'may', 'might', 'must',
        'shall', 'about', 'into', 'through', 'during', 'before', 'after', 'above', 'below',
        'up', 'down', 'out', 'off', 'over', 'under', 'again', 'further', 'then', 'once'
    }
    
    # Clean and split text
    cleaned_text = clean_text_string(text)
    words = cleaned_text.split()
    
    # Filter words
    keywords = []
    for word in words:
        word = word.strip('.,!?":;')
        if (len(word) >= min_length and 
            word not in stop_words and 
            not word.isdigit() and
            word not in keywords):
            keywords.append(word)
            
        if len(keywords) >= max_keywords:
            break
    
    return keywords

def format_file_size(size_bytes: int) -> str:
    """
    Convert bytes to human readable format
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    size = float(size_bytes)
    
    while size >= 1024.0 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1
    
    return f"{size:.1f} {size_names[i]}"

def format_camera_settings(iso: int = None, aperture: float = None, shutter_speed: str = None, focal_length: float = None) -> str:
    """
    Format camera settings into a readable string
    """
    settings = []
    
    if iso:
        settings.append(f"ISO {iso}")
    if aperture:
        settings.append(f"f/{aperture}")
    if shutter_speed:
        settings.append(f"{shutter_speed}s")
    if focal_length:
        settings.append(f"{focal_length}mm")
    
    return " • ".join(settings) if settings else "Unknown settings"

def safe_json_loads(json_str: str, default=None):
    """
    Safely load JSON string with fallback
    """
    try:
        return json.loads(json_str) if json_str else default
    except (json.JSONDecodeError, TypeError):
        return default

def create_search_summary(query: str, filters: Dict[str, Any], result_count: int) -> str:
    """
    Create a human-readable summary of search parameters and results
    """
    summary_parts = []
    
    if query:
        summary_parts.append(f"'{query}'")
    
    if filters:
        filter_parts = []
        
        if filters.get('date_from') or filters.get('date_to'):
            date_from = filters.get('date_from', '').strftime('%Y-%m-%d') if filters.get('date_from') else 'beginning'
            date_to = filters.get('date_to', '').strftime('%Y-%m-%d') if filters.get('date_to') else 'end'
            filter_parts.append(f"dates from {date_from} to {date_to}")
        
        if filters.get('camera_make'):
            filter_parts.append(f"camera make: {filters['camera_make']}")
        
        if filters.get('camera_model'):
            filter_parts.append(f"camera model: {filters['camera_model']}")
        
        if filters.get('iso_min') or filters.get('iso_max'):
            iso_min = filters.get('iso_min', 'any')
            iso_max = filters.get('iso_max', 'any')
            filter_parts.append(f"ISO {iso_min}-{iso_max}")
        
        if filters.get('format'):
            filter_parts.append(f"format: {filters['format']}")
        
        if filter_parts:
            summary_parts.append(f"filtered by {', '.join(filter_parts)}")
    
    search_desc = " and ".join(summary_parts) if summary_parts else "all images"
    return f"Found {result_count} results for {search_desc}"

def validate_image_format(file_name: str) -> bool:
    """
    Validate if file has a supported image format
    """
    supported_formats = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.webp'}
    file_extension = '.' + file_name.lower().split('.')[-1] if '.' in file_name else ''
    return file_extension in supported_formats

def calculate_image_aspect_ratio(width: int, height: int) -> str:
    """
    Calculate and format aspect ratio
    """
    if not width or not height:
        return "Unknown"
    
    def gcd(a, b):
        while b:
            a, b = b, a % b
        return a
    
    common_divisor = gcd(width, height)
    ratio_w = width // common_divisor
    ratio_h = height // common_divisor
    
    # Check for common ratios
    ratio_value = width / height
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

def get_image_category_from_dimensions(width: int, height: int) -> str:
    """
    Categorize image based on dimensions
    """
    if not width or not height:
        return "Unknown"
    
    total_pixels = width * height
    
    if total_pixels >= 20_000_000:  # 20MP+
        return "High Resolution"
    elif total_pixels >= 8_000_000:  # 8-20MP
        return "Medium-High Resolution"
    elif total_pixels >= 2_000_000:  # 2-8MP
        return "Medium Resolution"
    else:
        return "Low Resolution"

def extract_exif_data(image: Image.Image) -> Dict[str, Any]:
    """
    Extract EXIF data from PIL Image object
    """
    exif_data = {}
    
    try:
        # Get EXIF data
        exif = image._getexif()
        if exif is not None:
            for tag, value in exif.items():
                tag_name = ExifTags.TAGS.get(tag, tag)
                exif_data[tag_name] = value
    except (AttributeError, OSError):
        pass
    
    return exif_data

def create_thumbnail(image: Image.Image, size: tuple = (150, 150)) -> bytes:
    """
    Create thumbnail from PIL Image object
    """
    try:
        # Create a copy to avoid modifying the original
        thumbnail = image.copy()
        
        # Convert to RGB if necessary (for PNG with transparency)
        if thumbnail.mode in ('RGBA', 'LA', 'P'):
            thumbnail = thumbnail.convert('RGB')
        
        # Create thumbnail maintaining aspect ratio
        thumbnail.thumbnail(size, Image.Resampling.LANCZOS)
        
        # Save to bytes
        output = io.BytesIO()
        thumbnail.save(output, format='JPEG', quality=85)
        output.seek(0)
        
        return output.getvalue()
    except Exception as e:
        # Return empty bytes on error
        return b''

def validate_image_file(file_path: str) -> bool:
    """
    Validate if file path points to a valid image file
    """
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            return False
        
        # Check file extension
        if not validate_image_format(file_path):
            return False
        
        # Try to open with PIL
        with Image.open(file_path) as img:
            # Verify image can be loaded
            img.verify()
            return True
            
    except (UnidentifiedImageError, OSError, IOError):
        return False
    except Exception:
        return False 