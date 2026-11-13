from typing import Dict, Any, Optional


CANTEEN_MENU = {
    "high_protein": [
        {"name": "Paneer Sandwich", "cal": 320, "protein": "high", "price": 60, "tag": "🥪"},
        {"name": "Egg Bhurji + Bread", "cal": 280, "protein": "high", "price": 50, "tag": "🍳"},
        {"name": "Boiled Eggs (2)", "cal": 155, "protein": "high", "price": 30, "tag": "🥚"},
        {"name": "Curd + Fruit Bowl", "cal": 180, "protein": "medium", "price": 40, "tag": "🥣"},
        {"name": "Sprouts Salad", "cal": 140, "protein": "high", "price": 45, "tag": "🥗"},
        {"name": "Chicken Sandwich (if available)", "cal": 350, "protein": "high", "price": 80, "tag": "🥪"},
        {"name": "Dal Rice Plate", "cal": 380, "protein": "medium", "price": 70, "tag": "🍛"},
    ],
    "balanced": [
        {"name": "Veg Thali (Mini)", "cal": 450, "protein": "medium", "price": 80, "tag": "🍛"},
        {"name": "Rajma Chawal", "cal": 420, "protein": "medium", "price": 70, "tag": "🍛"},
        {"name": "Chole + Rice", "cal": 400, "protein": "medium", "price": 65, "tag": "🍛"},
        {"name": "Idli (3 pcs) + Sambar", "cal": 280, "protein": "medium", "price": 50, "tag": "🥞"},
        {"name": "Poha + Jalebi (small)", "cal": 320, "protein": "low", "price": 40, "tag": "🍚"},
        {"name": "Upma + Chutney", "cal": 260, "protein": "low", "price": 35, "tag": "🍲"},
        {"name": "Veg Sandwich", "cal": 240, "protein": "low", "price": 45, "tag": "🥪"},
    ],
    "light": [
        {"name": "Fruit Chat", "cal": 120, "protein": "low", "price": 40, "tag": "🍎"},
        {"name": "Buttermilk / Chaas", "cal": 60, "protein": "low", "price": 20, "tag": "🥛"},
        {"name": "Roasted Chana", "cal": 110, "protein": "medium", "price": 25, "tag": "🥜"},
        {"name": "Banana + Milk", "cal": 180, "protein": "medium", "price": 35, "tag": "🍌"},
        {"name": "Cucumber + Carrot Sticks", "cal": 50, "protein": "low", "price": 30, "tag": "🥕"},
    ],
    "avoid": [
        "Samosa (deep fried)", "Vada Pav", "French Fries",
        "Cold Drinks / Soda", "Maggi (excess)", "Pizza slice (regular)",
    ],
}


def recommend_canteen_meal(profile: Dict[str, Any], journey: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    goal = (profile.get("fitness_goal") or "general_wellness").lower()
    journey_cal = (journey or {}).get("calories_burned", 0)

    if goal == "build_strength":
        primary = CANTEEN_MENU["high_protein"][:3]
        side = CANTEEN_MENU["balanced"][:1]
        category = "High Protein (for muscle recovery)"
    elif goal == "improve_endurance":
        primary = CANTEEN_MENU["balanced"][:3]
        side = CANTEEN_MENU["light"][:2]
        category = "Balanced Meal (for sustained energy)"
    elif goal == "improve_fitness":
        primary = CANTEEN_MENU["balanced"][:2] + CANTEEN_MENU["high_protein"][:1]
        side = CANTEEN_MENU["light"][:1]
        category = "Balanced + Protein Mix"
    elif goal == "stay_active":
        primary = CANTEEN_MENU["light"][:3]
        side = CANTEEN_MENU["balanced"][:1]
        category = "Light & Fresh"
    else:
        primary = CANTEEN_MENU["balanced"][:3]
        side = CANTEEN_MENU["light"][:2]
        category = "Balanced Meal"

    hydration = "Drink 500ml water before meal"
    if journey_cal > 100:
        hydration = f"You burned ~{journey_cal} kcal on the way — rehydrate with 500ml water + electrolytes"

    tips = []
    if journey_cal > 50:
        tips.append("Great walk/cycle! You earned a proper meal 🎉")
    if goal == "build_strength":
        tips.append("Add a protein source to every meal — paneer, eggs, dal, or curd")
    if goal == "improve_endurance":
        tips.append("Include complex carbs (rice/roti) for sustained energy through classes")
    tips.append("Avoid sugary drinks — choose buttermilk or water instead")

    return {
        "category": category,
        "recommended": primary,
        "side_options": side,
        "avoid": CANTEEN_MENU["avoid"][:4],
        "hydration_tip": hydration,
        "tips": tips,
        "disclaimer": "General suggestions only — not medical/dietary advice.",
    }
