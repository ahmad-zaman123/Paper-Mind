from apps.documents.choices import DocumentStatus
from apps.documents.models import Document
from apps.documents.utils import extract_content


def ingest_document(*, owner, uploaded_file, title):
    """Create a Document and synchronously extract its text.

    Phase 2 extends this flow to chunk and embed the extracted text once
    extraction succeeds.
    """

    document = Document.objects.create(
        owner=owner,
        title=title,
        filename=uploaded_file.name,
        status=DocumentStatus.PROCESSING,
    )

    try:
        content = extract_content(uploaded_file)
        if not content.text:
            raise ValueError("No extractable text found — the file may be scanned images.")

        document.extracted_text = content.text
        document.page_count = content.page_count
        document.char_count = len(content.text)
        document.status = DocumentStatus.READY
        document.save(
            update_fields=("extracted_text", "page_count", "char_count", "status", "modified"),
        )
    except Exception as exc:
        document.status = DocumentStatus.FAILED
        document.error_message = str(exc)[:255]
        document.save(update_fields=("status", "error_message", "modified"))

    return document
