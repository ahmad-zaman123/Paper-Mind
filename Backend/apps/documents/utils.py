from dataclasses import dataclass

from docx import Document as DocxDocument
from pypdf import PdfReader


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
