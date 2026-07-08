from django.urls import path

from apps.documents.views import (
    DocumentAskAPIView,
    DocumentDetailAPIView,
    DocumentListCreateAPIView,
)

urlpatterns = (
    path("documents/", DocumentListCreateAPIView.as_view(), name="document-list-create"),
    path("documents/<uuid:pk>/", DocumentDetailAPIView.as_view(), name="document-detail"),
    path("documents/<uuid:pk>/ask/", DocumentAskAPIView.as_view(), name="document-ask"),
)
