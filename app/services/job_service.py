import os
import zipfile
import logging
from datetime import datetime, timezone
from typing import Optional, List
from pathlib import Path

from sqlalchemy.orm import Session
import app.database as database
from app.models import GenerationJob, CertificateItem, JobStatus, CertificateStatus
from app.schemas import JobCreateRequest
from app.services.validation_service import validate_recipient_data
from app.services.certificate_generator import build_certificate_pdf, generate_unique_code
from app.config import settings

logger = logging.getLogger(__name__)


def create_job(db: Session, request: JobCreateRequest) -> GenerationJob:
    """
    Creates a new generation job and its associated certificate items in PENDING state.
    """
    issue_date = request.issue_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    job = GenerationJob(
        title=request.title.strip(),
        issuer_name=request.issuer_name.strip(),
        issue_date=issue_date,
        template_type=request.template_type,
        certificate_heading=request.certificate_heading or "CERTIFICATE OF ACHIEVEMENT",
        status=JobStatus.PENDING,
        total_count=len(request.recipients),
        processed_count=0,
        success_count=0,
        failed_count=0,
    )
    db.add(job)
    db.flush()

    for recipient in request.recipients:
        cert_item = CertificateItem(
            job_id=job.id,
            recipient_name=recipient.recipient_name or "",
            recipient_email=recipient.recipient_email,
            custom_attributes=recipient.custom_attributes,
            status=CertificateStatus.PENDING,
        )
        db.add(cert_item)

    db.commit()
    db.refresh(job)
    return job


def process_job_background(job_id: str, db: Optional[Session] = None):
    """
    Background worker function that processes all certificate items in a job.
    Catches errors per recipient so one failure does not prevent processing others.
    """
    should_close = False
    if db is None:
        db = database.SessionLocal()
        should_close = True

    try:
        job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
        if not job:
            logger.error(f"Job {job_id} not found for processing")
            return

        job.status = JobStatus.PROCESSING
        db.commit()

        items: List[CertificateItem] = db.query(CertificateItem).filter(CertificateItem.job_id == job_id).all()

        for item in items:
            # 1. Validate recipient data
            is_valid, err_msg = validate_recipient_data(
                recipient_name=item.recipient_name,
                recipient_email=item.recipient_email
            )

            if not is_valid:
                item.status = CertificateStatus.FAILED
                item.error_message = err_msg
                job.failed_count += 1
                job.processed_count += 1
                db.commit()
                continue

            # 2. Attempt PDF generation
            try:
                cert_code = generate_unique_code()
                pdf_path = build_certificate_pdf(
                    certificate_id=item.id,
                    recipient_name=item.recipient_name,
                    title=job.title,
                    issuer_name=job.issuer_name,
                    issue_date=job.issue_date,
                    certificate_code=cert_code,
                    custom_attributes=item.custom_attributes,
                    template_type=job.template_type,
                    certificate_heading=job.certificate_heading,
                )

                item.status = CertificateStatus.SUCCESS
                item.certificate_code = cert_code
                item.file_path = str(pdf_path)
                item.generated_at = datetime.now(timezone.utc)
                job.success_count += 1

            except Exception as e:
                logger.exception(f"Failed generating certificate for item {item.id}")
                item.status = CertificateStatus.FAILED
                item.error_message = f"Certificate rendering failure: {str(e)}"
                job.failed_count += 1

            job.processed_count += 1
            db.commit()

        # Update final job status
        if job.success_count == job.total_count:
            job.status = JobStatus.COMPLETED
        elif job.failed_count == job.total_count:
            job.status = JobStatus.FAILED
        else:
            job.status = JobStatus.PARTIALLY_FAILED

        job.completed_at = datetime.now(timezone.utc)
        db.commit()

    except Exception as e:
        logger.exception(f"Fatal error processing job {job_id}: {str(e)}")
        if 'job' in locals() and job:
            job.status = JobStatus.FAILED
            db.commit()
    finally:
        if should_close:
            db.close()


def create_job_zip(db: Session, job_id: str) -> Optional[Path]:
    """
    Creates a zip file containing all successfully generated PDFs for a job.
    Returns the path to the zip file.
    """
    job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
    if not job:
        return None

    successful_certs = db.query(CertificateItem).filter(
        CertificateItem.job_id == job_id,
        CertificateItem.status == CertificateStatus.SUCCESS,
        CertificateItem.file_path.isnot(None)
    ).all()

    if not successful_certs:
        return None

    zip_dir = settings.STORAGE_DIR / "zips"
    zip_dir.mkdir(parents=True, exist_ok=True)
    zip_path = zip_dir / f"job_{job_id}.zip"

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for cert in successful_certs:
            if cert.file_path and os.path.exists(cert.file_path):
                raw_name = cert.recipient_name.replace(' ', '_')
                safe_name = "".join(c for c in raw_name if c.isalnum() or c in ('_', '-')).strip()
                filename = f"{safe_name}_{cert.certificate_code}.pdf"
                zip_file.write(cert.file_path, arcname=filename)

    return zip_path
