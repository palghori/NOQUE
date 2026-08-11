"""
gemini_client.py — Centralized Google Gemini API client.
Handles all interactions with the Gemini 1.5 Pro model.
"""
import json
from google import genai
from config import get_settings

settings = get_settings()
client = genai.Client(api_key=settings.GEMINI_API_KEY)


async def call_gemini(prompt: str, system_instruction: str = "", max_tokens: int = 8192) -> str:
    """
    Send a prompt to Gemini and return the text response.
    Uses the synchronous SDK wrapped for our async pipeline.
    """
    config = genai.types.GenerateContentConfig(
        max_output_tokens=max_tokens,
        temperature=0.2,  # Low temperature for deterministic, accurate output
    )
    if system_instruction:
        config.system_instruction = system_instruction

    response = client.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=prompt,
        config=config,
    )
    return response.text


async def call_gemini_json(prompt: str, system_instruction: str = "", max_tokens: int = 8192) -> dict | list:
    """
    Call Gemini and parse the response as JSON.
    Handles cases where the model wraps output in markdown code fences.
    """
    raw = await call_gemini(prompt, system_instruction, max_tokens)

    # Strip markdown code fences if present
    cleaned = raw.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # If JSON parsing fails, return the raw text wrapped in a dict
        return {"raw_response": raw}
