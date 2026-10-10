def test_upload_search_list_reindex_and_delete(client, pdf_factory):
    upload = client.post(
        "/api/documents",
        files={"file": ("guide.pdf", pdf_factory("Python vector search guide"), "application/pdf")},
        data={"chunk_size": 100, "chunk_overlap": 20},
    )
    assert upload.status_code == 201
    document = upload.json()
    assert document["filename"] == "guide.pdf"
    assert document["page_count"] == 1
    assert document["chunk_count"] == 1

    listed = client.get("/api/documents")
    assert [item["id"] for item in listed.json()] == [document["id"]]

    searched = client.post("/api/search", json={"query": "python search", "top_k": 5})
    assert searched.status_code == 200
    result = searched.json()["results"][0]
    assert result["pdf_name"] == "guide.pdf"
    assert result["page_number"] == 1
    assert "Python vector search" in result["text"]
    assert result["score"] > 0

    reindexed = client.post(
        f"/api/documents/{document['id']}/reindex", data={"chunk_size": 80, "chunk_overlap": 10}
    )
    assert reindexed.status_code == 200
    assert reindexed.json()["chunk_size"] == 80

    deleted = client.delete(f"/api/documents/{document['id']}")
    assert deleted.status_code == 200
    assert client.get("/api/documents").json() == []
    assert client.post("/api/search", json={"query": "python", "top_k": 5}).json() == {
        "results": []
    }


def test_upload_rejects_invalid_and_empty_pdf(client):
    invalid = client.post(
        "/api/documents", files={"file": ("broken.pdf", b"broken", "application/pdf")}
    )
    assert invalid.status_code == 400
    assert "readable PDF" in invalid.json()["detail"]


def test_search_rejects_blank_query(client):
    response = client.post("/api/search", json={"query": "   ", "top_k": 5})
    assert response.status_code == 422
