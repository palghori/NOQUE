"""
gemini_client.py — Centralized Google Gemini API client.
Handles all interactions with the Gemini model.
Includes automatic retry and model fallback for resilience.
"""
import json
import time
from google import genai
from google.genai import errors as genai_errors
from config import get_settings

settings = get_settings()
import itertools

keys_str = getattr(settings, "GEMINI_API_KEYS", "")
all_keys = [k.strip() for k in keys_str.split(",") if k.strip()]
if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY not in all_keys:
    all_keys.insert(0, settings.GEMINI_API_KEY)
if not all_keys:
    all_keys = [""]

clients = [genai.Client(api_key=k) for k in all_keys]
client_cycle = itertools.cycle(clients)

def get_next_client():
    return next(client_cycle)

# Fallback models in order of preference
FALLBACK_MODELS = [
    settings.GEMINI_MODEL,      # Primary (gemini-3.6-flash)
    "gemini-3.5-flash-lite",    # Fast fallback
    "gemini-flash-latest",      # Generic latest fallback
    "gemini-3.5-flash",         # Previous gen fallback
]

MAX_RETRIES = 5
RETRY_DELAY = 10  # seconds


import asyncio

async def call_gemini(prompt: str, system_instruction: str = "", max_tokens: int = 8192) -> str:
    """
    Send a prompt to Gemini and return the text response.
    Automatically retries with fallback models on 503/429 errors.
    """
    config = genai.types.GenerateContentConfig(
        max_output_tokens=max_tokens,
        temperature=0.2,  # Low temperature for deterministic, accurate output
    )
    if system_instruction:
        config.system_instruction = system_instruction

    last_error = None

    for model_name in FALLBACK_MODELS:
        for attempt in range(MAX_RETRIES):
            try:
                # IMPORTANT: Use .aio. for async calls so we don't block the FastAPI event loop
                response = await get_next_client().aio.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=config,
                )
                return response.text
            except genai_errors.ClientError as e:
                last_error = e
                error_str = str(e)
                # 503 UNAVAILABLE or 429 RESOURCE_EXHAUSTED → retry/fallback
                if "503" in error_str or "429" in error_str:
                    print(f"[NOQUE] Model {model_name} attempt {attempt+1} failed ({error_str[:60]}), retrying...")
                    await asyncio.sleep(RETRY_DELAY * (attempt + 1))
                    continue
                else:
                    # Other errors (400, 404, etc.) → don't retry, re-raise
                    raise
            except Exception as e:
                last_error = e
                print(f"[NOQUE] Unexpected error with {model_name}: {e}")
                await asyncio.sleep(RETRY_DELAY)
                break  # Move to next model

    # If all models and retries exhausted, raise the last error
    raise last_error


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
