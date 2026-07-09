import pytest


def test_add_and_query_returns_most_similar_first(tmp_env):
    import app.vectorstore as vectorstore

    doc_a = vectorstore.add_document("a.txt", ["chunk about cats"], [[1.0, 0.0, 0.0]])
    doc_b = vectorstore.add_document("b.txt", ["chunk about dogs"], [[0.0, 1.0, 0.0]])

    hits = vectorstore.query([1.0, 0.0, 0.0], top_k=2)

    assert len(hits) == 2
    assert hits[0]["filename"] == "a.txt"
    assert hits[0]["score"] == pytest.approx(1.0)
    assert hits[1]["filename"] == "b.txt"
    assert hits[0]["score"] > hits[1]["score"]
    assert doc_a != doc_b


def test_list_documents_reports_chunk_counts(tmp_env):
    import app.vectorstore as vectorstore

    vectorstore.add_document(
        "multi.txt",
        ["chunk 1", "chunk 2", "chunk 3"],
        [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
    )
    vectorstore.add_document("single.txt", ["only chunk"], [[1.0, 1.0, 0.0]])

    docs = {d["filename"]: d for d in vectorstore.list_documents()}

    assert docs["multi.txt"]["chunk_count"] == 3
    assert docs["single.txt"]["chunk_count"] == 1


def test_delete_document_removes_only_its_chunks(tmp_env):
    import app.vectorstore as vectorstore

    doc_id = vectorstore.add_document("gone.txt", ["will be deleted"], [[1.0, 0.0, 0.0]])
    vectorstore.add_document("stays.txt", ["will remain"], [[0.0, 1.0, 0.0]])

    vectorstore.delete_document(doc_id)

    filenames = {d["filename"] for d in vectorstore.list_documents()}
    assert filenames == {"stays.txt"}
