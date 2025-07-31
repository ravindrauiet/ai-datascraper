#!/usr/bin/env python3
"""
Run Advanced Pinterest Scraper
Demonstrates the enhanced scraper with comprehensive AI fashion analysis
"""

import json
import os
from pinterest_scraper import PinterestScraper

def main():
    """Run the advanced Pinterest scraper with comprehensive AI analysis"""
    
    print("🚀 Advanced Pinterest Scraper with Comprehensive AI Analysis")
    print("=" * 70)
    print("This scraper now provides detailed, influencer-style fashion analysis!")
    print("=" * 70)
    
    # Load configuration
    config_path = "config.json"
    if not os.path.exists(config_path):
        print(f"❌ Configuration file not found: {config_path}")
        print("Please ensure config.json exists with your API keys and Pinterest credentials")
        return
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return
    
    # Check if AI is enabled
    api_keys = config.get('gemini_api_keys', [])
    api_key = config.get('gemini_api_key')
    
    if not api_keys and not api_key:
        print("❌ No Gemini API keys found in config.json")
        print("Please add your Gemini API keys to enable advanced AI analysis")
        return
    
    print("✅ Configuration loaded successfully!")
    print(f"🤖 AI Analysis: {'Enabled' if (api_keys or api_key) else 'Disabled'}")
    
    # Initialize scraper
    print("\n🔧 Initializing advanced scraper...")
    scraper = PinterestScraper(config_path)
    
    # Example board URLs (you can modify these)
    board_urls = [
        "https://in.pinterest.com/mohanty2922/office/",
        "https://in.pinterest.com/mohanty2922/y2k-fashion/"
    ]
    
    print(f"\n📋 Target Boards ({len(board_urls)}):")
    for i, url in enumerate(board_urls, 1):
        print(f"   {i}. {url}")
    
    print(f"\n⚙️ Configuration:")
    print(f"   • Max pins per board: {config.get('max_pins_per_board', 100)}")
    print(f"   • Request delay: {config.get('request_delay', 2)}s")
    print(f"   • Max workers: {config.get('max_workers', 3)}")
    print(f"   • Headless mode: {config.get('headless', False)}")
    print(f"   • Undetected Chrome: {config.get('use_undetected_chrome', True)}")
    
    # Confirm before starting
    print(f"\n🎯 What you'll get:")
    print("   • Detailed fashion item detection with taxonomy")
    print("   • Comprehensive style analysis (like Rita Mota example)")
    print("   • Influencer/celebrity style matching")
    print("   • Color psychology and palette analysis")
    print("   • Silhouette and proportion analysis")
    print("   • Fabric and texture analysis")
    print("   • Occasion and versatility analysis")
    print("   • Trend forecasting and timeless elements")
    print("   • Brand aesthetic and price point analysis")
    print("   • Personal style insights and personality traits")
    print("   • Actionable styling recommendations")
    print("   • Sustainability and investment value analysis")
    print("   • Individual analysis reports for each image")
    print("   • MongoDB storage with complete metadata")
    
    print(f"\n📁 Output will be saved to: {config.get('output_dir', 'scraped_data')}")
    
    # Start scraping
    print(f"\n🚀 Starting advanced scraping...")
    print("This may take several minutes depending on the number of pins and AI analysis time.")
    
    try:
        # Run scraping with advanced analysis
        pins = scraper.scrape_boards(board_urls)
        
        if pins:
            print(f"\n✅ Advanced scraping completed successfully!")
            print(f"📊 Total pins processed: {len(pins)}")
            
            # Count pins with AI analysis
            pins_with_ai = sum(1 for pin in pins if pin.ai_analysis)
            print(f"🤖 Pins with AI analysis: {pins_with_ai}")
            
            # Generate training dataset
            print(f"\n📈 Generating training dataset...")
            training_dataset = scraper.generate_training_dataset(pins)
            print(f"✅ Training dataset created with {len(training_dataset.get('samples', []))} samples")
            
            # Show sample analysis
            if pins_with_ai > 0:
                print(f"\n📋 Sample Analysis Preview:")
                sample_pin = next(pin for pin in pins if pin.ai_analysis)
                
                style_analysis = sample_pin.ai_analysis.get("style_analysis", {})
                if style_analysis:
                    aesthetic = style_analysis.get('overall_aesthetic', 'Not specified')
                    category = style_analysis.get('style_category', 'Not specified')
                    influencers = style_analysis.get('influencer_matches', [])
                    
                    print(f"   🎨 Aesthetic: {aesthetic[:100]}...")
                    print(f"   🏷️ Category: {category}")
                    if influencers:
                        print(f"   🌟 Matches: {influencers[0].get('name', 'Unknown')}")
            
            print(f"\n📁 Files created:")
            print(f"   • {config.get('data_file', 'pinterest_data.json')} - Raw scraped data")
            print(f"   • training_dataset.json - ML-ready dataset")
            print(f"   • analysis_report_*.txt - Detailed analysis reports")
            print(f"   • scraper.log - Detailed logs")
            
            print(f"\n🎉 Your advanced fashion analysis system is ready!")
            print(f"💡 You can now use this data for:")
            print(f"   • Training AI fashion models")
            print(f"   • Building style recommendation systems")
            print(f"   • Creating fashion trend analysis")
            print(f"   • Developing personalized styling apps")
            
        else:
            print(f"\n⚠️ No pins were scraped. Check logs for details.")
            
    except KeyboardInterrupt:
        print(f"\n⏹️ Scraping interrupted by user")
    except Exception as e:
        print(f"\n❌ Scraping failed: {e}")
        print("Check logs/scraper.log for detailed error information.")

if __name__ == "__main__":
    main() 