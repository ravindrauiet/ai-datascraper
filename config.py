from pydantic_settings import BaseSettings
from typing import List, Optional
from dotenv import load_dotenv
import os

# Load .env if present
load_dotenv()

class Settings(BaseSettings):
    pinterest_email: str
    pinterest_password: str
    gemini_api_key: Optional[str] = None
    gemini_api_keys: Optional[str] = None  # Comma-separated API keys
    api_cooldown_minutes: int = 60
    max_retries: int = 3
    mongodb_url: str = "mongodb://localhost:27017"
    database_name: str = "pinterest_scraper"
    default_board_urls: str = ""
    check_interval_minutes: int = 30
    auto_start_scraper: bool = True
    enable_ai_analysis: bool = True
    # Added extra fields to match .env and prevent extra_forbidden errors
    log_level: str = "INFO"
    log_file: Optional[str] = None
    default_max_pins: int = 2
    request_delay: int = 2
    max_concurrent_jobs: int = 3
    api_key: Optional[str] = None
    jwt_secret_key: Optional[str] = None
    # Add all remaining .env fields
    app_name: Optional[str] = None
    app_version: Optional[str] = None
    debug: Optional[bool] = None
    host: Optional[str] = None
    port: Optional[int] = None
    
    def get_gemini_api_keys_list(self) -> List[str]:
        """Parse comma-separated API keys into a list"""
        if self.gemini_api_keys:
            # Split by comma and strip whitespace
            keys = [key.strip() for key in self.gemini_api_keys.split(',') if key.strip()]
            return keys
        elif self.gemini_api_key:
            # Backward compatibility - single key
            return [self.gemini_api_key]
        return []

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

def get_settings() -> Settings:
    return Settings()
