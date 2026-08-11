"""
explainer.py — Generates natural language explanations of code
at module and function level using Gemini.
"""
from services.gemini_client import call_gemini_json

SYSTEM_PROMPT = """You are a Senior Staff Engineer with 20 years of experience.
Your task is to explain legacy code clearly and accurately.
You must return ONLY valid JSON, no markdown fences, no extra text.
Rate your confidence in understanding each function on a scale of 0.0 to 1.0."""

EXPLANATION_PROMPT = """Analyze the following source code file and provide a detailed explanation.

**File:** `{file_path}`
**Language:** {language}

```
{code}
```

Return your analysis as JSON in this exact format:
{{
  "module_summary": "A 2-3 sentence high-level summary of what this file/module does overall.",
  "functions": [
    {{
      "name": "function_name",
      "purpose": "Clear explanation of what this function does and why.",
      "params": ["param1: description", "param2: description"],
      "returns": "Description of what it returns.",
      "confidence": 0.95
    }}
  ]
}}

Rules:
- Explain in simple, clear language that a junior developer would understand.
- For each function, explain the business logic, not just the syntax.
- If the code uses outdated patterns, mention what they are.
- The confidence score reflects how well you understand the function's intent (1.0 = fully clear, 0.5 = ambiguous).
"""


async def explain_file(file_path: str, language: str, code: str) -> dict:
    """
    Generate a natural language explanation for a single source file.
    Returns a dict with module_summary and per-function explanations.
    """
    prompt = EXPLANATION_PROMPT.format(
        file_path=file_path,
        language=language,
        code=code,
    )
    result = await call_gemini_json(prompt, system_instruction=SYSTEM_PROMPT)
    return result
