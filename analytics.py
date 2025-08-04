import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from typing import List, Dict, Any
import json
import numpy as np

from database.models import ImageEntry
from core.utils import safe_json_loads, format_file_size

def get_analytics_data(entries: List[ImageEntry]) -> Dict[str, Any]:
    """
    Extract analytics data from image entries
    """
    if not entries:
        return {}
    
    data = {
        'total_images': len(entries),
        'total_size': sum(entry.file_size or 0 for entry in entries),
        'formats': Counter(),
        'cameras': Counter(),
        'upload_dates': [],
        'dimensions': [],
        'iso_values': [],
        'aperture_values': [],
        'focal_lengths': [],
        'ai_labels': Counter(),
        'manual_labels': Counter(),
        'date_taken_values': [],
        'has_gps': 0,
        'has_ocr_text': 0
    }
    
    for entry in entries:
        # Format distribution
        if entry.format:
            data['formats'][entry.format] += 1
        
        # Camera distribution
        camera = f"{entry.camera_make} {entry.camera_model}".strip()
        if camera:
            data['cameras'][camera] += 1
        
        # Upload dates
        if entry.upload_date:
            data['upload_dates'].append(entry.upload_date)
        
        # Dimensions
        if entry.width and entry.height:
            data['dimensions'].append((entry.width, entry.height, entry.width * entry.height))
        
        # Camera settings
        if entry.iso_speed:
            data['iso_values'].append(entry.iso_speed)
        if entry.aperture:
            data['aperture_values'].append(entry.aperture)
        if entry.focal_length:
            data['focal_length'].append(entry.focal_length)
        
        # Date taken
        if entry.date_taken:
            data['date_taken_values'].append(entry.date_taken)
        
        # GPS and OCR
        if entry.gps_latitude and entry.gps_longitude:
            data['has_gps'] += 1
        if entry.ocr_text and entry.ocr_text.strip():
            data['has_ocr_text'] += 1
        
        # Labels
        ai_labels = safe_json_loads(entry.ai_labels, [])
        manual_labels = safe_json_loads(entry.manual_labels, [])
        
        if isinstance(ai_labels, list):
            for label in ai_labels:
                data['ai_labels'][label] += 1
        
        if isinstance(manual_labels, list):
            for label in manual_labels:
                data['manual_labels'][label] += 1
    
    return data

def create_format_distribution_chart(data: Dict[str, Any]):
    """Create a pie chart showing format distribution"""
    if not data.get('formats'):
        return None
    
    formats = dict(data['formats'])
    fig = px.pie(
        values=list(formats.values()),
        names=list(formats.keys()),
        title="Image Format Distribution"
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    return fig

def create_upload_timeline_chart(data: Dict[str, Any]):
    """Create a timeline chart of uploads"""
    if not data.get('upload_dates'):
        return None
    
    # Group by date
    upload_dates = data['upload_dates']
    date_counts = Counter(date.date() for date in upload_dates)
    
    dates = sorted(date_counts.keys())
    counts = [date_counts[date] for date in dates]
    
    fig = px.bar(
        x=dates,
        y=counts,
        title="Upload Timeline",
        labels={'x': 'Date', 'y': 'Number of Images'}
    )
    fig.update_layout(xaxis_title="Date", yaxis_title="Images Uploaded")
    return fig

def create_camera_usage_chart(data: Dict[str, Any]):
    """Create a bar chart of camera usage"""
    if not data.get('cameras'):
        return None
    
    cameras = dict(data['cameras'].most_common(10))  # Top 10 cameras
    
    fig = px.bar(
        x=list(cameras.values()),
        y=list(cameras.keys()),
        orientation='h',
        title="Top Cameras Used",
        labels={'x': 'Number of Images', 'y': 'Camera'}
    )
    fig.update_layout(height=400)
    return fig

def create_technical_settings_charts(data: Dict[str, Any]):
    """Create charts for camera technical settings"""
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=["ISO Distribution", "Aperture Distribution", 
                       "Focal Length Distribution", "Image Dimensions"],
        specs=[[{"type": "histogram"}, {"type": "histogram"}],
               [{"type": "histogram"}, {"type": "scatter"}]]
    )
    
    # ISO distribution
    if data.get('iso_values'):
        fig.add_trace(
            go.Histogram(x=data['iso_values'], name="ISO", nbinsx=20),
            row=1, col=1
        )
    
    # Aperture distribution
    if data.get('aperture_values'):
        fig.add_trace(
            go.Histogram(x=data['aperture_values'], name="Aperture", nbinsx=15),
            row=1, col=2
        )
    
    # Focal length distribution
    if data.get('focal_lengths'):
        fig.add_trace(
            go.Histogram(x=data['focal_lengths'], name="Focal Length", nbinsx=20),
            row=2, col=1
        )
    
    # Image dimensions scatter
    if data.get('dimensions'):
        widths = [d[0] for d in data['dimensions']]
        heights = [d[1] for d in data['dimensions']]
        megapixels = [d[2] / 1_000_000 for d in data['dimensions']]
        
        fig.add_trace(
            go.Scatter(
                x=widths, y=heights, 
                mode='markers',
                marker=dict(size=8, color=megapixels, colorscale='Viridis', showscale=True),
                name="Dimensions",
                text=[f"{w}×{h}<br>{mp:.1f}MP" for w, h, mp in zip(widths, heights, megapixels)],
                hovertemplate="Width: %{x}<br>Height: %{y}<br>%{text}<extra></extra>"
            ),
            row=2, col=2
        )
    
    fig.update_layout(height=600, showlegend=False, title_text="Technical Settings Analysis")
    return fig

