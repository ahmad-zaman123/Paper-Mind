from django.contrib import admin

from apps.documents.models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "owner", "status", "page_count", "char_count", "created")
    list_filter = ("status",)
    search_fields = ("title", "filename", "owner__email")
    readonly_fields = ("extracted_text",)
