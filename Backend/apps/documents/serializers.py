from rest_framework import serializers

from apps.documents.constants import ALLOWED_EXTENSIONS, MAX_UPLOAD_SIZE_BYTES, MAX_UPLOAD_SIZE_MB
from apps.documents.handlers import create_document
from apps.documents.models import Document


class DocumentSerializer(serializers.ModelSerializer):
    chunk_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Document
        fields = (
            "id",
            "title",
            "filename",
            "status",
            "page_count",
            "char_count",
            "chunk_count",
            "error_message",
            "created",
        )
        read_only_fields = fields


class DocumentDetailSerializer(DocumentSerializer):
    text_preview = serializers.ReadOnlyField()

    class Meta(DocumentSerializer.Meta):
        fields = DocumentSerializer.Meta.fields + ("text_preview",)
        read_only_fields = fields


class DocumentUploadSerializer(serializers.Serializer):
    file = serializers.FileField(write_only=True)
    title = serializers.CharField(required=False, allow_blank=True, max_length=255)

    def validate_file(self, value):
        extension = value.name.rsplit(".", 1)[-1].lower() if "." in value.name else ""
        if extension not in ALLOWED_EXTENSIONS:
            allowed = ", ".join(ALLOWED_EXTENSIONS)
            raise serializers.ValidationError("Unsupported file type. Allowed: " + allowed + ".")
        if value.size > MAX_UPLOAD_SIZE_BYTES:
            raise serializers.ValidationError("File too large (max " + str(MAX_UPLOAD_SIZE_MB) + " MB).")
        return value

    def create(self, validated_data):
        uploaded_file = validated_data["file"]
        title = validated_data.get("title") or uploaded_file.name
        return create_document(
            owner=self.context["request"].user,
            uploaded_file=uploaded_file,
            title=title,
        )

    def to_representation(self, instance):
        return DocumentSerializer(instance, context=self.context).data


class AskSerializer(serializers.Serializer):
    question = serializers.CharField(min_length=3, max_length=1000, trim_whitespace=True)


class CitationSerializer(serializers.Serializer):
    chunk_index = serializers.IntegerField()
    page = serializers.IntegerField()
    content = serializers.CharField()
    score = serializers.FloatField()


class AnswerSerializer(serializers.Serializer):
    answer = serializers.CharField()
    citations = CitationSerializer(many=True)
