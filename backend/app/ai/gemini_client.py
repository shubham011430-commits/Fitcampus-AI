"""Single Gemini client used by both the diet recommender and the chat assistant."""
import asyncio
import json
import logging
from typing import Any, Dict, Optional

import httpx

from app.config import settings

log = logging.getLogger("fitcampus.gemini")
BASE = "https://generativelanguage.googleapis.com/v1beta/models"


async def generate_text(
    prompt: str,
    system: Optional[str] = None,
    json_mode: bool = False,
    max_tokens: int = 1024,
    temperature: float = 0.7,
    timeout: float = 20.0,
) -> Optional[str]:
    """Return model text, or None if unconfigured or the call fails."""
    key = (settings.gemini_api_key or "").strip()
    if not key:
        return None

    body: Dict[str, Any] = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens},
    }
    if system:
        body["systemInstruction"] = {"parts": [{"text": system}]}
    if json_mode:
        body["generationConfig"]["responseMimeType"] = "application/json"

    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(60.0, connect=15.0)
        ) as client:

            for attempt in range(3):
                resp = await client.post(
                    f"{BASE}/{settings.ai_model}:generateContent",
                    headers={
                        "Content-Type": "application/json",
                        "x-goog-api-key": key,
                    },
                    json=body,
                )

                if resp.status_code == 200:
                    return (
                        resp.json()["candidates"][0]["content"]["parts"][0]["text"]
                        .strip()
                    )

                if resp.status_code == 503 and attempt < 2:
                    delay = 2 ** (attempt + 1)
                    log.warning(
                        "Gemini is busy (503). Retrying in %s seconds...",
                        delay,
                    )
                    await asyncio.sleep(delay)
                    continue

                log.warning(
                    "Gemini HTTP %s: %s",
                    resp.status_code,
                    resp.text[:200],
                )
                return None

    except httpx.TimeoutException:
        log.warning("Gemini request timed out.")
        return None
    except httpx.HTTPError:
        log.exception("Gemini network request failed")
        return None
    except Exception:
        log.exception("Unexpected Gemini error")
        return None
    
async def generate_diet_recommendation(
    profile: Dict[str, Any], menu_items: list, context: str = ""
) -> Optional[Dict[str, Any]]:
    items = "\n".join(
        f"- {i['name']} ({i['meal_type']}, {i.get('calories', 'N/A')} kcal, {i.get('category', 'veg')})"
        for i in menu_items[:20]
    )
    prompt = f"""Provide a practical daily meal plan for this Indian college student.

PROFILE: age {profile.get('age')}, {profile.get('weight')} kg, {profile.get('height')} cm,
level {profile.get('fitness_level')}, activity {profile.get('activity_level')},
goal {profile.get('fitness_goal')}, diet {profile.get('dietary_preference')},
allergies {profile.get('allergies', [])}, type {profile.get('student_type')}.

AVAILABLE MENU:
{items}
{context}

Rules: never include the listed allergens; respect the diet preference; prefer menu items;
keep it budget friendly; this is general wellness guidance, not medical advice.

Return JSON with keys: breakfast, lunch, snacks, dinner (lists of strings),
daily_calories_target (int), hydration (string), reasoning (string), tips (list of strings)."""
    text = await generate_text(prompt, json_mode=True, max_tokens=1024, timeout=20.0)
    if not text:
        return None
    if text.startswith("```"):
        text = text.strip("`").removeprefix("json").strip()
    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        return None