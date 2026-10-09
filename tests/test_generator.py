from pathlib import Path
from app.services.certificate_generator import generate_unique_code, build_certificate_pdf


def test_unique_code_generation():
    code1 = generate_unique_code()
    code2 = generate_unique_code()
    assert code1.startswith("CERT-")
    assert code2.startswith("CERT-")
    assert code1 != code2


def test_pdf_generation(tmp_path):
    cert_id = "test-cert-123"
    code = generate_unique_code()
    
    pdf_path = build_certificate_pdf(
        certificate_id=cert_id,
        recipient_name="David Miller",
        title="AI Engineering Certificate",
        issuer_name="Global AI Institute",
        issue_date="2026-10-09",
        certificate_code=code,
        custom_attributes={"specialization": "LLMs", "hours": 80},
        output_dir=tmp_path
    )

    assert pdf_path.exists()
    assert pdf_path.is_file()
    assert pdf_path.stat().st_size > 0


def test_pdf_generation_custom_theme_and_heading(tmp_path):
    cert_id = "test-cert-custom"
    code = generate_unique_code()

    pdf_path = build_certificate_pdf(
        certificate_id=cert_id,
        recipient_name="Sophia Martinez",
        title="Web Development Bootcamp",
        issuer_name="Tech Institute",
        issue_date="2026-10-09",
        certificate_code=code,
        template_type="emerald_gold",
        certificate_heading="CERTIFICATE OF EXCELLENCE",
        output_dir=tmp_path
    )

    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 0
