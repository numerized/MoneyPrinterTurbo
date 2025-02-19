import os
import streamlit as st
from loguru import logger
import tempfile
from moviepy.editor import VideoFileClip
from pathlib import Path
from typing import List

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

@st.cache_data(ttl=3600)
def get_video_data(preview_path):
    """Cache the video data to prevent reloading"""
    with open(preview_path, 'rb') as video_file:
        return video_file.read()

def download_and_preview_videos(task_id: str, params: VideoParams, search_terms: List[str]):
    """Download videos and show previews for selection"""
    st.write("### Downloading and Previewing Videos")
    
    # Create task directory for storing videos
    task_dir = utils.task_dir(task_id)
    if not os.path.exists(task_dir):
        os.makedirs(task_dir)
    
    # Initialize session states if not already present
    if 'downloaded_video_paths' not in st.session_state:
        logger.info("First run - downloading videos...")
        # Download videos with task directory as save location
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
            
        logger.info(f"Downloaded {len(downloaded_videos)} videos")
        st.session_state.downloaded_video_paths = downloaded_videos
        st.session_state.video_selections = {video: True for video in downloaded_videos}
        st.session_state.preview_paths = {}
    
    # Display videos for selection
    st.write("### Select Videos to Use")
    st.write("Choose which videos you want to include in the final video:")
    
    # Add refresh button
    col1, col2 = st.columns([8, 1])
    with col2:
        if st.button("🔄 Refresh Videos"):
            st.session_state.video_container = None
    
    # Create a form for the video selection
    with st.form(key="video_selection_form"):
        # Create a container for the video grid
        if 'video_container' not in st.session_state:
            st.session_state.video_container = st.container()
        
        # Display videos in the container
        with st.session_state.video_container:
            # Create columns for the grid display (4 columns)
            cols = st.columns(4)
            
            # Display all videos with their selection checkboxes
            for idx, video_path in enumerate(st.session_state.downloaded_video_paths):
                col_idx = idx % 4
                with cols[col_idx]:
                    st.markdown(f"#### Video {idx + 1}")
                    
                    # Get or create video preview
                    if video_path not in st.session_state.preview_paths:
                        preview_path = create_video_preview(video_path)
                        if preview_path and os.path.exists(preview_path):
                            st.session_state.preview_paths[video_path] = preview_path
                    
                    # Display video if we have a preview path
                    if video_path in st.session_state.preview_paths:
                        preview_path = st.session_state.preview_paths[video_path]
                        if os.path.exists(preview_path):
                            # Use cached video data
                            video_data = get_video_data(preview_path)
                            st.video(video_data)
                            
                            # Add checkbox below video
                            checkbox_key = f"video_select_{idx}"
                            prev_state = st.session_state.video_selections.get(video_path, True)
                            new_state = st.checkbox("Use this video", key=checkbox_key, value=prev_state)
                            
                            if new_state != prev_state:
                                st.session_state.video_selections[video_path] = new_state
                                logger.info(f"Video {idx + 1} selection changed: {prev_state} -> {new_state}")
                        else:
                            st.error(f"Preview file missing for video {idx + 1}")
                    else:
                        st.error(f"Could not create preview for video {idx + 1}")
        
        # Add submit button at the bottom of the form
        submitted = st.form_submit_button("Confirm Selection")
        
    # Handle form submission
    if submitted:
        selected_videos = [
            path for path, selected in st.session_state.video_selections.items()
            if selected
        ]
        
        if not selected_videos:
            st.error("Please select at least one video")
            logger.warning("No videos selected for confirmation")
            return None
        
        logger.info(f"Confirmed selection of {len(selected_videos)} videos")
        return selected_videos
    
    return None
