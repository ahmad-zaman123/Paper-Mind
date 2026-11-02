import logging

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import transaction
from pgvector.django import CosineDistance

from apps.documents.choices import DocumentStatus
from apps.documents.clients import GeminiClient
from apps.documents.models import Chunk, Document
from apps.documents.utils import (
    CITATION_REMINDER,
    build_rag_prompt,
    chunk_pages,
    extract_content,
    has_citation,
    says_not_found,
)

logger = logging.getLogger(__name__)


def create_document(*, owner, uploaded_file, title):
    """Create a Document and index it (extract, chunk, embed, store).

    Indexing runs inline so it works on every platform, including serverless.
    Batched embeddings keep the request short for normal-sized documents.
    """

    file_bytes = uploaded_file.read()
    filename = uploaded_file.name

    document = Document.objects.create(
        owner=owner,
        title=title,
        filename=filename,
        status=DocumentStatus.PROCESSING,
    )

    _index_document(document, file_bytes)
    document.chunk_count = document.chunks.count()
    return document


def _index_document(document, file_bytes):
    """Extract, chunk, and embed a document, then mark it ready or failed."""

    try:
        content = extract_content(SimpleUploadedFile(document.filename, file_bytes))
        if not content.text:
            raise ValueError("No extractable text found — the file may be scanned images.")

        chunks = chunk_pages(content.pages)
        if not chunks:
            raise ValueError("The document produced no text chunks to index.")

        embeddings = GeminiClient().embed_documents([piece for _, piece in chunks])
        with transaction.atomic():
            Chunk.objects.bulk_create(
                [
                    Chunk(document=document, content=piece, page=page, embedding=vector, chunk_index=index)
                    for index, ((page, piece), vector) in enumerate(zip(chunks, embeddings))
                ]
            )
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


def _citation_page(chunk, document):
    """The page to cite. Passages indexed before pages were stored have page 0."""

    if not chunk.page and document.page_count == 1 and document.filename.lower().endswith(".pdf"):
        return 1
    return chunk.page


def _generate_cited_answer(client, prompt, passage_count):
    """Generate an answer, asking once more if it neither cites a passage nor says it can't answer."""

    answer = client.generate_answer(prompt)
    if has_citation(answer, passage_count) or says_not_found(answer):
        return answer
    try:
        return client.generate_answer(prompt + CITATION_REMINDER) or answer
    except Exception:
        # The first answer is still usable, and it is shown as uncited.
        logger.warning("Retrying an uncited answer failed.", exc_info=True)
        return answer


def answer_question(*, document, question, history=None):
    """Answer a question about a document using retrieval-augmented generation.

    Embeds the question, retrieves the nearest chunks by cosine distance, prompts
    the model with that context (and any prior conversation turns), and returns the
    answer alongside the chunks used as citations.
    """

    client = GeminiClient()
    query_vector = client.embed_query(question)

    chunks = list(
        Chunk.objects.filter(document=document)
        .annotate(distance=CosineDistance("embedding", query_vector))
        .order_by("distance")[: settings.RETRIEVAL_TOP_K]
    )
    if not chunks:
        return {
            "answer": "This document has no indexed content to answer from.",
            "citations": [],
        }

    prompt = build_rag_prompt(question, chunks, history=history)
    answer = _generate_cited_answer(client, prompt, len(chunks))

    citations = [
        {
            "chunk_index": chunk.chunk_index,
            "page": _citation_page(chunk, document),
            "content": chunk.content,
            "score": round(1 - chunk.distance, 4),
        }
        for chunk in chunks
    ]
    if not has_citation(answer, len(chunks)):
        # "Not in the document" has no sources. Any other uncited answer gets the closest
        # passage, marked so the page can say the model did not cite it.
        citations = [] if says_not_found(answer) else [{**citations[0], "uncited": True}]
    return {"answer": answer, "citations": citations}
