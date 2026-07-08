from django.contrib import admin

from apps.conversations.models import Conversation, Message


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ("role", "content", "citations", "created")


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("__str__", "owner", "document", "created")
    search_fields = ("title", "owner__email", "document__title")
    inlines = (MessageInline,)
