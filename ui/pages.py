"""
Page modules for different sections of the Photo Manager.
"""

import streamlit as st
from typing import List, Dict, Any

from services.image_service import image_service
from services.search_service import search_service
from ui.components import (
    ImageCard, SearchFilters, StatsDisplay, 
    UploadProgress, GalleryControls
)
from analytics import AnalyticsService

class UploadPage:
    """Page for uploading and processing images."""
    
    @staticmethod
    def render():
        """Render the upload page."""
        st.header("Upload Images")
        st.write("Upload images to your semantic gallery. AI will automatically generate captions and extract metadata.")
        
        # Upload interface
        uploaded_files = st.file_uploader(
            "Choose image files",
            accept_multiple_files=True,
            type=['jpg', 'jpeg', 'png', 'tiff', 'tif', 'bmp', 'webp']
        )
        
        # Manual labels input
        manual_labels_input = st.text_input(
            "Manual Labels (optional, comma-separated)",
            placeholder="vacation, family, beach, sunset..."
        )
        
        if uploaded_files and st.button("Process Images", type="primary"):
            # Parse manual labels
            manual_labels = []
            if manual_labels_input:
                manual_labels = [label.strip() for label in manual_labels_input.split(",") if label.strip()]
            
            # Process files
            files_data = []
            for uploaded_file in uploaded_files:
                files_data.append({
                    'name': uploaded_file.name,
                    'size': uploaded_file.size,
                    'bytes': uploaded_file.read()
                })
            
            # Show progress
            progress_bar, status_text = UploadProgress.render_progress(0, len(files_data))
            
            # Upload images
            with st.spinner("Processing images..."):
                results = image_service.upload_images(files_data, manual_labels)
            
            # Update progress to complete
            progress_bar.progress(1.0)
            status_text.text(f"Upload complete! ({results['success_count']}/{results['total']})")
            
            # Show results
            UploadProgress.render_results(results)
        
        # Usage tips
        with st.expander("Upload Tips"):
            st.markdown("""
            - **Supported formats:** JPEG, PNG, TIFF, BMP, WebP
            - **Max file size:** 10MB per image
            - **AI Processing:** Automatic caption generation and OCR text extraction
            - **Manual Labels:** Add your own tags for better organization
            - **EXIF Data:** Camera metadata is automatically extracted when available
            """)

class GalleryPage:
    """Page for browsing the image gallery."""
    
    @staticmethod
    def render():
        """Render the gallery page."""
        st.header("Gallery")
        
        # Get all images
        images = image_service.get_all_images()
        
        if not images:
            st.info("No images uploaded yet. Go to the Upload tab to add some images!")
            return
        
        # Gallery controls
        controls = GalleryControls.render(len(images))
        
        # Sort images
        if controls['sort_by'] == "File Name":
            images.sort(key=lambda x: x.file_name)
        elif controls['sort_by'] == "Date Taken":
            images.sort(key=lambda x: x.date_taken or x.upload_date, reverse=True)
        else:  # Upload Date
            images.sort(key=lambda x: x.upload_date, reverse=True)
        
        # Display images
        for entry in images:
            ImageCard.render(entry, show_thumbnail=controls['show_thumbnails'])

class SearchPage:
    """Page for advanced image search."""
    
    @staticmethod
    def render():
        """Render the search page."""
        st.header("Search Images")
        st.write("Use semantic search and advanced filters to find specific images.")
        
        # Search interface
        col1, col2 = st.columns([3, 1])
        
        with col1:
            query = st.text_input(
                "Search Query",
                placeholder="Enter your search query (e.g., 'sunset over mountains', 'people laughing')"
            )
        
        with col2:
            search_button = st.button("Search", type="primary")
        
        # Advanced filters
        filters = SearchFilters.render()
        
        # Similarity threshold
        threshold = st.slider(
            "Similarity Threshold",
            min_value=0.0,
            max_value=1.0,
            value=0.5,
            step=0.05,
            help="Higher values return more relevant but fewer results"
        )
        
        # Perform search
        if query or any(filters.values()) or search_button:
            search_params = {
                'query': query,
                'threshold': threshold,
                'limit': 100,
                **filters
            }
            
            with st.spinner("Searching images..."):
                search_results = search_service.advanced_search(search_params)
            
            # Display results
            SearchPage._render_search_results(search_results)
        else:
            st.info("Enter a search query or apply filters to find images")
    
    @staticmethod
    def _render_search_results(results: Dict[str, Any]):
        """Render search results with scores."""
        relevant_results = results['relevant_results']
        below_threshold = results['below_threshold_results']
        
        # Search summary
        if results['query']:
            st.success(f"Found {results['relevant_count']} relevant results for '{results['query']}'")
        else:
            st.success(f"Found {results['relevant_count']} results matching your filters")
        
        # Relevant results
        if relevant_results:
            st.subheader("Relevant Results")
            for score, entry in relevant_results:
                ImageCard.render(entry, score=score)
        
        # Below threshold results
        if below_threshold:
            with st.expander(f"Below Threshold ({len(below_threshold)} results)"):
                for score, entry in below_threshold:
                    ImageCard.render(entry, score=score, show_thumbnail=True)
        
        if not relevant_results and not below_threshold:
            st.warning("No results found. Try adjusting your search query or filters.")

class AnalyticsPage:
    """Page for viewing analytics and insights."""
    
    @staticmethod
    def render():
        """Render the analytics page."""
        st.header("Analytics & Insights")
        st.write("Explore patterns and insights from your image collection.")
        
        try:
            analytics_service = AnalyticsService()
            
            # Quick stats
            stats = image_service.get_image_statistics()
            StatsDisplay.render_summary_metrics(stats)
            
            st.divider()
            
            # Analytics tabs
            tab1, tab2, tab3, tab4 = st.tabs([
                "Upload Trends", 
                "Camera Analysis", 
                "Label Insights", 
                "Location Data"
            ])
            
            with tab1:
                analytics_service.render_upload_timeline()
                analytics_service.render_activity_heatmap()
            
            with tab2:
                analytics_service.render_camera_distribution()
                analytics_service.render_technical_analysis()
            
            with tab3:
                analytics_service.render_label_frequency()
                analytics_service.render_keyword_trends()
            
            with tab4:
                analytics_service.render_gps_coverage()
                analytics_service.render_storage_analysis()
                
        except Exception as e:
            st.error(f"Error loading analytics: {e}")
            st.info("Analytics will be available once you upload some images.")

# Page registry for easy navigation
PAGES = {
    "Upload": UploadPage,
    "Gallery": GalleryPage, 
    "Search": SearchPage,
    "Analytics": AnalyticsPage
} 