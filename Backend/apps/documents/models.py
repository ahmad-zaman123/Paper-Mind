from django.db import models

from apps.core.models import BaseModel
from apps.documents.choices import DocumentStatus
from apps.documents.constants import TEXT_PREVIEW_CHARS


class Document(BaseModel):
    title = models.CharField(max_length=255)
    filename = models.CharField(max_length=255)
    status = models.CharField(
        max_length=31,
        choices=DocumentStatus.choices,
        default=DocumentStatus.PROCESSING,
    )
    page_count = models.PositiveIntegerField(default=0)
    char_count = models.PositiveIntegerField(default=0)
    extracted_text = models.TextField(blank=True)
    error_message = models.CharField(max_length=255, blank=True)

    owner = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="documents",
    )

    class Meta:
        verbose_name = "document"
        verbose_name_plural = "documents"
        db_table = "documents"
        ordering = ("-created",)

    @property
    def text_preview(self):
        return self.extracted_text[:TEXT_PREVIEW_CHARS]

    def __str__(self):
        return self.title
