import os
import logging
from uuid import uuid4
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def save_image_locally(image_bytes: bytes, pin_id: Optional[str] = None, folder: str = "images") -> str:
    """
    Saves image bytes to disk under images/{pin_id or uuid}.jpg. Returns relative file path.
    
    Args:
        image_bytes: Raw image data as bytes
        pin_id: Pinterest pin ID (optional, will generate UUID if not provided)
        folder: Folder to save images in (default: "images")
    
    Returns:
        str: Relative path to the saved image file
    
    Raises:
        ValueError: If image_bytes is empty or invalid
        OSError: If file operations fail
    """
    if not image_bytes:
        raise ValueError("image_bytes cannot be empty")
    
    if len(image_bytes) < 100:  # Basic validation for minimum file size
        raise ValueError("image_bytes appears to be too small to be a valid image")
    
    try:
        # Ensure directory exists
        if not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)
            logger.info(f"Created directory: {folder}")
        
        # Generate filename
        if pin_id:
            # Sanitize pin_id to be filesystem-safe
            safe_pin_id = "".join(c for c in str(pin_id) if c.isalnum() or c in "-_")
            fname = f"{safe_pin_id}.jpg"
        else:
            fname = f"{uuid4().hex}.jpg"
        
        fpath = os.path.join(folder, fname)
        
        # Check if file already exists
        if os.path.exists(fpath):
            logger.warning(f"File {fpath} already exists, overwriting...")
        
        # Save image
        with open(fpath, "wb") as f:
            f.write(image_bytes)
        
        # Verify file was written correctly
        if not os.path.exists(fpath) or os.path.getsize(fpath) != len(image_bytes):
            raise OSError(f"Failed to write image file correctly: {fpath}")
        
        logger.info(f"Successfully saved image: {fpath} ({len(image_bytes)} bytes)")
        return fpath
        
    except Exception as e:
        logger.error(f"Failed to save image locally: {e}")
        raise


def get_image_info(image_path: str) -> dict:
    """
    Get information about a saved image file.
    
    Args:
        image_path: Path to the image file
    
    Returns:
        dict: Image file information
    """
    try:
        if not os.path.exists(image_path):
            return {"exists": False, "error": "File not found"}
        
        stat = os.stat(image_path)
        return {
            "exists": True,
            "size_bytes": stat.st_size,
            "created_at": stat.st_ctime,
            "modified_at": stat.st_mtime,
            "absolute_path": os.path.abspath(image_path)
        }
        
    except Exception as e:
        return {"exists": False, "error": str(e)}
