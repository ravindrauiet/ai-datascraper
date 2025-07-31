"""
Pinterest Pin Storage Module

This module provides functionality to store Pinterest pins with their images and AI-generated metadata.

Main functions:
- save_image_locally: Save image bytes to local disk
- store_metadata_in_mongodb: Store pin metadata in MongoDB
- connect_to_mongo: Connect to MongoDB database
- store_complete_pin: Complete workflow to store pin with image and metadata
"""

from .local import save_image_locally, get_image_info
from .db import connect_to_mongo, test_connection, get_collection_stats
from .store import (
    store_metadata_in_mongodb,
    update_pin_metadata,
    get_pin_by_id,
    list_recent_pins
)

__all__ = [
    'save_image_locally',
    'get_image_info',
    'connect_to_mongo',
    'test_connection',
    'get_collection_stats',
    'store_metadata_in_mongodb',
    'update_pin_metadata',
    'get_pin_by_id',
    'list_recent_pins',
    'store_complete_pin'
]


def store_complete_pin(image_bytes: bytes, pin_id: str, source_url: str, metadata: dict, folder: str = "storage/images") -> dict:
    """
    Complete workflow to store a Pinterest pin with image and metadata.
    
    Args:
        image_bytes: Raw image data as bytes
        pin_id: Pinterest pin ID
        source_url: Original Pinterest pin URL
        metadata: AI analysis metadata dictionary
        folder: Folder to save images in
    
    Returns:
        dict: Result with success status and details
    """
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        # Save image locally
        image_path = save_image_locally(image_bytes, pin_id, folder)
        logger.info(f"Image saved to: {image_path}")
        
        # Store metadata in MongoDB
        success = store_metadata_in_mongodb(pin_id, source_url, metadata, image_path)
        
        if success:
            return {
                "success": True,
                "pin_id": pin_id,
                "image_path": image_path,
                "message": "Pin stored successfully"
            }
        else:
            return {
                "success": False,
                "pin_id": pin_id,
                "image_path": image_path,
                "message": "Image saved but metadata storage failed"
            }
            
    except Exception as e:
        logger.error(f"Failed to store complete pin {pin_id}: {e}")
        return {
            "success": False,
            "pin_id": pin_id,
            "error": str(e),
            "message": "Failed to store pin"
        }
