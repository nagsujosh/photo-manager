# Photo Manager

A AI-powered image management system with advanced search capabilities, comprehensive metadata extraction, and analytics dashboard. Built with a modular architecture for maintainability and extensibility.

## Key Features

### AI-Powered Analysis
- **Smart Captioning**: Automatic generation of short and detailed image descriptions
- **Keyword Extraction**: AI-generated labels and tags for better organization
- **OCR Text Extraction**: Extract and search text content within images
- **Semantic Embeddings**: Multi-vector embeddings for powerful similarity search

### Advanced Search & Filtering
- **Semantic Search**: Find images by meaning, not just keywords
- **Multi-Modal Search**: Combines AI captions, manual labels, and OCR text
- **Professional Metadata Filters**: Filter by camera settings, dates, dimensions, formats
- **Similarity Scoring**: Weighted relevance scoring with configurable thresholds

### Professional Metadata Handling
- **Complete EXIF Extraction**: Camera make/model, settings, GPS coordinates
- **Technical Analysis**: ISO, aperture, shutter speed, focal length
- **Image Properties**: Dimensions, format, color mode, file size
- **Thumbnail Generation**: Fast loading with optimized previews

### Analytics & Insights
- **Upload Timeline**: Track your photography activity over time
- **Camera Analysis**: Distribution of cameras and technical settings
- **Label Insights**: Most used tags and keyword trends
- **Storage Analytics**: File format distribution and storage usage
- **GPS Coverage**: Location data visualization and statistics

## Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL database (I used Neon DB)
- Tesseract OCR (for text extraction)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/nagsujosh/photo-manager
   cd photo-manager
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Tesseract OCR**
   ```bash
   # macOS
   brew install tesseract
   
   # Ubuntu/Debian
   sudo apt-get install tesseract-ocr
   
   # Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki
   ```

4. **Configure environment**
   
   Create a `.env` file or set environment variables:
   ```bash
   export DATABASE_URL="postgresql://username:password@host:port/database"
   export TESSERACT_CMD="/opt/homebrew/bin/tesseract"  # Adjust path as needed
   ```

5. **Run the application**
   ```bash
   python run_app.py
   ```
   
   Or start directly:
   ```bash
   streamlit run main.py
   ```

## Project Structure

```
photo-manager/
├── core/                    # Core utilities and configuration
│   ├── config.py           # Configuration management
│   ├── utils.py            # Utility functions
│   └── similarity.py       # Similarity calculations
├── database/               # Data access layer
│   ├── connection.py       # Database connection management
│   ├── models.py           # SQLAlchemy models
│   └── repository.py       # Repository pattern implementation
├── services/               # Business logic layer
│   ├── ai_service.py       # AI processing (captions, OCR, embeddings)
│   ├── image_service.py    # Image management operations
│   └── search_service.py   # Search and filtering logic
├── ui/                     # User interface components
│   ├── components.py       # Reusable UI components
│   └── pages.py           # Page-specific modules
├── main.py                 # Application entry point
├── analytics.py           # Analytics service
├── run_app.py             # Startup script with dependency checking
└── requirements.txt       # Python dependencies
```

## Configuration

The application uses a centralized configuration system that supports environment variables:

### Core Settings
- `DATABASE_URL`: PostgreSQL connection string
- `TESSERACT_CMD`: Path to Tesseract executable
- `CAPTION_MODEL_NAME`: AI model for image captioning
- `EMBEDDING_MODEL_NAME`: Model for generating semantic embeddings
- `SIMILARITY_THRESHOLD`: Minimum similarity score for search results

### Performance Settings
- `MAX_IMAGE_SIZE`: Maximum file size for uploads (default: 10MB)
- `BATCH_SIZE`: Number of images to process simultaneously
- `MAX_CONCURRENT_UPLOADS`: Limit for concurrent upload processing

### Search Weights
- `AI_WEIGHT`: Weight for AI-generated content in similarity scoring (default: 0.4)
- `MANUAL_WEIGHT`: Weight for manual labels (default: 0.3)
- `OCR_WEIGHT`: Weight for OCR text content (default: 0.3)

## Usage Guide

### Upload Images
1. Navigate to the **Upload** tab
2. Select multiple image files (JPEG, PNG, TIFF, BMP, WebP)
3. Add optional manual labels for better organization
4. Click "Process Images" to upload and analyze

### Browse Gallery
- View all uploaded images with comprehensive metadata
- Sort by upload date, filename, or date taken
- Toggle between thumbnail and full-size views
- Explore detailed metadata in organized tabs

### Advanced Search
- Enter semantic queries like "sunset over mountains" or "people laughing"
- Apply advanced filters:
  - Date ranges (upload date and EXIF date taken)
  - Camera make and model
  - Technical settings (ISO, aperture, focal length)
  - Image dimensions and formats
  - Manual labels
- Adjust similarity threshold for more precise results

### Analytics Dashboard
- **Upload Trends**: Visualize your photography activity
- **Camera Analysis**: See which cameras and settings you use most
- **Label Insights**: Track popular tags and keywords
- **Location Data**: View GPS coverage and location statistics

## Technical Details

### AI Models
- **Image Captioning**: Uses Moondream2 for generating natural language descriptions
- **Text Embeddings**: Sentence transformers for semantic similarity
- **OCR Processing**: Tesseract for text extraction from images

### Database Schema
- Comprehensive metadata storage with proper indexing
- JSON fields for flexible metadata and embeddings
- Optimized queries for fast search and filtering

### Performance Optimizations
- Lazy loading of AI models
- Thumbnail generation for faster gallery loading
- Database connection pooling
- Batch processing for uploads
- Indexed database queries

### Search Algorithm
1. **Filter Stage**: Database-level filtering using metadata
2. **Embedding Stage**: Generate query embedding for semantic search
3. **Similarity Stage**: Calculate weighted similarities across AI, manual, and OCR content
4. **Ranking Stage**: Sort results by relevance score

## Advanced Features

### Professional Metadata Extraction
- Complete EXIF data parsing and storage
- GPS coordinate conversion from DMS to decimal
- Camera-specific metadata interpretation
- Image quality categorization based on resolution

### Multi-Modal Semantic Search
- Combines multiple embedding types for comprehensive search
- Configurable similarity weights for different content types
- Threshold-based filtering for relevant results
- Support for complex query combinations

### Analytics Engine
- Real-time statistics calculation
- Visual charts and graphs using Plotly
- Trend analysis over time
- Export capabilities for further analysis

## System Requirements

### Minimum Requirements
- 4GB RAM (8GB recommended for large collections)
- 2GB storage space (plus space for your images)
- Modern web browser
- Internet connection (for initial AI model downloads)

### Recommended Setup
- 8GB+ RAM for optimal performance
- SSD storage for faster database operations
- Dedicated GPU (optional, for faster AI processing)

## Deployment

### Local Development
```bash
streamlit run main.py
```

### Production Deployment
1. Set up a PostgreSQL database
2. Configure environment variables
3. Use a production WSGI server
4. Set up reverse proxy (nginx recommended)
5. Configure SSL/TLS certificates

## Contributing

We welcome contributions! Please see our contribution guidelines:

1. Fork the repository
2. Create a feature branch
3. Make your changes with proper tests
4. Submit a pull request

### Development Setup
```bash
git clone <your-fork>
cd photo-manager
pip install -r requirements.txt
python run_app.py
```

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) file for details.
---

**Bored so built it**