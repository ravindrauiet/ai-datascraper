import os
import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB_NAME", "pinterest_relove")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def connect_to_mongo():
    """
    Connect to MongoDB using environment variables or defaults.
    Returns (client, db) tuple.
    Includes connection testing and database verification.
    """
    try:
        # Create client with timeout settings
        client = MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=5000,  # 5 second timeout
            connectTimeoutMS=5000,
            socketTimeoutMS=5000
        )
        
        # Test the connection
        client.admin.command('ping')
        logger.info(f"Successfully connected to MongoDB at {MONGO_URI}")
        
        # Get database
        db = client[MONGO_DB]
        
        # Ensure the database and collection exist by creating an index
        # This will create the collection if it doesn't exist
        collection = db.pinterest_pins
        
        # Create indexes for better performance
        try:
            collection.create_index("pin_id", unique=True)
            collection.create_index("created_at")
            collection.create_index("ai_analysis.style_category")
            logger.info(f"Database '{MONGO_DB}' and collection 'pinterest_pins' ready")
        except Exception as e:
            logger.warning(f"Index creation warning: {e}")
        
        return client, db
        
    except ConnectionFailure as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise
    except ServerSelectionTimeoutError as e:
        logger.error(f"MongoDB server selection timeout: {e}")
        logger.error("Please ensure MongoDB is running and accessible")
        raise
    except Exception as e:
        logger.error(f"Unexpected error connecting to MongoDB: {e}")
        raise


def test_connection():
    """
    Test MongoDB connection and return status.
    """
    try:
        client, db = connect_to_mongo()
        
        # Test write operation
        test_doc = {"test": "connection", "timestamp": "2025-01-01T00:00:00Z"}
        result = db.pinterest_pins.insert_one(test_doc)
        
        # Clean up test document
        db.pinterest_pins.delete_one({"_id": result.inserted_id})
        
        client.close()
        logger.info("MongoDB connection test successful")
        return True
        
    except Exception as e:
        logger.error(f"MongoDB connection test failed: {e}")
        return False


def get_collection_stats():
    """
    Get statistics about the pinterest_pins collection.
    """
    try:
        client, db = connect_to_mongo()
        collection = db.pinterest_pins
        
        stats = {
            "total_pins": collection.count_documents({}),
            "database_name": MONGO_DB,
            "collection_name": "pinterest_pins",
            "indexes": list(collection.list_indexes())
        }
        
        client.close()
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get collection stats: {e}")
        return None
