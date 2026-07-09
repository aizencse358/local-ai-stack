import io

from docx import Document
from pypdf import PdfReader


def extract_text(filename: str, content: bytes) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    try:
        if ext in ("txt", "md"):
            return content.decode("utf-8", errors="ignore")
        if ext == "pdf":
            reader = PdfReader(io.BytesIO(content))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        if ext == "docx":
            document = Document(io.BytesIO(content))
            return "\n".join(p.text for p in document.paragraphs)
    except Exception as e:
        raise ValueError(f"Could not read .{ext} file: {e}") from e

    raise ValueError(f"Unsupported file type: .{ext}")