def create_labels_word_cloud_data(data: Dict[str, Any]):
    """Prepare data for word cloud visualization"""
    # Combine AI and manual labels
    all_labels = Counter()
    
    if data.get('ai_labels'):
        all_labels.update(data['ai_labels'])
    
    if data.get('manual_labels'):
        all_labels.update(data['manual_labels'])
    
    # Return top labels for visualization
    return dict(all_labels.most_common(50))

def create_top_labels_chart(data: Dict[str, Any]):
    """Create a bar chart of most common labels"""
    labels_data = create_labels_word_cloud_data(data)
    
    if not labels_data:
        return None
    
    # Take top 20 for readability
    top_labels = dict(list(labels_data.items())[:20])
    
    fig = px.bar(
        x=list(top_labels.values()),
        y=list(top_labels.keys()),
        orientation='h',
        title="Most Common Image Labels",
        labels={'x': 'Frequency', 'y': 'Label'}
    )
    fig.update_layout(height=500)
    return fig

def create_monthly_upload_heatmap(data: Dict[str, Any]):
    """Create a heatmap of uploads by month and year"""
    if not data.get('upload_dates'):
        return None
    
    # Create a matrix of year-month data
    monthly_data = defaultdict(lambda: defaultdict(int))
    
    for date in data['upload_dates']:
        year = date.year
        month = date.month
        monthly_data[year][month] += 1
    
    if not monthly_data:
        return None
    
    # Convert to matrix for heatmap
    years = sorted(monthly_data.keys())
    months = list(range(1, 13))
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    z_data = []
    for year in years:
        row = [monthly_data[year][month] for month in months]
        z_data.append(row)
    
    fig = go.Figure(data=go.Heatmap(
        z=z_data,
        x=month_names,
        y=years,
        colorscale='Blues',
        hoverongaps=False
    ))
    
    fig.update_layout(
        title="Upload Activity Heatmap",
        xaxis_title="Month",
        yaxis_title="Year"
    )
    
    return fig

def display_summary_metrics(data: Dict[str, Any]):
    """Display key summary metrics"""
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Images", 
            f"{data.get('total_images', 0):,}"
        )
    
    with col2:
        total_size = data.get('total_size', 0)
        st.metric(
            "Total Storage", 
            format_file_size(total_size)
        )
    
    with col3:
        avg_size = total_size / data.get('total_images', 1) if data.get('total_images') else 0
        st.metric(
            "Avg Image Size",
            format_file_size(avg_size)
        )
    
    with col4:
        gps_percentage = (data.get('has_gps', 0) / data.get('total_images', 1)) * 100 if data.get('total_images') else 0
        st.metric(
            "Images with GPS",
            f"{gps_percentage:.1f}%"
        )

