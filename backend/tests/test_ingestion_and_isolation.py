from io import BytesIO


def upload(client, product_line: str, product_version: str, text: str):
    return client.post(
        "/api/admin/upload",
        params={"product_line": product_line, "product_version": product_version},
        headers={"X-Admin-Secret": "test-secret"},
        files={"file": ("guide.txt", BytesIO(text.encode("utf-8")), "text/plain")},
    )


def query(client, product_line: str, product_version: str, question: str):
    return client.post(
        "/api/query",
        json={"product_line": product_line, "product_version": product_version, "question": question},
    )


def test_cross_version_leakage_conflicting_fixture_documents(client):
    upload(client, "Alpha", "v1", "Reset code for Alpha v1 is BLUE-111.")
    upload(client, "Alpha", "v2", "Reset code for Alpha v2 is GREEN-222.")

    v1 = query(client, "Alpha", "v1", "What is the reset code?")
    v2 = query(client, "Alpha", "v2", "What is the reset code?")

    assert v1.status_code == 200
    assert v2.status_code == 200

    v1_sources = v1.json()["sources"]
    v2_sources = v2.json()["sources"]
    assert v1_sources
    assert v2_sources
    assert all(source["product_version"] == "v1" for source in v1_sources)
    assert all(source["product_version"] == "v2" for source in v2_sources)
    assert "GREEN-222" not in " ".join(source["text"] for source in v1_sources)
    assert "BLUE-111" not in " ".join(source["text"] for source in v2_sources)


def test_unsupported_file_type_is_rejected(client):
    response = client.post(
        "/api/admin/upload",
        params={"product_line": "Alpha", "product_version": "v1"},
        headers={"X-Admin-Secret": "test-secret"},
        files={"file": ("guide.exe", BytesIO(b"not allowed"), "application/octet-stream")},
    )
    assert response.status_code == 415

