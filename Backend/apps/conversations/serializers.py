from rest_framework import serializers

from apps.conversations.models import Conversation, Message


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ("id", "role", "content", "citations", "created")
        read_only_fields = fields


class ConversationSerializer(serializers.ModelSerializer):
    document_title = serializers.CharField(source="document.title", read_only=True)
    message_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Conversation
        fields = ("id", "title", "document", "document_title", "message_count", "created")
        read_only_fields = ("id", "title", "document_title", "message_count", "created")


class ConversationDetailSerializer(ConversationSerializer):
    messages = MessageSerializer(many=True, read_only=True)

    class Meta(ConversationSerializer.Meta):
        fields = ConversationSerializer.Meta.fields + ("messages",)


class ConversationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conversation
        fields = ("id", "title", "document")
        read_only_fields = ("id",)

    def validate_document(self, value):
        request = self.context["request"]
        if value.owner_id != request.user.id:
            raise serializers.ValidationError("Document not found.")
        return value

    def create(self, validated_data):
        return Conversation.objects.create(owner=self.context["request"].user, **validated_data)

    def to_representation(self, instance):
        return ConversationSerializer(instance, context=self.context).data
