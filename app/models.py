import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, Enum as SQLEnum, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class JobStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    PARTIALLY_FAILED = "PARTIALLY_FAILED"
    FAILED = "FAILED"


class CertificateStatus(str, enum.Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class GenerationJob(Base):
    __tablename__ = "generation_jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    issuer_name = Column(String(255), nullable=False, default="Organization")
    issue_date = Column(String(50), nullable=False)
    template_type = Column(String(50), nullable=False, default="standard_v1")
    certificate_heading = Column(String(255), nullable=True, default="CERTIFICATE OF ACHIEVEMENT")
    
    status = Column(SQLEnum(JobStatus), nullable=False, default=JobStatus.PENDING)
    total_count = Column(Integer, default=0, nullable=False)
    processed_count = Column(Integer, default=0, nullable=False)
    success_count = Column(Integer, default=0, nullable=False)
    failed_count = Column(Integer, default=0, nullable=False)

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    certificates = relationship("CertificateItem", back_populates="job", cascade="all, delete-orphan")


class CertificateItem(Base):
    __tablename__ = "certificate_items"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String(36), ForeignKey("generation_jobs.id", ondelete="CASCADE"), nullable=False)
    
    recipient_name = Column(String(255), nullable=False)
    recipient_email = Column(String(255), nullable=True)
    custom_attributes = Column(JSON, nullable=True)

    status = Column(SQLEnum(CertificateStatus), nullable=False, default=CertificateStatus.PENDING)
    error_message = Column(Text, nullable=True)
    certificate_code = Column(String(100), unique=True, index=True, nullable=True)
    file_path = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    generated_at = Column(DateTime(timezone=True), nullable=True)

    job = relationship("GenerationJob", back_populates="certificates")
