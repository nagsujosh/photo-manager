"""
Reusable UI components for the Semantic Image Gallery.
"""

import streamlit as st
import io
from PIL import Image
from typing import List, Dict, Any, Optional
from datetime import datetime, date

from database.models import ImageEntry
from core.utils import format_file_size, format_camera_settings, safe_json_loads
from services.image_service import image_service

class ImageCard:
    """Component for displaying image cards with metadata."""
    
    @staticmethod
    def render(entry: ImageEntry, score: float = None, show_thumbnail: bool = True):
        """Render a comprehensive image card with metadata."""
        
        with st.container():
            # Header with filename, score, and delete button
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.subheader(entry.file_name)
            with col2:
                if score is not None and score > 0:
                    st.metric("Similarity", f"{score:.3f}")
            with col3:
                # Delete button with confirmation
                delete_key = f"delete_{entry.id}"
                confirm_key = f"confirm_delete_{entry.id}"
                
                # Check if we're in confirmation mode for this image
                if st.session_state.get(confirm_key, False):
                    # Show confirmation buttons
                    col_confirm, col_cancel = st.columns(2)
                    
                    with col_confirm:
                        if st.button("Delete", key=f"confirm_{entry.id}", type="primary"):
                            with st.spinner(f"Deleting {entry.file_name}..."):
                                success = image_service.delete_image(entry.id)
                                if success:
                                    st.success(f"Successfully deleted {entry.file_name}")
                                    # Clear the confirmation state
                                    st.session_state[confirm_key] = False
                                    st.rerun()  # Refresh the page to remove the deleted image
                                else:
                                    st.error(f"Failed to delete {entry.file_name}. Please try again.")
                                    st.session_state[confirm_key] = False
                    
                    with col_cancel:
                        if st.button("Cancel", key=f"cancel_{entry.id}"):
                            st.session_state[confirm_key] = False
                            st.rerun()
                else:
                    # Show delete button
                    if st.button("Delete", key=delete_key, type="secondary", help="Delete this image"):
                        st.session_state[confirm_key] = True
                        st.rerun()
                
                # Show warning message when in confirmation mode
                if st.session_state.get(confirm_key, False):
                    st.warning(f"Delete **{entry.file_name}**?")
            
            # Image display
            if show_thumbnail and entry.thumbnail_data:
                try:
                    thumbnail = Image.open(io.BytesIO(entry.thumbnail_data))
                    st.image(thumbnail, caption=entry.file_name, width=256)
                except Exception:
                    # Fallback to full image
                    ImageCard._render_full_image(entry)
            else:
                ImageCard._render_full_image(entry)
            
            # Metadata tabs
            tab1, tab2, tab3, tab4 = st.tabs(["Labels & Text", "Camera Data", "Technical", "Details"])
            
            with tab1:
                ImageCard._render_labels_tab(entry)
            
            with tab2:
                ImageCard._render_camera_tab(entry)
            
            with tab3:
                ImageCard._render_technical_tab(entry)
            
            with tab4:
                ImageCard._render_details_tab(entry)
            
            st.divider()
    
    @staticmethod
    def _render_full_image(entry: ImageEntry):
        """Render full-size image with error handling."""
        try:
            image = Image.open(io.BytesIO(entry.image_data))
            st.image(image, caption=entry.file_name, use_container_width=True)
        except Exception as e:
            st.error(f"Error loading image: {e}")
    
    @staticmethod
    def _render_labels_tab(entry: ImageEntry):
        """Render labels and text content tab."""
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**AI Caption:**")
            st.write(entry.short_caption or "No caption")
            st.write("**AI Labels:**")
            ai_labels = safe_json_loads(entry.ai_labels, [])
            if ai_labels:
                st.write(", ".join(ai_labels))
            else:
                st.write("No AI labels")
        
        with col2:
            st.write("**Manual Labels:**")
            manual_labels = entry.manual_labels
            if manual_labels:
                st.write(", ".join(manual_labels))
            else:
                st.write("No manual labels")
            st.write("**OCR Text:**")
            if entry.ocr_text:
                st.text_area("OCR Text Content", entry.ocr_text, height=100, disabled=True, key=f"ocr_{entry.id}", label_visibility="collapsed")
            else:
                st.write("No text detected")
    
    @staticmethod
    def _render_camera_tab(entry: ImageEntry):
        """Render camera metadata tab."""
        col1, col2 = st.columns(2)
        
        with col1:
            camera_name = f"{entry.camera_make} {entry.camera_model}".strip()
            st.write(f"**Camera:** {camera_name or 'Unknown'}")
            st.write(f"**Date Taken:** {entry.date_taken or 'Unknown'}")
            st.write(f"**ISO:** {entry.iso_speed or 'Unknown'}")
        
        with col2:
            st.write(f"**Aperture:** f/{entry.aperture}" if entry.aperture else "**Aperture:** Unknown")
            st.write(f"**Shutter Speed:** {entry.shutter_speed or 'Unknown'}")
            st.write(f"**Focal Length:** {entry.focal_length}mm" if entry.focal_length else "**Focal Length:** Unknown")
    
    @staticmethod
    def _render_technical_tab(entry: ImageEntry):
        """Render technical specifications tab."""
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Dimensions:** {entry.width} × {entry.height}px")
            st.write(f"**Format:** {entry.format}")
            st.write(f"**Color Mode:** {entry.mode}")
            st.write(f"**Aspect Ratio:** {entry.aspect_ratio}")
        
        with col2:
            st.write(f"**File Size:** {format_file_size(entry.file_size) if entry.file_size else 'Unknown'}")
            st.write(f"**Resolution:** {entry.megapixels:.1f}MP" if entry.megapixels > 0 else "**Resolution:** Unknown")
            st.write(f"**Upload Date:** {entry.upload_date}")
            if entry.has_gps:
                st.write(f"**Location:** {entry.gps_latitude:.4f}, {entry.gps_longitude:.4f}")
            else:
                st.write("**Location:** No GPS data")
    
    @staticmethod
    def _render_details_tab(entry: ImageEntry):
        """Render detailed information tab."""
        st.write("**Detailed Caption:**")
        st.write(entry.detailed_caption or "No detailed caption")
        
        # Camera settings summary
        settings = format_camera_settings(
            entry.iso_speed, entry.aperture, entry.shutter_speed, entry.focal_length
        )
        st.write(f"**Camera Settings:** {settings}")
        
        if st.checkbox("Show EXIF Data", key=f"exif_{entry.id}"):
            exif_data = safe_json_loads(entry.exif_metadata, {})
            if exif_data:
                st.json(exif_data)
            else:
                st.write("No EXIF data available")

