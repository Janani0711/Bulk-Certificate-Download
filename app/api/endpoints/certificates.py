import os
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import CertificateItem, CertificateStatus, GenerationJob
from app.schemas import CertificateResponse, VerificationResponse

router = APIRouter(prefix="/certificates", tags=["Certificates"])


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


@router.get("/{certificate_id}", response_model=CertificateResponse)
def get_certificate_details(certificate_id: str, db: Session = Depends(get_db)):
    """
    Retrieve certificate status and details by certificate ID.
    """
    cert = db.query(CertificateItem).filter(CertificateItem.id == certificate_id).first()
    if not cert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certificate '{certificate_id}' not found"
        )
    return _to_certificate_response(cert)


@router.get("/{certificate_id}/preview")
def preview_certificate(certificate_id: str, db: Session = Depends(get_db)):
    """
    Inline PDF viewer endpoint for browser preview without triggering download prompts.
    """
    cert = db.query(CertificateItem).filter(CertificateItem.id == certificate_id).first()
    if not cert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certificate '{certificate_id}' not found"
        )

    if cert.status != CertificateStatus.SUCCESS or not cert.file_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Certificate for '{certificate_id}' is not generated (status: {cert.status})."
        )

    if not os.path.exists(cert.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificate PDF file missing on storage server."
        )

    return FileResponse(
        path=cert.file_path,
        media_type="application/pdf",
        headers={"Content-Disposition": "inline"}
    )


@router.get("/{certificate_id}/download")
def download_certificate(certificate_id: str, db: Session = Depends(get_db)):
    """
    Download the generated PDF certificate as an attachment.
    """
    cert = db.query(CertificateItem).filter(CertificateItem.id == certificate_id).first()
    if not cert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certificate '{certificate_id}' not found"
        )

    if cert.status != CertificateStatus.SUCCESS or not cert.file_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Certificate generation for '{certificate_id}' has not succeeded (status: {cert.status})."
        )

    if not os.path.exists(cert.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificate PDF file missing on storage server."
        )

    safe_filename = f"Certificate_{cert.recipient_name.replace(' ', '_')}_{cert.certificate_code}.pdf"

    return FileResponse(
        path=cert.file_path,
        filename=safe_filename,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{safe_filename}"'}
    )


@router.get("/verify/{certificate_code}", response_model=VerificationResponse)
def verify_certificate(certificate_code: str, db: Session = Depends(get_db)):
    """
    Public verification endpoint for validating certificate authenticity using certificate verification code.
    """
    cert = db.query(CertificateItem).filter(
        CertificateItem.certificate_code == certificate_code.strip()
    ).first()

    if not cert or cert.status != CertificateStatus.SUCCESS:
        return VerificationResponse(
            valid=False,
            certificate_code=certificate_code,
            message="Invalid or unverified certificate verification code."
        )

    job = db.query(GenerationJob).filter(GenerationJob.id == cert.job_id).first()

    return VerificationResponse(
        valid=True,
        certificate_code=cert.certificate_code,
        recipient_name=cert.recipient_name,
        title=job.title if job else None,
        issuer_name=job.issuer_name if job else None,
        issue_date=job.issue_date if job else None,
        generated_at=cert.generated_at,
        message="Certificate is authentic and valid."
    )
