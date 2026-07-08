from dataclasses import dataclass

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


def _extract_plain_text(uploaded_file):
    uploaded_file.seek(0)
    text = uploaded_file.read().decode("utf-8", errors="replace").strip()
    return ExtractedContent(text=text, page_count=1)


def extract_content(uploaded_file):
    """Extract plain text and page count from an uploaded PDF/txt/md file."""

    extension = uploaded_file.name.rsplit(".", 1)[-1].lower()
    if extension == "pdf":
        return _extract_pdf(uploaded_file)
    return _extract_plain_text(uploaded_file)
