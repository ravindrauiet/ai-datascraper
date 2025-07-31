import logging
from datetime import datetime
from typing import Dict, Any, Optional
from pymongo.errors import DuplicateKeyError
from .db import connect_to_mongo

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def store_metadata_in_mongodb(pin_id: str, source_url: str, metadata: dict, image_path: str) -> bool:
    """
    Stores pin metadata and image path in MongoDB.
    
    Args:
        pin_id: Pinterest pin ID (must be unique)
        source_url: Original Pinterest pin URL
        metadata: AI analysis metadata dictionary
        image_path: Local path to saved image
    
    Returns:
        bool: True if successfully stored, False otherwise
    
    Raises:
        ValueError: If required parameters are missing or invalid
    """
    # Validate inputs
    if not pin_id or not isinstance(pin_id, str):
        raise ValueError("pin_id must be a non-empty string")
    
    if not source_url or not isinstance(source_url, str):
        raise ValueError("source_url must be a non-empty string")
    
    if not metadata or not isinstance(metadata, dict):
        raise ValueError("metadata must be a non-empty dictionary")
    
    if not image_path or not isinstance(image_path, str):
        raise ValueError("image_path must be a non-empty string")
    
    try:
        client, db = connect_to_mongo()
        
        # Create document
        doc = {
            "pin_id": pin_id,
            "source_url": source_url,
            "local_image_path": image_path,
            "ai_analysis": metadata,
            "created_at": datetime.utcnow().isoformat() + "Z"
        }
        
        # Insert document
        result = db.pinterest_pins.insert_one(doc)
        
        if result.inserted_id:
            logger.info(f"Successfully stored pin {pin_id} in MongoDB with ID: {result.inserted_id}")
            client.close()
            return True
        else:
            logger.error(f"Failed to insert pin {pin_id} - no ID returned")
            client.close()
            return False
            
    except DuplicateKeyError:
        logger.warning(f"Pin {pin_id} already exists in database, skipping...")
        client.close()
        return False
        
    except Exception as e:
        logger.error(f"Failed to store pin {pin_id} in MongoDB: {e}")
        try:
            client.close()
        except:
            pass
        raise


def update_pin_metadata(pin_id: str, updates: Dict[str, Any]) -> bool:
    """
    Update existing pin metadata in MongoDB.
    
    Args:
        pin_id: Pinterest pin ID to update
        updates: Dictionary of fields to update
    
    Returns:
        bool: True if successfully updated, False otherwise
    """
    try:
        client, db = connect_to_mongo()
        
        # Add updated timestamp
        updates["updated_at"] = datetime.utcnow().isoformat() + "Z"
        
        result = db.pinterest_pins.update_one(
            {"pin_id": pin_id},
            {"$set": updates}
        )
        
        client.close()
        
        if result.modified_count > 0:
            logger.info(f"Successfully updated pin {pin_id}")
            return True
        else:
            logger.warning(f"No pin found with ID {pin_id} to update")
            return False
            
    except Exception as e:
        logger.error(f"Failed to update pin {pin_id}: {e}")
        return False


def get_pin_by_id(pin_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a pin by its ID from MongoDB.
    
    Args:
        pin_id: Pinterest pin ID to retrieve
    
    Returns:
        dict: Pin document if found, None otherwise
    """
    try:
        client, db = connect_to_mongo()
        
        pin = db.pinterest_pins.find_one({"pin_id": pin_id})
        
        client.close()
        
        if pin:
            # Convert ObjectId to string for JSON serialization
            pin["_id"] = str(pin["_id"])
            logger.info(f"Retrieved pin {pin_id} from database")
            return pin
        else:
            logger.info(f"Pin {pin_id} not found in database")
            return None
            
    except Exception as e:
        logger.error(f"Failed to retrieve pin {pin_id}: {e}")
        return None


def list_recent_pins(limit: int = 10) -> list:
    """
    Get the most recently added pins.
    
    Args:
        limit: Maximum number of pins to return
    
    Returns:
        list: List of recent pin documents
    """
    try:
        client, db = connect_to_mongo()
        
        pins = list(db.pinterest_pins.find()
                   .sort("created_at", -1)
                   .limit(limit))
        
        client.close()
        
        # Convert ObjectIds to strings
        for pin in pins:
            pin["_id"] = str(pin["_id"])
        
        logger.info(f"Retrieved {len(pins)} recent pins")
        return pins
        
    except Exception as e:
        logger.error(f"Failed to retrieve recent pins: {e}")
        return []
