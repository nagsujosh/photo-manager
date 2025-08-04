#!/usr/bin/env python3
"""
Startup script for the Photo Manager application.
This script ensures proper initialization and dependency checking.
"""

import sys
import subprocess
import os
from pathlib import Path

def check_dependencies():
    """Check if all required dependencies are installed"""
    required_packages = [
        'streamlit',
        'torch',
        'transformers',
        'pillow',
        'pytesseract',
        'sentence-transformers',
        'sqlalchemy',
        'numpy',
        'psycopg2-binary',
        'scikit-learn',
        'pandas',
        'plotly'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\nInstall missing packages with:")
        print(f"   pip install {' '.join(missing_packages)}")
        return False
    
    print("All dependencies are installed!")
    return True

def check_tesseract():
    """Check if Tesseract is available"""
    try:
        result = subprocess.run(['tesseract', '--version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("Tesseract OCR is available!")
            return True
    except FileNotFoundError:
        pass
    
    print("Tesseract OCR not found in PATH.")
    print("   Please install Tesseract and update TESSERACT_CMD in core/config.py")
    print("   Installation instructions:")
    print("   - macOS: brew install tesseract")
    print("   - Ubuntu: sudo apt-get install tesseract-ocr")
    print("   - Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki")
    return False

def check_config():
    """Check if configuration is properly set up"""
    try:
        from core.config import config
        
        # Check database URL
        if not config.DATABASE_URL or config.DATABASE_URL.startswith("postgresql://..."):
            print("DATABASE_URL not configured in core/config.py")
            print("   Please update with your Neon DB connection string")
            return False
        
        # Check if Tesseract path exists
        if not os.path.exists(config.TESSERACT_CMD):
            print(f"Tesseract not found at: {config.TESSERACT_CMD}")
            print("   Please update TESSERACT_CMD in core/config.py")
            return False
        
        print("Configuration looks good!")
        return True
        
    except ImportError as e:
        print(f"Configuration error: {e}")
        return False

def initialize_database():
    """Initialize database tables if needed"""
    try:
        from database.connection import init_database, test_connection
        
        # Test connection first
        if not test_connection():
            print("Database connection failed")
            print("   Please check your DATABASE_URL in core/config.py")
            return False
        
        # Initialize tables
        if not init_database():
            print("Database initialization failed")
            return False
        
        print("Database tables initialized!")
        return True
        
    except Exception as e:
        print(f"Database initialization failed: {e}")
        print("   Please check your DATABASE_URL in core/config.py")
        return False

def download_models():
    """Download required AI models if not already cached"""
    print("Checking AI models...")
    
    try:
        from sentence_transformers import SentenceTransformer
        from core.config import config
        
        # This will download the model if not already cached
        print(f"   Loading embedding model: {config.EMBEDDING_MODEL_NAME}")
        embedder = SentenceTransformer(config.EMBEDDING_MODEL_NAME)
        print("Embedding model ready!")
        
        # Note: Caption model will be downloaded on first use
        print("Caption model will download on first image upload")
        
        return True
        
    except Exception as e:
        print(f"Model loading failed: {e}")
        return False

def run_application():
    """Run the Streamlit application"""
    print("\nStarting Photo Manager...")
    print("   Access the application at: http://localhost:8501")
    print("   Press Ctrl+C to stop the application")
    
    try:
        os.system("streamlit run main.py")
    except KeyboardInterrupt:
        print("\nApplication stopped by user")
    except Exception as e:
        print(f"\nApplication error: {e}")

def main():
    """Main startup routine"""
    print("Photo Manager - Startup Check")
    print("=" * 50)
    
    # Run all checks
    checks_passed = True
    
    print("\n1. Checking Python dependencies...")
    if not check_dependencies():
        checks_passed = False
    
    print("\n2. Checking Tesseract OCR...")
    tesseract_available = check_tesseract()
    
    print("\n3. Checking configuration...")
    if not check_config():
        checks_passed = False
    
    print("\n4. Initializing database...")
    if not initialize_database():
        checks_passed = False
    
    print("\n5. Preparing AI models...")
    if not download_models():
        checks_passed = False
    
    if not checks_passed:
        print("\nSome checks failed. Please fix the issues above before running the application.")
        sys.exit(1)
    
    if not tesseract_available:
        print("\nTesseract not available - OCR features will be disabled")
        print("   The application will still work for image captioning and search")
        
        response = input("\n   Continue anyway? (y/N): ").lower()
        if response != 'y':
            print("   Please install Tesseract and try again.")
            sys.exit(1)
    
    print("\n" + "=" * 50)
    print("All checks passed! Ready to start the application.")
    
    # Ask user if they want to start the app
    response = input("\nStart the application now? (Y/n): ").lower()
    if response in ['', 'y', 'yes']:
        run_application()
    else:
        print("\nTo start manually, run: streamlit run main.py")

if __name__ == "__main__":
    main() 