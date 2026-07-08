import uuid

from django.db import models


class BaseModel(models.Model):
    """Abstract base with a UUID primary key and created/modified timestamps."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ("-created",)
