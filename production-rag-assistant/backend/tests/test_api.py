def upload(client, pdf_factory, filename, text):
    return client.post(
        "/api/documents",
        files={"file": (filename, pdf_factory(text), "application/pdf")},
        data={"chunk_size": 200, "chunk_overlap": 20},
    )


def test_rag_endpoint_returns_grounded_answer_and_sources(
    client, pdf_factory, services
):
    indexed = upload(
        client, pdf_factory, "python.pdf", "Python vector search uses embeddings."
    )
    assert indexed.status_code == 201

    response = client.post(
        "/api/ask",
        json={
            "question": "What is Python vector search?",
            "top_k": 3,
            "similarity_threshold": 0.1,
            "use_query_rewrite": True,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert "[Source 1]" in payload["answer"]
    assert payload["retrieval_query"] == "Python vector search"
    assert payload["insufficient_context"] is False
    assert payload["sources"][0]["pdf_name"] == "python.pdf"
    assert payload["sources"][0]["page_number"] == 1
    assert payload["sources"][0]["score"] > 0
    assert "Context:" in services[2].calls[0][1]


def test_document_metadata_filter(client, pdf_factory):
    python_doc = upload(
        client, pdf_factory, "python.pdf", "Python vector search"
    ).json()
    music_doc = upload(client, pdf_factory, "music.pdf", "Music database notes").json()
    response = client.post(
        "/api/ask",
        json={
            "question": "database",
            "top_k": 5,
            "similarity_threshold": -1,
            "document_ids": [music_doc["id"]],
        },
    )
    source_ids = {source["document_id"] for source in response.json()["sources"]}
    assert source_ids == {music_doc["id"]}
    assert python_doc["id"] not in source_ids


def test_blank_question_is_rejected(client):
    response = client.post("/api/ask", json={"question": "   "})
    assert response.status_code == 422


def test_document_management_is_preserved(client, pdf_factory):
    document = upload(client, pdf_factory, "guide.pdf", "Python search guide").json()
    assert client.get("/api/documents").json()[0]["id"] == document["id"]
    assert client.post(f"/api/documents/{document['id']}/reindex").status_code == 200
    assert client.delete(f"/api/documents/{document['id']}").status_code == 200
    assert client.get("/api/documents").json() == []
