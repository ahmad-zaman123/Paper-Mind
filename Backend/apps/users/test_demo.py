from datetime import timedelta
from unittest import mock

from django.core import mail
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from apps.conversations.models import Conversation, Message
from apps.documents.models import Chunk, Document
from apps.users.constants import (
    DEMO_EMAIL,
    DEMO_FULL,
    DEMO_LIMITS,
    DEMO_PASSWORD_LOCKED,
    DEMO_TEMPLATE_LOCKED,
    DEMO_TOO_MANY,
)
from apps.users.demo import DEMO_DOMAIN, DEMO_LIFETIME, PURGE_BATCH, is_demo_email
from apps.users.models import RateWindow, User
from apps.users.serializers import UserSerializer

DEMO = "/api/auth/demo/"


def vector(first):
    return [first] + [0.0] * 767


class DemoTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.template = User.objects.create_user(email=DEMO_EMAIL, password="demo1234")
        self.doc = Document.objects.create(
            owner=self.template,
            title="About Paper-Mind",
            filename="about.pdf",
            status="ready",
            page_count=2,
            char_count=40,
            extracted_text="Paper-Mind answers questions about your documents.",
        )
        for i in range(3):
            Chunk.objects.create(
                document=self.doc, content=f"passage {i}", page=i + 1, chunk_index=i, embedding=vector(i + 1.0)
            )
        Document.objects.create(owner=self.template, title="Broken", filename="x.pdf", status="failed")
        chat = Conversation.objects.create(owner=self.template, document=self.doc, title="What is it?")
        for i, role in enumerate(["user", "assistant", "user", "assistant"]):
            Message.objects.create(
                conversation=chat,
                role=role,
                content=f"message {i}",
                citations=[{"chunk_index": 0, "page": 1, "content": "passage 0", "score": 0.9}] if role == "assistant" else [],
            )

    def start(self, ip="203.0.113.5"):
        return self.client.post(DEMO, REMOTE_ADDR=ip)

    def auth(self, access):
        return {"HTTP_AUTHORIZATION": f"Bearer {access}"}

    def test_me_says_whether_the_account_is_a_demo(self):
        me = self.client.get("/api/auth/me/", **self.auth(self.start().json()["access"])).json()
        self.assertIs(me["is_demo"], True)
        self.assertIs(UserSerializer(User(email="sara@example.com")).data["is_demo"], False)

    def demo_user(self, response):
        email = self.client.get("/api/auth/me/", **self.auth(response.json()["access"])).json()["email"]
        return User.objects.get(email=email)

    def test_demo_gets_a_copy_of_the_template(self):
        response = self.start()
        self.assertEqual(response.status_code, 201)
        user = self.demo_user(response)
        self.assertTrue(user.email.endswith("@" + DEMO_DOMAIN))
        self.assertFalse(user.has_usable_password())

        docs = Document.objects.filter(owner=user)
        self.assertEqual([d.title for d in docs], ["About Paper-Mind"])  # failed documents are skipped
        copy = docs.get()
        self.assertNotEqual(copy.id, self.doc.id)
        self.assertEqual(copy.extracted_text, self.doc.extracted_text)
        chunks = list(Chunk.objects.filter(document=copy))
        self.assertEqual([c.chunk_index for c in chunks], [0, 1, 2])
        self.assertEqual([c.page for c in chunks], [1, 2, 3])
        self.assertEqual([float(c.embedding[0]) for c in chunks], [1.0, 2.0, 3.0])

        chat = Conversation.objects.get(owner=user)
        self.assertEqual(chat.document_id, copy.id)
        self.assertEqual(list(chat.messages.values_list("content", flat=True)), [f"message {i}" for i in range(4)])
        self.assertEqual(chat.messages.filter(role="assistant").first().citations[0]["page"], 1)

        # The template itself is untouched.
        self.assertEqual(Chunk.objects.filter(document=self.doc).count(), 3)
        self.assertEqual(Message.objects.filter(conversation__owner=self.template).count(), 4)

    def test_starting_a_demo_makes_no_gemini_calls(self):
        with mock.patch("apps.documents.clients.genai") as genai:
            self.assertEqual(self.start().status_code, 201)
        genai.Client.assert_not_called()

    def test_each_visitor_sees_only_their_own_copy(self):
        first = self.start().json()["access"]
        second = self.start().json()["access"]
        mine = self.client.get("/api/documents/", **self.auth(first)).json()
        theirs = self.client.get("/api/documents/", **self.auth(second)).json()
        ids = lambda page: {d["id"] for d in page.get("results", page)}  # noqa: E731
        self.assertEqual(len(ids(mine)), 1)
        self.assertFalse(ids(mine) & ids(theirs))
        self.assertNotIn(str(self.doc.id), ids(mine))

    def test_deleting_in_a_demo_leaves_the_template_alone(self):
        response = self.start()
        copy = Document.objects.get(owner=self.demo_user(response))
        deleted = self.client.delete(f"/api/documents/{copy.id}/", **self.auth(response.json()["access"]))
        self.assertIn(deleted.status_code, (200, 204))
        self.assertTrue(Document.objects.filter(id=self.doc.id).exists())

    def test_demo_works_without_a_template(self):
        self.template.delete()
        response = self.start()
        self.assertEqual(response.status_code, 201)
        self.assertFalse(Document.objects.filter(owner=self.demo_user(response)).exists())

    def test_demo_is_limited_per_address(self):
        for _ in range(DEMO_LIMITS["demo_ip"][0]):
            self.assertEqual(self.start().status_code, 201)
        blocked = self.start()
        self.assertEqual(blocked.status_code, 429)
        self.assertEqual(blocked.json()["detail"], DEMO_TOO_MANY)
        self.assertEqual(self.start(ip="198.51.100.7").status_code, 201)

    def test_demo_has_a_daily_total(self):
        self.start()
        RateWindow.objects.filter(key__startswith="demo_all:").update(count=DEMO_LIMITS["demo_all"][0])
        blocked = self.start(ip="198.51.100.8")
        self.assertEqual(blocked.status_code, 429)
        self.assertEqual(blocked.json()["detail"], DEMO_FULL)

    def test_old_demos_are_removed_when_a_new_one_starts(self):
        old = self.demo_user(self.start())
        User.objects.filter(id=old.id).update(created=timezone.now() - DEMO_LIFETIME - timedelta(minutes=1))
        real = User.objects.create_user(email="real@example.com", password="real-password-1")
        self.start()
        self.assertFalse(User.objects.filter(id=old.id).exists())
        self.assertFalse(Document.objects.filter(owner_id=old.id).exists())
        self.assertTrue(User.objects.filter(id=real.id).exists())
        self.assertTrue(User.objects.filter(id=self.template.id).exists())

    def test_cleanup_is_done_in_batches(self):
        for i in range(PURGE_BATCH + 3):
            User.objects.create(email=f"demo-old{i}@{DEMO_DOMAIN}")
        User.objects.filter(email__endswith="@" + DEMO_DOMAIN).update(
            created=timezone.now() - DEMO_LIFETIME - timedelta(minutes=1)
        )
        self.start()
        self.assertEqual(User.objects.filter(email__endswith="@" + DEMO_DOMAIN).count(), 4)

    def test_demo_cannot_set_a_password(self):
        access = self.start().json()["access"]
        response = self.client.post(
            "/api/auth/password/", {"new_password": "a-new-password-1"}, format="json", **self.auth(access)
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], [DEMO_PASSWORD_LOCKED])

    @override_settings(EMAIL_HOST="smtp.example")
    def test_demo_and_template_get_no_reset_email(self):
        email = self.demo_user(self.start()).email
        for address in (email, DEMO_EMAIL):
            self.client.post("/api/auth/password/forgot/", {"email": address}, format="json")
        self.assertEqual(len(mail.outbox), 0)

    def test_template_cannot_be_signed_into(self):
        response = self.client.post("/api/auth/token/", {"email": DEMO_EMAIL, "password": "demo1234"}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], [DEMO_TEMPLATE_LOCKED])

    def test_demo_emails_are_recognised(self):
        self.assertTrue(is_demo_email(DEMO_EMAIL))
        self.assertTrue(is_demo_email(f"DEMO-abc@{DEMO_DOMAIN.upper()}"))
        self.assertFalse(is_demo_email("someone@example.com"))
        self.assertFalse(is_demo_email(f"someone@not{DEMO_DOMAIN}"))
