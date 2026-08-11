from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime


# --- Request Schemas ---
class JobCreateGitHub(BaseModel):
    github_url: str = Field(..., description="Public GitHub repository URL")


# --- Response Schemas ---
class JobStatusResponse(BaseModel):
    id: UUID
    status: str
    progress: int
    total_files: int
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class ExplanationItem(BaseModel):
    file_path: str
    module_summary: Optional[str] = None
    function_name: Optional[str] = None
    purpose: Optional[str] = None
    params: Optional[list] = None
    returns: Optional[str] = None
    confidence: Optional[float] = None


class GraphEdgeItem(BaseModel):
    from_node: str
    to_node: str
    edge_type: str


class TestItem(BaseModel):
    file_path: str
    test_code: str
    coverage_pct: Optional[float] = None
    retry_count: int = 0
    passed: Optional[bool] = None


class BreakingChange(BaseModel):
    change: str
    risk: str
    migration_note: str


class RefactorItem(BaseModel):
    file_path: str
    original_code: str
    refactored_code: str
    breaking_changes: Optional[list[BreakingChange]] = None


class JobResultsResponse(BaseModel):
    job_id: UUID
    explanations: list[ExplanationItem]
    graph: dict  # { nodes: [...], edges: [...] }
    tests: list[TestItem]
    refactors: list[RefactorItem]
