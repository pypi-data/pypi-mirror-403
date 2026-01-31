"""
Database Models for QuantumFlow.

Tables:
- users: User accounts
- api_keys: API authentication keys
- jobs: Quantum job execution history
- usage_records: Usage tracking and billing
"""

import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime,
    ForeignKey, Text, JSON, Enum as SQLEnum
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship
import enum

Base = declarative_base()


class JobStatus(str, enum.Enum):
    """Job execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobType(str, enum.Enum):
    """Type of quantum job."""
    COMPRESS = "compress"
    GRADIENT = "gradient"
    ENTANGLE = "entangle"
    GROVER = "grover"
    QAOA = "qaoa"
    VQE = "vqe"
    QNN = "qnn"
    QSVM = "qsvm"
    QKD = "qkd"
    QRNG = "qrng"
    CUSTOM = "custom"


class User(Base):
    """User account model."""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    name = Column(String(255), nullable=True)

    # Account status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    # Usage limits
    tier = Column(String(50), default="free")  # free, pro, enterprise
    monthly_quota = Column(Integer, default=1000)  # API calls per month

    # Stripe billing
    stripe_customer_id = Column(String(255), nullable=True, unique=True)
    stripe_subscription_id = Column(String(255), nullable=True)
    stripe_subscription_item_id = Column(String(255), nullable=True)

    # Relationships
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    jobs = relationship("Job", back_populates="user", cascade="all, delete-orphan")
    usage_records = relationship("UsageRecord", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.email}>"


class APIKey(Base):
    """API key for authentication."""

    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Key info
    key = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)  # User-friendly name
    prefix = Column(String(10), nullable=False)  # e.g., "qf_" for display

    # Permissions
    scopes = Column(JSON, default=list)  # ["compress", "gradient", "all"]

    # Status
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="api_keys")

    def __repr__(self):
        return f"<APIKey {self.prefix}***>"


class Job(Base):
    """Quantum job execution record."""

    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Job info
    job_type = Column(SQLEnum(JobType), nullable=False)
    status = Column(SQLEnum(JobStatus), default=JobStatus.PENDING)

    # Backend info
    backend = Column(String(50), default="simulator")  # simulator, ibm, google
    n_qubits = Column(Integer, nullable=True)
    shots = Column(Integer, default=1024)

    # Input/Output
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)

    # Metrics
    execution_time_ms = Column(Float, nullable=True)
    fidelity = Column(Float, nullable=True)
    compression_ratio = Column(Float, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="jobs")

    def __repr__(self):
        return f"<Job {self.id} {self.job_type} {self.status}>"


class UsageRecord(Base):
    """Usage tracking for billing and analytics."""

    __tablename__ = "usage_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Usage info
    endpoint = Column(String(255), nullable=False)  # /v1/compress
    method = Column(String(10), nullable=False)  # POST

    # Metrics
    tokens_input = Column(Integer, default=0)
    tokens_output = Column(Integer, default=0)
    qubits_used = Column(Integer, default=0)
    execution_time_ms = Column(Float, default=0)

    # Cost (for paid tiers)
    credits_used = Column(Float, default=0)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)

    # Request metadata
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(255), nullable=True)

    # Relationships
    user = relationship("User", back_populates="usage_records")

    def __repr__(self):
        return f"<UsageRecord {self.endpoint} {self.created_at}>"


# Indexes for common queries
from sqlalchemy import Index

Index("ix_jobs_user_created", Job.user_id, Job.created_at.desc())
Index("ix_jobs_status", Job.status)
Index("ix_usage_user_created", UsageRecord.user_id, UsageRecord.created_at.desc())
