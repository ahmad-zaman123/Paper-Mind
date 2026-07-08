from apps.documents.choices import DocumentStatus
from apps.documents.clients import GeminiClient
from apps.documents.models import Chunk, Document
from apps.documents.utils import chunk_text, extract_content


def ingest_document(*, owner, uploaded_file, title):
    """Create a Document, extract its text, then chunk and embed it.

    A document is only marked ``ready`` once its chunks are embedded and stored,
    so ``ready`` reliably means the document is searchable.
    """

    document = Document.objects.create(
        owner=owner,
        title=title,
        filename=uploaded_file.name,
        status=DocumentStatus.PROCESSING,
    )
    document.chunk_count = 0

    try:
        content = extract_content(uploaded_file)
        if not content.text:
            raise ValueError("No extractable text found — the file may be scanned images.")

        chunks = chunk_text(content.text)
        if not chunks:
            raise ValueError("The document produced no text chunks to index.")

        embeddings = GeminiClient().embed_documents(chunks)
        Chunk.objects.bulk_create(
            [
                Chunk(document=document, content=piece, embedding=vector, chunk_index=index)
                for index, (piece, vector) in enumerate(zip(chunks, embeddings))
            ]
        )

        document.extracted_text = content.text
        document.page_count = content.page_count
        document.char_count = len(content.text)
        document.status = DocumentStatus.READY
        document.chunk_count = len(chunks)
        document.save(
            update_fields=("extracted_text", "page_count", "char_count", "status", "modified"),
        )
    except Exception as exc:
        document.status = DocumentStatus.FAILED
        document.error_message = str(exc)[:255]
        document.save(update_fields=("status", "error_message", "modified"))

    return document
