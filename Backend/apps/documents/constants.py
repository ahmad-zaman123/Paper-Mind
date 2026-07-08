MAX_UPLOAD_SIZE_MB = 10
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024

ALLOWED_EXTENSIONS = ("pdf", "docx", "txt", "md")

TEXT_PREVIEW_CHARS = 2000

# Upper bound on chunks per document to keep ingestion time and cost bounded.
MAX_CHUNKS_PER_DOCUMENT = 400
