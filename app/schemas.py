from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class RecipientInput(BaseModel):
    recipient_name: Optional[str] = Field(default="", description="Full name of the certificate recipient")
    recipient_email: Optional[str] = Field(default=None, description="Email address of recipient")
    custom_attributes: Optional[Dict[str, Any]] = Field(
        default=None, 
        description="Optional custom key-value metadata (e.g., grade, hours, role)"
    )


class JobCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, description="Event or Course title for the certificate")
    issuer_name: str = Field(default="Organization", min_length=1, description="Issuing organization or authority")
    issue_date: Optional[str] = Field(default=None, description="Issue date string (e.g. YYYY-MM-DD)")
    template_type: str = Field(default="standard_v1", description="Predefined template style identifier (standard_v1, emerald_gold, burgundy_luxury, slate_corporate)")
    certificate_heading: Optional[str] = Field(default="CERTIFICATE OF ACHIEVEMENT", description="Custom certificate main title")
    recipients: List[RecipientInput] = Field(..., min_length=1, description="List of recipient records")


class CertificateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    job_id: str
    recipient_name: str
    recipient_email: Optional[str] = None
    custom_attributes: Optional[Dict[str, Any]] = None
    status: str
    error_message: Optional[str] = None
    certificate_code: Optional[str] = None
    created_at: datetime
    generated_at: Optional[datetime] = None
    download_url: Optional[str] = None
    preview_url: Optional[str] = None


class JobStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    issuer_name: str
    issue_date: str
    template_type: str
    certificate_heading: Optional[str] = "CERTIFICATE OF ACHIEVEMENT"
    status: str
    total_count: int
    processed_count: int
    success_count: int
    failed_count: int
    progress_percentage: float
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None


class JobDetailResponse(JobStatusResponse):
    certificates: List[CertificateResponse] = []


class VerificationResponse(BaseModel):
    valid: bool
    certificate_code: str
    recipient_name: Optional[str] = None
    title: Optional[str] = None
    issuer_name: Optional[str] = None
    issue_date: Optional[str] = None
    generated_at: Optional[datetime] = None
    message: Optional[str] = None
