import math
import time

from django.conf import settings
from google import genai
from google.genai import types

_MAX_RETRIES = 3
_RETRY_BACKOFF_SECONDS = 2

# Per-request timeout (milliseconds). Without it a stalled connection hangs the
# call forever; with it, a stall raises and is retried.
_REQUEST_TIMEOUT_MS = 30000

# Number of texts sent per embedding request. Batching turns N sequential
# round-trips into ceil(N / batch) requests, which keeps ingestion fast enough
# to run synchronously.
_EMBED_BATCH_SIZE = 100


def _normalize(vector):
    magnitude = math.sqrt(sum(value * value for value in vector))
    if magnitude == 0:
        return vector
    return [value / magnitude for value in vector]


def _strip_model_prefix(name):
    prefix = "models/"
    return name[len(prefix):] if name.startswith(prefix) else name


class GeminiClient:
    """Thin wrapper over the google-genai SDK for embeddings and generation.

    Embeddings are requested at a fixed dimensionality and L2-normalized so that
    cosine and inner-product similarity behave consistently in pgvector.
    """

    def __init__(self):
        if not settings.GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY is not configured.")
        self._client = genai.Client(
            api_key=settings.GEMINI_API_KEY,
            http_options=types.HttpOptions(timeout=_REQUEST_TIMEOUT_MS),
        )
        self._embedding_model = _strip_model_prefix(settings.GEMINI_EMBEDDING_MODEL)
        self._chat_model = _strip_model_prefix(settings.GEMINI_CHAT_MODEL)
        self._dimensions = settings.EMBEDDING_DIMENSIONS

    def _embed_batch(self, texts, task_type):
        config = types.EmbedContentConfig(
            task_type=task_type,
            output_dimensionality=self._dimensions,
        )
        last_error = None
        for attempt in range(_MAX_RETRIES):
            try:
                response = self._client.models.embed_content(
                    model=self._embedding_model,
                    contents=list(texts),
                    config=config,
                )
                return [_normalize(embedding.values) for embedding in response.embeddings]
            except Exception as error:
                last_error = error
                time.sleep(_RETRY_BACKOFF_SECONDS * (attempt + 1))
        raise last_error

    def embed_documents(self, texts):
        texts = list(texts)
        vectors = []
        for start in range(0, len(texts), _EMBED_BATCH_SIZE):
            batch = texts[start:start + _EMBED_BATCH_SIZE]
            vectors.extend(self._embed_batch(batch, "RETRIEVAL_DOCUMENT"))
        return vectors

    def embed_query(self, text):
        return self._embed_batch([text], "RETRIEVAL_QUERY")[0]

    def generate_answer(self, prompt):
        response = self._client.models.generate_content(
            model=self._chat_model,
            contents=prompt,
        )
        return response.text
