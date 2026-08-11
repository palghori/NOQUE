import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, Numeric, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from db import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_type = Column(String(10), nullable=False)  # 'zip' or 'github'
    source_ref = Column(Text, nullable=True)  # GitHub URL or original filename
    status = Column(String(20), default="queued")  # queued, processing, complete, failed
    progress = Column(Integer, default=0)
    total_files = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    files = relationship("File", back_populates="job", cascade="all, delete-orphan")
    explanations = relationship("Explanation", back_populates="job", cascade="all, delete-orphan")
    graph_edges = relationship("GraphEdge", back_populates="job", cascade="all, delete-orphan")
    tests = relationship("Test", back_populates="job", cascade="all, delete-orphan")
    refactors = relationship("Refactor", back_populates="job", cascade="all, delete-orphan")


class File(Base):
    __tablename__ = "files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False)
    file_path = Column(Text, nullable=False)
    language = Column(String(20), nullable=False)  # 'python' or 'javascript'
    line_count = Column(Integer, default=0)

    job = relationship("Job", back_populates="files")


class Explanation(Base):
    __tablename__ = "explanations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False)
    file_path = Column(Text, nullable=False)
    module_summary = Column(Text, nullable=True)
    function_name = Column(Text, nullable=True)
    purpose = Column(Text, nullable=True)
    params = Column(JSON, nullable=True)
    returns = Column(Text, nullable=True)
    confidence = Column(Numeric, nullable=True)

    job = relationship("Job", back_populates="explanations")


class GraphEdge(Base):
    __tablename__ = "graph_edges"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False)
    from_node = Column(Text, nullable=False)
    to_node = Column(Text, nullable=False)
    edge_type = Column(String(20), nullable=False)  # 'import' or 'call'

    job = relationship("Job", back_populates="graph_edges")


class Test(Base):
    __tablename__ = "tests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False)
    file_path = Column(Text, nullable=False)
    test_code = Column(Text, nullable=False)
    coverage_pct = Column(Numeric, nullable=True)
    retry_count = Column(Integer, default=0)
    passed = Column(Boolean, nullable=True)

    job = relationship("Job", back_populates="tests")


class Refactor(Base):
    __tablename__ = "refactors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False)
    file_path = Column(Text, nullable=False)
    original_code = Column(Text, nullable=False)
    refactored_code = Column(Text, nullable=False)
    breaking_changes = Column(JSON, nullable=True)  # [{change, risk, migration_note}]

    job = relationship("Job", back_populates="refactors")
