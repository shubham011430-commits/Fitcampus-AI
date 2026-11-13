import asyncio

from app.config import settings
from google import genai


async def test_gemini():

    async with genai.Client(
        api_key=settings.gemini_api_key
    ).aio as client:

        response = await client.models.generate_content(
            model=settings.ai_model,
            contents="Say: FitCampus Gemini Connected!"
        )

        print("Gemini Response:")
        print(response.text)


asyncio.run(test_gemini())