"""
pipeline.py — The main orchestrator.
Runs the full processing pipeline as a FastAPI background task:
  1. Ingest (unzip / clone)
  2. Parse (tree-sitter)
  3. Explain + Refactor (concurrent Gemini calls)
  4. Generate Tests + Coverage Loop
  5. Mark job complete
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

            # --- Stage 3: AI Processing (Explain + Refactor concurrently per file) ---
            progress_per_file = 80 // max(total_files, 1)
            current_progress = 10

            for parsed in parsed_files:
                rel_path = os.path.relpath(parsed["file_path"], source_dir)
                code = parsed["code"]
                language = parsed["language"]

                # Run explanation and refactoring concurrently
                explain_task = explain_file(rel_path, language, code)
                refactor_task = refactor_file(rel_path, language, code)

                explanation_result, refactor_result = await asyncio.gather(
                    explain_task, refactor_task, return_exceptions=True
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

                current_progress += progress_per_file
                await _update_job(db, job_id, progress=min(current_progress, 90))
                await db.flush()

            # --- Stage 4: Test Generation with Coverage Loop ---
            for parsed in parsed_files:
                rel_path = os.path.relpath(parsed["file_path"], source_dir)
                code = parsed["code"]
                language = parsed["language"]

                test_result = await generate_tests(
                    file_path=parsed["file_path"],
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
