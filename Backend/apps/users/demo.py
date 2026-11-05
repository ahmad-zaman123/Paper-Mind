"""Private demo accounts.

Each visitor who clicks "Try the live demo" gets a fresh account holding a copy of the template
account's documents, chunks (with their embeddings) and conversations. Copying the stored vectors
means no Gemini calls are made, so starting a demo never touches the free-tier quota.
"""

import uuid
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from apps.conversations.models import Conversation, Message
from apps.documents.choices import DocumentStatus
from apps.documents.models import Chunk, Document
from apps.users.constants import DEMO_EMAIL
from apps.users.models import User

DEMO_DOMAIN = "demo.paper-mind.app"
DEMO_LIFETIME = timedelta(days=2)
PURGE_BATCH = 50


def is_demo_email(email):
    email = (email or "").lower()
    return email == DEMO_EMAIL or email.endswith("@" + DEMO_DOMAIN)


def is_demo_user(user):
    return is_demo_email(getattr(user, "email", ""))


def purge_expired_demos():
    """Delete a batch of demo accounts older than DEMO_LIFETIME (their data goes with them)."""
    cutoff = timezone.now() - DEMO_LIFETIME
    ids = list(
        User.objects.filter(email__endswith="@" + DEMO_DOMAIN, created__lt=cutoff)
        .order_by("created")
        .values_list("id", flat=True)[:PURGE_BATCH]
    )
    if ids:
        User.objects.filter(id__in=ids).delete()


def copy_template_into(user):
    """Copy the template account's ready documents and their chats to `user`. Returns documents copied."""
    template = User.objects.filter(email__iexact=DEMO_EMAIL).first()
    if template is None:
        return 0
    documents = list(Document.objects.filter(owner=template, status=DocumentStatus.READY))
    copied = {}
    for source in documents:
        copied[source.id] = Document.objects.create(
            owner=user,
            title=source.title,
            filename=source.filename,
            status=source.status,
            page_count=source.page_count,
            char_count=source.char_count,
            extracted_text=source.extracted_text,
        )
    Chunk.objects.bulk_create(
        Chunk(
            document=copied[chunk.document_id],
            content=chunk.content,
            embedding=chunk.embedding,
            chunk_index=chunk.chunk_index,
            page=chunk.page,
        )
        for chunk in Chunk.objects.filter(document_id__in=copied)
    )
    for source in Conversation.objects.filter(owner=template, document_id__in=copied).prefetch_related("messages"):
        conversation = Conversation.objects.create(
            owner=user, document=copied[source.document_id], title=source.title
        )
        messages = Message.objects.bulk_create(
            Message(conversation=conversation, role=m.role, content=m.content, citations=m.citations)
            for m in source.messages.all()
        )
        # `created` is set automatically and drives message order, so space the copies out to
        # keep each question before its answer.
        start = timezone.now()
        for i, message in enumerate(messages):
            Message.objects.filter(id=message.id).update(created=start + timedelta(milliseconds=i))
    return len(copied)


def create_demo_user():
    purge_expired_demos()
    with transaction.atomic():
        user = User(email=f"demo-{uuid.uuid4().hex[:12]}@{DEMO_DOMAIN}", full_name="Demo User")
        user.set_unusable_password()
        user.save()
        copy_template_into(user)
    return user