def create_comprehensive_analytics_dashboard(entries: List[ImageEntry]):
    """Create a comprehensive analytics dashboard"""
    
    if not entries:
        st.info("No images to analyze yet.")
        return
    
    # Get analytics data
    data = get_analytics_data(entries)
    
    # Summary metrics
    st.subheader("Summary")
    display_summary_metrics(data)
    
    st.divider()
    
    # Charts in tabs
    tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Camera Data", "Labels", "Timeline"])
    
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            format_chart = create_format_distribution_chart(data)
            if format_chart:
                st.plotly_chart(format_chart, use_container_width=True)
            else:
                st.info("No format data available")
        
        with col2:
            camera_chart = create_camera_usage_chart(data)
            if camera_chart:
                st.plotly_chart(camera_chart, use_container_width=True)
            else:
                st.info("No camera data available")
    
    with tab2:
        technical_chart = create_technical_settings_charts(data)
        if technical_chart:
            st.plotly_chart(technical_chart, use_container_width=True)
        else:
            st.info("No technical data available")
    
    with tab3:
        labels_chart = create_top_labels_chart(data)
        if labels_chart:
            st.plotly_chart(labels_chart, use_container_width=True)
        else:
            st.info("No label data available")
        
        # Additional metrics for labels
        if data.get('ai_labels') or data.get('manual_labels'):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Unique AI Labels", len(data.get('ai_labels', {})))
            with col2:
                st.metric("Unique Manual Labels", len(data.get('manual_labels', {})))
            with col3:
                ocr_percentage = (data.get('has_ocr_text', 0) / data.get('total_images', 1)) * 100 if data.get('total_images') else 0
                st.metric("Images with Text", f"{ocr_percentage:.1f}%")
    
    with tab4:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            upload_chart = create_upload_timeline_chart(data)
            if upload_chart:
                st.plotly_chart(upload_chart, use_container_width=True)
            else:
                st.info("No upload timeline data available")
        
        with col2:
            heatmap_chart = create_monthly_upload_heatmap(data)
            if heatmap_chart:
                st.plotly_chart(heatmap_chart, use_container_width=True)
            else:
                st.info("No monthly data available")

class AnalyticsService:
    """Service class for handling analytics operations and rendering."""
    
    def __init__(self):
        self.image_service = None
        try:
            from services.image_service import image_service
            self.image_service = image_service
        except ImportError:
            pass
    
    def _get_entries(self):
        """Get all image entries for analytics."""
        if self.image_service:
            return self.image_service.get_all_images()
        return []
    
    def render_upload_timeline(self):
        """Render upload timeline chart."""
        entries = self._get_entries()
        if not entries:
            st.info("No images uploaded yet.")
            return
        
        data = get_analytics_data(entries)
        fig = create_upload_timeline_chart(data)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No upload data available.")
    
    def render_activity_heatmap(self):
        """Render monthly upload activity heatmap."""
        entries = self._get_entries()
        if not entries:
            return
        
        data = get_analytics_data(entries)
        fig = create_monthly_upload_heatmap(data)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Not enough data for heatmap visualization.")
    
    def render_camera_distribution(self):
        """Render camera usage distribution chart."""
        entries = self._get_entries()
        if not entries:
            st.info("No camera data available.")
            return
        
        data = get_analytics_data(entries)
        fig = create_camera_usage_chart(data)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No camera metadata found.")
    
    def render_technical_analysis(self):
        """Render technical camera settings analysis."""
        entries = self._get_entries()
        if not entries:
            return
        
        data = get_analytics_data(entries)
        fig = create_technical_settings_charts(data)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No technical metadata available.")
    
    def render_label_frequency(self):
        """Render label frequency analysis."""
        entries = self._get_entries()
        if not entries:
            st.info("No labels available.")
            return
        
        data = get_analytics_data(entries)
        
        # AI Labels
        if data.get('ai_labels'):
            st.subheader("🤖 AI Generated Labels")
            fig = create_top_labels_chart(data)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
        
        # Manual Labels
        if data.get('manual_labels'):
            st.subheader("👤 Manual Labels")
            manual_data = {'ai_labels': data['manual_labels']}
            fig = create_top_labels_chart(manual_data)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
    
    def render_keyword_trends(self):
        """Render keyword and label trends."""
        entries = self._get_entries()
        if not entries:
            return
        
        data = get_analytics_data(entries)
        word_cloud_data = create_labels_word_cloud_data(data)
        
        if word_cloud_data:
            st.subheader("🏷️ Label Word Cloud Data")
            st.json(word_cloud_data)
        else:
            st.info("No label data available for trends.")
    
    def render_gps_coverage(self):
        """Render GPS coverage information."""
        entries = self._get_entries()
        if not entries:
            return
        
        data = get_analytics_data(entries)
        gps_count = data.get('has_gps', 0)
        total_count = data.get('total_images', 0)
        
        if total_count > 0:
            gps_percentage = (gps_count / total_count) * 100
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Images with GPS", gps_count)
            with col2:
                st.metric("GPS Coverage", f"{gps_percentage:.1f}%")
        else:
            st.info("No GPS data available.")
    
    def render_storage_analysis(self):
        """Render storage and file format analysis."""
        entries = self._get_entries()
        if not entries:
            return
        
        data = get_analytics_data(entries)
        
        # Format distribution
        if data.get('formats'):
            fig = create_format_distribution_chart(data)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
        
        # Storage metrics
        total_size = data.get('total_size', 0)
        total_images = data.get('total_images', 0)
        
        if total_images > 0:
            avg_size = total_size / total_images
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Storage", format_file_size(total_size))
            with col2:
                st.metric("Average File Size", format_file_size(avg_size))
            with col3:
                st.metric("Total Images", total_images) 