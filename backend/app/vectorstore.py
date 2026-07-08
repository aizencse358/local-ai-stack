import os
import uuid

import chromadb

CHROMA_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_data")

_client = chromadb.PersistentClient(path=CHROMA_DIR)
_collection = _client.get_or_create_collection("documents")


def add_document(filename: str, chunks: list[str], embeddings: list[list[float]]) -> str:
    document_id = str(uuid.uuid4())
    ids = [f"{document_id}:{i}" for i in range(len(chunks))]
    metadatas = [
        {"document_id": document_id, "filename": filename, "chunk_index": i}
        for i in range(len(chunks))
    ]
    _collection.add(ids=ids, documents=chunks, embeddings=embeddings, metadatas=metadatas)
    return document_id


def query(query_embedding: list[float], top_k: int = 4) -> list[dict]:
    result = _collection.query(query_embeddings=[query_embedding], n_results=top_k)

    documents = result.get("documents") or [[]]
    metadatas = result.get("metadatas") or [[]]
    distances = result.get("distances") or [[]]

    hits = []
    for text, metadata, distance in zip(documents[0], metadatas[0], distances[0]):
        hits.append(
            {
                "filename": metadata.get("filename", "unknown"),
                "text": text,
                "score": distance,
            }
        )
    return hits


def list_documents() -> list[dict]:
    result = _collection.get()
    metadatas = result.get("metadatas") or []

    documents: dict[str, dict] = {}
    for metadata in metadatas:
        document_id = metadata["document_id"]
        if document_id not in documents:
            documents[document_id] = {
                "id": document_id,
                "filename": metadata["filename"],
                "chunk_count": 0,
            }
        documents[document_id]["chunk_count"] += 1

    return list(documents.values())


def delete_document(document_id: str) -> None:
    _collection.delete(where={"document_id": document_id})
