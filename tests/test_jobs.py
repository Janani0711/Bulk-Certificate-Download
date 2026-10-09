from fastapi import status


def test_create_generation_job(client):
    payload = {
        "title": "Python Developer Certification",
        "issuer_name": "Tech Certifications Inc",
        "issue_date": "2026-10-09",
        "recipients": [
            {"recipient_name": "Alice Johnson", "recipient_email": "alice@example.com"},
            {"recipient_name": "Bob Smith", "recipient_email": "bob@example.com"}
        ]
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == status.HTTP_202_ACCEPTED
    data = response.json()
    assert "id" in data
    assert data["title"] == "Python Developer Certification"
    assert data["total_count"] == 2
    assert data["status"] in ["PENDING", "COMPLETED", "PROCESSING"]


def test_get_job_status_and_certificates(client):
    payload = {
        "title": "Data Science Masterclass",
        "issuer_name": "Data Academy",
        "recipients": [
            {
                "recipient_name": "Charlie Brown",
                "recipient_email": "charlie@example.com",
                "custom_attributes": {"score": "98%", "grade": "A+"}
            }
        ]
    }
    create_resp = client.post("/api/v1/jobs", json=payload)
    assert create_resp.status_code == status.HTTP_202_ACCEPTED
    job_id = create_resp.json()["id"]

    status_resp = client.get(f"/api/v1/jobs/{job_id}")
    assert status_resp.status_code == status.HTTP_200_OK
    job_data = status_resp.json()
    assert job_data["id"] == job_id
    assert job_data["status"] == "COMPLETED"
    assert job_data["success_count"] == 1
    assert job_data["failed_count"] == 0
    assert len(job_data["certificates"]) == 1
    assert job_data["certificates"][0]["recipient_name"] == "Charlie Brown"
    assert job_data["certificates"][0]["custom_attributes"]["grade"] == "A+"
