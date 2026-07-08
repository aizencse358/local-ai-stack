def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 150) -> list[str]:
    """Split text into overlapping fixed-size chunks."""
    stripped = text.strip()
    if not stripped:
        return []

    chunks = []
    start = 0
    length = len(stripped)
    step = chunk_size - overlap

    while start < length:
        chunk = stripped[start : start + chunk_size].strip()
        if chunk:
            chunks.append(chunk)
        start += step

    return chunks
