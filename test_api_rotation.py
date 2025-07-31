#!/usr/bin/env python3
"""
Test script for Gemini API key rotation functionality
Demonstrates how the API manager handles rate limits and switches between keys
"""

import os
import sys
import json
import time
import logging
from pathlib import Path
from PIL import Image
from api_key_manager import GeminiAPIManager
from ai_fashion_analyzer import AIFashionAnalyzer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_api_keys_from_config():
    """Load API keys from config.json file"""
    config_path = Path("config.json")
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                api_keys = config.get('gemini_api_keys', [])
                # Filter out placeholder keys
                real_keys = [key for key in api_keys if not key.startswith('your_api_key')]
                return real_keys
        except Exception as e:
            print(f"❌ Error reading config.json: {e}")
    return []

def get_available_api_keys():
    """Get API keys from environment variables or config.json"""
    # Try environment variables first
    env_keys = os.getenv('GEMINI_API_KEYS')
    if env_keys:
        return [key.strip() for key in env_keys.split(',') if key.strip()]
    
    # Try single key from environment
    single_key = os.getenv('GEMINI_API_KEY')
    if single_key:
        return [single_key]
    
    # Try config.json
    config_keys = load_api_keys_from_config()
    if config_keys:
        return config_keys
    
    return []

def test_api_manager_basic():
    """Test basic API manager functionality"""
    print("\n" + "="*60)
    print("TESTING API MANAGER BASIC FUNCTIONALITY")
    print("="*60)
    
    # Get real API keys from config or environment
    test_keys = get_available_api_keys()
    
    if not test_keys:
        print("❌ No API keys found in config.json or environment variables")
        print("ℹ️  Using dummy keys for basic functionality test")
        test_keys = ["dummy_key_1", "dummy_key_2", "dummy_key_3"]
    else:
        print(f"✅ Found {len(test_keys)} API keys from configuration")
    
    try:
        # Initialize API manager
        api_manager = GeminiAPIManager(
            api_keys=test_keys,
            model_name='gemini-1.5-flash-002',
            cooldown_minutes=1,  # Short cooldown for testing
            max_retries=2
        )
        
        print(f"✅ API Manager initialized with {len(test_keys)} keys")
        
        # Get status
        status = api_manager.get_status()
        print(f"📊 Status: {json.dumps(status, indent=2)}")
        
        return api_manager
        
    except Exception as e:
        print(f"❌ Failed to initialize API manager: {e}")
        return None

def test_ai_analyzer_with_rotation():
    """Test AI Fashion Analyzer with API rotation"""
    print("\n" + "="*60)
    print("TESTING AI FASHION ANALYZER WITH ROTATION")
    print("="*60)
    
    # Get real API keys from config or environment
    test_keys = get_available_api_keys()
    
    if not test_keys:
        print("❌ No API keys found in config.json or environment variables")
        print("ℹ️  Using dummy keys for basic functionality test")
        test_keys = ["dummy_key_1", "dummy_key_2", "dummy_key_3"]
    else:
        print(f"✅ Found {len(test_keys)} API keys from configuration")
    
    try:
        # Initialize analyzer with multiple keys
        analyzer = AIFashionAnalyzer(
            api_keys=test_keys,
            cooldown_minutes=1,  # Short cooldown for testing
            max_retries=2
        )
        
        print(f"✅ AI Analyzer initialized with {len(test_keys)} keys")
        
        # Get API status
        status = analyzer.get_api_status()
        print(f"📊 API Status: {json.dumps(status, indent=2)}")
        
        return analyzer
        
    except Exception as e:
        print(f"❌ Failed to initialize AI analyzer: {e}")
        return None

def test_with_sample_image(analyzer):
    """Test analysis with a sample image"""
    print("\n" + "="*60)
    print("TESTING WITH SAMPLE IMAGE")
    print("="*60)
    
    # Look for sample images in scraped_data directory
    scraped_dir = Path("scraped_data")
    if not scraped_dir.exists():
        print("❌ No scraped_data directory found. Please run the scraper first to get sample images.")
        return
    
    # Find first image file
    image_files = list(scraped_dir.glob("*.jpg")) + list(scraped_dir.glob("*.png"))
    if not image_files:
        print("❌ No image files found in scraped_data directory.")
        return
    
    sample_image = image_files[0]
    print(f"🖼️  Testing with sample image: {sample_image}")
    
    try:
        # Analyze the image
        result = analyzer.comprehensive_analysis(str(sample_image))
        
        if result:
            print("✅ Analysis successful!")
            print(f"📝 Description: {result.get('description', 'N/A')[:100]}...")
            print(f"🏷️  Tags: {result.get('tags', [])[:5]}")
            print(f"🎨 Colors: {result.get('color_analysis', {}).get('dominant_colors', [])}")
            print(f"📊 Trend Score: {result.get('ai_trend_score', 'N/A')}")
        else:
            print("❌ Analysis failed - no result returned")
            
    except Exception as e:
        print(f"❌ Analysis failed with error: {e}")

