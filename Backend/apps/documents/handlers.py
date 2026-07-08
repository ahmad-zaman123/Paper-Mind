from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import transaction
from pgvector.django import CosineDistance

from apps.documents.choices import DocumentStatus
from apps.documents.clients import GeminiClient
from apps.documents.models import Chunk, Document
from apps.documents.utils import build_rag_prompt, chunk_text, extract_content


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

        chunks = chunk_text(content.text)
        if not chunks:
            raise ValueError("The document produced no text chunks to index.")

        embeddings = GeminiClient().embed_documents(chunks)
        with transaction.atomic():
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
            document.save(
                update_fields=("extracted_text", "page_count", "char_count", "status", "modified"),
            )
    except Exception as exc:
        document.status = DocumentStatus.FAILED
        document.error_message = str(exc)[:255]
        document.save(update_fields=("status", "error_message", "modified"))


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
    answer = client.generate_answer(prompt)

    citations = [
        {
            "chunk_index": chunk.chunk_index,
            "page": chunk.page,
            "content": chunk.content,
            "score": round(1 - chunk.distance, 4),
        }
        for chunk in chunks
    ]
    return {"answer": answer, "citations": citations}
