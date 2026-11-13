import re
from app.ai.gemini_client import generate_text
from typing import Dict, Any

from app.config import settings


SYSTEM_PROMPT = (
    "You are FitCampus AI, a friendly student fitness assistant. "
    "You help with exercise guidance, activity ideas, general diet tips, and motivation. "
    "Never give medical diagnoses. Always recommend professional help for medical issues. "
    "Keep responses concise, encouraging, and practical."
)


def _has(pattern: str, text: str) -> bool:
    return re.search(pattern, text) is not None


async def _rule_based_reply(message: str, profile: Dict[str, Any]) -> str:
    m = message.lower()
    name = profile.get("name", "there")
    goal = (profile.get("fitness_goal") or "general_wellness").replace("_", " ")

    if _has(r"\b(motivat\w*|tired|lazy|unmotivated)\b", m):
        return (
            f"You've got this, {name}! 💪 Even a 10-minute walk counts. "
            f"Remember your goal: {goal}. Small consistent steps beat occasional big efforts."
        )
    if _has(r"\b(diet|food|eat|meal|nutrition)\b", m):
        return (
            "For balanced student meals: include a protein source (eggs, dal, paneer, chicken), "
            "complex carbs (roti, rice, oats), vegetables, and healthy fats (nuts, seeds). "
            "Stay hydrated — aim for 2–3 L of water daily. Avoid crash diets; they're unsustainable."
        )
    if _has(r"\b(squats?|push-?ups?|form)\b", m):
        return (
            "Great question on form! For squats: feet shoulder-width, chest up, knees track over toes, "
            "go until thighs are parallel. For push-ups: hands shoulder-width, body straight, "
            "lower until elbows ~90°. Use the Form Check feature for live feedback."
        )
    if _has(r"\b(workout|exercise|suggest)\b|what should i do", m):
        level = profile.get("fitness_level", "beginner")
        if level == "beginner":
            return "Try a 20-min brisk walk + 10-min stretching today. Easy and effective!"
        if level == "intermediate":
            return "How about a 25-min jog + 3 sets of squats and push-ups?"
        return "Push it: 30-min run + HIIT circuit + core work. You're strong!"
    if _has(r"\b(streak|rank|points?)\b", m):
        pts = profile.get("points", 0)
        streak = profile.get("current_streak", 0)
        return f"You have {pts} points and a {streak}-day streak 🔥. Keep going to climb the leaderboard!"
    if _has(r"\b(hello|hi|hey)\b", m):
        return f"Hi {name}! 👋 How can I help you stay active today?"
    if _has(r"\bthank", m):
        return "Anytime! Keep moving 🏃‍♂️"

    return (
        "I'm here to help with workouts, form tips, activity ideas, and general wellness. "
        "Try asking: 'Suggest a workout', 'How do I do squats?', or 'Give me diet tips'."
    )


async def chat(message: str, profile: Dict[str, Any]) -> Dict[str, str]:
    message = (message or "")[:1000]
    system = SYSTEM_PROMPT + f" Student: {profile.get('name')}, level {profile.get('fitness_level')}, goal {profile.get('fitness_goal')}."
    reply = await generate_text(message, system=system, max_tokens=300, timeout=20.0)
    if reply:
        return {"reply": reply, "source": "llm"}
    return {"reply": await _rule_based_reply(message, profile), "source": "rule_based"}