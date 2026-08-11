"""
refactorer.py — Generates modernized code and breaking change warnings using Gemini.
"""
from services.gemini_client import call_gemini_json

SYSTEM_PROMPT = """You are a Senior Software Architect specializing in legacy code modernization.
You modernize code to follow current best practices while preserving all original functionality.
You MUST identify every breaking change and migration risk.
You must return ONLY valid JSON, no markdown fences, no extra text."""

REFACTOR_PROMPT = """Modernize the following legacy source code.

**File:** `{file_path}`
**Language:** {language}

```
{code}
```

Return your result as JSON in this exact format:
{{
  "refactored_code": "The complete modernized code as a single string.",
  "breaking_changes": [
    {{
      "change": "What was changed (e.g., 'Renamed function X to Y')",
      "risk": "high | medium | low",
      "migration_note": "What the developer needs to do to migrate (e.g., 'Update all callers of X to use Y instead')"
    }}
  ]
}}

Modernization rules:
- **Python:** Convert Python 2 syntax to Python 3.10+. Use type hints, f-strings, pathlib, dataclasses, match statements where appropriate. Replace `print` statements with logging. Replace `os.path` with `pathlib`.
- **JavaScript:** Convert `var` to `const`/`let`. Use arrow functions, template literals, async/await, ES module imports. Replace callbacks with Promises.
- Improve variable names if they are single-letter or cryptic.
- Add docstrings/JSDoc comments where missing.
- If no breaking changes exist, return an empty array for `breaking_changes`.
"""


async def refactor_file(file_path: str, language: str, code: str) -> dict:
    """
    Generate a modernized version of a source file with breaking change warnings.
    Returns a dict with refactored_code and breaking_changes.
    """
    prompt = REFACTOR_PROMPT.format(
        file_path=file_path,
        language=language,
        code=code,
    )
    result = await call_gemini_json(prompt, system_instruction=SYSTEM_PROMPT, max_tokens=16384)
    return result
