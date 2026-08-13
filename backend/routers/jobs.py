import uuid
import os
import shutil
import zipfile
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from db import get_db
from config import get_settings
from models.models import Job, Explanation, GraphEdge, Test, Refactor
from models.schemas import JobStatusResponse, JobResultsResponse, ExplanationItem, GraphEdgeItem, TestItem, RefactorItem

router = APIRouter(prefix="/api/jobs", tags=["jobs"])
settings = get_settings()


@router.post("", status_code=202)
async def create_job(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    file: UploadFile | None = File(None),
    github_url: str | None = Form(None),
):
    """
    Create a new analysis job.
    Accepts either a ZIP file upload or a GitHub repository URL.
    Returns immediately with a job ID (202 Accepted).
    """
    if not file and not github_url:
        raise HTTPException(status_code=400, detail="Provide either a ZIP file or a GitHub URL.")

    job_id = uuid.uuid4()
    source_type = "zip" if file else "github"
    source_ref = file.filename if file else github_url

    # Save uploaded ZIP to temp directory
    job_dir = os.path.join(settings.TEMP_DIR, str(job_id))
    os.makedirs(job_dir, exist_ok=True)

    if file:
        if not file.filename.endswith(".zip"):
            raise HTTPException(status_code=400, detail="Only ZIP files are supported.")
        zip_path = os.path.join(job_dir, "upload.zip")
        with open(zip_path, "wb") as f:
            content = await file.read()
            if len(content) > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
                raise HTTPException(status_code=400, detail=f"File exceeds {settings.MAX_FILE_SIZE_MB}MB limit.")
            f.write(content)

    # Create job record in DB
    job = Job(
        id=job_id,
        source_type=source_type,
        source_ref=source_ref,
        status="queued",
    )
    db.add(job)
    await db.commit()

    # Trigger the processing pipeline as a background task
    from services.pipeline import run_pipeline
    background_tasks.add_task(run_pipeline, str(job_id))

    return {"job_id": str(job_id)}


@router.get("/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str, db: AsyncSession = Depends(get_db)):
    """Poll this endpoint to check job progress."""
    result = await db.execute(select(Job).where(Job.id == uuid.UUID(job_id)))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    return JobStatusResponse(
        id=job.id,
        status=job.status,
        progress=job.progress,
        total_files=job.total_files,
        created_at=job.created_at,
        completed_at=job.completed_at,
        error_message=job.error_message,
    )


@router.get("/{job_id}/results", response_model=JobResultsResponse)
async def get_job_results(job_id: str, db: AsyncSession = Depends(get_db)):
    """Fetch the full analysis results once the job is complete."""
    uid = uuid.UUID(job_id)

    # Check job exists and is complete
    result = await db.execute(select(Job).where(Job.id == uid))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    if job.status != "complete":
        raise HTTPException(status_code=409, detail=f"Job is not complete yet. Current status: {job.status}")

    # Fetch all results
    explanations_result = await db.execute(select(Explanation).where(Explanation.job_id == uid))
    explanations = explanations_result.scalars().all()

    edges_result = await db.execute(select(GraphEdge).where(GraphEdge.job_id == uid))
    edges = edges_result.scalars().all()

    tests_result = await db.execute(select(Test).where(Test.job_id == uid))
    tests = tests_result.scalars().all()

    refactors_result = await db.execute(select(Refactor).where(Refactor.job_id == uid))
    refactors = refactors_result.scalars().all()

    # Build graph structure
    node_set = set()
    edge_list = []
    for edge in edges:
        node_set.add(edge.from_node)
        node_set.add(edge.to_node)
        edge_list.append(GraphEdgeItem(from_node=edge.from_node, to_node=edge.to_node, edge_type=edge.edge_type))

    graph = {
        "nodes": [{"id": n, "label": n.split("/")[-1]} for n in node_set],
        "edges": [e.model_dump() for e in edge_list],
    }

    return JobResultsResponse(
        job_id=uid,
        explanations=[
            ExplanationItem(
                file_path=e.file_path,
                module_summary=e.module_summary,
                function_name=e.function_name,
                purpose=e.purpose,
                params=e.params,
                returns=e.returns,
                confidence=float(e.confidence) if e.confidence else None,
            )
            for e in explanations
        ],
        graph=graph,
        tests=[
            TestItem(
                file_path=t.file_path,
                test_code=t.test_code,
                coverage_pct=float(t.coverage_pct) if t.coverage_pct else None,
                retry_count=t.retry_count,
                passed=t.passed,
            )
            for t in tests
        ],
        refactors=[
            RefactorItem(
                file_path=r.file_path,
                original_code=r.original_code,
                refactored_code=r.refactored_code,
                breaking_changes=r.breaking_changes,
            )
            for r in refactors
        ],
    )
