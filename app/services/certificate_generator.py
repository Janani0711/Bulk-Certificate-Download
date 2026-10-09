import os
import uuid
from pathlib import Path
from typing import Optional, Dict, Any
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from app.config import settings


def generate_unique_code() -> str:
    """Generates a unique certificate verification code."""
    short_uuid = uuid.uuid4().hex[:8].upper()
    return f"CERT-{short_uuid}"


# Color palettes for design themes
THEMES = {
    "standard_v1": {  # Navy & Gold
        "primary": colors.HexColor("#1E3A8A"),
        "secondary": colors.HexColor("#D97706"),
        "text_dark": colors.HexColor("#0F172A"),
        "text_body": colors.HexColor("#374151"),
        "text_muted": colors.HexColor("#6B7280"),
    },
    "emerald_gold": {  # Emerald & Gold
        "primary": colors.HexColor("#065F46"),
        "secondary": colors.HexColor("#B45309"),
        "text_dark": colors.HexColor("#064E3B"),
        "text_body": colors.HexColor("#1F2937"),
        "text_muted": colors.HexColor("#4B5563"),
    },
    "burgundy_luxury": {  # Royal Burgundy & Rose Gold
        "primary": colors.HexColor("#831843"),
        "secondary": colors.HexColor("#9D174D"),
        "text_dark": colors.HexColor("#500724"),
        "text_body": colors.HexColor("#374151"),
        "text_muted": colors.HexColor("#6B7280"),
    },
    "slate_corporate": {  # Slate & Silver
        "primary": colors.HexColor("#334155"),
        "secondary": colors.HexColor("#64748B"),
        "text_dark": colors.HexColor("#0F172A"),
        "text_body": colors.HexColor("#334155"),
        "text_muted": colors.HexColor("#64748B"),
    }
}


def build_certificate_pdf(
    certificate_id: str,
    recipient_name: str,
    title: str,
    issuer_name: str,
    issue_date: str,
    certificate_code: str,
    custom_attributes: Optional[Dict[str, Any]] = None,
    template_type: str = "standard_v1",
    certificate_heading: Optional[str] = None,
    output_dir: Optional[Path] = None
) -> Path:
    """
    Generates a professional customizable PDF certificate for a recipient.
    Returns the Path to the generated PDF file.
    """
    target_dir = output_dir or settings.STORAGE_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    file_path = target_dir / f"{certificate_id}.pdf"

    theme = THEMES.get(template_type, THEMES["standard_v1"])
    heading_text = (certificate_heading or "CERTIFICATE OF ACHIEVEMENT").upper()

    # Landscape Letter size: 792 x 612 points
    c = canvas.Canvas(str(file_path), pagesize=landscape(letter))
    width, height = landscape(letter)

    # 1. Background / Outer Border
    c.setStrokeColor(theme["primary"])
    c.setLineWidth(6)
    c.rect(20, 20, width - 40, height - 40)

    # 2. Inner Secondary Accent Border
    c.setStrokeColor(theme["secondary"])
    c.setLineWidth(2)
    c.rect(28, 28, width - 56, height - 56)

    # 3. Top Decorative Ribbon / Banner
    c.setFillColor(theme["primary"])
    c.rect(28, height - 38, width - 56, 10, fill=1, stroke=0)
    c.rect(28, 28, width - 56, 10, fill=1, stroke=0)

    # 4. Certificate Heading
    c.setFillColor(theme["primary"])
    c.setFont("Helvetica-Bold", 28)
    c.drawCentredString(width / 2.0, height - 90, heading_text)

    # 5. Subtitle
    c.setFillColor(theme["text_body"])
    c.setFont("Helvetica", 14)
    c.drawCentredString(width / 2.0, height - 125, "THIS IS PROUDLY PRESENTED TO")

    # 6. Recipient Name
    c.setFillColor(theme["text_dark"])
    c.setFont("Helvetica-Bold", 30)
    c.drawCentredString(width / 2.0, height - 175, recipient_name.strip())

    # 7. Decorative Line under recipient name
    c.setStrokeColor(theme["secondary"])
    c.setLineWidth(1.5)
    c.line(width / 2.0 - 180, height - 190, width / 2.0 + 180, height - 190)

    # 8. Completion Statement
    c.setFillColor(theme["text_body"])
    c.setFont("Helvetica", 14)
    c.drawCentredString(width / 2.0, height - 230, "for successful completion of")

    # 9. Event / Course Title
    c.setFillColor(theme["primary"])
    c.setFont("Helvetica-Bold", 22)
    c.drawCentredString(width / 2.0, height - 265, title.strip())

    # 10. Custom Attributes (Grade, Score, Extra Details)
    current_y = height - 305
    if custom_attributes:
        formatted_attrs = []
        for k, v in custom_attributes.items():
            if v is not None and str(v).strip():
                clean_k = k.replace('_', ' ').capitalize()
                formatted_attrs.append(f"{clean_k}: {v}")
        
        if formatted_attrs:
            attr_text = "  |  ".join(formatted_attrs)
            c.setFillColor(theme["text_body"])
            c.setFont("Helvetica-Oblique", 12)
            c.drawCentredString(width / 2.0, current_y, attr_text)

    # 11. Footer Section: Date, Issuer Signature, Verification Code
    c.setFillColor(theme["text_body"])
    c.setFont("Helvetica", 11)
    c.drawString(60, 100, f"Date: {issue_date}")
    c.setStrokeColor(colors.HexColor("#9CA3AF"))
    c.setLineWidth(1)
    c.line(60, 115, 200, 115)

    # Right: Issuer Signature Line
    c.drawString(width - 240, 100, f"Issued by: {issuer_name}")
    c.line(width - 240, 115, width - 60, 115)

    # Center Bottom: Certificate Verification Code
    c.setFillColor(theme["text_muted"])
    c.setFont("Helvetica", 10)
    c.drawCentredString(width / 2.0, 50, f"Verification Code: {certificate_code}")

    c.showPage()
    c.save()

    return file_path
