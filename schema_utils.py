import logging
from typing import Any, Dict, List

# Define required schema fields and defaults for FashionLook, FashionItem, and StyleAnalysis
REQUIRED_FASHION_ITEM_FIELDS = {
    "category": "Unknown",
    "specific_type": "Unknown",
    "color": "Unknown",
    "pattern": "Unknown",
    "material": "Unknown",
    "brand": "Unknown"
}

REQUIRED_STYLE_ANALYSIS_FIELDS = {
    "overall_aesthetic": "Unknown",
    "style_category": "Unknown",
    "influencer_matches": [],
    "color_analysis": {},
    "silhouette_analysis": {},
    "fabric_texture_analysis": {},
    "styling_techniques": [],
    "fashion_nuances": [],
    "occasion_analysis": {},
    "trend_analysis": {},
    "brand_aesthetic": {},
    "personal_style_insights": {},
    "styling_recommendations": [],
    "sustainability_notes": {}
}

REQUIRED_FASHION_LOOK_FIELDS = {
    "fashion_items": [],
    "style_analysis": {},
}

def ensure_analysis_schema(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure the AI analysis dict matches the Pinterest pin ai_analysis schema, filling defaults if needed.
    """
    return {
        "description": data.get("description", ""),
        "tags": data.get("tags", []),
        "dominant_colors": data.get("dominant_colors", []),
        "season": data.get("season", ""),
        "style_category": data.get("style_category", ""),
        "gender": data.get("gender", "Unisex"),
        "ai_trend_score": float(data.get("ai_trend_score", 0.0)),
        "trend_analysis": {
            "match_with_latest_trend": bool(data.get("trend_analysis", {}).get("match_with_latest_trend", False)),
            "inspired_by": data.get("trend_analysis", {}).get("inspired_by", []),
            "fashion_cycle_stage": data.get("trend_analysis", {}).get("fashion_cycle_stage", ""),
            "social_popularity_score": int(data.get("trend_analysis", {}).get("social_popularity_score", 0)),
            "predicted_lifespan_months": int(data.get("trend_analysis", {}).get("predicted_lifespan_months", 0)),
        },
        "detected_objects": data.get("detected_objects", []),
        "ai_model_version": data.get("ai_model_version", "")
    }

def ensure_schema_compliance(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure that the AI output dict is fully compliant with the MongoDB/Pydantic schema.
    Fills missing required fields and corrects types as needed.
    """
    if not isinstance(data, dict):
        logging.warning("AI output is not a dict. Returning empty compliant object.")
        return {
            "fashion_items": [],
            "style_analysis": {**REQUIRED_STYLE_ANALYSIS_FIELDS}
        }

    # Ensure top-level fields
    for field, default in REQUIRED_FASHION_LOOK_FIELDS.items():
        if field not in data or data[field] is None:
            logging.info(f"Filling missing top-level field: {field}")
            data[field] = default.copy() if isinstance(default, list) else dict(default)

    # Ensure fashion_items is a list
    if not isinstance(data["fashion_items"], list):
        logging.info("Converting fashion_items to list.")
        data["fashion_items"] = []

    # Fix each fashion item
    for i, item in enumerate(data["fashion_items"]):
        if not isinstance(item, dict):
            logging.warning(f"Fashion item at index {i} is not a dict. Skipping.")
            continue
        for field, default in REQUIRED_FASHION_ITEM_FIELDS.items():
            if field not in item or item[field] is None:
                logging.info(f"Filling missing field in fashion_item[{i}]: {field}")
                item[field] = default
            # Convert material to string if list
            if field == "material" and isinstance(item[field], list):
                item[field] = ", ".join(str(x) for x in item[field])

    # Ensure style_analysis is a dict
    if not isinstance(data["style_analysis"], dict):
        logging.info("Converting style_analysis to dict.")
        data["style_analysis"] = dict(REQUIRED_STYLE_ANALYSIS_FIELDS)

    for field, default in REQUIRED_STYLE_ANALYSIS_FIELDS.items():
        if field not in data["style_analysis"] or data["style_analysis"][field] is None:
            logging.info(f"Filling missing field in style_analysis: {field}")
            data["style_analysis"][field] = default.copy() if isinstance(default, list) else default
        # Convert influencer_matches to list of dicts if not already
        if field == "influencer_matches" and not isinstance(data["style_analysis"][field], list):
            data["style_analysis"][field] = []
        # Convert color_palette, occasions, trends to list if not already
        if field in ["color_palette", "occasions", "trends"] and not isinstance(data["style_analysis"][field], list):
            data["style_analysis"][field] = []

    return data
