#!/usr/bin/env python3
"""
AI Fashion Analyzer Module
Enhanced version of your existing fashion analyzer with production features
"""

import google.generativeai as genai
import json
import enum
import typing
import os
from PIL import Image
from datetime import datetime
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from api_key_manager import GeminiAPIManager, create_gemini_manager_from_config

# =============================================================================
# FASHION TAXONOMY DEFINITIONS (From your existing code)
# =============================================================================

class ApparelCategory(enum.Enum):
    DRESS = "Dress"
    TOP = "Top"
    KNIT_TOP = "Knit or Sweater Top"
    SHIRT = "Shirt"
    PANTS = "Pants"
    SHORTS = "Shorts"
    SKIRT = "Skirt"
    SHOES = "Shoes"
    OUTERWEAR = "Outerwear"
    UNDERGARMENTS = "Undergarments"
    BAG = "Bag"
    ACCESSORY = "Accessory"

class Waist(enum.Enum):
    RIB_CAGE = "Rib cage"
    HIGH_WAISTED = "High Waisted"
    NATURAL_WAIST = "Natural Waist"
    MIDRISE = "Midrise"
    LOWRISE = "Lowrise"
    HIP_HUGGER = "Hip Hugger"

class PantsType(enum.Enum):
    JEANS = "Jeans"
    CHINOS = "Chinos"
    JOGGERS = "Joggers"
    FORMAL = "Formal"
    CARGO = "Cargo"

class PantsLength(enum.Enum):
    FULL_LENGTH = "Full Length"
    ANKLE = "Ankle"
    CROPPED = "Cropped"
    SHORTS = "Shorts"

class ShirtStyle(enum.Enum):
    BUTTON_DOWN = "Button Down"
    POLO = "Polo"
    TEE = "T-shirt"
    LONG_SLEEVE = "Long Sleeve"
    SHORT_SLEEVE = "Short Sleeve"

class ShoeType(enum.Enum):
    SNEAKERS = "Sneakers"
    BOOTS = "Boots"
    SANDALS = "Sandals"
    FORMAL_SHOES = "Formal Shoes"
    SLIPPERS = "Slippers"

class WatchType(enum.Enum):
    ANALOG = "Analog"
    DIGITAL = "Digital"
    SMARTWATCH = "Smartwatch"

class FabricDetails(typing.TypedDict):
    material: str
    texture: str

class ClothingItem(typing.TypedDict):
    category: ApparelCategory
    colors: list[str]
    fabric: str
    fabric_details: list[FabricDetails]
    specific_type: str
    additional_attributes: dict

class FashionCategory(enum.Enum):
    CLOTHING = "Clothing"
    FOOTWEAR = "Footwear"
    ACCESSORY = "Accessory"
    BAG = "Bag"

class FootwearType(enum.Enum):
    SNEAKERS = "Sneakers"
    BOOTS = "Boots"
    SANDALS = "Sandals"
    FORMAL_SHOES = "Formal Shoes"
    SLIPPERS = "Slippers"

class FashionItem(typing.TypedDict):
    category: FashionCategory
    type: str
    color: str
    material: str
    style: str
    brand: str

# =============================================================================
# AI FASHION ANALYZER CLASS
# =============================================================================

