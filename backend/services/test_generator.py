"""
test_generator.py — Generates unit tests using Gemini and runs
a coverage verification loop (retry up to 3 times if < 60%).
"""
import os
import subprocess
import re
from services.gemini_client import call_gemini

SYSTEM_PROMPT = """You are an expert test engineer.
You write thorough unit tests that achieve high line coverage.
You focus on edge cases, boundary conditions, and error handling.
Return ONLY valid, runnable test code. No markdown fences, no explanations."""

TEST_GEN_PROMPT = """Write comprehensive unit tests for the following {language} code.

**File:** `{file_path}`

```{lang_tag}
{code}
```

Requirements:
- Target >60% line coverage. Cover all branches, edge cases, and error paths.
- For Python: use `pytest`. Import the functions/classes directly. Use `pytest.raises` for exception tests.
- For JavaScript: use `jest`. Use `describe`/`it` blocks. Use `expect` matchers.
- Mock external dependencies (file I/O, network, databases) if needed.
- Include both positive (happy path) and negative (error) test cases.
- Return ONLY the test code, no explanations or markdown.
"""

TEST_RETRY_PROMPT = """The previous unit tests only achieved {coverage}% line coverage, which is below the 60% threshold.

**Original source code:**
```{lang_tag}
{code}
```

**Previous test code:**
```{lang_tag}
{previous_tests}
```

**Coverage report / errors:**
```
{failure_log}
```

Write IMPROVED tests that cover the missing lines and edge cases. Combine the good tests from the previous attempt with new ones.
Return ONLY the complete, runnable test code.
"""


async def generate_tests(
    file_path: str,
    language: str,
    code: str,
    job_dir: str,
    max_retries: int = 3,
    coverage_threshold: int = 60,
) -> dict:
    """
    Generate unit tests and run the coverage verification loop.
    Returns:
        {
            "test_code": str,
            "coverage_pct": float,
            "retry_count": int,
            "passed": bool,
        }
    """
    lang_tag = "python" if language == "python" else "javascript"

    # Initial generation
    prompt = TEST_GEN_PROMPT.format(
        language=language,
        file_path=file_path,
        lang_tag=lang_tag,
        code=code,
    )
    test_code = await call_gemini(prompt, system_instruction=SYSTEM_PROMPT, max_tokens=8192)
    test_code = _clean_code_output(test_code, lang_tag)

    coverage_pct = 0.0
    retry_count = 0
    passed = False

    for attempt in range(max_retries + 1):
        # Write and run the tests
        coverage_pct, failure_log, passed = _run_tests(
            file_path, test_code, language, job_dir
        )

        if coverage_pct >= coverage_threshold:
            break

        if attempt < max_retries:
            # Retry with feedback
            retry_prompt = TEST_RETRY_PROMPT.format(
                coverage=coverage_pct,
                lang_tag=lang_tag,
                code=code,
                previous_tests=test_code,
                failure_log=failure_log,
            )
            test_code = await call_gemini(retry_prompt, system_instruction=SYSTEM_PROMPT, max_tokens=8192)
            test_code = _clean_code_output(test_code, lang_tag)
            retry_count += 1

    return {
        "test_code": test_code,
        "coverage_pct": coverage_pct,
        "retry_count": retry_count,
        "passed": passed,
    }


def _clean_code_output(text: str, lang_tag: str) -> str:
    """Strip markdown code fences from LLM output."""
    cleaned = text.strip()
    if cleaned.startswith(f"```{lang_tag}"):
        cleaned = cleaned[len(f"```{lang_tag}"):]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    return cleaned.strip()


def _run_tests(source_path: str, test_code: str, language: str, job_dir: str) -> tuple[float, str, bool]:
    """
    Write the test code to disk and run the test framework.
    Returns (coverage_pct, log_output, all_passed).
    """
    if language == "python":
        return _run_pytest(source_path, test_code, job_dir)
    elif language == "javascript":
        return _run_jest(source_path, test_code, job_dir)
    return (0.0, "Unsupported language", False)


def _run_pytest(source_path: str, test_code: str, job_dir: str) -> tuple[float, str, bool]:
    """Run pytest with coverage on generated Python tests."""
    test_file = os.path.join(job_dir, "test_generated.py")
    with open(test_file, "w") as f:
        f.write(test_code)

    try:
        result = subprocess.run(
            [
                "python", "-m", "pytest", test_file,
                f"--cov={os.path.dirname(source_path)}",
                "--cov-report=term",
                "--tb=short",
                "-q",
                "--no-header",
            ],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=job_dir,
            env={**os.environ, "PYTHONPATH": job_dir},
        )
        output = result.stdout + "\n" + result.stderr

        # Parse coverage percentage from output
        coverage_pct = _parse_coverage(output)
        passed = result.returncode == 0

        return (coverage_pct, output, passed)

    except subprocess.TimeoutExpired:
        return (0.0, "Test execution timed out after 60 seconds", False)
    except Exception as e:
        return (0.0, f"Error running tests: {str(e)}", False)


def _run_jest(source_path: str, test_code: str, job_dir: str) -> tuple[float, str, bool]:
    """Run jest with coverage on generated JavaScript tests."""
    test_file = os.path.join(job_dir, "test_generated.test.js")
    with open(test_file, "w") as f:
        f.write(test_code)

    try:
        result = subprocess.run(
            ["npx", "jest", test_file, "--coverage", "--no-cache"],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=job_dir,
        )
        output = result.stdout + "\n" + result.stderr
        coverage_pct = _parse_jest_coverage(output)
        passed = result.returncode == 0
        return (coverage_pct, output, passed)

    except subprocess.TimeoutExpired:
        return (0.0, "Test execution timed out after 60 seconds", False)
    except Exception as e:
        return (0.0, f"Error running tests: {str(e)}", False)


def _parse_coverage(output: str) -> float:
    """Parse the TOTAL coverage percentage from pytest-cov output."""
    # Matches lines like: TOTAL    150    30    80%
    match = re.search(r"TOTAL\s+\d+\s+\d+\s+(\d+)%", output)
    if match:
        return float(match.group(1))
    return 0.0


def _parse_jest_coverage(output: str) -> float:
    """Parse the coverage percentage from Jest output."""
    # Matches lines like: All files |   85.71 |      100 |      80 |   85.71 |
    match = re.search(r"All files\s*\|\s*([\d.]+)", output)
    if match:
        return float(match.group(1))
    return 0.0
