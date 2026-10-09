from fastapi import status
from app.services.validation_service import validate_recipient_data


def test_validation_service_direct():
    is_valid, msg = validate_recipient_data("John Doe", "john@example.com")
    assert is_valid is True
    assert msg is None

    is_valid, msg = validate_recipient_data("", "john@example.com")
    assert is_valid is False
    assert "cannot be empty" in msg

    is_valid, msg = validate_recipient_data("John Doe", "invalid-email-format")
    assert is_valid is False
    assert "Invalid recipient email" in msg


def test_api_empty_recipients_validation(client):
    payload = {
        "title": "Web Development Bootcamp",
        "recipients": []
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_individual_certificate_failure_handling(client):
    """
    Test job with mixed valid and invalid recipients.
    Valid recipients should generate successfully.
    Invalid recipient should fail without stopping the valid ones.
    """
    payload = {
        "title": "Cloud Computing Workshop",
        "issuer_name": "Tech Corp",
        "recipients": [
            {"recipient_name": "Valid Student", "recipient_email": "student@example.com"},
            {"recipient_name": "Bad Email Recipient", "recipient_email": "not-an-email"},
            {"recipient_name": "   ", "recipient_email": "empty_name@example.com"}
        ]
    }

    create_resp = client.post("/api/v1/jobs", json=payload)
    assert create_resp.status_code == status.HTTP_202_ACCEPTED
    job_id = create_resp.json()["id"]

    # Check status
    get_resp = client.get(f"/api/v1/jobs/{job_id}")
    assert get_resp.status_code == status.HTTP_200_OK
    job_data = get_resp.json()

    assert job_data["status"] == "PARTIALLY_FAILED"
    assert job_data["total_count"] == 3
    assert job_data["success_count"] == 1
    assert job_data["failed_count"] == 2

    certificates = job_data["certificates"]
    
    # Valid student succeeded
    valid_cert = next(c for c in certificates if c["recipient_name"] == "Valid Student")
    assert valid_cert["status"] == "SUCCESS"
    assert valid_cert["certificate_code"] is not None

    # Invalid email failed
    bad_email_cert = next(c for c in certificates if c["recipient_name"] == "Bad Email Recipient")
    assert bad_email_cert["status"] == "FAILED"
    assert "Invalid recipient email" in bad_email_cert["error_message"]

    # Empty name failed
    empty_name_cert = next(c for c in certificates if c["recipient_email"] == "empty_name@example.com")
    assert empty_name_cert["status"] == "FAILED"
    assert "cannot be empty" in empty_name_cert["error_message"]
