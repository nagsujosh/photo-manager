# Photo Manager

## Overview

Photo Manager has been completely refactored into a modular, professional-grade architecture following best practices for maintainability, scalability, and separation of concerns.

## Directory Structure

```
ScreenshotManager/
├── core/                           # Core utilities and shared components
│   ├── __init__.py
│   ├── config.py                   # Configuration management with env variables
│   ├── utils.py                    # Utility functions for text processing, formatting
│   └── similarity.py               # Similarity calculation algorithms
│
├── database/                       # Data access layer
│   ├── __init__.py
│   ├── connection.py               # Database connection and session management
│   ├── models.py                   # SQLAlchemy database models
│   └── repository.py               # Repository pattern for data operations
│
├── services/                       # Business logic layer
│   ├── __init__.py
│   ├── ai_service.py               # AI processing (captions, embeddings, OCR)
│   ├── image_service.py            # Image upload and management logic
│   └── search_service.py           # Search and filtering logic
│
├── ui/                            # User interface components
│   ├── __init__.py
│   ├── components.py               # Reusable Streamlit components
│   └── pages.py                    # Page-specific UI modules
│
├── main.py                        # Main application entry point
├── analytics.py                   # Analytics service (kept separate for now)
├── run_app.py                     # Application startup script
├── requirements.txt               # Dependencies
└── README.md                      # Project documentation
```

## Architecture Principles

### 1. Separation of Concerns
- **Core**: Shared utilities and configuration
- **Database**: All data persistence logic
- **Services**: Business logic and operations
- **UI**: User interface components and pages

### 2. Dependency Injection
- Services are injected into UI components
- Database connections managed centrally
- Configuration accessed through global config object

### 3. Repository Pattern
- `ImageRepository` provides clean interface for data operations
- Database queries isolated from business logic
- Consistent error handling and transaction management

### 4. Service Layer Architecture
- `AIService`: Handles all AI-related operations
- `ImageService`: Manages image upload and processing workflow
- `SearchService`: Handles search and filtering operations

### 5. Component-Based UI
- Reusable UI components in `ui/components.py`
- Page modules in `ui/pages.py`
- Consistent styling and behavior

## Key Components

### Core Module (`core/`)

#### `config.py`
- Centralized configuration management
- Environment variable support
- Configuration validation
- Default values and settings

#### `utils.py`
- Text processing utilities
- File size formatting
- Keyword extraction
- Search summary generation

#### `similarity.py`
- Cosine similarity calculations
- Vector comparison utilities

### Database Layer (`database/`)

#### `connection.py`
- Database engine setup
- Session management with context managers
- Connection testing and initialization

#### `models.py`
- SQLAlchemy models with comprehensive metadata
- Database indexes for performance
- Model properties and methods

#### `repository.py`
- Repository pattern implementation
- CRUD operations with error handling
- Advanced querying and filtering
- Statistics generation

### Services Layer (`services/`)

#### `ai_service.py`
- AI model management (lazy loading)
- Image analysis and captioning
- EXIF metadata extraction
- OCR text extraction
- Embedding generation
- Thumbnail creation

#### `image_service.py`
- Image upload workflow
- File validation
- Batch processing
- Image management operations
- Integration with AI service

#### `search_service.py`
- Semantic search implementation
- Advanced filtering
- Similarity scoring
- Query building
- Results ranking

### UI Layer (`ui/`)

#### `components.py`
- `ImageCard`: Comprehensive image display component
- `SearchFilters`: Advanced filtering interface
- `StatsDisplay`: Statistics visualization
- `UploadProgress`: Upload progress tracking
- `GalleryControls`: Gallery view controls

#### `pages.py`
- `UploadPage`: Image upload interface
- `GalleryPage`: Image browsing interface
- `SearchPage`: Advanced search interface
- `AnalyticsPage`: Analytics dashboard

## Data Flow

### 1. Image Upload Flow
```
UI (UploadPage) → ImageService → AIService → Repository → Database
```

### 2. Search Flow
```
UI (SearchPage) → SearchService → Repository → Database
                ↓
              AIService (for embeddings)
```

### 3. Gallery Display Flow
```
UI (GalleryPage) → ImageService → Repository → Database
```

## Benefits of Modular Architecture

### 1. **Maintainability**
- Clear separation of concerns
- Easy to locate and modify specific functionality
- Reduced coupling between components

### 2. **Testability**
- Each module can be tested independently
- Mock dependencies for unit testing
- Clear interfaces for integration testing

### 3. **Scalability**
- Easy to add new features
- Simple to replace or upgrade individual components
- Horizontal scaling possibilities

### 4. **Reusability**
- Components can be reused across different contexts
- Services can be used by multiple UI components
- Utilities shared across the application

### 5. **Development Experience**
- Clear structure for new developers
- Consistent patterns throughout codebase
- Easy to extend and modify

## Configuration Management

The application uses a centralized configuration system with:

- Environment variable support
- Validation and error checking
- Default values for development
- Runtime configuration access

Example:
```python
from core.config import config

# Access configuration
db_url = config.DATABASE_URL
ai_model = config.CAPTION_MODEL_NAME

# Validate configuration
if config.validate():
    # Configuration is valid
    pass
```

## Database Operations

All database operations go through the repository pattern:

```python
from database.repository import image_repository

# Create image
entry = image_repository.create(image_data)

# Search with filters
results = image_repository.search_by_filters(filters)

# Get statistics
stats = image_repository.get_statistics()
```

## Service Usage

Services provide high-level business operations:

```python
from services.image_service import image_service
from services.search_service import search_service

# Upload images
results = image_service.upload_images(files, labels)

# Perform search
search_results = search_service.advanced_search(params)
```

## Error Handling

- Consistent error handling patterns across all modules
- Graceful degradation when services are unavailable
- User-friendly error messages in UI
- Logging for debugging and monitoring

## Performance Considerations

- Lazy loading of AI models
- Database connection pooling
- Thumbnail generation for faster loading
- Indexed database queries
- Batch processing for uploads

## Future Extensibility

The modular architecture makes it easy to:

- Add new AI models or services
- Implement caching layers
- Add new search algorithms
- Create different UI frameworks
- Implement API endpoints
- Add authentication and authorization
- Scale individual components

## Development Guidelines

1. **Keep modules focused**: Each module should have a single responsibility
2. **Use dependency injection**: Don't import services directly in UI components
3. **Handle errors gracefully**: Always provide fallbacks and user feedback
4. **Document interfaces**: Clear docstrings for all public methods
5. **Test individual modules**: Write unit tests for each service and component
6. **Follow naming conventions**: Consistent naming across the codebase

This modular architecture provides a solid foundation for maintaining and extending the Photo Manager while ensuring code quality and developer productivity. 