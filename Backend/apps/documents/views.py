from django.db.models import Count
from rest_framework import generics
from rest_framework.parsers import FormParser, MultiPartParser

from apps.documents.models import Document
from apps.documents.serializers import (
    DocumentDetailSerializer,
    DocumentSerializer,
    DocumentUploadSerializer,
)


class DocumentListCreateAPIView(generics.ListCreateAPIView):
    parser_classes = (MultiPartParser, FormParser)

    def get_queryset(self, *args, **kwargs):
        return (
            Document.objects.filter(owner=self.request.user)
            .annotate(chunk_count=Count("chunks"))
        )

    def get_serializer_class(self, *args, **kwargs):
        if self.request.method == "POST":
            return DocumentUploadSerializer
        return DocumentSerializer


class DocumentDetailAPIView(generics.RetrieveDestroyAPIView):
    serializer_class = DocumentDetailSerializer

    def get_queryset(self, *args, **kwargs):
        return (
            Document.objects.filter(owner=self.request.user)
            .annotate(chunk_count=Count("chunks"))
        )
