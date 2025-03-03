"""
MediaFileHandler - Utility for handling game media assets in Streamlit applications.

This module provides functionality for loading, caching, and serving various media files 
such as images, sounds, and other assets needed for games.
"""

import os
import base64
from pathlib import Path
from typing import Dict, Union, Optional, List
import streamlit as st
from PIL import Image
import io

class MediaFileHandler:
    """
    Handles loading, caching, and serving media files for Streamlit games.
    
    This class provides methods to:
    - Load images and other media files
    - Cache assets for performance
    - Generate data URLs for embedding in Streamlit
    - Handle different file types with appropriate methods
    """
    
    def __init__(self, base_path: Optional[str] = None):
        """
        Initialize the MediaFileHandler.
        
        Args:
            base_path: Optional base directory for media files. If None, will use default locations.
        """
        # Determine the base path for assets
        if base_path:
            self.base_path = Path(base_path)
        else:
            # Default to a directory called 'assets' in the same directory as the script
            self.base_path = Path(os.path.dirname(os.path.dirname(__file__))) / 'assets'
            
        # Create base path if it doesn't exist
        os.makedirs(self.base_path, exist_ok=True)
        
        # Cache for loaded assets
        self._image_cache: Dict[str, Image.Image] = {}
        self._audio_cache: Dict[str, bytes] = {}
        self._data_url_cache: Dict[str, str] = {}
        
        # List of valid image extensions
        self.valid_image_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']
        
        # List of valid audio extensions
        self.valid_audio_extensions = ['.mp3', '.wav', '.ogg']
    
    def get_image(self, filename: str) -> Optional[Image.Image]:
        """
        Load and return an image file. Uses cache if already loaded.
        
        Args:
            filename: Name of the image file to load
            
        Returns:
            PIL Image object or None if file not found
        """
        # Check cache first
        if filename in self._image_cache:
            return self._image_cache[filename]
        
        # Determine file path
        file_path = self.base_path / 'images' / filename
        if not file_path.exists():
            print(f"Warning: Image file not found: {file_path}")
            return None
        
        try:
            # Load the image
            image = Image.open(file_path)
            # Store in cache
            self._image_cache[filename] = image
            return image
        except Exception as e:
            print(f"Error loading image {filename}: {e}")
            return None
    
    def get_data_url(self, filename: str, file_type: str = None) -> Optional[str]:
        """
        Convert a file to a data URL for embedding in HTML/CSS.
        
        Args:
            filename: Name of the file
            file_type: Optional file type (if None, will be determined from extension)
            
        Returns:
            Data URL string or None if conversion fails
        """
        # Check cache first
        cache_key = f"{filename}_{file_type}"
        if cache_key in self._data_url_cache:
            return self._data_url_cache[cache_key]
        
        # Determine file path and type
        if '/' in filename:
            # If filename includes a subdirectory
            file_path = self.base_path / filename
        else:
            # Try to determine the correct subdirectory
            extension = Path(filename).suffix.lower()
            if not file_type:
                if extension in self.valid_image_extensions:
                    file_path = self.base_path / 'images' / filename
                    file_type = f"image/{extension[1:]}"
                elif extension in self.valid_audio_extensions:
                    file_path = self.base_path / 'audio' / filename
                    file_type = f"audio/{extension[1:]}"
                else:
                    file_path = self.base_path / filename
                    file_type = "application/octet-stream"
            else:
                # Use specified subdirectory
                file_path = self.base_path / file_type / filename
        
        # Check if file exists
        if not file_path.exists():
            print(f"Warning: File not found: {file_path}")
            return None
        
        try:
            # Read file content
            with open(file_path, "rb") as f:
                file_content = f.read()
            
            # Convert to base64 and create data URL
            b64_content = base64.b64encode(file_content).decode()
            data_url = f"data:{file_type};base64,{b64_content}"
            
            # Store in cache
            self._data_url_cache[cache_key] = data_url
            return data_url
        except Exception as e:
            print(f"Error creating data URL for {filename}: {e}")
            return None
    
    def list_files(self, directory: str = None, extensions: List[str] = None) -> List[str]:
        """
        List files in a specific subdirectory with optional extension filtering.
        
        Args:
            directory: Subdirectory to search within the base path
            extensions: List of file extensions to filter (e.g. ['.png', '.jpg'])
            
        Returns:
            List of filenames
        """
        search_path = self.base_path
        if directory:
            search_path = search_path / directory
            
        if not search_path.exists():
            print(f"Warning: Directory not found: {search_path}")
            return []
            
        files = []
        for f in search_path.iterdir():
            if f.is_file():
                if extensions is None or f.suffix.lower() in extensions:
                    files.append(f.name)
        return files
    
    def get_image_as_bytes(self, image: Union[str, Image.Image], format: str = "PNG") -> bytes:
        """
        Convert image to bytes for Streamlit components.
        
        Args:
            image: Either a filename or a PIL Image object
            format: Image format for bytes conversion
            
        Returns:
            Image as bytes
        """
        if isinstance(image, str):
            # Load the image if it's a filename
            img = self.get_image(image)
            if img is None:
                return None
        else:
            img = image
            
        # Convert to bytes
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format=format)
        return img_byte_arr.getvalue()
    
    def create_asset_dirs(self):
        """Create standard asset directories if they don't exist."""
        os.makedirs(self.base_path / 'images', exist_ok=True)
        os.makedirs(self.base_path / 'audio', exist_ok=True)
        os.makedirs(self.base_path / 'fonts', exist_ok=True)
        print(f"Asset directories created at {self.base_path}")

# Initialize singleton instance for global use
if 'media_handler' not in st.session_state:
    st.session_state.media_handler = MediaFileHandler()

def get_media_handler() -> MediaFileHandler:
    """
    Get the global MediaFileHandler instance.
    
    Returns:
        MediaFileHandler: The global media handler instance
    """
    return st.session_state.media_handler
