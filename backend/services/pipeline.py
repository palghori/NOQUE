"""
pipeline.py — The main orchestrator.
Runs the full processing pipeline as a FastAPI background task:
  1. Ingest (unzip / clone)
  2. Parse (tree-sitter)
  3. Explain + Refactor (concurrent Gemini calls in batches)
  4. Generate Tests + Coverage Loop (concurrent in batches)
  5. Mark job complete

Performance: Files are processed in parallel batches of BATCH_SIZE
for a ~5x speedup over sequential processing.
"""
import os
import shutil
import zipfile
import asyncio
import traceback
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update

from db import async_session
from config import get_settings
from models.models import Job, File, Explanation, GraphEdge, Test, Refactor
from services.parser import collect_files, parse_file
from services.explainer import explain_file
from services.refactorer import refactor_file
from services.test_generator import generate_tests

settings = get_settings()

# Number of files to process concurrently
BATCH_SIZE = 5


async def run_pipeline(job_id: str):
    """
    Main pipeline entry point. Called as a background task by FastAPI.
    All state is written to PostgreSQL so the frontend can poll for progress.
    """
    async with async_session() as db:
        try:
            await _update_job(db, job_id, status="processing", progress=0)

            # --- Stage 1: Ingestion ---
            job_dir = os.path.join(settings.TEMP_DIR, job_id)
            source_dir = await _ingest(db, job_id, job_dir)

            # --- Stage 2: Parse files with Tree-sitter ---
            source_files = collect_files(source_dir, settings.SUPPORTED_EXTENSIONS)
            total_files = len(source_files)
            if total_files == 0:
                await _update_job(db, job_id, status="failed", error_message="No supported source files found in the upload.")
                return

            await _update_job(db, job_id, total_files=total_files)

            parsed_files = []
            for fpath in source_files:
                parsed = parse_file(fpath)
                if parsed:
                    parsed_files.append(parsed)
                    # Register file in DB
                    rel_path = os.path.relpath(fpath, source_dir)
                    file_record = File(
                        job_id=job_id,
                        file_path=rel_path,
                        language=parsed["language"],
                        line_count=parsed["line_count"],
                    )
                    db.add(file_record)

            await db.flush()

            # --- Stage 2b: Build Dependency Graph ---
            for parsed in parsed_files:
                rel_path = os.path.relpath(parsed["file_path"], source_dir)
                for imp in parsed["imports"]:
                    edge = GraphEdge(
                        job_id=job_id,
                        from_node=rel_path,
                        to_node=imp,
                        edge_type="import",
                    )
                    db.add(edge)
                for call in parsed["calls"]:
                    edge = GraphEdge(
                        job_id=job_id,
                        from_node=rel_path,
                        to_node=call,
                        edge_type="call",
                    )
                    db.add(edge)

            await db.flush()
            await _update_job(db, job_id, progress=10)

            # --- Stage 3: AI Processing (Explain + Refactor) — BATCHED ---
            progress_per_file = 70 // max(len(parsed_files), 1)
            current_progress = 10

            # Process files in parallel batches
            for batch_start in range(0, len(parsed_files), BATCH_SIZE):
                batch = parsed_files[batch_start:batch_start + BATCH_SIZE]

                # Create concurrent tasks for the entire batch
                batch_tasks = []
                for parsed in batch:
                    rel_path = os.path.relpath(parsed["file_path"], source_dir)
                    code = parsed["code"]
                    language = parsed["language"]
                    batch_tasks.append(
                        _process_single_file(db, job_id, rel_path, language, code)
                    )

                # Run all files in this batch concurrently
                await asyncio.gather(*batch_tasks, return_exceptions=True)

                # Update progress after each batch
                current_progress += progress_per_file * len(batch)
                await _update_job(db, job_id, progress=min(current_progress, 80))
                await db.flush()

            # --- Stage 4: Test Generation — BATCHED ---
            await _update_job(db, job_id, progress=80)

            for batch_start in range(0, len(parsed_files), BATCH_SIZE):
                batch = parsed_files[batch_start:batch_start + BATCH_SIZE]

                test_tasks = []
                for parsed in batch:
                    rel_path = os.path.relpath(parsed["file_path"], source_dir)
                    code = parsed["code"]
                    language = parsed["language"]
                    test_tasks.append(
                        _generate_test_for_file(
                            db, job_id, rel_path, parsed["file_path"],
                            language, code, job_dir,
                        )
                    )

                await asyncio.gather(*test_tasks, return_exceptions=True)

                test_progress = 80 + (20 * (batch_start + len(batch)) // max(len(parsed_files), 1))
                await _update_job(db, job_id, progress=min(test_progress, 95))
                await db.flush()

            # --- Stage 5: Mark Complete ---
            await _update_job(db, job_id, status="complete", progress=100, completed_at=datetime.utcnow())
            await db.commit()

        except Exception as e:
            traceback.print_exc()
            await _update_job(db, job_id, status="failed", error_message=str(e))
            await db.commit()

        finally:
            # Clean up temp files
            job_dir = os.path.join(settings.TEMP_DIR, job_id)
            if os.path.exists(job_dir):
                shutil.rmtree(job_dir, ignore_errors=True)


async def _process_single_file(db: AsyncSession, job_id: str, rel_path: str, language: str, code: str):
    """Process a single file: explain + refactor concurrently."""
    try:
        # Run explanation and refactoring concurrently for this file
        explanation_result, refactor_result = await asyncio.gather(
            explain_file(rel_path, language, code),
            refactor_file(rel_path, language, code),
            return_exceptions=True,
        )

        # Save explanation results
        if isinstance(explanation_result, dict) and "raw_response" not in explanation_result:
            # Module-level explanation
            module_summary = explanation_result.get("module_summary", "")
            db.add(Explanation(
                job_id=job_id,
                file_path=rel_path,
                module_summary=module_summary,
            ))
            # Function-level explanations
            for func in explanation_result.get("functions", []):
                db.add(Explanation(
                    job_id=job_id,
                    file_path=rel_path,
                    function_name=func.get("name"),
                    purpose=func.get("purpose"),
                    params=func.get("params"),
                    returns=func.get("returns"),
                    confidence=func.get("confidence"),
                ))
        else:
            # Fallback: store raw response as module summary
            raw = explanation_result if isinstance(explanation_result, dict) else {"raw_response": str(explanation_result)}
            db.add(Explanation(
                job_id=job_id,
                file_path=rel_path,
                module_summary=raw.get("raw_response", str(explanation_result)),
            ))

        # Save refactor results
        if isinstance(refactor_result, dict) and "refactored_code" in refactor_result:
            db.add(Refactor(
                job_id=job_id,
                file_path=rel_path,
                original_code=code,
                refactored_code=refactor_result["refactored_code"],
                breaking_changes=refactor_result.get("breaking_changes", []),
            ))
        else:
            raw = str(refactor_result)
            db.add(Refactor(
                job_id=job_id,
                file_path=rel_path,
                original_code=code,
                refactored_code=raw,
                breaking_changes=[],
            ))

    except Exception as e:
        print(f"[NOQUE] Error processing file {rel_path}: {e}")
        # Store error as explanation so the user sees something
        db.add(Explanation(
            job_id=job_id,
            file_path=rel_path,
            module_summary=f"Error during analysis: {str(e)}",
        ))


async def _generate_test_for_file(
    db: AsyncSession, job_id: str, rel_path: str,
    file_path: str, language: str, code: str, job_dir: str,
):
    """Generate tests for a single file."""
    try:
        test_result = await generate_tests(
            file_path=file_path,
            language=language,
            code=code,
            job_dir=job_dir,
            max_retries=settings.MAX_TEST_RETRIES,
            coverage_threshold=settings.COVERAGE_THRESHOLD,
        )

        db.add(Test(
            job_id=job_id,
            file_path=rel_path,
            test_code=test_result["test_code"],
            coverage_pct=test_result["coverage_pct"],
            retry_count=test_result["retry_count"],
            passed=test_result["passed"],
        ))
    except Exception as e:
        print(f"[NOQUE] Error generating tests for {rel_path}: {e}")
        db.add(Test(
            job_id=job_id,
            file_path=rel_path,
            test_code=f"# Test generation failed: {str(e)}",
            coverage_pct=0.0,
            retry_count=0,
            passed=False,
        ))


async def _ingest(db: AsyncSession, job_id: str, job_dir: str) -> str:
    """
    Extract the uploaded ZIP or clone the GitHub repo.
    Returns the path to the extracted source directory.
    """
    source_dir = os.path.join(job_dir, "source")
    os.makedirs(source_dir, exist_ok=True)

    zip_path = os.path.join(job_dir, "upload.zip")
    if os.path.exists(zip_path):
        with zipfile.ZipFile(zip_path, "r") as z:
            z.extractall(source_dir)
        os.remove(zip_path)
    else:
        # GitHub clone
        from sqlalchemy import select
        from models.models import Job
        result = await db.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one()
        if job.source_ref:
            import subprocess
            subprocess.run(
                ["git", "clone", "--depth", "1", job.source_ref, source_dir],
                capture_output=True,
                timeout=120,
            )

    return source_dir


async def _update_job(db: AsyncSession, job_id: str, **kwargs):
    """Update job fields in the database."""
    stmt = update(Job).where(Job.id == job_id).values(**kwargs)
    await db.execute(stmt)
    await db.flush()
