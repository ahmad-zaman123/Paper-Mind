MAX_UPLOAD_SIZE_MB = 10
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024

ALLOWED_EXTENSIONS = ("pdf", "docx", "txt", "md")

TEXT_PREVIEW_CHARS = 2000

# Upper bound on chunks per document to keep ingestion time and cost bounded.
MAX_CHUNKS_PER_DOCUMENT = 400

# PDFs longer than this are refused before any text is read, so a crafted file can't keep a request busy.
MAX_PDF_PAGES = 300

# Gemini is on a small daily quota shared by every visitor, so each person, each address and the whole site
# get a share: (limit, window in seconds). Starting another demo doesn't reset the per-address limits.
AI_LIMITS = {
    "ask_user_hour": (10, 3600),
    "ask_user_day": (25, 86400),
    "ask_ip_day": (40, 86400),
    "ask_all_day": (60, 86400),
    "upload_user_hour": (10, 3600),
    "upload_ip_day": (25, 86400),
    "upload_all_day": (200, 86400),
}
ASK_TOO_MANY = "You've asked a lot of questions for now. Please try again later."
ASK_FULL = "Paper-Mind has answered as many questions as it can today. Please try again tomorrow."
UPLOAD_TOO_MANY = "You've uploaded a lot of documents for now. Please try again later."
UPLOAD_FULL = "Paper-Mind has read as many documents as it can today. Please try again tomorrow."
