from django.urls import path

from apps.documents.views import DocumentDetailAPIView, DocumentListCreateAPIView

urlpatterns = (
    path("documents/", DocumentListCreateAPIView.as_view(), name="document-list-create"),
    path("documents/<uuid:pk>/", DocumentDetailAPIView.as_view(), name="document-detail"),
)
