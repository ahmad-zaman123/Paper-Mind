from dataclasses import dataclass

from django.conf import settings
from docx import Document as DocxDocument
from pypdf import PdfReader

from apps.documents.constants import MAX_CHUNKS_PER_DOCUMENT


@dataclass
class ExtractedContent:
    text: str
    page_count: int


def _extract_pdf(uploaded_file):
    uploaded_file.seek(0)
    reader = PdfReader(uploaded_file)
    parts = [(page.extract_text() or "") for page in reader.pages]
    text = "\n\n".join(parts).strip()
    return ExtractedContent(text=text, page_count=len(reader.pages))


def _extract_docx(uploaded_file):
    uploaded_file.seek(0)
    document = DocxDocument(uploaded_file)
    parts = [paragraph.text for paragraph in document.paragraphs if paragraph.text.strip()]
    text = "\n".join(parts).strip()
    # Word documents have no reliable page markers, so page count is left as 1.
    return ExtractedContent(text=text, page_count=1)


def _extract_plain_text(uploaded_file):
    uploaded_file.seek(0)
    text = uploaded_file.read().decode("utf-8", errors="replace").strip()
    return ExtractedContent(text=text, page_count=1)


def extract_content(uploaded_file):
    """Extract plain text and page count from an uploaded PDF/docx/txt/md file."""

    extension = uploaded_file.name.rsplit(".", 1)[-1].lower()
    if extension == "pdf":
        return _extract_pdf(uploaded_file)
    if extension == "docx":
        return _extract_docx(uploaded_file)
    return _extract_plain_text(uploaded_file)


def chunk_text(text, chunk_size=None, overlap=None):
    """Split text into overlapping, word-boundary-aligned chunks for embedding."""

    chunk_size = chunk_size or settings.CHUNK_SIZE
    overlap = overlap or settings.CHUNK_OVERLAP

    normalized = " ".join(text.split())
    if not normalized:
        return []

    chunks = []
    start = 0
    length = len(normalized)
    while start < length and len(chunks) < MAX_CHUNKS_PER_DOCUMENT:
        end = start + chunk_size
        if end < length:
            boundary = normalized.rfind(" ", start, end)
            if boundary > start:
                end = boundary
        piece = normalized[start:end].strip()
        if piece:
            chunks.append(piece)
        if end >= length:
            break
        start = max(end - overlap, start + 1)

    return chunks
