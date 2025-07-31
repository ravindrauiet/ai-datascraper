#!/usr/bin/env python3
"""
Pinterest Pin Storage Demo

This script demonstrates how to store Pinterest pins with images and AI metadata.
It includes comprehensive testing and verification of the storage system.
"""

import requests
import logging
import sys
from storage import (
    store_complete_pin,
    test_connection,
    get_collection_stats,
    get_pin_by_id,
    list_recent_pins
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Example data (replace with real data in actual use)
pin_id = "87923487238472"
source_url = "https://www.pinterest.com/pin/87923487238472"
image_url = "https://i.pinimg.com/originals/2a/3e/4f/2a3e4f3c8e2e7c5e3c7e4d3e4f3e4c7e.jpg"  # Example image
ai_analysis = {
    "description": "A modern streetwear outfit with oversized hoodie and chunky sneakers.",
    "tags": [
        "streetwear", "oversized hoodie", "chunky sneakers", "urban fashion", "2025 trend"
    ],
    "dominant_colors": ["#1e1e1e", "#fafafa", "#c0c0c0"],
    "season": "Fall/Winter 2025",
    "style_category": "Urban Casual",
    "gender": "Unisex",
    "ai_trend_score": 0.89,
    "trend_analysis": {
        "match_with_latest_trend": True,
        "inspired_by": ["Balenciaga", "Fear of God"],
        "fashion_cycle_stage": "peak",
        "social_popularity_score": 92,
        "predicted_lifespan_months": 6
    },
    "detected_objects": ["hoodie", "sneakers", "jeans"],
    "ai_model_version": "v2.3.1"
}


def test_mongodb_connection():
    """Test MongoDB connection and display status."""
    print("\n" + "="*50)
    print("TESTING MONGODB CONNECTION")
    print("="*50)
    
    try:
        if test_connection():
            print("✅ MongoDB connection successful!")
            
            # Get collection stats
            stats = get_collection_stats()
            if stats:
                print(f"📊 Database: {stats['database_name']}")
                print(f"📊 Collection: {stats['collection_name']}")
                print(f"📊 Total pins: {stats['total_pins']}")
                print(f"📊 Indexes: {len(stats['indexes'])}")
            
            return True
        else:
            print("❌ MongoDB connection failed!")
            return False
            
    except Exception as e:
        print(f"❌ MongoDB connection error: {e}")
        return False


def download_and_store_pin():
    """Download image and store complete pin."""
    print("\n" + "="*50)
    print("DOWNLOADING AND STORING PIN")
    print("="*50)
    
    try:
        # Download image
        print(f"📥 Downloading image from: {image_url}")
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()
        image_bytes = response.content
        print(f"✅ Downloaded {len(image_bytes)} bytes")
        
        # Store complete pin
        result = store_complete_pin(
            image_bytes=image_bytes,
            pin_id=pin_id,
            source_url=source_url,
            metadata=ai_analysis,
            folder="storage/images"
        )
        
        if result["success"]:
            print(f"✅ {result['message']}")
            print(f"📁 Image saved to: {result['image_path']}")
            print(f"🆔 Pin ID: {result['pin_id']}")
            return True
        else:
            print(f"❌ {result['message']}")
            if "error" in result:
                print(f"❌ Error: {result['error']}")
            return False
            
    except requests.RequestException as e:
        print(f"❌ Failed to download image: {e}")
        return False
    except Exception as e:
        print(f"❌ Failed to store pin: {e}")
        return False


def verify_stored_data():
    """Verify that the pin was stored correctly."""
    print("\n" + "="*50)
    print("VERIFYING STORED DATA")
    print("="*50)
    
    try:
        # Retrieve the stored pin
        pin = get_pin_by_id(pin_id)
        
        if pin:
            print(f"✅ Pin {pin_id} found in database!")
            print(f"📅 Created at: {pin['created_at']}")
            print(f"🔗 Source URL: {pin['source_url']}")
            print(f"📁 Image path: {pin['local_image_path']}")
            print(f"🎨 Style category: {pin['ai_analysis'].get('style_category', 'N/A')}")
            print(f"🏷️  Tags: {', '.join(pin['ai_analysis'].get('tags', [])[:3])}...")
            return True
        else:
            print(f"❌ Pin {pin_id} not found in database!")
            return False
            
    except Exception as e:
        print(f"❌ Failed to verify stored data: {e}")
        return False


def show_recent_pins():
    """Display recently stored pins."""
    print("\n" + "="*50)
    print("RECENT PINS IN DATABASE")
    print("="*50)
    
    try:
        pins = list_recent_pins(limit=5)
        
        if pins:
            print(f"📋 Found {len(pins)} recent pins:")
            for i, pin in enumerate(pins, 1):
                print(f"\n{i}. Pin ID: {pin['pin_id']}")
                print(f"   Created: {pin['created_at']}")
                print(f"   Style: {pin['ai_analysis'].get('style_category', 'N/A')}")
                print(f"   Image: {pin['local_image_path']}")
        else:
            print("📋 No pins found in database")
            
    except Exception as e:
        print(f"❌ Failed to retrieve recent pins: {e}")


def main():
    """Main demo function."""
    print("🎯 Pinterest Pin Storage Demo")
    print("This demo will test the complete pin storage workflow.")
    
    # Test MongoDB connection
    if not test_mongodb_connection():
        print("\n❌ Cannot proceed without MongoDB connection.")
        print("Please ensure MongoDB is running and accessible.")
        sys.exit(1)
    
    # Download and store pin
    if download_and_store_pin():
        # Verify stored data
        verify_stored_data()
        
        # Show recent pins
        show_recent_pins()
        
        print("\n" + "="*50)
        print("✅ DEMO COMPLETED SUCCESSFULLY!")
        print("="*50)
        print("\n📋 Summary:")
        print("• MongoDB connection tested")
        print("• Image downloaded and saved locally")
        print("• Metadata stored in MongoDB")
        print("• Data verification completed")
        print("\n🎉 Your Pinterest pin storage system is working correctly!")
        
    else:
        print("\n❌ Demo failed. Please check the error messages above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
