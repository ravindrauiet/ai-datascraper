#!/usr/bin/env python3
"""
View latest scraped data from MongoDB to see the new enhanced AI analysis format
"""

import json
from storage.db import get_database
from storage.store import get_collection_stats
from datetime import datetime
import sys

def view_latest_pins(limit=5):
    """View the latest pins with enhanced AI analysis"""
    try:
        db = get_database()
        collection = db.pinterest_pins
        
        # Get latest pins
        latest_pins = list(collection.find().sort("scraped_at", -1).limit(limit))
        
        if not latest_pins:
            print("❌ No pins found in MongoDB")
            return
        
        print(f"🔍 Found {len(latest_pins)} latest pins with enhanced AI analysis:")
        print("=" * 80)
        
        for i, pin in enumerate(latest_pins, 1):
            print(f"\n📌 PIN {i}: {pin.get('title', 'Untitled')}")
            print(f"🆔 ID: {pin.get('pin_id', 'Unknown')}")
            print(f"📅 Scraped: {pin.get('scraped_at', 'Unknown')}")
            
            # Show AI analysis
            ai_analysis = pin.get('ai_analysis', {})
            if ai_analysis:
                print(f"\n🤖 AI ANALYSIS:")
                print(f"📝 Description: {ai_analysis.get('description', 'N/A')[:100]}...")
                
                # Show fashion items
                fashion_items = ai_analysis.get('fashion_items', [])
                if fashion_items:
                    print(f"👗 Fashion Items ({len(fashion_items)}):")
                    for item in fashion_items[:3]:  # Show first 3
                        if isinstance(item, dict):
                            print(f"   - {item.get('type', 'Unknown')} ({item.get('color', 'Unknown')} {item.get('material', 'Unknown')})")
                
                # Show style analysis
                style_analysis = ai_analysis.get('style_analysis', {})
                if style_analysis:
                    print(f"🎨 Style: {style_analysis.get('style_category', 'N/A')}")
                    print(f"📊 Trend Score: {style_analysis.get('trend_score', 'N/A')}")
                
                # Show color analysis
                color_analysis = ai_analysis.get('color_analysis', {})
                if color_analysis:
                    colors = color_analysis.get('dominant_colors', [])
                    print(f"🌈 Colors: {', '.join(colors[:3])}")
                
                # Show other key fields
                print(f"🏷️  Tags: {', '.join(ai_analysis.get('tags', [])[:5])}")
                print(f"👤 Gender: {ai_analysis.get('gender', 'N/A')}")
                print(f"🎯 Occasion: {ai_analysis.get('occasion', 'N/A')}")
                
                # Show brand suggestions
                brands = ai_analysis.get('brand_suggestions', [])
                if brands:
                    print(f"🛍️  Brand Suggestions: {', '.join(brands[:3])}")
                
                # Show improvement suggestions
                improvements = ai_analysis.get('improvement_suggestions', '')
                if improvements:
                    print(f"💡 Suggestions: {improvements[:80]}...")
                
            print("-" * 80)
        
    except Exception as e:
        print(f"❌ Error accessing MongoDB: {e}")
        print("💡 Make sure MongoDB is running and accessible")

def show_collection_stats():
    """Show collection statistics"""
    try:
        stats = get_collection_stats()
        print(f"📊 COLLECTION STATISTICS:")
        print(f"Total pins: {stats.get('total_documents', 0)}")
        print(f"Latest update: {stats.get('latest_document', {}).get('scraped_at', 'Unknown')}")
        print(f"Has AI analysis: {stats.get('documents_with_ai_analysis', 0)}")
        
    except Exception as e:
        print(f"❌ Error getting stats: {e}")

def export_latest_to_json(filename="latest_enhanced_data.json", limit=3):
    """Export latest pins to JSON file to see full structure"""
    try:
        db = get_database()
        collection = db.pinterest_pins
        
        # Get latest pins
        latest_pins = list(collection.find().sort("scraped_at", -1).limit(limit))
        
        if not latest_pins:
            print("❌ No pins found to export")
            return
        
        # Convert ObjectId to string for JSON serialization
        for pin in latest_pins:
            if '_id' in pin:
                pin['_id'] = str(pin['_id'])
        
        # Export to JSON
        with open(filename, 'w') as f:
            json.dump(latest_pins, f, indent=2, default=str)
        
        print(f"✅ Exported {len(latest_pins)} latest pins to {filename}")
        print(f"📁 You can now view the full enhanced AI analysis structure!")
        
    except Exception as e:
        print(f"❌ Error exporting data: {e}")

def main():
    print("🔍 MONGODB DATA VIEWER - Enhanced AI Analysis")
    print("=" * 60)
    
    # Show collection stats
    show_collection_stats()
    
    # View latest pins
    view_latest_pins(limit=5)
    
    # Export to JSON for detailed viewing
    export_latest_to_json(limit=3)
    
    print("\n✅ Data viewing complete!")
    print("💡 Check 'latest_enhanced_data.json' for full AI analysis structure")

if __name__ == "__main__":
    main()
