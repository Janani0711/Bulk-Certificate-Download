from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import GenerationJob, CertificateItem, JobStatus, CertificateStatus
from app.schemas import (
    JobCreateRequest,
    JobStatusResponse,
    JobDetailResponse,
    CertificateResponse,
)
from app.services.job_service import create_job, process_job_background, create_job_zip

router = APIRouter(prefix="/jobs", tags=["Jobs"])


def _to_job_status_response(job: GenerationJob) -> JobStatusResponse:
    progress = 0.0
    if job.total_count > 0:
        progress = round((job.processed_count / job.total_count) * 100.0, 2)

    return JobStatusResponse(
        id=job.id,
        title=job.title,
        issuer_name=job.issuer_name,
        issue_date=job.issue_date,
        template_type=job.template_type,
        certificate_heading=job.certificate_heading or "CERTIFICATE OF ACHIEVEMENT",
        status=job.status,
        total_count=job.total_count,
        processed_count=job.processed_count,
        success_count=job.success_count,
        failed_count=job.failed_count,
        progress_percentage=progress,
        created_at=job.created_at,
        updated_at=job.updated_at,
        completed_at=job.completed_at,
    )


def _to_certificate_response(cert: CertificateItem) -> CertificateResponse:
    download_url = None
    preview_url = None
    if cert.status == CertificateStatus.SUCCESS:
        download_url = f"/api/v1/certificates/{cert.id}/download"
        preview_url = f"/api/v1/certificates/{cert.id}/preview"

    return CertificateResponse(
        id=cert.id,
        job_id=cert.job_id,
        recipient_name=cert.recipient_name,
        recipient_email=cert.recipient_email,
        custom_attributes=cert.custom_attributes,
        status=cert.status,
        error_message=cert.error_message,
        certificate_code=cert.certificate_code,
        created_at=cert.created_at,
        generated_at=cert.generated_at,
        download_url=download_url,
        preview_url=preview_url,
    )


@router.post("", response_model=JobStatusResponse, status_code=status.HTTP_202_ACCEPTED)
def submit_job(
    request: JobCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Submit a bulk certificate generation request.
    Creates job records in the database and triggers background generation.
    """
    job = create_job(db, request)
    background_tasks.add_task(process_job_background, job.id)
    return _to_job_status_response(job)


@router.get("/{job_id}", response_model=JobDetailResponse)
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    """
    Retrieve current status, progress, and certificates for a given job.
    """
    job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Generation job '{job_id}' not found"
        )

    job_resp = _to_job_status_response(job)
    certs = [_to_certificate_response(c) for c in job.certificates]

    return JobDetailResponse(
        **job_resp.model_dump(),
        certificates=certs
    )


@router.get("/{job_id}/certificates", response_model=List[CertificateResponse])
def get_job_certificates(
    job_id: str,
    status_filter: Optional[CertificateStatus] = Query(None, alias="status"),
    db: Session = Depends(get_db)
):
    """
    List all certificate items in a job, optionally filtered by status (PENDING, SUCCESS, FAILED).
    """
    job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Generation job '{job_id}' not found"
        )

    query = db.query(CertificateItem).filter(CertificateItem.job_id == job_id)
    if status_filter:
        query = query.filter(CertificateItem.status == status_filter)

    certs = query.all()
    return [_to_certificate_response(c) for c in certs]


@router.get("/{job_id}/download-all")
def download_all_job_certificates(job_id: str, db: Session = Depends(get_db)):
    """
    Download a ZIP archive containing all successfully generated certificates for a job.
    """
    zip_path = create_job_zip(db, job_id)
    if not zip_path or not zip_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No generated certificates available for download or job not found."
        )

    return FileResponse(
        path=str(zip_path),
        filename=f"certificates_job_{job_id}.zip",
        media_type="application/zip"
    )