class AIFashionAnalyzer:
    """Production-level AI Fashion Analyzer with enhanced capabilities and API key rotation"""
    
    def __init__(self, api_keys: List[str] = None, api_key: str = None, model_name: str = 'gemini-1.5-flash-002', 
                 cooldown_minutes: int = 60, max_retries: int = 3):
        """Initialize the AI Fashion Analyzer with API key rotation support
        
        Args:
            api_keys: List of Gemini API keys for rotation (preferred)
            api_key: Single API key for backward compatibility
            model_name: Gemini model to use
            cooldown_minutes: Minutes to wait before retrying rate-limited key
            max_retries: Maximum retries per request
        """
        self.logger = logging.getLogger(__name__)
        
        # Handle API keys - support both single key and multiple keys
        if api_keys:
            self.api_manager = GeminiAPIManager(
                api_keys=api_keys,
                model_name=model_name,
                cooldown_minutes=cooldown_minutes,
                max_retries=max_retries
            )
            self.logger.info(f"AI Fashion Analyzer initialized with {len(api_keys)} API keys")
        elif api_key:
            # Backward compatibility - single key
            self.api_manager = GeminiAPIManager(
                api_keys=[api_key],
                model_name=model_name,
                cooldown_minutes=cooldown_minutes,
                max_retries=max_retries
            )
            self.logger.info("AI Fashion Analyzer initialized with single API key")
        else:
            raise ValueError("Either api_keys (list) or api_key (string) must be provided")
        
        self.model_name = model_name
    
    # =============================================================================
    # PROMPTS (Enhanced versions of your existing prompts)
    # =============================================================================
    
    @property
    def comprehensive_prompt(self) -> str:
        """Enhanced prompt for comprehensive fashion analysis with trend data."""
        return '''
        You are a world-class fashion stylist, trend analyst, and AI fashion expert. Analyze the provided image and return a comprehensive JSON object with detailed fashion analysis, trend insights, and social popularity metrics.

        The JSON output MUST conform to this EXACT structure:

        {
          "description": "A detailed description of the fashion look, style, and overall aesthetic",
          "tags": [
            "List of relevant fashion tags (e.g., streetwear, oversized hoodie, chunky sneakers, urban fashion, 2025 trend)"
          ],
          "dominant_colors": ["#hexcode1", "#hexcode2", "#hexcode3"],
          "season": "Spring/Summer 2025 | Fall/Winter 2025 | All Season",
          "style_category": "Urban Casual | Bohemian Chic | Minimalist | Streetwear | Business Casual | Formal | etc.",
          "gender": "Male | Female | Unisex",
          "ai_trend_score": 0.85,
          "trend_analysis": {
            "match_with_latest_trend": true,
            "inspired_by": ["Brand1", "Brand2", "Designer3"],
            "fashion_cycle_stage": "emerging | peak | declining | classic",
            "social_popularity_score": 85,
            "predicted_lifespan_months": 6,
            "current_trends": [
              "List of current fashion trends represented in this look"
            ],
            "timeless_elements": [
              "List of classic, timeless fashion elements in this outfit"
            ],
            "trend_forecast": "Detailed analysis of how this style will evolve and its future relevance in fashion"
          },
          "detected_objects": ["hoodie", "sneakers", "jeans", "accessories"],
          "fashion_items": [
            {
              "category": "Clothing | Footwear | Accessory | Bag",
              "type": "Specific item name",
              "color": ["color1", "color2"],
              "material": ["material1", "material2"],
              "style": "style descriptor",
              "brand": "Brand name or Unknown",
              "price_range": "Budget | Mid-range | Luxury",
              "trend_status": "Classic | Trending | Emerging | Declining"
            }
          ],
          "style_analysis": {
            "overall_aesthetic": "Description of the complete look",
            "color_coordination": "Analysis of color harmony and palette",
            "silhouette": "Description of the outfit's shape and fit",
            "occasion_suitability": {
              "casual": 9,
              "work": 3,
              "evening": 7,
              "formal": 2
            },
            "versatility_score": 0.75,
            "confidence_level": "high | medium | low"
          },
          "influencer_matches": [
            {
              "name": "Influencer name",
              "similarity_score": 0.85,
              "reason": "Why this matches their style"
            }
          ],
          "brand_suggestions": ["Brand1", "Brand2", "Brand3"],
          "improvement_suggestions": "Specific advice to enhance the look",
          "sustainability_score": 0.6,
          "ai_model_version": "v2.3.1"
        }

        IMPORTANT INSTRUCTIONS:
        - Analyze the image thoroughly and provide detailed, specific insights
        - Use actual hex color codes for dominant_colors (e.g., #1e1e1e, #fafafa)
        - Provide realistic trend scores between 0.0 and 1.0
        - Include specific brand names when identifiable
        - Give actionable improvement suggestions
        - Consider current 2025 fashion trends
        - All numeric scores should be realistic and well-reasoned
        - Ensure all JSON is properly formatted and valid
        '''
    
    def comprehensive_analysis(self, image_path: str) -> Optional[Dict]:
        """Performs a comprehensive fashion analysis using the enhanced prompt format with API rotation."""
        self.logger.info(f"Performing enhanced fashion analysis for: {image_path}")
        try:
            img = Image.open(image_path)
            
            # Generate content with enhanced prompt using API manager
            response = self.api_manager.generate_content(
                [self.comprehensive_prompt, img]
            )
            
            # Parse the JSON response
            if response and response.text:
                try:
                    analysis_result = json.loads(response.text)
                    self.logger.info(f"Enhanced fashion analysis completed for: {Path(image_path).name}")
                    return analysis_result
                except json.JSONDecodeError as json_err:
                    self.logger.error(f"JSON parsing error for {image_path}: {json_err}")
                    self.logger.error(f"Raw response: {response.text[:500]}...")
                    return None
            else:
                self.logger.error(f"Empty response from AI model for {image_path}")
                return None
                
        except Exception as e:
            self.logger.error(f"Enhanced fashion analysis failed for {image_path}: {e}")
            return None
    
    def get_api_status(self) -> Dict[str, Any]:
        """Get status of all API keys"""
        return self.api_manager.get_status()
    
    def reset_api_cooldowns(self) -> None:
        """Reset all API key cooldowns"""
        self.api_manager.reset_cooldowns()
    
    def add_api_key(self, api_key: str) -> None:
        """Add a new API key to the rotation"""
        self.api_manager.add_api_key(api_key)
    
    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> 'AIFashionAnalyzer':
        """Create AIFashionAnalyzer from configuration dict
        
        Expected config format:
        {
            'gemini_api_keys': ['key1', 'key2', 'key3'],  # List of API keys (preferred)
            'gemini_api_key': 'single_key',               # Single key for backward compatibility
            'gemini_model': 'gemini-1.5-flash-002',       # Optional
            'api_cooldown_minutes': 60,                   # Optional
            'max_retries': 3                              # Optional
        }
        """
        api_keys = config.get('gemini_api_keys')
        api_key = config.get('gemini_api_key')
        
        return cls(
            api_keys=api_keys,
            api_key=api_key,
            model_name=config.get('gemini_model', 'gemini-1.5-flash-002'),
            cooldown_minutes=config.get('api_cooldown_minutes', 60),
            max_retries=config.get('max_retries', 3)
        )
    
    def extract_training_labels(self, analysis_result: Dict) -> Dict:
        """Extract labels suitable for ML training from analysis result"""
        labels = {
            "categories": [],
            "types": [],
            "colors": [],
            "materials": [],
            "styles": [],
            "brands": [],
            "occasions": [],
            "seasons": [],
            "price_ranges": [],
            "trend_status": [],
            "tags": []
        }
        
        # Extract from fashion items analysis
        fashion_items = analysis_result.get("fashion_items_analysis", {}).get("fashion_items", [])
        
        for item in fashion_items:
            # Basic attributes
            if "category" in item:
                labels["categories"].append(item["category"].lower())
            if "type" in item:
                labels["types"].append(item["type"].lower().replace(" ", "_"))
            if "color" in item:
                colors = item["color"] if isinstance(item["color"], list) else [item["color"]]
                labels["colors"].extend([c.lower().replace(" ", "_") for c in colors])
            if "material" in item:
                labels["materials"].append(item["material"].lower().replace(" ", "_"))
            if "style" in item:
                labels["styles"].append(item["style"].lower().replace(" ", "_"))
            if "brand" in item and item["brand"] != "Unknown":
                labels["brands"].append(item["brand"].lower().replace(" ", "_"))
            
            # Extended attributes
            if "occasion_suitability" in item:
                occasions = item["occasion_suitability"] if isinstance(item["occasion_suitability"], list) else [item["occasion_suitability"]]
                labels["occasions"].extend([o.lower().replace(" ", "_") for o in occasions])
            
            if "season_appropriateness" in item:
                seasons = item["season_appropriateness"] if isinstance(item["season_appropriateness"], list) else [item["season_appropriateness"]]
                labels["seasons"].extend([s.lower() for s in seasons])
            
            if "price_range_estimate" in item:
                labels["price_ranges"].append(item["price_range_estimate"].lower().replace(" ", "_"))
            
            if "trend_status" in item:
                labels["trend_status"].append(item["trend_status"].lower())
        
        # Extract from style analysis
        style_analysis = analysis_result.get("advanced_style_analysis", {}).get("style_analysis", {})
        
        if "style_category" in style_analysis:
            labels["styles"].append(style_analysis["style_category"].lower().replace(" ", "_"))
        
        # Create comprehensive tag list
        all_labels = []
        for label_type, label_list in labels.items():
            all_labels.extend(label_list)
        
        labels["tags"] = list(set(all_labels))  # Remove duplicates
        
        # Remove duplicates from all lists
        for key in labels:
            if isinstance(labels[key], list):
                labels[key] = list(set(labels[key]))
        
        return labels

