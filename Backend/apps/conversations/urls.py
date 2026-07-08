from django.urls import path

from apps.conversations.views import (
    ConversationAskAPIView,
    ConversationDetailAPIView,
    ConversationListCreateAPIView,
)

urlpatterns = (
    path("conversations/", ConversationListCreateAPIView.as_view(), name="conversation-list-create"),
    path("conversations/<uuid:pk>/", ConversationDetailAPIView.as_view(), name="conversation-detail"),
    path("conversations/<uuid:pk>/ask/", ConversationAskAPIView.as_view(), name="conversation-ask"),
)
