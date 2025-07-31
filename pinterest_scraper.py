#!/usr/bin/env python3
"""
Pinterest Board Scraper with AI Tagging
Production-level scraper for extracting images from Pinterest boards
with anti-bot detection measures and AI-powered tagging.
"""

import os
import json
import time
import random
import requests
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from urllib.parse import urlparse, urljoin
import logging
from dataclasses import dataclass, asdict
import concurrent.futures
from threading import Lock

# Selenium imports
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

# Image processing
from PIL import Image
import google.generativeai as genai
from api_key_manager import GeminiAPIManager
from ai_fashion_analyzer import AIFashionAnalyzer

# Anti-detection
try:
    import undetected_chromedriver as uc
    UNDETECTED_AVAILABLE = True
except ImportError:
    UNDETECTED_AVAILABLE = False
    print("Warning: undetected-chromedriver not available. Install with: pip install undetected-chromedriver")

@dataclass
class PinData:
    """Data structure for Pinterest pin information"""
    pin_id: str
    title: str
    description: str
    image_url: str
    board_name: str
    board_url: str
    author: str
    save_count: Optional[int] = None
    created_date: Optional[str] = None
    tags: List[str] = None
    ai_analysis: Optional[Dict] = None
    local_image_path: Optional[str] = None
    scraped_at: str = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.scraped_at is None:
            self.scraped_at = datetime.now().isoformat()

