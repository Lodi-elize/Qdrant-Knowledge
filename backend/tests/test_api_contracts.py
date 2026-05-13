from io import BytesIO


def test_query_requires_scope_and_question(client):
    response = client.post("/api/query", json={"question": "hello"})
    assert response.status_code == 422


def test_admin_upload_requires_admin_credentials(client):
    response = client.post(
        "/api/admin/upload",
        params={"product_line": "Alpha", "product_version": "v1"},
        files={"file": ("guide.txt", BytesIO(b"Alpha v1 setup guide"), "text/plain")},
    )
    assert response.status_code == 401


def test_admin_secret_stays_server_side_and_allows_upload(client):
    login = client.post("/api/admin/login", json={"admin_secret": "test-secret"})
    assert login.status_code == 200
    assert client.cookies.get("admin_session") != "test-secret"

    response = client.post(
        "/api/admin/upload",
        params={"product_line": "Alpha", "product_version": "v1"},
        files={"file": ("guide.txt", BytesIO(b"Alpha v1 setup guide"), "text/plain")},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["product_line"] == "Alpha"
    assert payload["product_version"] == "v1"
    assert payload["chunks_indexed"] >= 1


def test_query_response_shape(client):
    client.post(
        "/api/admin/upload",
        params={"product_line": "Alpha", "product_version": "v1"},
        headers={"X-Admin-Secret": "test-secret"},
        files={"file": ("guide.txt", BytesIO(b"Alpha v1 reset password steps"), "text/plain")},
    )
    response = client.post(
        "/api/query",
        json={"product_line": "Alpha", "product_version": "v1", "question": "How do I reset password?"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {
        "answer",
        "grounded_summary",
        "sources",
        "used_supplemental_knowledge",
        "supplemental_note",
    }
    assert payload["sources"]
    assert payload["sources"][0]["product_line"] == "Alpha"
    assert payload["sources"][0]["product_version"] == "v1"
