from app.chunking import chunk_text


def test_empty_input_returns_no_chunks():
    assert chunk_text("") == []
    assert chunk_text("   \n\t  ") == []


def test_short_input_returns_single_chunk():
    assert chunk_text("Hello world", chunk_size=1000, overlap=150) == ["Hello world"]


def test_input_is_stripped():
    assert chunk_text("  Hello world  \n") == ["Hello world"]


def test_overlap_repeats_boundary_text():
    text = "abcdefghij" * 5  # 50 chars
    chunks = chunk_text(text, chunk_size=20, overlap=5)

    assert len(chunks) > 1
    # the tail of each chunk should reappear at the head of the next
    for first, second in zip(chunks, chunks[1:]):
        assert first[-5:] == second[:5]


def test_chunks_cover_the_whole_input():
    text = "x" * 47
    chunks = chunk_text(text, chunk_size=20, overlap=5)

    covered = set()
    position = 0
    for chunk in chunks:
        covered.update(range(position, position + len(chunk)))
        position += 20 - 5
    assert covered.issuperset(range(len(text)))


def test_custom_chunk_size_and_overlap_respected():
    text = "1234567890" * 3  # 30 chars
    chunks = chunk_text(text, chunk_size=10, overlap=0)

    assert chunks == ["1234567890", "1234567890", "1234567890"]
