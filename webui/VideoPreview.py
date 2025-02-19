import os
import streamlit as st
from loguru import logger
import tempfile
from moviepy.editor import VideoFileClip
from pathlib import Path

from app.models.schema import VideoParams
from app.services import material
from app.utils import utils

def create_video_preview(video_path, max_duration=5):
    """Create a preview of the video and return the path to the preview file"""
    try:
        # Create a preview directory if it doesn't exist
        preview_dir = Path(tempfile.gettempdir()) / "video_previews"
        preview_dir.mkdir(exist_ok=True)
        
        # Create a short preview filename based on the original
        preview_name = f"preview_{Path(video_path).stem[:30]}.mp4"
        preview_path = preview_dir / preview_name
        
        # Skip if preview already exists
        if preview_path.exists():
            return str(preview_path)
        
        with VideoFileClip(video_path) as clip:
            # Take first max_duration seconds
            preview_clip = clip.subclip(0, min(clip.duration, max_duration))
            
            # Create the preview file
            preview_clip.write_videofile(
                str(preview_path),
                codec='libx264',
                audio=False,
                preset='ultrafast',
                logger=None
            )
            
            return str(preview_path)
    except Exception as e:
        logger.error(f"Error creating preview for {video_path}: {str(e)}")
        return None

def download_and_preview_videos(task_id: str, params: VideoParams, search_terms: list):
    """Download videos and show previews for selection"""
    st.write("### Downloading and Previewing Videos")
    
    # Download videos
    downloaded_videos = material.download_videos(
        task_id=task_id,
        search_terms=search_terms,
        source=params.video_source,
        video_aspect=params.video_aspect,
        video_contact_mode=params.video_concat_mode,
        audio_duration=300,  # Download more videos than needed for selection
        max_clip_duration=params.video_clip_duration,
    )
    
    if not downloaded_videos:
        st.error("Failed to download videos. Please check your internet connection and API keys.")
        return None
    
    # Create a dictionary to store video selections
    if 'video_selections' not in st.session_state:
        st.session_state.video_selections = {}
    
    # Display videos for selection
    st.write("### Select Videos to Use")
    st.write("Choose which videos you want to include in the final video:")
    
    # Create columns for the grid display
    cols = st.columns(3)
    
    for idx, video_path in enumerate(downloaded_videos):
        col_idx = idx % 3
        with cols[col_idx]:
            # Create unique key for checkbox
            checkbox_key = f"video_select_{idx}"
            
            # Show video preview
            preview_path = create_video_preview(video_path)
            if preview_path and os.path.exists(preview_path):
                # Use streamlit's native video player
                with open(preview_path, 'rb') as video_file:
                    video_bytes = video_file.read()
                st.video(video_bytes)
                
                # Store selection in session state
                st.session_state.video_selections[video_path] = st.checkbox(
                    "Use this video",
                    key=checkbox_key,
                    value=st.session_state.video_selections.get(video_path, True)
                )
            else:
                st.error(f"Could not preview video {idx + 1}")
    
    # Add a button to confirm selection
    if st.button("Confirm Selection"):
        # Get selected videos
        selected_videos = [
            path for path, selected in st.session_state.video_selections.items()
            if selected
        ]
        
        if not selected_videos:
            st.error("Please select at least one video")
            return None
            
        return selected_videos
        
    return None
