from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase, override_settings

from apps.documents.clients import GeminiClient, GeminiUnavailable
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


class AnswerCitationTests(TestCase):
    def ask(self, *answers):
        owner = get_user_model().objects.create_user(email="answers@example.com", password="Str0ng-pass-1")
        document = Document.objects.create(owner=owner, title="Doc", filename="doc.pdf", status="ready")
        for index, vector in enumerate(([1.0] + [0.0] * 767, [0.0] * 767 + [1.0])):
            Chunk.objects.create(
                document=document, content="passage " + str(index), page=index + 1, embedding=vector, chunk_index=index
            )
        with patch("apps.documents.handlers.GeminiClient") as client:
            client.return_value.embed_query.return_value = [1.0] + [0.0] * 767
            client.return_value.generate_answer.side_effect = answers
            result = answer_question(document=document, question="Why?")
            self.prompts = [call.args[0] for call in client.return_value.generate_answer.call_args_list]
        return result

    def test_cited_answer_is_not_retried_and_keeps_its_passages(self):
        result = self.ask("Because [1].")
        self.assertEqual(len(self.prompts), 1)
        self.assertEqual(len(result["citations"]), 2)
        self.assertNotIn("uncited", result["citations"][0])

    def test_grouped_citation_counts(self):
        self.assertEqual(len(self.ask("Because [1, 2].")["citations"]), 2)
        self.assertEqual(len(self.prompts), 1)

    def test_not_found_answer_is_not_retried_and_has_no_sources(self):
        result = self.ask("The document does not contain that information.")
        self.assertEqual(len(self.prompts), 1)
        self.assertEqual(result["citations"], [])

    def test_uncited_answer_is_retried_with_a_reminder(self):
        result = self.ask("Because.", "Because [2].")
        self.assertEqual(len(self.prompts), 2)
        self.assertIn("cited no passages", self.prompts[1])
        self.assertEqual(result["answer"], "Because [2].")
        self.assertEqual(len(result["citations"]), 2)

    def test_retry_can_end_in_not_found(self):
        result = self.ask("Because.", "The document does not contain that information.")
        self.assertEqual(result["citations"], [])

    def test_still_uncited_answer_gets_the_closest_passage_marked_uncited(self):
        result = self.ask("Because.", "Still because.")
        self.assertEqual(result["answer"], "Still because.")
        self.assertEqual(len(result["citations"]), 1)
        self.assertTrue(result["citations"][0]["uncited"])
        self.assertEqual(result["citations"][0]["content"], "passage 0")

    def test_marker_outside_the_passages_does_not_count(self):
        result = self.ask("Because [9].", "Still [9].")
        self.assertEqual(len(self.prompts), 2)
        self.assertTrue(result["citations"][0]["uncited"])

    def test_failed_retry_keeps_the_first_answer(self):
        result = self.ask("Because.", RuntimeError("model down"))
        self.assertEqual(result["answer"], "Because.")
        self.assertTrue(result["citations"][0]["uncited"])


@override_settings(
    GEMINI_API_KEY="test", GEMINI_CHAT_MODEL="models/first", GEMINI_FALLBACK_MODELS=["models/second", "models/third"]
)
class GenerateAnswerTests(SimpleTestCase):
    def generate(self, *replies):
        with patch("apps.documents.clients.genai") as genai:
            generate_content = genai.Client.return_value.models.generate_content
            generate_content.side_effect = replies
            try:
                return GeminiClient().generate_answer("prompt")
            finally:
                self.models = [call.kwargs["model"] for call in generate_content.call_args_list]

    def test_first_model_answers(self):
        self.assertEqual(self.generate(SimpleNamespace(text="Answer")), "Answer")
        self.assertEqual(self.models, ["first"])

    def test_failed_model_falls_back(self):
        self.assertEqual(self.generate(RuntimeError("429"), SimpleNamespace(text="Answer")), "Answer")
        self.assertEqual(self.models, ["first", "second"])

    def test_empty_reply_falls_back(self):
        self.assertEqual(self.generate(SimpleNamespace(text=None), SimpleNamespace(text="Answer")), "Answer")

    def test_error_raised_when_every_model_fails(self):
        with self.assertRaises(GeminiUnavailable):
            self.generate(RuntimeError("429"), RuntimeError("429"), RuntimeError("429"))
        self.assertEqual(self.models, ["first", "second", "third"])

    def test_models_are_tried_in_order(self):
        self.assertEqual(self.generate(RuntimeError("429"), RuntimeError("429"), SimpleNamespace(text="Answer")), "Answer")
        self.assertEqual(self.models, ["first", "second", "third"])

    def test_no_new_model_starts_after_the_deadline(self):
        with patch("apps.documents.clients.time.monotonic", side_effect=[0, 0, 21]):
            with self.assertRaises(GeminiUnavailable):
                self.generate(RuntimeError("timed out"), SimpleNamespace(text="Answer"))
        self.assertEqual(self.models, ["first"])
