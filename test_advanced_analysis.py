#!/usr/bin/env python3
"""
Test Advanced Fashion Analysis
Demonstrates the enhanced AI fashion analyzer with comprehensive style analysis
"""

import os
import json
from pathlib import Path
from ai_fashion_analyzer import AIFashionAnalyzer
from api_key_manager import create_gemini_manager_from_config

def test_advanced_analysis():
    """Test the advanced comprehensive fashion analysis"""
    
    print("🚀 Advanced Fashion Analysis Test")
    print("=" * 60)
    
    # Load configuration
    config_path = "config.json"
    if not os.path.exists(config_path):
        print(f"❌ Configuration file not found: {config_path}")
        return
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return
    
    # Initialize AI analyzer
    print("🤖 Initializing AI Fashion Analyzer...")
    ai_analyzer = AIFashionAnalyzer.from_config(config)
    
    if not ai_analyzer:
        print("❌ Failed to initialize AI analyzer")
        return
    
    print("✅ AI analyzer initialized successfully!")
    
    # Test with a sample image from scraped data
    images_dir = Path("scraped_data/images")
    if not images_dir.exists():
        print(f"❌ Images directory not found: {images_dir}")
        return
    
    # Find a sample image
    image_files = list(images_dir.glob("*.jpg"))
    if not image_files:
        print("❌ No images found in scraped_data/images/")
        return
    
    test_image = str(image_files[0])
    print(f"🔍 Testing with image: {os.path.basename(test_image)}")
    
    # Perform advanced analysis
    print("\n📊 Performing Advanced Comprehensive Analysis...")
    print("Step 1: Fashion Item Detection")
    print("Step 2: Comprehensive Style Analysis")
    print("Step 3: Influencer Matching & Detailed Insights")
    
    analysis_result = ai_analyzer.advanced_comprehensive_analysis(test_image)
    
    if analysis_result:
        print("\n✅ Advanced analysis completed successfully!")
        
        # Display formatted report
        print("\n" + "=" * 60)
        print("📋 ADVANCED FASHION ANALYSIS REPORT")
        print("=" * 60)
        
        formatted_report = ai_analyzer.format_advanced_output(analysis_result)
        print(formatted_report)
        
        # Save detailed results
        output_file = f"advanced_analysis_{os.path.basename(test_image).split('.')[0]}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_result, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Detailed results saved to: {output_file}")
        
        # Show key insights
        print("\n🎯 KEY INSIGHTS SUMMARY:")
        print("-" * 40)
        
        fashion_items = analysis_result.get("fashion_items", [])
        if fashion_items:
            print(f"👕 Detected {len(fashion_items)} fashion items:")
            for item in fashion_items[:3]:  # Show first 3 items
                print(f"   • {item.get('type', 'Unknown')} ({item.get('category', 'Unknown')})")
        
        style_analysis = analysis_result.get("style_analysis", {})
        if style_analysis:
            # Overall aesthetic
            aesthetic = style_analysis.get('overall_aesthetic', 'Not specified')
            category = style_analysis.get('style_category', 'Not specified')
            print(f"\n🎨 Overall Aesthetic: {aesthetic}")
            print(f"🏷️ Style Category: {category}")
            
            # Influencer matches
            influencers = style_analysis.get('influencer_matches', [])
            if influencers:
                print(f"\n🌟 Top Influencer Match: {influencers[0].get('name', 'Unknown')}")
                print(f"   Reason: {influencers[0].get('similarity_reason', 'Not specified')}")
            
            # Color analysis
            color_analysis = style_analysis.get('color_analysis', {})
            if color_analysis:
                palette = color_analysis.get('palette', 'Not specified')
                psychology = color_analysis.get('color_psychology', 'Not specified')
                print(f"\n🎨 Color Palette: {palette}")
                print(f"🧠 Color Psychology: {psychology}")
            
            # Occasion analysis
            occasion = style_analysis.get('occasion_analysis', {})
            if occasion:
                primary_occasions = occasion.get('primary_occasions', [])
                if primary_occasions:
                    print(f"\n📅 Perfect for: {', '.join(primary_occasions[:3])}")
            
            # Trend analysis
            trend_analysis = style_analysis.get('trend_analysis', {})
            if trend_analysis:
                current_trends = trend_analysis.get('current_trends', [])
                if current_trends:
                    print(f"\n📈 Current Trends: {', '.join(current_trends[:3])}")
            
            # Styling recommendations
            recommendations = style_analysis.get('styling_recommendations', [])
            if recommendations:
                print(f"\n💡 Top Styling Tip: {recommendations[0]}")
        
        print("\n" + "=" * 60)
        print("✅ Advanced analysis test completed successfully!")
        print("This provides the detailed, nuanced analysis you requested!")
        
    else:
        print("❌ Advanced analysis failed")
        return

def test_multiple_images():
    """Test analysis on multiple images to show variety"""
    
    print("\n🔄 Testing Multiple Images...")
    print("=" * 40)
    
    # Load configuration
    with open("config.json", 'r') as f:
        config = json.load(f)
    
    ai_analyzer = AIFashionAnalyzer.from_config(config)
    
    # Test with 3 different images
    images_dir = Path("scraped_data/images")
    image_files = list(images_dir.glob("*.jpg"))[:3]  # First 3 images
    
    for i, image_path in enumerate(image_files, 1):
        print(f"\n📸 Image {i}: {os.path.basename(image_path)}")
        print("-" * 30)
        
        analysis_result = ai_analyzer.advanced_comprehensive_analysis(str(image_path))
        
        if analysis_result:
            style_analysis = analysis_result.get("style_analysis", {})
            
            # Quick summary
            aesthetic = style_analysis.get('overall_aesthetic', 'Not specified')
            category = style_analysis.get('style_category', 'Not specified')
            influencers = style_analysis.get('influencer_matches', [])
            
            print(f"🎨 Aesthetic: {aesthetic[:100]}...")
            print(f"🏷️ Category: {category}")
            if influencers:
                print(f"🌟 Matches: {influencers[0].get('name', 'Unknown')}")
            
            # Save individual report
            report_filename = f"analysis_report_{os.path.basename(image_path).split('.')[0]}.txt"
            formatted_report = ai_analyzer.format_advanced_output(analysis_result)
            with open(report_filename, 'w', encoding='utf-8') as f:
                f.write(formatted_report)
            print(f"💾 Report saved: {report_filename}")
        else:
            print("❌ Analysis failed")

if __name__ == "__main__":
    # Test single image with detailed output
    test_advanced_analysis()
    
    # Test multiple images with summaries
    test_multiple_images()
    
    print("\n🎉 All tests completed!")
    print("\n📋 What you now get:")
    print("• Detailed fashion item detection with taxonomy")
    print("• Comprehensive style analysis like Rita Mota example")
    print("• Influencer/celebrity style matching")
    print("• Color psychology and palette analysis")
    print("• Silhouette and proportion analysis")
    print("• Fabric and texture analysis")
    print("• Occasion and versatility analysis")
    print("• Trend forecasting and timeless elements")
    print("• Brand aesthetic and price point analysis")
    print("• Personal style insights and personality traits")
    print("• Actionable styling recommendations")
    print("• Sustainability and investment value analysis") 