# =============================================================================
# ADVANCED STYLE ANALYSIS PROMPT (Ravindra's Enhanced Version)
# =============================================================================

    @property
    def advanced_style_prompt(self) -> str:
        """Advanced prompt for comprehensive, influencer-style fashion analysis."""
        return '''
        Based on the fashion items detected in the image, provide a comprehensive, influencer-style analysis similar to how fashion bloggers analyze celebrity and influencer outfits. Return a JSON response with the following structure:

        {
          "style_analysis": {
            "overall_aesthetic": "Detailed description of the overall style aesthetic",
            "style_category": "Specific style category (e.g., 'Soft Minimalism', 'Street Style', 'Business Casual', 'Boho Chic')",
            "influencer_matches": [
              {
                "name": "Influencer/Celebrity name",
                "instagram": "@handle",
                "similarity_reason": "Why this person's style matches",
                "style_notes": "Specific style elements they share"
              }
            ],
            "color_analysis": {
              "palette": "Primary color palette description",
              "color_harmony": "How colors work together",
              "seasonal_colors": "Seasonal color analysis",
              "color_psychology": "What the color choices convey"
            },
            "silhouette_analysis": {
              "overall_shape": "Description of the outfit's silhouette",
              "proportions": "Analysis of proportions and balance",
              "fit_philosophy": "The fit approach (oversized, fitted, etc.)"
            },
            "fabric_texture_analysis": {
              "texture_mix": "How different textures work together",
              "fabric_quality": "Perceived quality and feel",
              "seasonal_appropriateness": "How fabrics suit the season"
            },
            "styling_techniques": [
              "Specific styling techniques used in this outfit"
            ],
            "fashion_nuances": [
              "Detailed fashion details and subtle styling choices"
            ],
            "occasion_analysis": {
              "primary_occasions": ["Best occasions for this outfit"],
              "style_versatility": "How versatile this outfit is",
              "dress_code_appropriateness": "Formality level and dress codes"
            },
            "trend_analysis": {
              "current_trends": ["Current trends represented"],
              "timeless_elements": ["Timeless elements in the outfit"],
              "trend_forecast": "How this outfit fits future trends"
            },
            "brand_aesthetic": {
              "similar_brands": ["Brands with similar aesthetic"],
              "price_point": "Estimated price range",
              "luxury_indicators": ["Elements that suggest luxury or quality"]
            },
            "personal_style_insights": {
              "personality_traits": ["Personality traits this style suggests"],
              "lifestyle_indications": ["Lifestyle this outfit suggests"],
              "confidence_level": "How confident this style choice appears"
            },
            "styling_recommendations": [
              "Specific styling suggestions and improvements"
            ],
            "sustainability_notes": {
              "sustainable_aspects": ["Sustainable elements if any"],
              "longevity_potential": "How long this outfit will remain stylish",
              "investment_value": "Whether this represents good investment pieces"
            }
          }
        }

        Be extremely detailed and nuanced in your analysis. Think like a fashion expert analyzing a celebrity outfit for a high-end fashion blog. Consider:
        - Current fashion landscape and trends
        - Influencer and celebrity style patterns
        - Color theory and psychology
        - Fabric and texture relationships
        - Silhouette and proportion principles
        - Brand positioning and market segments
        - Personal style development
        - Sustainability and conscious fashion

        Provide specific, actionable insights that would help someone understand and potentially replicate this style.
        '''

    @property
    def fashion_item_identifier_prompt(self) -> str:
        """Enhanced prompt for detailed fashion item identification with taxonomy."""
        return '''
        Identify and classify all fashion-related items in the image using the defined taxonomy.
        For each detected fashion item, return a structured JSON following these rules:

        - "category": Choose from ["Clothing", "Footwear", "Accessory", "Bag"].
        - "type": The specific item type (e.g., "T-shirt", "Jeans", "Sneakers", "Watch").
        - "color": List of detected colors.
        - "material": The primary material (e.g., "Denim", "Leather", "Cotton", "Metal").
        - "style": The fashion style (e.g., "Casual", "Formal", "Sporty").
        - "brand": The visible brand name (if identifiable) or "Unknown".

        If the item belongs to "Clothing", also include:
        - "fabric_details": List of material and texture.
        - "specific_type": More specific clothing type (e.g., "Maxi Dress", "T-shirt", "Jeans").
        - "additional_attributes": Category-specific details, such as:
          - For Pants:
            - "pants_type": Choose from ["Jeans", "Chinos", "Joggers", "Formal", "Cargo"].
            - "length": Choose from ["Full Length", "Ankle", "Cropped", "Shorts"].
            - "waist": Choose from ["Rib cage", "High Waisted", "Natural Waist", "Midrise", "Lowrise", "Hip Hugger"].
          - For Shirt:
            - "shirt_style": Choose from ["Button Down", "Polo", "T-shirt", "Long Sleeve", "Short Sleeve"].
            - "neckline": Choose from ["Round", "V-neck", "Collared"].
            - "sleeve_type": Choose from ["Short Sleeve", "Long Sleeve", "Sleeveless"].
          - For Shorts:
            - "short_length": Choose from ["Short", "Knee-length", "Mid-thigh"].
            - "waist_type": Choose from ["High Waist", "Mid Waist", "Low Waist"].
          - For Skirt:
            - "skirt_length": Choose from ["Mini", "Midi", "Maxi"].
            - "waist_type": Choose from ["High Waist", "Mid Waist", "Low Waist"].
          - For Shoes:
            - "shoe_type": Choose from ["Sneakers", "Boots", "Sandals", "Formal Shoes", "Slippers"].
            - "heel_height": Choose from ["Flat", "Low", "Mid", "High"].
          - For Watches:
            - "watch_type": Choose from ["Analog", "Digital", "Smartwatch"].
            - "features": Any additional features like "Waterproof", "Smart Features", etc.
          - For Bags:
            - "bag_type": Choose from ["Handbag", "Crossbody", "Backpack", "Tote"].
            - "closure_type": Choose from ["Zipper", "Magnetic", "Button"].
            - "size": Choose from ["Small", "Medium", "Large"].
          - For Accessories:
            - "accessory_type": Choose from ["Bracelet", "Necklace", "Earrings", "Sunglasses"].
            - "material": Choose from ["Metal", "Plastic", "Wood", etc.].

        If no relevant fashion items are detected, return an empty list [].
        '''

    def advanced_comprehensive_analysis(self, image_path: str) -> Optional[Dict]:
        """Performs a two-step advanced analysis: fashion item detection + comprehensive style analysis."""
        self.logger.info(f"Performing advanced comprehensive analysis for: {image_path}")
        
        try:
            img = Image.open(image_path)
            
            # Step 1: Detect fashion items
            self.logger.info("Step 1: Detecting fashion items...")
            fashion_response = self.api_manager.generate_content(
                [self.fashion_item_identifier_prompt, img]
            )
            
            fashion_data = None
            if hasattr(fashion_response, '_result') and hasattr(fashion_response._result, 'candidates'):
                candidates = fashion_response._result.candidates
                if candidates:
                    content_text = candidates[0].content.parts[0].text
                    try:
                        fashion_data = json.loads(content_text)
                        self.logger.info("✅ Fashion items detected successfully!")
                    except json.JSONDecodeError as e:
                        self.logger.error(f"❌ Error parsing fashion items JSON: {e}")
                        return None
            
            # Step 2: Perform advanced style analysis
            self.logger.info("Step 2: Performing advanced style analysis...")
            
            # Create combined prompt with detected items
            combined_prompt = f"""
Based on these detected fashion items:
{json.dumps(fashion_data, indent=2) if fashion_data else "No fashion items detected"}

{self.advanced_style_prompt}
"""
            
            style_response = self.api_manager.generate_content(
                [combined_prompt, img]
            )
            
            style_analysis = None
            if hasattr(style_response, '_result') and hasattr(style_response._result, 'candidates'):
                candidates = style_response._result.candidates
                if candidates:
                    content_text = candidates[0].content.parts[0].text
                    try:
                        style_analysis = json.loads(content_text)
                        self.logger.info("✅ Advanced style analysis completed!")
                    except json.JSONDecodeError as e:
                        self.logger.error(f"❌ Error parsing style analysis JSON: {e}")
            
            # Combine results
            combined_result = {
                "fashion_items": fashion_data.get("fashion_items", []) if fashion_data else [],
                "style_analysis": style_analysis.get("style_analysis", {}) if style_analysis else {},
                "analyzed_at": datetime.now().isoformat(),
                "ai_model_version": "v3.0.0-advanced"
            }
            
            return combined_result
            
        except Exception as e:
            self.logger.error(f"Error in advanced comprehensive analysis: {e}")
            return None

    def format_advanced_output(self, analysis_result: Dict) -> str:
        """Format the advanced analysis into a readable, influencer-style report."""
        output = []
        
        # Header
        output.append("🎨 **Advanced Fashion Analysis Report**")
        output.append("=" * 60)
        output.append("")
        
        # Fashion Items Section
        fashion_items = analysis_result.get("fashion_items", [])
        if fashion_items:
            output.append("👕 **Detected Fashion Items:**")
            output.append("")
            
            for i, item in enumerate(fashion_items, 1):
                output.append(f"**{i}. {item.get('type', 'Unknown Item')}**")
                
                # Category and basic info
                category = item.get('category', 'Unknown')
                colors = item.get('color', [])
                material = item.get('material', 'Unknown')
                style = item.get('style', 'Unknown')
                
                output.append(f"   • **Category:** {category}")
                output.append(f"   • **Colors:** {', '.join(colors) if isinstance(colors, list) else colors}")
                output.append(f"   • **Material:** {material}")
                output.append(f"   • **Style:** {style}")
                
                # Brand if available
                brand = item.get('brand', 'Unknown')
                if brand != 'Unknown':
                    output.append(f"   • **Brand:** {brand}")
                
                # Additional attributes for clothing
                if category == "Clothing" and 'additional_attributes' in item:
                    attrs = item['additional_attributes']
                    if attrs:
                        output.append(f"   • **Details:** {', '.join([f'{k}: {v}' for k, v in attrs.items()])}")
                
                output.append("")
        
        # Advanced Style Analysis Section
        style_analysis = analysis_result.get("style_analysis", {})
        if style_analysis:
            output.append("🎯 **Comprehensive Style Analysis:**")
            output.append("")
            
            # Overall Aesthetic
            overall_aesthetic = style_analysis.get('overall_aesthetic', 'Not specified')
            style_category = style_analysis.get('style_category', 'Not specified')
            output.append(f"**Overall Aesthetic:** {overall_aesthetic}")
            output.append(f"**Style Category:** {style_category}")
            output.append("")
            
            # Influencer Matches
            influencer_matches = style_analysis.get('influencer_matches', [])
            if influencer_matches:
                output.append("🌟 **Style Influencer Matches:**")
                for match in influencer_matches:
                    name = match.get('name', 'Unknown')
                    instagram = match.get('instagram', '')
                    reason = match.get('similarity_reason', '')
                    notes = match.get('style_notes', '')
                    
                    output.append(f"   **{name}** {instagram}")
                    output.append(f"   • **Why:** {reason}")
                    output.append(f"   • **Style Notes:** {notes}")
                    output.append("")
            
            # Color Analysis
            color_analysis = style_analysis.get('color_analysis', {})
            if color_analysis:
                output.append("🎨 **Color Analysis:**")
                palette = color_analysis.get('palette', 'Not specified')
                harmony = color_analysis.get('color_harmony', 'Not specified')
                seasonal = color_analysis.get('seasonal_colors', 'Not specified')
                psychology = color_analysis.get('color_psychology', 'Not specified')
                
                output.append(f"   • **Palette:** {palette}")
                output.append(f"   • **Harmony:** {harmony}")
                output.append(f"   • **Seasonal:** {seasonal}")
                output.append(f"   • **Psychology:** {psychology}")
                output.append("")
            
            # Silhouette Analysis
            silhouette = style_analysis.get('silhouette_analysis', {})
            if silhouette:
                output.append("📐 **Silhouette Analysis:**")
                shape = silhouette.get('overall_shape', 'Not specified')
                proportions = silhouette.get('proportions', 'Not specified')
                fit = silhouette.get('fit_philosophy', 'Not specified')
                
                output.append(f"   • **Shape:** {shape}")
                output.append(f"   • **Proportions:** {proportions}")
                output.append(f"   • **Fit Philosophy:** {fit}")
                output.append("")
            
            # Fabric & Texture
            fabric_analysis = style_analysis.get('fabric_texture_analysis', {})
            if fabric_analysis:
                output.append("🧵 **Fabric & Texture Analysis:**")
                texture_mix = fabric_analysis.get('texture_mix', 'Not specified')
                quality = fabric_analysis.get('fabric_quality', 'Not specified')
                seasonal = fabric_analysis.get('seasonal_appropriateness', 'Not specified')
                
                output.append(f"   • **Texture Mix:** {texture_mix}")
                output.append(f"   • **Quality:** {quality}")
                output.append(f"   • **Seasonal:** {seasonal}")
                output.append("")
            
            # Styling Techniques
            styling_techniques = style_analysis.get('styling_techniques', [])
            if styling_techniques:
                output.append("✨ **Styling Techniques:**")
                for technique in styling_techniques:
                    output.append(f"   • {technique}")
                output.append("")
            
            # Fashion Nuances
            nuances = style_analysis.get('fashion_nuances', [])
            if nuances:
                output.append("🔍 **Fashion Nuances:**")
                for nuance in nuances:
                    output.append(f"   • {nuance}")
                output.append("")
            
            # Occasion Analysis
            occasion = style_analysis.get('occasion_analysis', {})
            if occasion:
                output.append("📅 **Occasion Analysis:**")
                primary = occasion.get('primary_occasions', [])
                versatility = occasion.get('style_versatility', 'Not specified')
                dress_code = occasion.get('dress_code_appropriateness', 'Not specified')
                
                if primary:
                    output.append("   **Perfect for:**")
                    for occ in primary:
                        output.append(f"   • {occ}")
                output.append(f"   **Versatility:** {versatility}")
                output.append(f"   **Dress Code:** {dress_code}")
                output.append("")
            
            # Trend Analysis
            trend_analysis = style_analysis.get('trend_analysis', {})
            if trend_analysis:
                output.append("📈 **Trend Analysis:**")
                current = trend_analysis.get('current_trends', [])
                timeless = trend_analysis.get('timeless_elements', [])
                forecast = trend_analysis.get('trend_forecast', 'Not specified')
                
                if current:
                    output.append("   **Current Trends:**")
                    for trend in current:
                        output.append(f"   • {trend}")
                if timeless:
                    output.append("   **Timeless Elements:**")
                    for element in timeless:
                        output.append(f"   • {element}")
                output.append(f"   **Future Outlook:** {forecast}")
                output.append("")
            
            # Brand Aesthetic
            brand_aesthetic = style_analysis.get('brand_aesthetic', {})
            if brand_aesthetic:
                output.append("🏷️ **Brand Aesthetic:**")
                similar_brands = brand_aesthetic.get('similar_brands', [])
                price_point = brand_aesthetic.get('price_point', 'Not specified')
                luxury = brand_aesthetic.get('luxury_indicators', [])
                
                if similar_brands:
                    output.append("   **Similar Brands:**")
                    for brand in similar_brands:
                        output.append(f"   • {brand}")
                output.append(f"   **Price Point:** {price_point}")
                if luxury:
                    output.append("   **Luxury Indicators:**")
                    for indicator in luxury:
                        output.append(f"   • {indicator}")
                output.append("")
            
            # Personal Style Insights
            personal = style_analysis.get('personal_style_insights', {})
            if personal:
                output.append("👤 **Personal Style Insights:**")
                personality = personal.get('personality_traits', [])
                lifestyle = personal.get('lifestyle_indications', [])
                confidence = personal.get('confidence_level', 'Not specified')
                
                if personality:
                    output.append("   **Personality Traits:**")
                    for trait in personality:
                        output.append(f"   • {trait}")
                if lifestyle:
                    output.append("   **Lifestyle Indications:**")
                    for indication in lifestyle:
                        output.append(f"   • {indication}")
                output.append(f"   **Confidence Level:** {confidence}")
                output.append("")
            
            # Styling Recommendations
            recommendations = style_analysis.get('styling_recommendations', [])
            if recommendations:
                output.append("💡 **Styling Recommendations:**")
                for rec in recommendations:
                    output.append(f"   • {rec}")
                output.append("")
            
            # Sustainability Notes
            sustainability = style_analysis.get('sustainability_notes', {})
            if sustainability:
                output.append("🌱 **Sustainability Notes:**")
                aspects = sustainability.get('sustainable_aspects', [])
                longevity = sustainability.get('longevity_potential', 'Not specified')
                investment = sustainability.get('investment_value', 'Not specified')
                
                if aspects:
                    output.append("   **Sustainable Elements:**")
                    for aspect in aspects:
                        output.append(f"   • {aspect}")
                output.append(f"   **Longevity:** {longevity}")
                output.append(f"   **Investment Value:** {investment}")
                output.append("")
        
        # Footer
        output.append("=" * 60)
        output.append(f"*Advanced analysis generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}*")
        
        return "\n".join(output)

def main():
    """Test the AI Fashion Analyzer"""
    print("🤖 AI Fashion Analyzer Test")
    print("=" * 40)
    
    # IMPORTANT: Set your Gemini API key as an environment variable
    # (e.g., export GEMINI_API_KEY='your_key_here')
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        print("ERROR: GEMINI_API_KEY environment variable not set.")
        return
    
    analyzer = AIFashionAnalyzer(api_key)
    
    # Test with a sample image (replace with a real image path)
    # You can download a test image or use one from the scraper's output
    test_image = "path/to/your/test_image.jpg"
    
    if Path(test_image).exists():
        print(f"Analyzing test image: {test_image}")
        result = analyzer.comprehensive_analysis(test_image)
        
        if result:
            print("\n✅ Analysis successful!")
            # Pretty print the JSON result
            print(json.dumps(result, indent=2))
            
            # Extract training labels
            labels = analyzer.extract_training_labels(result)
            print("\n🏷️ Extracted Training Labels:")
            print(json.dumps(labels, indent=2))
        else:
            print("\n❌ Analysis failed. Check logs for details.")
    else:
        print(f"Test image not found: {test_image}")
        print("Please update the 'test_image' variable with a valid path.")

if __name__ == "__main__":
    main()
