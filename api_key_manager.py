#!/usr/bin/env python3
"""
API Key Manager for Gemini AI
Handles automatic rotation between multiple API keys when rate limits are hit
"""

import google.generativeai as genai
import logging
import time
import random
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import json

@dataclass
class APIKeyStatus:
    """Track the status of an individual API key"""
    key: str
    is_active: bool = True
    last_error_time: Optional[datetime] = None
    error_count: int = 0
    cooldown_until: Optional[datetime] = None
    total_requests: int = 0
    successful_requests: int = 0

class GeminiAPIManager:
    """
    Manages multiple Gemini API keys with automatic rotation and rate limit handling
    """
    
    def __init__(self, api_keys: List[str], model_name: str = 'gemini-1.5-flash-002', 
                 cooldown_minutes: int = 60, max_retries: int = 3):
        """
        Initialize the API manager
        
        Args:
            api_keys: List of Gemini API keys
            model_name: Gemini model to use
            cooldown_minutes: Minutes to wait before retrying a rate-limited key
            max_retries: Maximum retries per request across all keys
        """
        self.api_keys = [APIKeyStatus(key) for key in api_keys]
        self.model_name = model_name
        self.cooldown_minutes = cooldown_minutes
        self.max_retries = max_retries
        self.current_key_index = 0
        self.logger = logging.getLogger(__name__)
        
        # Generation config
        self.generation_config = genai.GenerationConfig(
            response_mime_type="application/json"
        )
        
        if not api_keys:
            raise ValueError("At least one API key must be provided")
        
        self.logger.info(f"Initialized GeminiAPIManager with {len(api_keys)} API keys")
        self._setup_current_key()
    
    def _setup_current_key(self) -> bool:
        """Setup the current API key and model"""
        current_key = self.api_keys[self.current_key_index]
        
        # Check if key is in cooldown
        if current_key.cooldown_until and datetime.now() < current_key.cooldown_until:
            self.logger.warning(f"Current key is in cooldown until {current_key.cooldown_until}")
            return False
        
        try:
            genai.configure(api_key=current_key.key)
            self.model = genai.GenerativeModel(self.model_name)
            current_key.is_active = True
            self.logger.info(f"Configured API key {self.current_key_index + 1}/{len(self.api_keys)}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to configure API key {self.current_key_index + 1}: {e}")
            current_key.is_active = False
            return False
    
    def _rotate_to_next_key(self) -> bool:
        """Rotate to the next available API key"""
        original_index = self.current_key_index
        attempts = 0
        
        while attempts < len(self.api_keys):
            self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
            attempts += 1
            
            current_key = self.api_keys[self.current_key_index]
            
            # Skip keys in cooldown
            if current_key.cooldown_until and datetime.now() < current_key.cooldown_until:
                continue
            
            if self._setup_current_key():
                self.logger.info(f"Rotated to API key {self.current_key_index + 1}/{len(self.api_keys)}")
                return True
        
        self.logger.error("No available API keys found")
        return False
    
    def _handle_rate_limit_error(self, error: Exception) -> None:
        """Handle rate limit error by putting current key in cooldown"""
        current_key = self.api_keys[self.current_key_index]
        current_key.error_count += 1
        current_key.last_error_time = datetime.now()
        current_key.cooldown_until = datetime.now() + timedelta(minutes=self.cooldown_minutes)
        current_key.is_active = False
        
        self.logger.warning(
            f"API key {self.current_key_index + 1} hit rate limit. "
            f"Cooldown until {current_key.cooldown_until}. Error: {error}"
        )
    
    def _is_rate_limit_error(self, error: Exception) -> bool:
        """Check if the error is a rate limit error"""
        error_str = str(error).lower()
        rate_limit_indicators = [
            'quota exceeded',
            'rate limit',
            'too many requests',
            '429',
            'resource_exhausted',
            'quota_exceeded'
        ]
        return any(indicator in error_str for indicator in rate_limit_indicators)
    
    def generate_content(self, content: List[Any], **kwargs) -> Optional[Any]:
        """
        Generate content with automatic API key rotation on rate limits
        
        Args:
            content: Content to send to the model (prompt + image)
            **kwargs: Additional arguments for generate_content
            
        Returns:
            Generated response or None if all keys failed
        """
        retries = 0
        last_error = None
        
        while retries < self.max_retries:
            current_key = self.api_keys[self.current_key_index]
            
            try:
                # Ensure current key is properly configured
                if not current_key.is_active or not hasattr(self, 'model'):
                    if not self._setup_current_key():
                        if not self._rotate_to_next_key():
                            break
                        continue
                
                # Add generation config if not provided
                if 'generation_config' not in kwargs:
                    kwargs['generation_config'] = self.generation_config
                
                # Make the API call
                current_key.total_requests += 1
                response = self.model.generate_content(content, **kwargs)
                
                # Success
                current_key.successful_requests += 1
                self.logger.debug(f"Successful request with API key {self.current_key_index + 1}")
                return response
                
            except Exception as e:
                last_error = e
                self.logger.error(f"Error with API key {self.current_key_index + 1}: {e}")
                
                # Check if it's a rate limit error
                if self._is_rate_limit_error(e):
                    self._handle_rate_limit_error(e)
                    
                    # Try to rotate to next key
                    if self._rotate_to_next_key():
                        retries += 1
                        continue
                    else:
                        # No more keys available
                        break
                else:
                    # Non-rate-limit error, still try next key but count as retry
                    retries += 1
                    if not self._rotate_to_next_key():
                        break
        
        self.logger.error(f"All API keys failed after {retries} retries. Last error: {last_error}")
        return None
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of all API keys"""
        status = {
            'total_keys': len(self.api_keys),
            'current_key_index': self.current_key_index,
            'keys': []
        }
        
        for i, key_status in enumerate(self.api_keys):
            key_info = {
                'index': i + 1,
                'key_preview': f"{key_status.key[:8]}...{key_status.key[-4:]}",
                'is_active': key_status.is_active,
                'error_count': key_status.error_count,
                'total_requests': key_status.total_requests,
                'successful_requests': key_status.successful_requests,
                'success_rate': (
                    key_status.successful_requests / key_status.total_requests 
                    if key_status.total_requests > 0 else 0
                ),
                'in_cooldown': (
                    key_status.cooldown_until and datetime.now() < key_status.cooldown_until
                ),
                'cooldown_until': key_status.cooldown_until.isoformat() if key_status.cooldown_until else None
            }
            status['keys'].append(key_info)
        
        return status
    
    def reset_cooldowns(self) -> None:
        """Reset all cooldowns (useful for testing or manual intervention)"""
        for key_status in self.api_keys:
            key_status.cooldown_until = None
            key_status.is_active = True
        self.logger.info("All API key cooldowns have been reset")
    
    def add_api_key(self, api_key: str) -> None:
        """Add a new API key to the rotation"""
        self.api_keys.append(APIKeyStatus(api_key))
        self.logger.info(f"Added new API key. Total keys: {len(self.api_keys)}")
    
    def remove_api_key(self, api_key: str) -> bool:
        """Remove an API key from rotation"""
        for i, key_status in enumerate(self.api_keys):
            if key_status.key == api_key:
                del self.api_keys[i]
                # Adjust current index if necessary
                if self.current_key_index >= len(self.api_keys):
                    self.current_key_index = 0
                self.logger.info(f"Removed API key. Total keys: {len(self.api_keys)}")
                return True
        return False

# Convenience function for easy integration
def create_gemini_manager_from_config(config: Dict[str, Any]) -> GeminiAPIManager:
    """
    Create GeminiAPIManager from configuration
    
    Expected config format:
    {
        'gemini_api_keys': ['key1', 'key2', 'key3'],  # List of API keys
        'gemini_model': 'gemini-1.5-flash-002',       # Optional, defaults to gemini-1.5-flash-002
        'api_cooldown_minutes': 60,                   # Optional, defaults to 60
        'max_retries': 3                              # Optional, defaults to 3
    }
    """
    api_keys = config.get('gemini_api_keys', [])
    if not api_keys:
        # Fallback to single key for backward compatibility
        single_key = config.get('gemini_api_key')
        if single_key:
            api_keys = [single_key]
        else:
            raise ValueError("No Gemini API keys found in configuration")
    
    return GeminiAPIManager(
        api_keys=api_keys,
        model_name=config.get('gemini_model', 'gemini-1.5-flash-002'),
        cooldown_minutes=config.get('api_cooldown_minutes', 60),
        max_retries=config.get('max_retries', 3)
    )
