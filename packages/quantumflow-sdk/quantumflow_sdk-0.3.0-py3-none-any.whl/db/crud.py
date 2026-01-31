"""
CRUD Operations for QuantumFlow.

Provides clean interface for database operations.
"""

import secrets
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import select, and_
import bcrypt

from db.models import User, APIKey, Job, UsageRecord, JobStatus, JobType


# ============== User CRUD ==============

def get_user(db: Session, user_id: UUID) -> Optional[User]:
    """Get user by ID."""
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email."""
    return db.query(User).filter(User.email == email).first()


def create_user(
    db: Session,
    email: str,
    password: str,
    name: Optional[str] = None,
) -> User:
    """Create a new user."""
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    user = User(
        email=email,
        hashed_password=hashed_password,
        name=name,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against hash."""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Authenticate user by email and password."""
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def update_user_login(db: Session, user: User) -> User:
    """Update user's last login timestamp."""
    user.last_login = datetime.utcnow()
    db.commit()
    db.refresh(user)
    return user


# ============== API Key CRUD ==============

def create_api_key(
    db: Session,
    user_id: UUID,
    name: str,
    scopes: Optional[list[str]] = None,
    expires_in_days: Optional[int] = None,
) -> tuple[APIKey, str]:
    """
    Create a new API key.

    Returns:
        Tuple of (APIKey object, raw key string)
        The raw key is only returned once and should be shown to user.
    """
    # Generate secure random key
    raw_key = f"qf_{secrets.token_hex(24)}"
    prefix = raw_key[:7]

    expires_at = None
    if expires_in_days:
        expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

    api_key = APIKey(
        user_id=user_id,
        key=raw_key,
        name=name,
        prefix=prefix,
        scopes=scopes or ["all"],
        expires_at=expires_at,
    )

    db.add(api_key)
    db.commit()
    db.refresh(api_key)

    return api_key, raw_key


def get_api_key(db: Session, key: str) -> Optional[APIKey]:
    """Get API key by key string."""
    api_key = db.query(APIKey).filter(
        and_(
            APIKey.key == key,
            APIKey.is_active == True,
        )
    ).first()

    # Check expiration
    if api_key and api_key.expires_at and api_key.expires_at < datetime.utcnow():
        return None

    return api_key


def get_user_api_keys(db: Session, user_id: UUID) -> list[APIKey]:
    """Get all API keys for a user."""
    return db.query(APIKey).filter(APIKey.user_id == user_id).all()


def revoke_api_key(db: Session, key_id: UUID) -> bool:
    """Revoke an API key."""
    api_key = db.query(APIKey).filter(APIKey.id == key_id).first()
    if api_key:
        api_key.is_active = False
        db.commit()
        return True
    return False


def update_api_key_usage(db: Session, api_key: APIKey) -> APIKey:
    """Update API key's last used timestamp."""
    api_key.last_used = datetime.utcnow()
    db.commit()
    return api_key


# ============== Job CRUD ==============

def create_job(
    db: Session,
    user_id: UUID,
    job_type: JobType,
    backend: str = "simulator",
    input_data: Optional[dict] = None,
    n_qubits: Optional[int] = None,
    shots: int = 1024,
) -> Job:
    """Create a new quantum job."""
    job = Job(
        user_id=user_id,
        job_type=job_type,
        backend=backend,
        input_data=input_data,
        n_qubits=n_qubits,
        shots=shots,
        status=JobStatus.PENDING,
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    return job


def get_job(db: Session, job_id: UUID) -> Optional[Job]:
    """Get job by ID."""
    return db.query(Job).filter(Job.id == job_id).first()


def get_user_jobs(
    db: Session,
    user_id: UUID,
    limit: int = 100,
    offset: int = 0,
    status: Optional[JobStatus] = None,
) -> list[Job]:
    """Get jobs for a user."""
    query = db.query(Job).filter(Job.user_id == user_id)

    if status:
        query = query.filter(Job.status == status)

    return query.order_by(Job.created_at.desc()).offset(offset).limit(limit).all()


def update_job_status(
    db: Session,
    job: Job,
    status: JobStatus,
    output_data: Optional[dict] = None,
    error_message: Optional[str] = None,
    execution_time_ms: Optional[float] = None,
    fidelity: Optional[float] = None,
    compression_ratio: Optional[float] = None,
) -> Job:
    """Update job status and results."""
    job.status = status

    if status == JobStatus.RUNNING:
        job.started_at = datetime.utcnow()
    elif status in [JobStatus.COMPLETED, JobStatus.FAILED]:
        job.completed_at = datetime.utcnow()

    if output_data is not None:
        job.output_data = output_data
    if error_message is not None:
        job.error_message = error_message
    if execution_time_ms is not None:
        job.execution_time_ms = execution_time_ms
    if fidelity is not None:
        job.fidelity = fidelity
    if compression_ratio is not None:
        job.compression_ratio = compression_ratio

    db.commit()
    db.refresh(job)

    return job


# ============== Usage CRUD ==============

def create_usage_record(
    db: Session,
    user_id: UUID,
    endpoint: str,
    method: str,
    tokens_input: int = 0,
    tokens_output: int = 0,
    qubits_used: int = 0,
    execution_time_ms: float = 0,
    credits_used: float = 0,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> UsageRecord:
    """Create a usage record."""
    record = UsageRecord(
        user_id=user_id,
        endpoint=endpoint,
        method=method,
        tokens_input=tokens_input,
        tokens_output=tokens_output,
        qubits_used=qubits_used,
        execution_time_ms=execution_time_ms,
        credits_used=credits_used,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    return record


def get_user_usage(
    db: Session,
    user_id: UUID,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> dict:
    """Get usage summary for a user."""
    query = db.query(UsageRecord).filter(UsageRecord.user_id == user_id)

    if start_date:
        query = query.filter(UsageRecord.created_at >= start_date)
    if end_date:
        query = query.filter(UsageRecord.created_at <= end_date)

    records = query.all()

    return {
        "total_requests": len(records),
        "total_tokens_input": sum(r.tokens_input for r in records),
        "total_tokens_output": sum(r.tokens_output for r in records),
        "total_qubits_used": sum(r.qubits_used for r in records),
        "total_execution_time_ms": sum(r.execution_time_ms for r in records),
        "total_credits_used": sum(r.credits_used for r in records),
    }


def get_monthly_usage(db: Session, user_id: UUID) -> int:
    """Get current month's API call count."""
    now = datetime.utcnow()
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    count = db.query(UsageRecord).filter(
        and_(
            UsageRecord.user_id == user_id,
            UsageRecord.created_at >= start_of_month,
        )
    ).count()

    return count


def check_quota(db: Session, user: User) -> bool:
    """Check if user is within their monthly quota."""
    usage = get_monthly_usage(db, user.id)
    return usage < user.monthly_quota
