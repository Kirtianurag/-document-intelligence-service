import io


def test_upload_invalid_file_type(client, auth_headers):
    file_content = b"Plain text sample content"
    response = client.post(
        "/api/v1/documents/upload",
        headers=auth_headers,
        files={"file": ("invalid_doc.txt", io.BytesIO(file_content), "text/plain")}
    )
    assert response.status_code == 400
    assert "Unsupported file extension" in response.json()["detail"]


def test_unauthorized_upload(client):
    file_content = b"%PDF-1.4 sample content"
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("sample.pdf", io.BytesIO(file_content), "application/pdf")}
    )
    assert response.status_code == 401
