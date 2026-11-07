import io
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from pypdf import PdfWriter
from rest_framework.test import APIClient

from apps.conversations.models import Conversation
from apps.documents.constants import ASK_FULL, ASK_TOO_MANY, MAX_PDF_PAGES, UPLOAD_TOO_MANY
from apps.documents.models import Chunk, Document
from apps.documents.utils import extract_content

SMALL = {
    "ask_user_hour": (2, 3600),
    "ask_user_day": (25, 86400),
    "ask_ip_day": (3, 86400),
    "ask_all_day": (4, 86400),
    "upload_user_hour": (2, 3600),
    "upload_ip_day": (25, 86400),
    "upload_all_day": (200, 86400),
}


@override_settings(GEMINI_API_KEY="test", GEMINI_FALLBACK_MODELS=[])
@patch.dict("apps.documents.limits.AI_LIMITS", SMALL)
class AskLimitTests(TestCase):
    def person(self, email):
        owner = get_user_model().objects.create_user(email=email, password="Str0ng-pass-1")
        document = Document.objects.create(owner=owner, title="Doc", filename="doc.pdf", status="ready")
        Chunk.objects.create(document=document, content="passage", page=1, embedding=[1.0] * 768, chunk_index=0)
        conversation = Conversation.objects.create(owner=owner, document=document)
        api = APIClient()
        api.force_authenticate(owner)
        return api, conversation

    def ask(self, person, ip="203.0.113.1", question="Why?"):
        api, conversation = person
        with patch("apps.documents.clients.genai") as genai:
            models = genai.Client.return_value.models
            models.embed_content.return_value = SimpleNamespace(embeddings=[SimpleNamespace(values=[1.0] * 768)])
            models.generate_content.return_value = SimpleNamespace(text="Because [1]")
            response = api.post(
                f"/api/conversations/{conversation.id}/ask/", {"question": question}, format="json", REMOTE_ADDR=ip
            )
            response.gemini_calls = models.generate_content.call_count
        return response

    def test_one_person_gets_a_share_of_questions(self):
        sara = self.person("sara@example.com")
        self.assertEqual([self.ask(sara).status_code for _ in range(2)], [200, 200])
        refused = self.ask(sara)
        self.assertEqual(refused.status_code, 429)
        self.assertEqual(refused.json()["detail"], ASK_TOO_MANY)
        self.assertEqual(refused.gemini_calls, 0)
        self.assertEqual(sara[1].messages.count(), 4)

    def test_new_demo_accounts_from_one_address_share_its_limit(self):
        first, second, third = (self.person(f"demo-{n}@example.com") for n in range(3))
        self.assertEqual([self.ask(first).status_code, self.ask(first).status_code], [200, 200])
        self.assertEqual(self.ask(second).status_code, 200)
        refused = self.ask(third)
        self.assertEqual(refused.status_code, 429)
        self.assertEqual(refused.json()["detail"], ASK_TOO_MANY)
        self.assertEqual(self.ask(third, ip="198.51.100.7").status_code, 200)

    def test_the_site_stops_before_the_daily_quota_runs_out(self):
        for number in range(4):
            self.assertEqual(self.ask(self.person(f"p{number}@example.com"), ip=f"192.0.2.{number}").status_code, 200)
        full = self.ask(self.person("late@example.com"), ip="192.0.2.99")
        self.assertEqual(full.status_code, 429)
        self.assertEqual(full.json()["detail"], ASK_FULL)

    def test_someone_turned_away_doesnt_use_the_sites_share(self):
        sara = self.person("sara@example.com")
        for _ in range(6):
            self.ask(sara)
        self.assertEqual(self.ask(self.person("omar@example.com"), ip="198.51.100.7").status_code, 200)

    def test_an_invalid_question_isnt_counted(self):
        sara = self.person("sara@example.com")
        for _ in range(3):
            self.assertEqual(self.ask(sara, question="").status_code, 400)
        self.assertEqual(self.ask(sara).status_code, 200)

    def test_asking_a_document_directly_is_limited_too(self):
        api, conversation = self.person("sara@example.com")
        with patch("apps.documents.clients.genai") as genai:
            models = genai.Client.return_value.models
            models.embed_content.return_value = SimpleNamespace(embeddings=[SimpleNamespace(values=[1.0] * 768)])
            models.generate_content.return_value = SimpleNamespace(text="Because [1]")
            codes = [
                api.post(f"/api/documents/{conversation.document_id}/ask/", {"question": "Why?"}, format="json").status_code
                for _ in range(3)
            ]
        self.assertEqual(codes, [200, 200, 429])


@override_settings(GEMINI_API_KEY="test")
@patch.dict("apps.documents.limits.AI_LIMITS", SMALL)
class UploadLimitTests(TestCase):
    def test_one_person_gets_a_share_of_uploads(self):
        owner = get_user_model().objects.create_user(email="sara@example.com", password="Str0ng-pass-1")
        api = APIClient()
        api.force_authenticate(owner)
        codes = []
        with patch("apps.documents.handlers.GeminiClient") as client:
            client.return_value.embed_documents.side_effect = lambda pieces: [[0.0] * 768 for _ in pieces]
            for number in range(3):
                upload = SimpleUploadedFile(f"notes-{number}.txt", b"Some notes to read.", content_type="text/plain")
                response = api.post("/api/documents/", {"file": upload}, format="multipart")
                codes.append(response.status_code)
        self.assertEqual(codes, [201, 201, 429])
        self.assertEqual(response.json()["detail"], UPLOAD_TOO_MANY)
        self.assertEqual(Document.objects.filter(owner=owner).count(), 2)


class PdfPageLimitTests(TestCase):
    def pdf(self, pages):
        writer = PdfWriter()
        for _ in range(pages):
            writer.add_blank_page(width=200, height=200)
        data = io.BytesIO()
        writer.write(data)
        return SimpleUploadedFile("long.pdf", data.getvalue(), content_type="application/pdf")

    def test_very_long_pdfs_are_refused_before_reading(self):
        with self.assertRaisesMessage(ValueError, f"more than {MAX_PDF_PAGES} pages"):
            extract_content(self.pdf(MAX_PDF_PAGES + 1))

    def test_a_pdf_at_the_limit_is_read(self):
        self.assertEqual(extract_content(self.pdf(MAX_PDF_PAGES)).page_count, MAX_PDF_PAGES)