class PinterestScraper:
    """Production-level Pinterest scraper with anti-bot measures"""
    
    def __init__(self, config_path: str = "config.json"):
        self.config = self._load_config(config_path)
        self.setup_logging()
        self.setup_directories()
        self.setup_ai_analyzer()
        
        # Thread safety
        self.download_lock = Lock()
        self.analysis_lock = Lock()
        
        # Rate limiting
        self.last_request_time = 0
        self.request_delay = self.config.get('request_delay', 2)
        
        # User agents for rotation
        self.user_agents = [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0"
        ]
        
        self.driver = None
        self.session = requests.Session()
        
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from JSON file"""
        default_config = {
            "output_dir": "scraped_data",
            "images_dir": "images",
            "data_file": "pinterest_data.json",
            "log_file": "scraper.log",
            "max_pins_per_board": 100,
            "request_delay": 2,
            "max_workers": 3,
            "headless": False,
            "use_undetected_chrome": True,
            "gemini_api_key": "",
            "gemini_api_keys": [],  # List of API keys for rotation
            "api_cooldown_minutes": 60,
            "max_retries": 3,
            "proxy_list": [],
            "pinterest_email": "",
            "pinterest_password": ""
        }
        
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        else:
            # Create default config file
            with open(config_path, 'w') as f:
                json.dump(default_config, f, indent=4)
            print(f"Created default config file: {config_path}")
            print("Please update the config with your Pinterest credentials and Gemini API key")
        
        return default_config
    
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.config['log_file']),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def setup_directories(self):
        """Create necessary directories"""
        self.output_dir = Path(self.config['output_dir'])
        self.images_dir = self.output_dir / self.config['images_dir']
        
        self.output_dir.mkdir(exist_ok=True)
        self.images_dir.mkdir(exist_ok=True)
        
        self.logger.info(f"Output directory: {self.output_dir}")
        self.logger.info(f"Images directory: {self.images_dir}")
    
    def setup_ai_analyzer(self):
        """Setup Gemini AI for image analysis with API key rotation"""
        # Check for multiple API keys first (preferred)
        api_keys = self.config.get('gemini_api_keys', [])
        api_key = self.config.get('gemini_api_key')
        
        # Handle environment variables if config doesn't have keys
        if not api_keys and not api_key:
            env_keys = os.getenv('GEMINI_API_KEYS')
            if env_keys:
                api_keys = [key.strip() for key in env_keys.split(',') if key.strip()]
            else:
                api_key = os.getenv('GEMINI_API_KEY')
        
        if not api_keys and not api_key:
            self.logger.warning("No Gemini API keys provided. AI analysis will be skipped.")
            self.ai_enabled = False
            return
        
        try:
            # Use AIFashionAnalyzer which has the advanced analysis methods
            if api_keys:
                self.ai_analyzer = AIFashionAnalyzer(
                    api_keys=api_keys,
                    model_name='gemini-1.5-flash-002',
                    cooldown_minutes=self.config.get('api_cooldown_minutes', 60),
                    max_retries=self.config.get('max_retries', 3)
                )
                self.logger.info(f"AI analyzer initialized with {len(api_keys)} API keys")
            else:
                # Backward compatibility with single key
                self.ai_analyzer = AIFashionAnalyzer(
                    api_key=api_key,
                    model_name='gemini-1.5-flash-002',
                    cooldown_minutes=self.config.get('api_cooldown_minutes', 60),
                    max_retries=self.config.get('max_retries', 3)
                )
                self.logger.info("AI analyzer initialized with single API key")
            
            self.ai_enabled = True
        except Exception as e:
            self.logger.error(f"Failed to initialize AI analyzer: {e}")
            self.ai_enabled = False
    
    def setup_driver(self) -> webdriver.Chrome:
        """Setup Chrome driver with anti-detection measures"""
        options = Options()
        
        # Basic anti-detection options
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Random user agent
        user_agent = random.choice(self.user_agents)
        options.add_argument(f"--user-agent={user_agent}")
        
        # Additional stealth options
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins-discovery")
        options.add_argument("--disable-web-security")
        options.add_argument("--disable-features=VizDisplayCompositor")
        
        if self.config.get('headless', False):
            options.add_argument("--headless")
        
        # Proxy support
        proxy_list = self.config.get('proxy_list', [])
        if proxy_list:
            proxy = random.choice(proxy_list)
            options.add_argument(f"--proxy-server={proxy}")
            self.logger.info(f"Using proxy: {proxy}")
        
        try:
            if UNDETECTED_AVAILABLE and self.config.get('use_undetected_chrome', True):
                driver = uc.Chrome(options=options)
                self.logger.info("Using undetected-chromedriver")
            else:
                driver = webdriver.Chrome(options=options)
                self.logger.info("Using standard ChromeDriver")
            
            # Execute script to remove webdriver property
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            return driver
            
        except Exception as e:
            self.logger.error(f"Failed to setup driver: {e}")
            raise
    
    def login_to_pinterest(self) -> bool:
        """Login to Pinterest with credentials"""
        email = self.config.get('pinterest_email')
        password = self.config.get('pinterest_password')
        
        if not email or not password:
            self.logger.warning("No Pinterest credentials provided. Continuing without login.")
            return False
        
        try:
            self.logger.info("Attempting to login to Pinterest...")
            self.driver.get("https://www.pinterest.com/login/")
            
            # Wait for page load and add random delay
            time.sleep(random.uniform(3, 6))
            
            # Find and fill email
            email_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "email"))
            )
            self._human_type(email_input, email)
            
            # Find and fill password
            password_input = self.driver.find_element(By.ID, "password")
            self._human_type(password_input, password)
            
            # Click login button
            login_button = self.driver.find_element(By.CSS_SELECTOR, "[data-test-id='registerFormSubmitButton']")
            login_button.click()
            
            # Wait for login to complete
            time.sleep(random.uniform(5, 8))
            
            # Check if login was successful
            if "pinterest.com/login" not in self.driver.current_url:
                self.logger.info("Successfully logged in to Pinterest")
                return True
            else:
                self.logger.warning("Login may have failed - still on login page")
                return False
                
        except Exception as e:
            self.logger.error(f"Login failed: {e}")
            return False
    
    def _human_type(self, element, text: str):
        """Type text with human-like delays"""
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.05, 0.15))
    
    def _rate_limit(self):
        """Implement rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.request_delay:
            sleep_time = self.request_delay - time_since_last + random.uniform(0.5, 1.5)
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def extract_board_pins(self, board_url: str) -> List[Dict]:
        """Extract all pins from a Pinterest board"""
        self.logger.info(f"Extracting pins from board: {board_url}")
        
        try:
            self.driver.get(board_url)
            self._rate_limit()
            
            # Wait for page to load
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-test-id='pin']"))
            )
            
            pins_data = []
            max_pins = self.config.get('max_pins_per_board', 100)
            scroll_attempts = 0
            max_scroll_attempts = 20
            
            # Enhanced duplicate handling with better Pinterest infinite scroll support
            duplicate_scrolls = 0
            max_duplicate_scrolls = 8  # increased threshold for Pinterest's lazy loading
            consecutive_no_new_pins = 0
            max_no_new_pins = 5
            from storage.store import get_pin_by_id
            
            # Track processed pin IDs to avoid re-processing
            processed_pin_ids = set()

            while len(pins_data) < max_pins and scroll_attempts < max_scroll_attempts:
                # Get current pin elements
                current_pin_elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-test-id='pin']")
                new_pins_this_scroll = []
                pins_found_this_scroll = 0

                # Process all visible pins
                for pin_element in current_pin_elements:
                    if len(pins_data) >= max_pins:
                        break
                    try:
                        pin_data = self._extract_pin_data(pin_element, board_url)
                        if not pin_data or pin_data['pin_id'] in processed_pin_ids:
                            continue
                        
                        processed_pin_ids.add(pin_data['pin_id'])
                        pins_found_this_scroll += 1
                        
                        # Check DB for duplicate
                        pin_id = pin_data['pin_id']
                        db_pin = get_pin_by_id(pin_id)
                        if not db_pin:
                            pins_data.append(pin_data)
                            new_pins_this_scroll.append(pin_data)
                            self.logger.info(f"Extracted NEW pin {len(pins_data)}: {pin_data['title'][:50]}...")
                        else:
                            self.logger.debug(f"Pin {pin_id} already in database, skipping")
                    except Exception as e:
                        self.logger.warning(f"Failed to extract pin data: {e}")
                        continue

                # Track duplicate scrolls and no-new-pins scrolls separately
                if not new_pins_this_scroll:
                    if pins_found_this_scroll > 0:
                        duplicate_scrolls += 1
                        self.logger.info(f"Scroll yielded only duplicates ({duplicate_scrolls}/{max_duplicate_scrolls}) - found {pins_found_this_scroll} existing pins")
                    else:
                        consecutive_no_new_pins += 1
                        self.logger.info(f"No new pins found in scroll ({consecutive_no_new_pins}/{max_no_new_pins})")
                else:
                    duplicate_scrolls = 0  # reset counters when new pins found
                    consecutive_no_new_pins = 0
                    self.logger.info(f"Found {len(new_pins_this_scroll)} new pins in this scroll")

                # More aggressive scrolling for Pinterest
                scroll_height = self.driver.execute_script("return document.body.scrollHeight")
                self.driver.execute_script(f"window.scrollTo(0, {scroll_height});")
                time.sleep(random.uniform(3, 5))  # longer wait for Pinterest loading
                
                # Additional scroll to trigger more loading
                self.driver.execute_script("window.scrollBy(0, 1000);")
                time.sleep(random.uniform(1, 2))
                scroll_attempts += 1

                # Stop conditions
                if duplicate_scrolls >= max_duplicate_scrolls:
                    self.logger.info(f"Stopping scroll: {max_duplicate_scrolls} consecutive duplicate scrolls")
                    break
                    
                if consecutive_no_new_pins >= max_no_new_pins:
                    self.logger.info(f"Stopping scroll: {max_no_new_pins} consecutive scrolls with no pins found")
                    break

                # Check if page stopped loading new content
                new_scroll_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_scroll_height == scroll_height and consecutive_no_new_pins >= 2:
                    self.logger.info("Page height unchanged and no new pins - likely reached end")
                    break
            
            self.logger.info(f"Extracted {len(pins_data)} NEW pins from board (processed {len(processed_pin_ids)} total pins)")
            self.logger.info(f"Scroll stats: {scroll_attempts} scrolls, {duplicate_scrolls} duplicate scrolls, {consecutive_no_new_pins} empty scrolls")
            return pins_data
            
        except Exception as e:
            self.logger.error(f"Failed to extract pins from board {board_url}: {e}")
            return []
    
    def _extract_pin_data(self, pin_element, board_url: str) -> Optional[Dict]:
        """Extract data from a single pin element"""
        try:
            # Extract pin ID from data attributes or URL
            pin_id = pin_element.get_attribute("data-test-pin-id")
            if not pin_id:
                # Try to get from link
                link_element = pin_element.find_element(By.TAG_NAME, "a")
                href = link_element.get_attribute("href")
                if "/pin/" in href:
                    pin_id = href.split("/pin/")[1].split("/")[0]
            
            if not pin_id:
                return None
            
            # Extract image URL
            img_element = pin_element.find_element(By.TAG_NAME, "img")
            image_url = img_element.get_attribute("src")
            
            # Get high-resolution image URL
            if "236x" in image_url:
                image_url = image_url.replace("236x", "736x")
            elif "474x" in image_url:
                image_url = image_url.replace("474x", "736x")
            
            # Extract title and description
            title = img_element.get_attribute("alt") or ""
            
            # Try to get description from pin overlay
            description = ""
            try:
                desc_elements = pin_element.find_elements(By.CSS_SELECTOR, "[data-test-id='pin-description']")
                if desc_elements:
                    description = desc_elements[0].text
            except:
                pass
            
            # Extract board name from URL
            board_name = board_url.split("/")[-2] if board_url.endswith("/") else board_url.split("/")[-1]
            
            # Extract author (board owner)
            author = ""
            try:
                author_elements = pin_element.find_elements(By.CSS_SELECTOR, "[data-test-id='board-owner']")
                if author_elements:
                    author = author_elements[0].text
                else:
                    # Extract from board URL
                    author = board_url.split("/")[3] if len(board_url.split("/")) > 3 else ""
            except:
                pass
            
            return {
                'pin_id': pin_id,
                'title': title,
                'description': description,
                'image_url': image_url,
                'board_name': board_name,
                'board_url': board_url,
                'author': author,
                'scraped_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.warning(f"Failed to extract pin data: {e}")
            return None
    
    def download_image(self, pin_data: Dict) -> Optional[str]:
        """Download image from Pinterest"""
        try:
            image_url = pin_data['image_url']
            pin_id = pin_data['pin_id']
            
            # Create filename
            filename = f"{pin_id}.jpg"
            filepath = self.images_dir / filename
            
            # Skip if already downloaded
            if filepath.exists():
                self.logger.info(f"Image already exists: {filename}")
                return str(filepath)
            
            # Download with session
            headers = {
                'User-Agent': random.choice(self.user_agents),
                'Referer': 'https://www.pinterest.com/'
            }
            
            with self.download_lock:
                response = self.session.get(image_url, headers=headers, timeout=30)
                response.raise_for_status()
                
                # Save image
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                # Verify image
                try:
                    with Image.open(filepath) as img:
                        img.verify()
                    self.logger.info(f"Downloaded image: {filename}")
                    return str(filepath)
                except Exception as e:
                    self.logger.error(f"Invalid image downloaded: {e}")
                    filepath.unlink()
                    return None
                    
        except Exception as e:
            self.logger.error(f"Failed to download image {pin_data.get('pin_id', 'unknown')}: {e}")
            return None
    
    def analyze_image_with_ai(self, image_path: str) -> Optional[Dict]:
        """Analyze image using advanced AI fashion analyzer with comprehensive style analysis"""
        if not self.ai_enabled:
            return None
        
        try:
            with self.analysis_lock:
                # Use the advanced comprehensive analysis from AI analyzer
                analysis_result = self.ai_analyzer.advanced_comprehensive_analysis(image_path)
                
                if analysis_result:
                    self.logger.info(f"Advanced AI analysis completed for image: {os.path.basename(image_path)}")
                    
                    # Save detailed analysis report to file
                    try:
                        report_filename = f"analysis_report_{os.path.basename(image_path).split('.')[0]}.txt"
                        report_path = os.path.join(self.config['output_dir'], report_filename)
                        
                        formatted_report = self.ai_analyzer.format_advanced_output(analysis_result)
                        with open(report_path, 'w', encoding='utf-8') as f:
                            f.write(formatted_report)
                        
                        self.logger.info(f"Detailed analysis report saved to: {report_path}")
                    except Exception as report_err:
                        self.logger.warning(f"Failed to save analysis report: {report_err}")
                    
                    return analysis_result
                else:
                    self.logger.warning(f"Empty analysis result for: {os.path.basename(image_path)}")
                    return None
                
        except Exception as e:
            self.logger.error(f"Advanced AI analysis failed for {image_path}: {e}")
            return None
    
    def process_pin(self, pin_data: Dict) -> PinData:
        """Process a single pin: download image and analyze with AI"""
        # Download image
        image_path = self.download_image(pin_data)
        
        # Analyze with AI if image downloaded successfully
        ai_analysis = None
        if image_path and self.ai_enabled:
            ai_analysis = self.analyze_image_with_ai(image_path)
        
        # Create PinData object
        pin_obj = PinData(
            pin_id=pin_data['pin_id'],
            title=pin_data['title'],
            description=pin_data['description'],
            image_url=pin_data['image_url'],
            board_name=pin_data['board_name'],
            board_url=pin_data['board_url'],
            author=pin_data['author'],
            local_image_path=image_path,
            ai_analysis=ai_analysis,
            scraped_at=pin_data['scraped_at']
        )
        
        # Store in MongoDB if AI analysis is available
        if ai_analysis and image_path:
            try:
                from storage.store import store_metadata_in_mongodb
                success = store_metadata_in_mongodb(
                    pin_id=pin_data['pin_id'],
                    source_url=pin_data['image_url'],
                    metadata=ai_analysis,
                    image_path=image_path
                )
                if success:
                    self.logger.info(f"Stored pin {pin_data['pin_id']} in MongoDB")
                else:
                    self.logger.warning(f"Failed to store pin {pin_data['pin_id']} in MongoDB")
            except Exception as e:
                self.logger.warning(f"MongoDB storage failed for pin {pin_data['pin_id']}: {e}")
        
        return pin_obj
    
    def scrape_boards(self, board_urls: List[str]) -> List[PinData]:
        """Main method to scrape multiple Pinterest boards"""
        self.logger.info(f"Starting to scrape {len(board_urls)} boards")
        
        # Setup driver
        self.driver = self.setup_driver()
        
        try:
            # Login if credentials provided
            self.login_to_pinterest()
            
            all_pins = []
            
            for board_url in board_urls:
                self.logger.info(f"Processing board: {board_url}")
                
                # Extract pins from board
                pins_data = self.extract_board_pins(board_url)
                
                if not pins_data:
                    self.logger.warning(f"No pins extracted from {board_url}")
                    continue
                
                # Process pins with threading
                with concurrent.futures.ThreadPoolExecutor(max_workers=self.config['max_workers']) as executor:
                    future_to_pin = {executor.submit(self.process_pin, pin_data): pin_data for pin_data in pins_data}
                    
                    for future in concurrent.futures.as_completed(future_to_pin):
                        try:
                            pin_obj = future.result()
                            all_pins.append(pin_obj)
                            self.logger.info(f"Processed pin: {pin_obj.title[:50]}...")
                        except Exception as e:
                            self.logger.error(f"Failed to process pin: {e}")
                
                # Save progress after each board
                self.save_data(all_pins)
                
                # Random delay between boards
                time.sleep(random.uniform(10, 20))
            
            self.logger.info(f"Scraping completed. Total pins processed: {len(all_pins)}")
            return all_pins
            
        finally:
            if self.driver:
                self.driver.quit()
    
    def save_data(self, pins: List[PinData]):
        """Save scraped data to JSON file"""
        data_file = self.output_dir / self.config['data_file']
        
        # Convert to dict for JSON serialization
        pins_dict = [asdict(pin) for pin in pins]
        
        # Add metadata
        metadata = {
            'total_pins': len(pins),
            'scraped_at': datetime.now().isoformat(),
            'ai_analysis_enabled': self.ai_enabled,
            'pins': pins_dict
        }
        
        with open(data_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        self.logger.info(f"Data saved to {data_file}")
    
    def generate_training_dataset(self, pins: List[PinData]) -> Dict:
        """Generate ML training dataset format"""
        dataset = {
            'metadata': {
                'total_samples': len(pins),
                'created_at': datetime.now().isoformat(),
                'description': 'Pinterest fashion dataset with AI analysis'
            },
            'samples': []
        }
        
        for pin in pins:
            if pin.local_image_path and pin.ai_analysis:
                sample = {
                    'image_path': pin.local_image_path,
                    'image_id': pin.pin_id,
                    'title': pin.title,
                    'description': pin.description,
                    'source_url': pin.image_url,
                    'board': pin.board_name,
                    'author': pin.author,
                    'labels': pin.ai_analysis.get('fashion_items', []),
                    'tags': self._extract_tags_from_analysis(pin.ai_analysis)
                }
                dataset['samples'].append(sample)
        
        # Save training dataset
        training_file = self.output_dir / 'training_dataset.json'
        with open(training_file, 'w') as f:
            json.dump(dataset, f, indent=2)
        
        self.logger.info(f"Training dataset saved to {training_file}")
        return dataset
    
    def _extract_tags_from_analysis(self, ai_analysis: Dict) -> List[str]:
        """Extract tags from enhanced AI analysis for training"""
        tags = []
        
        if not ai_analysis:
            return tags
        
        # Extract tags from the main tags field
        if 'tags' in ai_analysis and ai_analysis['tags']:
            if isinstance(ai_analysis['tags'], list):
                tags.extend([str(tag).lower().replace(' ', '_') for tag in ai_analysis['tags'] if tag])
        
        # Extract style category
        if 'style_category' in ai_analysis and ai_analysis['style_category']:
            tags.append(ai_analysis['style_category'].lower().replace(' ', '_'))
        
        # Extract detected objects
        if 'detected_objects' in ai_analysis and ai_analysis['detected_objects']:
            if isinstance(ai_analysis['detected_objects'], list):
                tags.extend([str(obj).lower().replace(' ', '_') for obj in ai_analysis['detected_objects'] if obj])
        
        # Extract from fashion items if available
        if 'fashion_items' in ai_analysis and ai_analysis['fashion_items']:
            for item in ai_analysis['fashion_items']:
                # Add category
                if 'category' in item and item['category']:
                    if isinstance(item['category'], str):
                        tags.append(item['category'].lower())
                    elif isinstance(item['category'], list):
                        tags.extend([str(cat).lower() for cat in item['category'] if cat])
                
                # Add type
                if 'type' in item and item['type']:
                    if isinstance(item['type'], str):
                        tags.append(item['type'].lower().replace(' ', '_'))
                    elif isinstance(item['type'], list):
                        tags.extend([str(t).lower().replace(' ', '_') for t in item['type'] if t])
                
                # Add colors
                if 'color' in item and item['color']:
                    colors = item['color'] if isinstance(item['color'], list) else [item['color']]
                    tags.extend([str(color).lower().replace(' ', '_') for color in colors if color])
                
                # Add style
                if 'style' in item and item['style']:
                    if isinstance(item['style'], str):
                        tags.append(item['style'].lower().replace(' ', '_'))
                    elif isinstance(item['style'], list):
                        tags.extend([str(s).lower().replace(' ', '_') for s in item['style'] if s])
                
                # Add material - handle both string and list
                if 'material' in item and item['material']:
                    if isinstance(item['material'], str):
                        tags.append(item['material'].lower().replace(' ', '_'))
                    elif isinstance(item['material'], list):
                        tags.extend([str(mat).lower().replace(' ', '_') for mat in item['material'] if mat])
                
                # Add brand if available
                if 'brand' in item and item['brand'] and item['brand'] != 'Unknown':
                    if isinstance(item['brand'], str):
                        tags.append(item['brand'].lower().replace(' ', '_'))
                    elif isinstance(item['brand'], list):
                        tags.extend([str(b).lower().replace(' ', '_') for b in item['brand'] if b and b != 'Unknown'])
        
        # Extract brand suggestions
        if 'brand_suggestions' in ai_analysis and ai_analysis['brand_suggestions']:
            if isinstance(ai_analysis['brand_suggestions'], list):
                tags.extend([str(brand).lower().replace(' ', '_') for brand in ai_analysis['brand_suggestions'] if brand])
        
        # Extract season
        if 'season' in ai_analysis and ai_analysis['season']:
            tags.append(ai_analysis['season'].lower().replace(' ', '_').replace('/', '_'))
        
        # Extract gender
        if 'gender' in ai_analysis and ai_analysis['gender']:
            tags.append(ai_analysis['gender'].lower())
        
        # Extract from trend analysis
        if 'trend_analysis' in ai_analysis and ai_analysis['trend_analysis']:
            trend_data = ai_analysis['trend_analysis']
            
            # Extract current trends
            if 'current_trends' in trend_data and trend_data['current_trends']:
                if isinstance(trend_data['current_trends'], list):
                    tags.extend([str(trend).lower().replace(' ', '_') for trend in trend_data['current_trends'] if trend])
            
            # Extract timeless elements
            if 'timeless_elements' in trend_data and trend_data['timeless_elements']:
                if isinstance(trend_data['timeless_elements'], list):
                    tags.extend([str(element).lower().replace(' ', '_') for element in trend_data['timeless_elements'] if element])
            
            # Extract fashion cycle stage
            if 'fashion_cycle_stage' in trend_data and trend_data['fashion_cycle_stage']:
                tags.append(trend_data['fashion_cycle_stage'].lower().replace(' ', '_'))
            
            # Extract inspired by brands
            if 'inspired_by' in trend_data and trend_data['inspired_by']:
                if isinstance(trend_data['inspired_by'], list):
                    tags.extend([str(brand).lower().replace(' ', '_') for brand in trend_data['inspired_by'] if brand])
        
        return list(set(tags))  # Remove duplicates

def main():
    """Main execution function"""
    print("🚀 Pinterest Scraper with AI Tagging")
    print("=" * 50)
    
    # Initialize scraper
    scraper = PinterestScraper()
    
    # Fashion-focused Pinterest board URLs
    board_urls = [
        "https://in.pinterest.com/mohanty2922/office/",
        "https://in.pinterest.com/mohanty2922/y2k-fashion/",
        "https://in.pinterest.com/mohanty2922/rita-mota-fashion/",
        "https://in.pinterest.com/mohanty2922/hailey-bieber-fashion/"
     
    ]
    
    print(f"Starting scraping of {len(board_urls)} fashion boards...")
    print("Pinterest credentials and Gemini API key loaded from config.json")
    
    try:
        # Run scraping
        pins = scraper.scrape_boards(board_urls)
        
        if pins:
            # Generate training dataset
            training_dataset = scraper.generate_training_dataset(pins)
            print(f"\n✅ Scraping completed! {len(pins)} pins processed.")
            print(f"📊 Training dataset generated with {len(training_dataset.get('samples', []))} samples.")
            print(f"📁 Data saved to: {scraper.output_dir}")
        else:
            print("\n⚠️ No pins were scraped. Check logs for details.")
            
    except Exception as e:
        print(f"\n❌ Scraping failed: {e}")
        print("Check logs/scraper.log for detailed error information.")

if __name__ == "__main__":
    main()
