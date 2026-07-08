from django.db.models import Count
from rest_framework import generics, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from apps.documents.choices import DocumentStatus
from apps.documents.handlers import answer_question
from apps.documents.models import Document
from apps.documents.serializers import (
    AnswerSerializer,
    AskSerializer,
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


class DocumentAskAPIView(generics.GenericAPIView):
    serializer_class = AskSerializer

    def get_queryset(self, *args, **kwargs):
        return Document.objects.filter(owner=self.request.user)

    def post(self, request, *args, **kwargs):
        document = self.get_object()
        if document.status != DocumentStatus.READY:
            return Response(
                {"detail": "Document is not ready for questions (status: " + document.status + ")."},
                status=status.HTTP_409_CONFLICT,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = answer_question(
            document=document,
            question=serializer.validated_data["question"],
        )
        return Response(AnswerSerializer(result).data, status=status.HTTP_200_OK)
