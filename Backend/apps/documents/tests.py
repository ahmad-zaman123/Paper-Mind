from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.documents.constants import MAX_CHUNKS_PER_DOCUMENT
from apps.documents.handlers import _index_document, answer_question
from apps.documents.models import Chunk, Document
from apps.documents.utils import ExtractedContent, chunk_pages


class ChunkPagesTests(TestCase):
    def test_each_passage_keeps_its_own_page(self):
        chunks = chunk_pages([(1, "first page words"), (2, ""), (3, "third page words")])
        self.assertEqual(chunks, [(1, "first page words"), (3, "third page words")])

    def test_long_page_splits_into_passages_on_the_same_page(self):
        chunks = chunk_pages([(4, "word " * 2000)])
        self.assertGreater(len(chunks), 1)
        self.assertEqual({page for page, _ in chunks}, {4})

    def test_total_is_capped_across_pages(self):
        pages = [(number, "word " * 2000) for number in range(1, 200)]
        self.assertEqual(len(chunk_pages(pages)), MAX_CHUNKS_PER_DOCUMENT)


class IndexDocumentTests(TestCase):
    def index(self, content):
        owner = get_user_model().objects.create_user(email="pages@example.com", password="Str0ng-pass-1")
        document = Document.objects.create(owner=owner, title="Doc", filename="doc.pdf", status="processing")
        with (
            patch("apps.documents.handlers.extract_content", return_value=content),
            patch("apps.documents.handlers.GeminiClient") as client,
        ):
            client.return_value.embed_documents.side_effect = lambda pieces: [[0.0] * 768 for _ in pieces]
            _index_document(document, b"file")
        document.refresh_from_db()
        return document

    def test_pdf_passages_store_their_page(self):
        document = self.index(ExtractedContent("one\n\ntwo", 2, [(1, "one"), (2, "two")]))
        self.assertEqual(document.status, "ready")
        stored = list(document.chunks.order_by("chunk_index").values_list("page", "content"))
        self.assertEqual(stored, [(1, "one"), (2, "two")])

    def test_formats_without_pages_store_page_zero(self):
        document = self.index(ExtractedContent("plain text", 1, [(0, "plain text")]))
        self.assertEqual(list(document.chunks.values_list("page", flat=True)), [0])


class CitationPageTests(TestCase):
    def cited_page(self, filename, page_count, page):
        owner = get_user_model().objects.create_user(email="cite@example.com", password="Str0ng-pass-1")
        document = Document.objects.create(
            owner=owner, title="Doc", filename=filename, status="ready", page_count=page_count
        )
        Chunk.objects.create(document=document, content="text", page=page, embedding=[1.0] * 768, chunk_index=0)
        with patch("apps.documents.handlers.GeminiClient") as client:
            client.return_value.embed_query.return_value = [1.0] * 768
            client.return_value.generate_answer.return_value = "Answer [1]"
            return answer_question(document=document, question="Why?")["citations"][0]["page"]

    def test_older_one_page_pdf_cites_page_one(self):
        self.assertEqual(self.cited_page("doc.PDF", 1, 0), 1)

    def test_older_longer_pdf_stays_unknown(self):
        self.assertEqual(self.cited_page("doc.pdf", 3, 0), 0)

    def test_word_document_has_no_page(self):
        self.assertEqual(self.cited_page("doc.docx", 1, 0), 0)

    def test_stored_page_is_kept(self):
        self.assertEqual(self.cited_page("doc.pdf", 3, 2), 2)
