from django.db import models

from apps.conversations.choices import MessageRole
from apps.core.models import BaseModel


class Conversation(BaseModel):
    title = models.CharField(max_length=255, blank=True)

    owner = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="conversations",
    )
    document = models.ForeignKey(
        "documents.Document",
        on_delete=models.CASCADE,
        related_name="conversations",
    )

    class Meta:
        verbose_name = "conversation"
        verbose_name_plural = "conversations"
        db_table = "conversations"
        ordering = ("-created",)

    def __str__(self):
        return self.title or ("Conversation " + str(self.id))


class Message(BaseModel):
    role = models.CharField(max_length=15, choices=MessageRole.choices)
    content = models.TextField()
    citations = models.JSONField(default=list, blank=True)

    conversation = models.ForeignKey(
        "conversations.Conversation",
        on_delete=models.CASCADE,
        related_name="messages",
    )

    class Meta:
        verbose_name = "message"
        verbose_name_plural = "messages"
        db_table = "messages"
        ordering = ("created",)

    def __str__(self):
        return self.role + ": " + self.content[:40]
