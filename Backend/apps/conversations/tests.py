from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.conversations.models import Conversation
from apps.documents.models import Chunk, Document


@override_settings(GEMINI_API_KEY="test", GEMINI_FALLBACK_MODELS=["models/backup"])
class ConversationAskTests(TestCase):
    def setUp(self):
        owner = get_user_model().objects.create_user(email="ask@example.com", password="Str0ng-pass-1")
        document = Document.objects.create(owner=owner, title="Doc", filename="doc.pdf", status="ready")
        Chunk.objects.create(document=document, content="passage", page=1, embedding=[1.0] * 768, chunk_index=0)
        self.conversation = Conversation.objects.create(owner=owner, document=document)
        self.api = APIClient()
        self.api.force_authenticate(owner)

    def ask(self, *replies):
        with patch("apps.documents.clients.genai") as genai:
            models = genai.Client.return_value.models
            models.embed_content.return_value = SimpleNamespace(embeddings=[SimpleNamespace(values=[1.0] * 768)])
            models.generate_content.side_effect = replies
            return self.api.post(f"/api/conversations/{self.conversation.id}/ask/", {"question": "Why?"}, format="json")

    def test_answer_saves_question_and_answer(self):
        response = self.ask(SimpleNamespace(text="Because [1]"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["citations"][0]["page"], 1)
        roles = list(self.conversation.messages.values_list("role", flat=True))
        self.assertEqual(roles, ["user", "assistant"])
        self.conversation.refresh_from_db()
        self.assertEqual(self.conversation.title, "Why?")

    def test_answer_from_fallback_model(self):
        response = self.ask(RuntimeError("429"), SimpleNamespace(text="Because [1]"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["content"], "Because [1]")

    def test_failure_gives_clear_error_and_saves_nothing(self):
        response = self.ask(RuntimeError("429"), RuntimeError("429"))
        self.assertEqual(response.status_code, 503)
        self.assertIn("try again", response.json()["detail"])
        self.assertFalse(self.conversation.messages.exists())
        self.conversation.refresh_from_db()
        self.assertEqual(self.conversation.title, "")