def simulate_rate_limit_scenario():
    """Simulate rate limit scenario for testing"""
    print("\n" + "="*60)
    print("SIMULATING RATE LIMIT SCENARIO")
    print("="*60)
    
    print("ℹ️  This test simulates what happens when API keys hit rate limits.")
    print("ℹ️  In a real scenario, the system would automatically rotate to the next key.")
    print("ℹ️  For this demo, we'll show the status tracking functionality.")
    
    # Example with dummy keys to show status tracking
    dummy_keys = ["dummy_key_1", "dummy_key_2", "dummy_key_3"]
    
    try:
        api_manager = GeminiAPIManager(
            api_keys=dummy_keys,
            cooldown_minutes=1,
            max_retries=2
        )
        
        print("📊 Initial status:")
        status = api_manager.get_status()
        for key_info in status['keys']:
            print(f"  Key {key_info['index']}: Active={key_info['is_active']}, "
                  f"Requests={key_info['total_requests']}, "
                  f"Success Rate={key_info['success_rate']:.2%}")
        
        print("\n🔄 In a real scenario with valid keys:")
        print("  1. API manager makes request with Key 1")
        print("  2. If Key 1 hits rate limit, it gets put in cooldown")
        print("  3. API manager automatically switches to Key 2")
        print("  4. Process continues with remaining keys")
        print("  5. After cooldown period, Key 1 becomes available again")
        
    except Exception as e:
        print(f"❌ Error in simulation: {e}")

def test_config_integration():
    """Test integration with config system"""
    print("\n" + "="*60)
    print("TESTING CONFIG INTEGRATION")
    print("="*60)
    
    # Example config
    config = {
        'gemini_api_keys': ['key1', 'key2', 'key3'],
        'api_cooldown_minutes': 60,
        'max_retries': 3
    }
    
    try:
        # Test AIFashionAnalyzer.from_config
        analyzer = AIFashionAnalyzer.from_config(config)
        print("✅ AIFashionAnalyzer.from_config() works correctly")
        
        status = analyzer.get_api_status()
        print(f"📊 Config-based analyzer has {status['total_keys']} keys configured")
        
    except Exception as e:
        print(f"❌ Config integration test failed: {e}")

def print_usage_instructions():
    """Print instructions for using the API rotation system"""
    print("\n" + "="*60)
    print("HOW TO USE API KEY ROTATION IN YOUR PROJECT")
    print("="*60)
    
    print("""
🔧 SETUP INSTRUCTIONS:

1. Add your API keys to .env file:
   GEMINI_API_KEYS=key1_here,key2_here,key3_here,key4_here,key5_here

2. Optional settings in .env:
   API_COOLDOWN_MINUTES=60    # How long to wait before retrying a rate-limited key
   MAX_RETRIES=3              # Maximum retries across all keys

3. The system will automatically:
   ✅ Rotate between keys when one hits rate limits
   ✅ Put rate-limited keys in cooldown
   ✅ Track success rates and error counts
   ✅ Resume using keys after cooldown period

📊 MONITORING:
   - Use analyzer.get_api_status() to check key status
   - Check logs for rotation events
   - Use analyzer.reset_api_cooldowns() to manually reset if needed

🔄 BACKWARD COMPATIBILITY:
   - Single GEMINI_API_KEY still works
   - Existing code continues to work unchanged
   - New multi-key features are opt-in
""")

def main():
    """Main test function"""
    print("🚀 GEMINI API KEY ROTATION TEST SUITE")
    print("="*60)
    
    # Check if we have real API keys from any source
    available_keys = get_available_api_keys()
    has_real_keys = len(available_keys) > 0 and not all(key.startswith('dummy_') for key in available_keys)
    
    if not has_real_keys:
        print("⚠️  No real API keys found in environment variables or config.json.")
        print("⚠️  Running limited tests with dummy data.")
        print("⚠️  To test with real API calls, add keys to config.json or .env file.")
    else:
        print(f"✅ Found {len(available_keys)} real API keys for testing!")
        print("🚀 Running tests with your actual API keys...")
    
    # Run tests
    print_usage_instructions()
    
    # Test basic functionality
    api_manager = test_api_manager_basic()
    
    # Test AI analyzer
    analyzer = test_ai_analyzer_with_rotation()
    
    # Test with sample image (only if we have real keys and analyzer)
    if has_real_keys and analyzer:
        test_with_sample_image(analyzer)
    
    # Test config integration
    test_config_integration()
    
    # Simulate rate limit scenario
    simulate_rate_limit_scenario()
    
    print("\n" + "="*60)
    print("✅ TEST SUITE COMPLETED")
    print("="*60)
    print("📝 Next steps:")
    print("   1. Add your real API keys to .env file")
    print("   2. Run your Pinterest scraper - it will automatically use rotation")
    print("   3. Monitor logs to see rotation in action when rate limits hit")

if __name__ == "__main__":
    main()
