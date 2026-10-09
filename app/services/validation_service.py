import re
from typing import Tuple, Optional


EMAIL_REGEX = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")


def validate_recipient_data(recipient_name: str, recipient_email: Optional[str] = None) -> Tuple[bool, Optional[str]]:
    """
    Validates recipient details for certificate generation.
    Returns (is_valid, error_message).
    """
    if not recipient_name or not str(recipient_name).strip():
        return False, "Recipient name cannot be empty or whitespace"
    
    clean_name = str(recipient_name).strip()
    if len(clean_name) < 2:
        return False, "Recipient name must be at least 2 characters long"

    if recipient_email is not None and str(recipient_email).strip():
        clean_email = str(recipient_email).strip()
        if not EMAIL_REGEX.match(clean_email):
            return False, f"Invalid recipient email format: '{recipient_email}'"

    return True, None
