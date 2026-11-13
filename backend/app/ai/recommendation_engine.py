from typing import Dict, Any, List
import random


ACTIVITY_LIBRARY = [
    {"name": "10-min Warm-up", "type": "stretching", "duration": 10, "difficulty": "easy", "calories": 40, "desc": "Dynamic stretches to prepare your body."},
    {"name": "20-min Brisk Walk", "type": "walking", "duration": 20, "difficulty": "easy", "calories": 90, "desc": "A steady walk around campus."},
    {"name": "15-min Jog", "type": "running", "duration": 15, "difficulty": "medium", "calories": 140, "desc": "Light jog to boost cardio."},
    {"name": "Squat Challenge", "type": "general", "duration": 10, "difficulty": "medium", "calories": 70, "desc": "3 sets of 15 squats."},
    {"name": "Yoga Flow", "type": "yoga", "duration": 25, "difficulty": "easy", "calories": 80, "desc": "Sun salutations and breathing."},
    {"name": "30-min Run", "type": "running", "duration": 30, "difficulty": "hard", "calories": 280, "desc": "Steady-state run."},
    {"name": "Sports Session", "type": "sports", "duration": 45, "difficulty": "hard", "calories": 350, "desc": "Basketball/football with friends."},
    {"name": "Stretching Recovery", "type": "stretching", "duration": 15, "difficulty": "easy", "calories": 45, "desc": "Cool-down stretching."},
    {"name": "HIIT Quick Burst", "type": "general", "duration": 15, "difficulty": "hard", "calories": 180, "desc": "High-intensity intervals."},
    {"name": "Core Circuit", "type": "general", "duration": 20, "difficulty": "medium", "calories": 150, "desc": "Planks, crunches, leg raises."},
]


def _difficulty_for(fitness_level: str, activity_level: str) -> List[str]:
    level = (fitness_level or "beginner").lower()
    act = (activity_level or "low").lower()
    if level == "advanced" or act in ("high", "very_high"):
        return ["medium", "hard"]
    if level == "intermediate" or act == "moderate":
        return ["easy", "medium"]
    return ["easy"]


def _goal_bias(goal: str) -> List[str]:
    g = (goal or "general_wellness").lower()
    if g == "build_strength":
        return ["general", "sports"]
    if g == "improve_endurance":
        return ["running", "walking"]
    if g == "improve_fitness":
        return ["running", "general", "sports"]
    if g == "stay_active":
        return ["walking", "stretching", "yoga"]
    return ["walking", "stretching", "yoga", "general"]


def recommend_daily_activities(profile: Dict[str, Any], recent_types: List[str],
                               available_minutes: int = 60) -> List[Dict[str, Any]]:
    diffs = _difficulty_for(profile.get("fitness_level"), profile.get("activity_level"))
    bias = _goal_bias(profile.get("fitness_goal"))
    recent = set((recent_types or [])[:3])  # recent_types holds activity *types*

    candidates = [
        a for a in ACTIVITY_LIBRARY
        if a["difficulty"] in diffs and a["type"] in bias and a["duration"] <= available_minutes
    ]
    fresh = [a for a in candidates if a["type"] not in recent]
    candidates = fresh or candidates
    if not candidates:
        candidates = [a for a in ACTIVITY_LIBRARY if a["duration"] <= available_minutes]

    random.shuffle(candidates)
    return candidates[:4]


def recommend_exercises(profile: Dict[str, Any]) -> List[Dict[str, Any]]:
    level = (profile.get("fitness_level") or "beginner").lower()
    base = [
        {"name": "Squats", "difficulty": "easy", "reps": 15, "desc": "Keep back straight, knees over toes."},
        {"name": "Push-ups", "difficulty": "medium", "reps": 10, "desc": "Core tight, full range of motion."},
        {"name": "Lunges", "difficulty": "medium", "reps": 12, "desc": "Alternate legs, knee at 90°."},
        {"name": "Jumping Jacks", "difficulty": "easy", "reps": 30, "desc": "Cardio warm-up."},
        {"name": "Plank", "difficulty": "medium", "duration_sec": 30, "desc": "Keep body in straight line."},
        {"name": "Stretching", "difficulty": "easy", "duration_sec": 300, "desc": "Full-body mobility."},
    ]
    if level == "beginner":
        return base[:4] + [base[5]]
    if level == "advanced":
        return base
    return base[:5]
