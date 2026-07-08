import math
import time

import google.generativeai as genai
from django.conf import settings

_MAX_RETRIES = 3
_RETRY_BACKOFF_SECONDS = 2


def _normalize(vector):
    magnitude = math.sqrt(sum(value * value for value in vector))
    if magnitude == 0:
        return vector
    return [value / magnitude for value in vector]


class GeminiClient:
    """Thin wrapper over the Gemini API for embeddings and answer generation.

    Embeddings are requested at a fixed dimensionality and L2-normalized so that
    cosine and inner-product similarity behave consistently in pgvector.
    """

    def __init__(self):
        if not settings.GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY is not configured.")
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self._embedding_model = settings.GEMINI_EMBEDDING_MODEL
        self._chat_model = settings.GEMINI_CHAT_MODEL
        self._dimensions = settings.EMBEDDING_DIMENSIONS

    def _embed_one(self, text, task_type):
        last_error = None
        for attempt in range(_MAX_RETRIES):
            try:
                response = genai.embed_content(
                    model=self._embedding_model,
                    content=text,
                    task_type=task_type,
                    output_dimensionality=self._dimensions,
                )
                return _normalize(response["embedding"])
            except Exception as error:
                last_error = error
                time.sleep(_RETRY_BACKOFF_SECONDS * (attempt + 1))
        raise last_error

    def embed_documents(self, texts):
        return [self._embed_one(text, "retrieval_document") for text in texts]

    def embed_query(self, text):
        return self._embed_one(text, "retrieval_query")

    def generate_answer(self, prompt):
        model = genai.GenerativeModel(self._chat_model)
        response = model.generate_content(prompt)
        return response.text
