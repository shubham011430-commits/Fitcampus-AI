"""
Hybrid diet recommender: Gemini API + rule-based fallback.
Respects allergies and dietary preferences.
"""
from typing import Dict, Any, List, Optional
from app.ai.gemini_client import generate_diet_recommendation


# Rule-based meal library (fallback)
MEALS = {
    "breakfast": {
        "veg": ["Oats with banana & nuts", "Vegetable poha", "Whole-grain toast with peanut butter", "Sprouts + fruit", "Idli with sambar"],
        "non_veg": ["Egg white omelette + toast", "Boiled eggs + fruit", "Paneer bhurji + roti"],
        "vegan": ["Oats with almond milk & berries", "Fruit smoothie bowl", "Poha without ghee"],
        "eggetarian": ["Egg white omelette + toast", "Oats with banana", "Sprouts + fruit"],
    },
    "lunch": {
        "veg": ["Roti + dal + sabzi + salad", "Brown rice + rajma + curd", "Veg thali (mini)", "Mixed veg khichdi + curd"],
        "non_veg": ["Roti + chicken/paneer + sabzi", "Rice + fish curry + veggies", "Egg curry + roti"],
        "vegan": ["Roti + dal + sabzi", "Brown rice + chole + salad", "Quinoa bowl with veggies"],
        "eggetarian": ["Roti + dal + sabzi + egg", "Rice + egg curry + salad"],
    },
    "dinner": {
        "veg": ["Roti + sabzi + dal", "Paneer tikka + salad", "Veg soup + bread"],
        "non_veg": ["Grilled chicken/fish + veggies", "Dal + roti + sabzi", "Egg curry + roti"],
        "vegan": ["Roti + dal + sabzi", "Veg soup + sandwich", "Tofu curry + roti"],
        "eggetarian": ["Roti + dal + sabzi + egg", "Paneer/egg bhurji + roti"],
    },
    "snacks": ["Handful of nuts", "Fruit (apple/banana/orange)", "Roasted chana", "Yogurt", "Vegetable sticks + hummus", "Buttermilk"],
}


def _has_allergen(item_name: str, allergens: List[str]) -> bool:
    """Check if an item likely contains an allergen (simple heuristic)."""
    name_lower = item_name.lower()
    allergen_map = {
        "peanuts": ["peanut", "groundnut", "moongfali"],
        "dairy": ["milk", "curd", "yogurt", "paneer", "ghee", "cheese", "butter", "lassi"],
        "gluten": ["wheat", "roti", "bread", "maida", "paratha"],
        "eggs": ["egg", "omelette", "bhurji"],
        "soy": ["soy", "tofu", "soya"],
        "nuts": ["nuts", "almond", "cashew", "walnut", "pista"],
    }
    for allergen in allergens:
        keywords = allergen_map.get(allergen.lower(), [allergen.lower()])
        if any(kw in name_lower for kw in keywords):
            return True
    return False


def _filter_by_preference(items: List[str], preference: str, allergens: List[str]) -> List[str]:
    """Filter items by dietary preference and allergens."""
    filtered = []
    for item in items:
        if _has_allergen(item, allergens):
            continue
        # Simple preference filter
        if preference == "vegan" and any(w in item.lower() for w in ["egg", "paneer", "curd", "ghee", "milk"]):
            continue
        if preference == "veg" and any(w in item.lower() for w in ["chicken", "fish", "egg"]):
            continue
        if preference == "eggetarian" and any(w in item.lower() for w in ["chicken", "fish"]):
            continue
        filtered.append(item)
    return filtered