class SearchFilters:
    """Component for advanced search filters."""
    
    @staticmethod
    def render() -> Dict[str, Any]:
        """Render search filters and return selected values."""
        filters = {}
        
        with st.expander("Advanced Filters"):
            col1, col2 = st.columns(2)
            
            with col1:
                filters.update(SearchFilters._render_date_filters())
                filters.update(SearchFilters._render_camera_filters())
                filters.update(SearchFilters._render_technical_filters())
            
            with col2:
                filters.update(SearchFilters._render_dimension_filters())
                filters.update(SearchFilters._render_aperture_filters())
                filters.update(SearchFilters._render_format_filters())
        
        return filters
    
    @staticmethod
    def _render_date_filters() -> Dict[str, Any]:
        """Render date range filters."""
        st.subheader("Date Range")
        date_from = st.date_input("From", value=None)
        date_to = st.date_input("To", value=None)
        
        filters = {}
        if date_from:
            filters['date_from'] = date_from
        if date_to:
            filters['date_to'] = date_to
        
        return filters
    
    @staticmethod
    def _render_camera_filters() -> Dict[str, Any]:
        """Render camera-specific filters."""
        st.subheader("Camera")
        camera_make = st.text_input("Make", placeholder="Canon, Nikon, Sony...")
        camera_model = st.text_input("Model", placeholder="EOS R5, D850...")
        
        filters = {}
        if camera_make:
            filters['camera_make'] = camera_make
        if camera_model:
            filters['camera_model'] = camera_model
        
        return filters
    
    @staticmethod
    def _render_technical_filters() -> Dict[str, Any]:
        """Render technical settings filters."""
        st.subheader("Technical Settings")
        col_iso1, col_iso2 = st.columns(2)
        
        with col_iso1:
            iso_min = st.number_input("Min ISO", min_value=50, value=50, step=50)
        with col_iso2:
            iso_max = st.number_input("Max ISO", min_value=50, value=6400, step=50)
        
        filters = {}
        if iso_min > 50:
            filters['iso_min'] = iso_min
        if iso_max < 6400:
            filters['iso_max'] = iso_max
        
        return filters
    
    @staticmethod
    def _render_dimension_filters() -> Dict[str, Any]:
        """Render image dimension filters."""
        st.subheader("Image Dimensions")
        col_w1, col_w2 = st.columns(2)
        
        with col_w1:
            width_min = st.number_input("Min Width", min_value=1, value=1)
        with col_w2:
            height_min = st.number_input("Min Height", min_value=1, value=1)
        
        filters = {}
        if width_min > 1:
            filters['width_min'] = width_min
        if height_min > 1:
            filters['height_min'] = height_min
        
        return filters
    
    @staticmethod
    def _render_aperture_filters() -> Dict[str, Any]:
        """Render aperture range filters."""
        st.subheader("Aperture Range")
        col_ap1, col_ap2 = st.columns(2)
        
        with col_ap1:
            aperture_min = st.number_input("Min f/", min_value=1.0, value=1.0, step=0.1)
        with col_ap2:
            aperture_max = st.number_input("Max f/", min_value=1.0, value=22.0, step=0.1)
        
        filters = {}
        if aperture_min > 1.0:
            filters['aperture_min'] = aperture_min
        if aperture_max < 22.0:
            filters['aperture_max'] = aperture_max
        
        return filters
    
    @staticmethod
    def _render_format_filters() -> Dict[str, Any]:
        """Render format and label filters."""
        st.subheader("Format & Labels")
        format_filter = st.selectbox("Format", ["", "JPEG", "PNG", "TIFF"])
        manual_labels_filter = st.text_input("Manual Labels (comma-separated)", placeholder="vacation, family...")
        
        filters = {}
        if format_filter:
            filters['format'] = format_filter
        if manual_labels_filter:
            filters['manual_labels'] = manual_labels_filter
        
        return filters

