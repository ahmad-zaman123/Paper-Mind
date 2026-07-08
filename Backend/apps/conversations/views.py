from django.db.models import Count, Prefetch
from rest_framework import generics, status
from rest_framework.response import Response

from apps.conversations.choices import MessageRole
from apps.conversations.constants import HISTORY_WINDOW, TITLE_FROM_QUESTION_CHARS
from apps.conversations.models import Conversation, Message
from apps.conversations.serializers import (
    ConversationCreateSerializer,
    ConversationDetailSerializer,
    ConversationSerializer,
    MessageSerializer,
)
from apps.documents.choices import DocumentStatus
from apps.documents.handlers import answer_question
from apps.documents.serializers import AskSerializer


class ConversationListCreateAPIView(generics.ListCreateAPIView):
    def get_queryset(self, *args, **kwargs):
        return (
            Conversation.objects.filter(owner=self.request.user)
            .select_related("document")
            .annotate(message_count=Count("messages"))
        )

    def get_serializer_class(self, *args, **kwargs):
        if self.request.method == "POST":
            return ConversationCreateSerializer
        return ConversationSerializer


class ConversationDetailAPIView(generics.RetrieveDestroyAPIView):
    serializer_class = ConversationDetailSerializer

    def get_queryset(self, *args, **kwargs):
        return (
            Conversation.objects.filter(owner=self.request.user)
            .select_related("document")
            .annotate(message_count=Count("messages"))
            .prefetch_related(Prefetch("messages", queryset=Message.objects.order_by("created")))
        )


class ConversationAskAPIView(generics.GenericAPIView):
    serializer_class = AskSerializer

    def get_queryset(self, *args, **kwargs):
        return Conversation.objects.filter(owner=self.request.user).select_related("document")

    def post(self, request, *args, **kwargs):
        conversation = self.get_object()
        document = conversation.document
        if document.status != DocumentStatus.READY:
            return Response(
                {"detail": "Document is not ready for questions (status: " + document.status + ")."},
                status=status.HTTP_409_CONFLICT,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        question = serializer.validated_data["question"]

        recent = list(conversation.messages.order_by("-created")[:HISTORY_WINDOW])[::-1]
        history = [{"role": message.role, "content": message.content} for message in recent]

        Message.objects.create(
            conversation=conversation,
            role=MessageRole.USER,
            content=question,
        )

        result = answer_question(document=document, question=question, history=history)

        assistant_message = Message.objects.create(
            conversation=conversation,
            role=MessageRole.ASSISTANT,
            content=result["answer"],
            citations=result["citations"],
        )

        if not conversation.title:
            conversation.title = question[:TITLE_FROM_QUESTION_CHARS]
            conversation.save(update_fields=("title", "modified"))

        return Response(MessageSerializer(assistant_message).data, status=status.HTTP_200_OK)
