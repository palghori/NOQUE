"""
gemini_client.py — Centralized Google Gemini API client.
Handles all interactions with the Gemini model.
Includes automatic retry, key rotation, and model fallback for resilience.
"""
import json
import time
import asyncio
import itertools
import os
from google import genai
from google.genai import errors as genai_errors
from config import get_settings

settings = get_settings()

# ============================================================
# BULLETPROOF KEY LOADING — reads from ALL possible sources
# ============================================================
all_keys = []

# Source 1: GEMINI_API_KEYS (plural, comma-separated)
keys_str = os.environ.get("GEMINI_API_KEYS", "") or getattr(settings, "GEMINI_API_KEYS", "")
for k in keys_str.split(","):
    k = k.strip()
    if k and k not in all_keys:
        all_keys.append(k)

# Source 2: GEMINI_API_KEY (singular)
single_key = os.environ.get("GEMINI_API_KEY", "") or getattr(settings, "GEMINI_API_KEY", "")
if single_key and single_key.strip() not in all_keys:
    all_keys.insert(0, single_key.strip())

if not all_keys:
    all_keys = [""]

print(f"[NOQUE] ====== LOADED {len(all_keys)} API KEYS ======")
for i, k in enumerate(all_keys):
    print(f"[NOQUE] Key {i+1}: {k[:8]}...{k[-4:] if len(k) > 12 else '???'}")

clients = [genai.Client(api_key=k) for k in all_keys]
_key_index = 0
_key_lock = asyncio.Lock()

async def get_next_client():
    """Thread-safe round-robin client selection."""
    global _key_index
    async with _key_lock:
        client = clients[_key_index % len(clients)]
        _key_index += 1
        return client

# Fallback models
FALLBACK_MODELS = [
    settings.GEMINI_MODEL,      # Primary (gemini-3.6-flash)
    "gemini-3.5-flash-lite",
    "gemini-3.5-flash",
]

MAX_RETRIES = 3
BASE_RETRY_DELAY = 15  # Start with 15 seconds, then exponential

# ============================================================
# STRICT GLOBAL RATE LIMITER
# With 4 keys @ 15 RPM each = 60 RPM total = 1 request per second
# But we'll be safe and force 4 second gaps
# ============================================================
_last_call_time = 0.0
_rate_lock = asyncio.Lock()
MIN_CALL_GAP = 4.0  # seconds between any two API calls

async def _enforce_rate_limit():
    """Ensure at least MIN_CALL_GAP seconds between consecutive API calls."""
    global _last_call_time
    async with _rate_lock:
        now = time.time()
        wait = MIN_CALL_GAP - (now - _last_call_time)
        if wait > 0:
            print(f"[NOQUE] Rate limiter: waiting {wait:.1f}s")
            await asyncio.sleep(wait)
        _last_call_time = time.time()


async def call_gemini(prompt: str, system_instruction: str = "", max_tokens: int = 8192) -> str:
    """
    Send a prompt to Gemini and return the text response.
    Automatically retries with exponential backoff and fallback models.
    """
    config = genai.types.GenerateContentConfig(
        max_output_tokens=max_tokens,
        temperature=0.2,
    )
    if system_instruction:
        config.system_instruction = system_instruction

    last_error = None

    for model_name in FALLBACK_MODELS:
        for attempt in range(MAX_RETRIES):
            try:
                # Enforce strict rate limit BEFORE every call
                await _enforce_rate_limit()
                
                client = await get_next_client()
                print(f"[NOQUE] Calling {model_name} (attempt {attempt+1}, key #{_key_index % len(clients)})")
                
                response = await client.aio.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=config,
                )
                print(f"[NOQUE] SUCCESS with {model_name}")
                return response.text
                
            except genai_errors.ClientError as e:
                last_error = e
                error_str = str(e)
                if "503" in error_str or "429" in error_str:
                    # Exponential backoff: 15s, 30s, 60s
                    delay = BASE_RETRY_DELAY * (2 ** attempt)
                    print(f"[NOQUE] {model_name} attempt {attempt+1} FAILED (429/503). Waiting {delay}s before retry...")
                    await asyncio.sleep(delay)
                    continue
                else:
                    raise
            except Exception as e:
                last_error = e
                print(f"[NOQUE] Unexpected error with {model_name}: {e}")
                await asyncio.sleep(BASE_RETRY_DELAY)
                break  # Move to next model

    raise last_error


async def call_gemini_json(prompt: str, system_instruction: str = "", max_tokens: int = 8192) -> dict | list:
    """
    Call Gemini and parse the response as JSON.
    """
    raw = await call_gemini(prompt, system_instruction, max_tokens)

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
        return {"raw_response": raw}