class StatsDisplay:
    """Component for displaying statistics."""
    
    @staticmethod
    def render_sidebar_stats(stats: Dict[str, Any]):
        """Render statistics in the sidebar."""
        st.divider()
        st.subheader("Statistics")
        
        try:
            total_images = stats.get('total_images', 0)
            total_size = stats.get('total_size', 0) / (1024 * 1024)  # Convert to MB
            
            st.metric("Total Images", f"{total_images:,}")
            st.metric("Total Size", f"{total_size:.1f} MB")
            
            # Format distribution
            format_dist = stats.get('format_distribution', {})
            if format_dist:
                st.write("**By Format:**")
                for fmt, count in format_dist.items():
                    st.write(f"• {fmt}: {count}")
            
            # Additional metrics
            gps_count = stats.get('images_with_gps', 0)
            ocr_count = stats.get('images_with_ocr', 0)
            
            if total_images > 0:
                gps_percentage = (gps_count / total_images) * 100
                ocr_percentage = (ocr_count / total_images) * 100
                
                st.write(f"**With GPS:** {gps_percentage:.1f}%")
                st.write(f"**With OCR Text:** {ocr_percentage:.1f}%")
                
        except Exception as e:
            st.error(f"Error loading stats: {e}")
    
    @staticmethod
    def render_summary_metrics(stats: Dict[str, Any]):
        """Render summary metrics in columns."""
        col1, col2, col3, col4 = st.columns(4)
        
        total_images = stats.get('total_images', 0)
        total_size = stats.get('total_size', 0)
        gps_count = stats.get('images_with_gps', 0)
        
        with col1:
            st.metric("Total Images", f"{total_images:,}")
        
        with col2:
            st.metric("Total Storage", format_file_size(total_size))
        
        with col3:
            avg_size = total_size / total_images if total_images > 0 else 0
            st.metric("Avg Image Size", format_file_size(avg_size))
        
        with col4:
            gps_percentage = (gps_count / total_images) * 100 if total_images > 0 else 0
            st.metric("Images with GPS", f"{gps_percentage:.1f}%")

class UploadProgress:
    """Component for upload progress tracking."""
    
    @staticmethod
    def render_progress(current: int, total: int, current_file: str = ""):
        """Render upload progress."""
        progress_bar = st.progress(current / total if total > 0 else 0)
        status_text = st.empty()
        
        if current_file:
            status_text.text(f"Processing {current_file}... ({current}/{total})")
        else:
            status_text.text(f"Upload complete! ({current}/{total})")
        
        return progress_bar, status_text
    
    @staticmethod
    def render_results(results: Dict[str, Any]):
        """Render upload results summary."""
        success_count = results.get('success_count', 0)
        error_count = results.get('error_count', 0)
        successful = results.get('successful', [])
        failed = results.get('failed', [])
        
        if success_count > 0:
            st.success(f"Successfully uploaded {success_count} images")
            
            with st.expander("View successful uploads"):
                for item in successful:
                    st.write(f"• {item['file_name']}")
        
        if error_count > 0:
            st.error(f"Failed to upload {error_count} images")
            
            with st.expander("View failed uploads"):
                for item in failed:
                    st.write(f"• {item['file_name']}: {item['error']}")

class GalleryControls:
    """Component for gallery controls and options."""
    
    @staticmethod
    def render(total_images: int) -> Dict[str, Any]:
        """Render gallery control options."""
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.write(f"**Total Images:** {total_images}")
        
        with col2:
            sort_by = st.selectbox("Sort by", ["Upload Date", "File Name", "Date Taken"])
        
        with col3:
            show_thumbnails = st.checkbox("Thumbnails", value=True)
        
        return {
            'sort_by': sort_by,
            'show_thumbnails': show_thumbnails
        } 