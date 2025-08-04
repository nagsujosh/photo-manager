"""
Photo Manager - Main Application
A professional image management system with AI-powered search and comprehensive metadata analysis.

This is the main entry point that coordinates between all modular components.
"""

# Fix PyTorch/Streamlit compatibility issues
import sys
import warnings
import os

# Suppress PyTorch warnings
warnings.filterwarnings('ignore', category=UserWarning, module='torch')
warnings.filterwarnings('ignore', message='.*torch.classes.*')

# Set environment variables to suppress the specific errors
os.environ['TORCH_DISABLE_AUTOCAST'] = '1'

# Monkey patch torch classes to avoid the __path__._path error
try:
    import torch
    if hasattr(torch, '_classes'):
        # Create a dummy __path__ attribute to prevent the error
        class DummyPath:
            _path = []
        torch.classes.__path__ = DummyPath()
except ImportError:
    pass
except Exception:
    pass

import streamlit as st

# Configure Streamlit page
st.set_page_config(
    page_title="Photo Manager", 
    page_icon="📷",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import modular components
from core.config import config
from database.connection import init_database, test_connection
from services.image_service import image_service
from ui.pages import PAGES
from ui.components import StatsDisplay

@st.cache_data(ttl=60)  # Cache for 5 minutes # I wish I was using Redis
def get_cached_stats():
    """Get image statistics with caching to reduce rendering overhead."""
    return image_service.get_image_statistics()

@st.cache_resource
def initialize_app_resources():
    """Initialize app resources once and cache them."""
    # Validate configuration
    if not config.validate():
        st.error("Configuration validation failed. Please check your settings.")
        st.stop()
    
    # Test database connection
    if not test_connection():
        st.error("Database connection failed. Please check your DATABASE_URL.")
        st.stop()
    
    # Initialize database
    if not init_database():
        st.error("Database initialization failed.")
        st.stop()
    
    return True

def initialize_app():
    """Initialize the application with necessary setup."""
    initialize_app_resources()

def render_sidebar():
    """Render the application sidebar with navigation and stats."""
    
    with st.sidebar:
        # App title and info
        st.title("Photo Manager")
        st.markdown("*AI-Powered Image Management*")
        
        # Navigation
        st.divider()
        page_names = list(PAGES.keys())
        icons = ["Upload", "Gallery", "Search", "Analytics"]
        
        # Create navigation with icons
        selected_page = st.radio(
            "Navigate to:",
            page_names,
            format_func=lambda x: f"{icons[page_names.index(x)]} {x}",
            key="navigation"
        )
        
        # Display statistics with caching
        try:
            stats = get_cached_stats()
            StatsDisplay.render_sidebar_stats(stats)
        except Exception as e:
            st.warning(f"Stats unavailable: {e}")
        
        # App info
        st.divider()
        st.markdown("### About")
        st.markdown("""
        **Features:**
        - AI-powered image analysis
        - Semantic search
        - EXIF metadata extraction
        - Analytics dashboard
        - Smart labeling system
        """)
        
        with st.expander("System Info"):
            st.write(f"**AI Model:** {config.CAPTION_MODEL_NAME}")
            st.write(f"**Embedding Model:** {config.EMBEDDING_MODEL_NAME}")
            st.write(f"**Similarity Threshold:** {config.SIMILARITY_THRESHOLD}")
        
        return selected_page

def main():
    """Main application entry point."""
    
    # Initialize the application
    try:
        initialize_app()
    except Exception as e:
        st.error(f"Failed to initialize application: {e}")
        st.stop()
    
    # Render sidebar and get selected page
    selected_page = render_sidebar()
    
    # Render the selected page
    try:
        page_class = PAGES[selected_page]
        page_class.render()
    except Exception as e:
        st.error(f"Error rendering {selected_page} page: {e}")
        st.write("Please try refreshing the page or contact support if the issue persists.")

if __name__ == "__main__":
    main()