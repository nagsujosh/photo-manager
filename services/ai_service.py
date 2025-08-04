"""
AI service for handling image analysis, captioning, and embedding generation.
"""

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from PIL import Image, ExifTags
try:
    from PIL.ExifTags import IFDRational
except ImportError:
    # Fallback for older PIL versions
    IFDRational = None
import pytesseract
from sentence_transformers import SentenceTransformer
import numpy as np
import io
from datetime import datetime
from typing import Dict, List, Any
import json

from core.config import config
from core.utils import clean_text_string, extract_keywords

class AIService:
    """Service for AI-powered image analysis."""
    
    def __init__(self):
        self._caption_model = None
        self._tokenizer = None
        self._embedder = None
        self._device = None
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize AI models lazily."""
        try:
            # Initialize device
            self._device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
            
            # Initialize embedding model (lighter, load immediately)
            self._embedder = SentenceTransformer(config.EMBEDDING_MODEL_NAME)
            
            # Caption model will be loaded on first use
            print("AI Service initialized successfully")
            
        except Exception as e:
            print(f"Warning: Error initializing AI models: {e}")
    
    def _load_caption_model(self):
        """Load caption model on demand."""
        if self._caption_model is None:
            try:
                self._caption_model = AutoModelForCausalLM.from_pretrained(
                    config.CAPTION_MODEL_NAME,
                    revision=config.CAPTION_MODEL_REVISION,
                    trust_remote_code=True,
                    cache_dir=config.get_model_cache_dir()
                )
                self._tokenizer = AutoTokenizer.from_pretrained(
                    config.CAPTION_MODEL_NAME,
                    trust_remote_code=True,
                    cache_dir=config.get_model_cache_dir()
                )
                self._caption_model.to(self._device)
                self._caption_model.eval()
                print("Caption model loaded successfully")
            except Exception as e:
                print(f"Error loading caption model: {e}")
    
    def extract_exif_metadata(self, image: Image.Image) -> Dict[str, Any]:
        """Extract comprehensive EXIF metadata from an image."""
        metadata = {}
        
        def serialize_exif_value(value):
            """Convert EXIF values to JSON-serializable format."""
            from PIL.ExifTags import IFD
            
            # Handle IFDRational objects (common in EXIF data)
            if IFDRational and isinstance(value, IFDRational):
                if value.denominator == 0:
                    return float(value.numerator)
                return float(value.numerator) / float(value.denominator)
            elif hasattr(value, 'numerator') and hasattr(value, 'denominator'):
                # This is likely an IFDRational object or similar fraction
                if value.denominator == 0:
                    return float(value.numerator)
                return float(value.numerator) / float(value.denominator)
            
            # Handle bytes
            elif isinstance(value, bytes):
                try:
                    return value.decode('utf-8', errors='ignore')
                except:
                    return str(value)
            
            # Handle lists/tuples of values (like GPS coordinates)
            elif isinstance(value, (list, tuple)):
                return [serialize_exif_value(v) for v in value]
            
            # Handle dictionaries (like GPSInfo)
            elif isinstance(value, dict):
                return {str(k): serialize_exif_value(v) for k, v in value.items()}
            
            # Handle basic types
            elif isinstance(value, (int, float, str, bool)):
                return value
            
            # Handle None
            elif value is None:
                return None
            
            # Fallback to string representation
            else:
                return str(value)
        
        try:
            exif_data = image._getexif()
            if exif_data:
                for tag, value in exif_data.items():
                    tag_name = ExifTags.TAGS.get(tag, str(tag))
                    try:
                        metadata[tag_name] = serialize_exif_value(value)
                    except Exception as e:
                        # If serialization fails, store as string
                        metadata[tag_name] = str(value)
        except AttributeError:
            # Image has no EXIF data
            pass
        except Exception as e:
            print(f"Warning: Error extracting EXIF data: {e}")
        
        return metadata
    
    def parse_camera_metadata(self, exif_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse specific camera metadata from EXIF data."""
        camera_info = {}
        
        # Camera make and model
        camera_info['make'] = exif_data.get('Make', '').strip()
        camera_info['model'] = exif_data.get('Model', '').strip()
        
        # Date taken
        date_str = exif_data.get('DateTime') or exif_data.get('DateTimeOriginal')
        if date_str:
            try:
                camera_info['date_taken'] = datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
            except ValueError:
                camera_info['date_taken'] = None
        else:
            camera_info['date_taken'] = None
        
        # ISO speed
        iso = exif_data.get('ISOSpeedRatings') or exif_data.get('ISO')
        camera_info['iso_speed'] = int(iso) if iso else None
        
        # Aperture
        aperture = exif_data.get('FNumber') or exif_data.get('ApertureValue')
        if aperture:
            if isinstance(aperture, (list, tuple)) and len(aperture) == 2:
                camera_info['aperture'] = float(aperture[0]) / float(aperture[1])
            else:
                camera_info['aperture'] = float(aperture)
        else:
            camera_info['aperture'] = None
        
        # Shutter speed
        shutter = exif_data.get('ExposureTime')
        if shutter:
            if isinstance(shutter, (list, tuple)) and len(shutter) == 2:
                if shutter[1] != 0:
                    camera_info['shutter_speed'] = f"1/{int(shutter[1]/shutter[0])}"
                else:
                    camera_info['shutter_speed'] = str(shutter[0])
            else:
                camera_info['shutter_speed'] = str(shutter)
        else:
            camera_info['shutter_speed'] = None
        
        # Focal length
        focal = exif_data.get('FocalLength')
        if focal:
            if isinstance(focal, (list, tuple)) and len(focal) == 2:
                camera_info['focal_length'] = float(focal[0]) / float(focal[1])
            else:
                camera_info['focal_length'] = float(focal)
        else:
            camera_info['focal_length'] = None
        
        # GPS coordinates
        gps_info = exif_data.get('GPSInfo', {})
        if gps_info:
            try:
                lat = gps_info.get(2)  # GPSLatitude
                lat_ref = gps_info.get(1)  # GPSLatitudeRef
                lon = gps_info.get(4)  # GPSLongitude
                lon_ref = gps_info.get(3)  # GPSLongitudeRef
                
                if lat and lon:
                    def dms_to_decimal(dms, ref):
                        degrees = float(dms[0])
                        minutes = float(dms[1]) / 60.0
                        seconds = float(dms[2]) / 3600.0
                        decimal = degrees + minutes + seconds
                        if ref in ['S', 'W']:
                            decimal = -decimal
                        return decimal
                    
                    camera_info['gps_latitude'] = dms_to_decimal(lat, lat_ref)
                    camera_info['gps_longitude'] = dms_to_decimal(lon, lon_ref)
            except (KeyError, IndexError, TypeError, ValueError):
                camera_info['gps_latitude'] = None
                camera_info['gps_longitude'] = None
        else:
            camera_info['gps_latitude'] = None
            camera_info['gps_longitude'] = None
        
        return camera_info
    
    def generate_captions(self, image: Image.Image) -> Dict[str, str]:
        """Generate short and detailed captions using the AI model."""
        captions = {"short_caption": "", "detailed_caption": ""}
        
        self._load_caption_model()
        
        if self._caption_model is None or self._tokenizer is None:
            # Fallback captions
            captions["short_caption"] = "Image"
            captions["detailed_caption"] = "An image uploaded to the system"
            return captions
        
        try:
            # Generate short caption
            short_prompt = "Describe this image briefly:"
            short_caption = self._caption_model.answer_question(image, short_prompt, self._tokenizer)
            captions["short_caption"] = clean_text_string(short_caption)
            
            # Generate detailed caption
            detailed_prompt = "Describe this image in detail, including objects, people, activities, setting, and mood:"
            detailed_caption = self._caption_model.answer_question(image, detailed_prompt, self._tokenizer)
            captions["detailed_caption"] = clean_text_string(detailed_caption)
            
        except Exception as e:
            print(f"Error generating captions: {e}")
            captions["short_caption"] = "Image"
            captions["detailed_caption"] = "An image uploaded to the system"
        
        return captions
    
    def extract_ocr_text(self, image: Image.Image) -> str:
        """Extract text from image using OCR."""
        try:
            pytesseract.pytesseract.tesseract_cmd = config.TESSERACT_CMD
            ocr_text = pytesseract.image_to_string(image, config='--psm 6')
            return clean_text_string(ocr_text)
        except Exception as e:
            print(f"Error in OCR extraction: {e}")
            return ""
    
    def create_thumbnail(self, image: Image.Image) -> bytes:
        """Create a thumbnail of the image."""
        try:
            thumbnail = image.copy()
            thumbnail.thumbnail(config.THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
            
            buffer = io.BytesIO()
            if thumbnail.mode in ('RGBA', 'LA', 'P'):
                thumbnail = thumbnail.convert('RGB')
            thumbnail.save(buffer, format='JPEG', quality=85)
            return buffer.getvalue()
        except Exception as e:
            print(f"Error creating thumbnail: {e}")
            return b""
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text."""
        try:
            if self._embedder and text.strip():
                return self._embedder.encode(text).tolist()
            else:
                return [0] * 384  # Default embedding size
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return [0] * 384
    
    def process_image(self, image: Image.Image) -> Dict[str, Any]:
        """Comprehensive image processing to extract all metadata and generate embeddings."""
        results = {}
        
        # Basic image properties
        results['width'] = image.width
        results['height'] = image.height
        results['format'] = image.format or 'Unknown'
        results['mode'] = image.mode
        
        # Extract EXIF metadata
        exif_data = self.extract_exif_metadata(image)
        results['exif_metadata'] = exif_data
        
        # Parse camera-specific metadata
        camera_info = self.parse_camera_metadata(exif_data)
        results.update(camera_info)
        
        # Generate AI captions
        captions = self.generate_captions(image)
        results.update(captions)
        
        # Extract OCR text
        results['ocr_text'] = self.extract_ocr_text(image)
        
        # Create thumbnail
        results['thumbnail_data'] = self.create_thumbnail(image)
        
        # Generate AI labels from captions using enhanced keyword extraction
        combined_text = f"{results['short_caption']} {results['detailed_caption']}"
        results['ai_labels'] = extract_keywords(combined_text, min_length=3, max_keywords=15)
        
        # Generate embeddings
        try:
            results['ai_embedding'] = self.generate_embedding(combined_text)
            results['ocr_embedding'] = self.generate_embedding(results['ocr_text'])
            
            # Prepare combined text for embedding
            metadata_text = f"{results['short_caption']} {results['detailed_caption']} {results['ocr_text']} {' '.join(results['ai_labels'])}"
            results['metadata_text'] = metadata_text
            results['combined_embedding'] = self.generate_embedding(metadata_text)
            
        except Exception as e:
            print(f"Error generating embeddings: {e}")
            # Fallback empty embeddings
            embedding_size = 384
            results['ai_embedding'] = [0] * embedding_size
            results['ocr_embedding'] = [0] * embedding_size
            results['combined_embedding'] = [0] * embedding_size
            results['metadata_text'] = ""
        
        return results 