def _rule_based_recommendation(profile: Dict[str, Any], menu_items: List[Dict]) -> Dict[str, Any]:
    """Rule-based fallback recommendation."""
    preference = (profile.get("dietary_preference") or "veg").lower()
    allergens = profile.get("allergies") or []
    goal = (profile.get("fitness_goal") or "general_wellness").lower()

    # Get meals for preference
    breakfast = _filter_by_preference(MEALS["breakfast"].get(preference, MEALS["breakfast"]["veg"]), preference, allergens)
    lunch = _filter_by_preference(MEALS["lunch"].get(preference, MEALS["lunch"]["veg"]), preference, allergens)
    dinner = _filter_by_preference(MEALS["dinner"].get(preference, MEALS["dinner"]["veg"]), preference, allergens)
    snacks = _filter_by_preference(MEALS["snacks"], preference, allergens)

    # Prefer menu items when available
    if menu_items:
        menu_by_meal = {"breakfast": [], "lunch": [], "snacks": [], "dinner": []}
        for item in menu_items:
            if _has_allergen(item.get("name", ""), allergens):
                continue
            cat = item.get("category", "veg")
            if preference == "vegan" and cat in ["non_veg"]:
                continue
            if preference == "veg" and cat == "non_veg":
                continue
            meal = item.get("meal_type")
            if meal in menu_by_meal:
                menu_by_meal[meal].append(item["name"])

        # Mix menu items with fallback
        for meal_type in ["breakfast", "lunch", "dinner", "snacks"]:
            if menu_by_meal[meal_type]:
                # Use up to 2 menu items + 1 fallback
                combined = menu_by_meal[meal_type][:2]
                fallback = {"breakfast": breakfast, "lunch": lunch, "dinner": dinner, "snacks": snacks}[meal_type]
                for fb in fallback:
                    if fb not in combined and len(combined) < 3:
                        combined.append(fb)
                if meal_type == "breakfast": breakfast = combined
                elif meal_type == "lunch": lunch = combined
                elif meal_type == "dinner": dinner = combined
                else: snacks = combined

    # Calorie target
    weight = profile.get("weight") or 70
    activity = (profile.get("activity_level") or "low").lower()
    mult = {"low": 25, "moderate": 30, "high": 35, "very_high": 40}.get(activity, 25)
    target = weight * mult
    if goal == "build_strength":
        target += 300
    elif goal == "stay_active":
        target -= 100

    hydration = f"Target ~{max(2, round(weight * 0.033, 1))} L water daily"

    # Reasoning
    reasons = []
    if menu_items:
        reasons.append("Suggestions prioritize items available in your mess/canteen.")
    if allergens:
        reasons.append(f"Allergens avoided: {', '.join(allergens)}.")
    if goal == "build_strength":
        reasons.append("Higher calories for muscle recovery and strength gains.")
    elif goal == "improve_endurance":
        reasons.append("Balanced carbs for sustained energy.")
    reasons.append("General wellness guidance only — not medical advice.")

    return {
        "breakfast": breakfast[:3],
        "lunch": lunch[:3],
        "dinner": dinner[:3],
        "snacks": snacks[:4],
        "daily_calories_target": int(target),
        "hydration": hydration,
        "reasoning": " ".join(reasons),
        "tips": [
            "Eat slowly and mindfully — avoid rushing through meals between classes.",
            "Include a protein source in every main meal.",
            "Avoid sugary drinks; choose water, buttermilk, or fresh juice.",
        ],
        "source": "rule_based",
    }


async def recommend_diet(profile: Dict[str, Any], menu_items: List[Dict]) -> Dict[str, Any]:
    """
    Try Gemini first, fall back to rule-based.
    Always validates allergens in the final output.
    """
    allergens = profile.get("allergies") or []

    # Try Gemini
    gemini_result = await generate_diet_recommendation(profile, menu_items)
    if gemini_result:
        # Validate allergens in Gemini output
        for meal_key in ["breakfast", "lunch", "dinner", "snacks"]:
            items = gemini_result.get(meal_key, [])
            safe_items = [i for i in items if not _has_allergen(i, allergens)]
            gemini_result[meal_key] = safe_items
        gemini_result["source"] = "gemini"
        if "tips" not in gemini_result:
            gemini_result["tips"] = ["General wellness guidance only — not medical advice."]
        return gemini_result

    # Fallback to rule-based
    result = _rule_based_recommendation(profile, menu_items)
    return result