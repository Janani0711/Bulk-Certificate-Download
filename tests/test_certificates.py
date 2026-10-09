import zipfile
import io
from fastapi import status


def test_certificate_retrieval_download_and_verify(client):
    # 1. Create job
    payload = {
        "title": "Fullstack Engineering",
        "issuer_name": "Tech Institute",
        "issue_date": "2026-10-09",
        "recipients": [
            {"recipient_name": "Eva Green", "recipient_email": "eva@example.com"}
        ]
    }
    job_resp = client.post("/api/v1/jobs", json=payload)
    job_id = job_resp.json()["id"]

    # 2. Get certificate list for job
    certs_resp = client.get(f"/api/v1/jobs/{job_id}/certificates")
    assert certs_resp.status_code == status.HTTP_200_OK
    certs = certs_resp.json()
    assert len(certs) == 1
    cert = certs[0]
    cert_id = cert["id"]
    cert_code = cert["certificate_code"]

    # 3. Retrieve single certificate metadata
    single_resp = client.get(f"/api/v1/certificates/{cert_id}")
    assert single_resp.status_code == status.HTTP_200_OK
    assert single_resp.json()["recipient_name"] == "Eva Green"

    # 4. Download individual PDF
    download_resp = client.get(f"/api/v1/certificates/{cert_id}/download")
    assert download_resp.status_code == status.HTTP_200_OK
    assert download_resp.headers["content-type"] == "application/pdf"
    assert len(download_resp.content) > 0

    # 5. Public verification endpoint
    verify_resp = client.get(f"/api/v1/certificates/verify/{cert_code}")
    assert verify_resp.status_code == status.HTTP_200_OK
    vdata = verify_resp.json()
    assert vdata["valid"] is True
    assert vdata["recipient_name"] == "Eva Green"
    assert vdata["title"] == "Fullstack Engineering"

    # Verify invalid code
    bad_verify = client.get("/api/v1/certificates/verify/NONEXISTENT_CODE")
    assert bad_verify.status_code == status.HTTP_200_OK
    assert bad_verify.json()["valid"] is False


def test_download_all_job_certificates_zip(client):
    payload = {
        "title": "Machine Learning Specialization",
        "issuer_name": "AI Academy",
        "recipients": [
            {"recipient_name": "Frank White", "recipient_email": "frank@example.com"},
            {"recipient_name": "Grace Hopper", "recipient_email": "grace@example.com"}
        ]
    }
    job_resp = client.post("/api/v1/jobs", json=payload)
    job_id = job_resp.json()["id"]

    zip_resp = client.get(f"/api/v1/jobs/{job_id}/download-all")
    assert zip_resp.status_code == status.HTTP_200_OK
    assert zip_resp.headers["content-type"] == "application/zip"

    # Read zip file content and check files inside
    with zipfile.ZipFile(io.BytesIO(zip_resp.content)) as zf:
        file_list = zf.namelist()
        assert len(file_list) == 2
        assert any("Frank_White" in f for f in file_list)
        assert any("Grace_Hopper" in f for f in file_list)
