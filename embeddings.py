import os
import time

import httpx
from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings

from config import (
    EMBEDDING_MODEL,
    EMBEDDING_PROVIDER,
    OLLAMA_BASE_URL,
    OLLAMA_EMBED_MODEL,
    require_env,
)

BATCH_SIZE = 32
MAX_ATTEMPTS = 5


class OllamaEmbeddings(Embeddings):
    """Embeddings locales servidos por Ollama. El mismo modelo indexa y consulta."""

    def __init__(self, model: str, base_url: str):
        self.model = model
        self.base_url = base_url.rstrip("/")

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for start in range(0, len(texts), BATCH_SIZE):
            vectors.extend(self._embed_batch(texts[start : start + BATCH_SIZE]))
        return vectors

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]

    def _embed_batch(self, texts: list[str]) -> list[list[float]]:
        last_error = ""
        for attempt in range(1, MAX_ATTEMPTS + 1):
            response = httpx.post(
                f"{self.base_url}/api/embed",
                json={"model": self.model, "input": texts},
                timeout=300,
            )
            if response.status_code == 404 and "not found" in response.text.lower():
                raise RuntimeError(
                    f"Ollama no tiene el modelo '{self.model}'. "
                    f"Descargalo con: ollama pull {self.model}"
                )
            if response.status_code == 429 or response.status_code >= 500:
                last_error = response.text[:300]
                time.sleep(2 * attempt)
                continue
            response.raise_for_status()
            payload = response.json()
            vectors = payload.get("embeddings")
            if not vectors and "embedding" in payload:
                vectors = [payload["embedding"]]
            if not vectors or len(vectors) != len(texts):
                raise RuntimeError("Ollama no devolvió un embedding por texto.")
            return [[float(value) for value in vector] for vector in vectors]
        raise RuntimeError(f"Ollama rechazó el lote de embeddings: {last_error}")


class GeminiEmbeddings(Embeddings):
    """Embeddings de Gemini con dimensión fija, compatible con el índice serverless."""

    def __init__(self, api_key: str, model: str, dimensions: int = 1536):
        self.api_key = api_key
        self.model = model
        self.dimensions = dimensions

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._embed_many(texts, "RETRIEVAL_DOCUMENT")

    def embed_query(self, text: str) -> list[float]:
        return self._embed_many([text], "RETRIEVAL_QUERY")[0]

    def _embed_many(self, texts: list[str], task_type: str) -> list[list[float]]:
        vectors: list[list[float]] = []
        for start in range(0, len(texts), BATCH_SIZE):
            batch = texts[start : start + BATCH_SIZE]
            vectors.extend(self._embed_batch(batch, task_type))
        return vectors

    def _embed_batch(self, texts: list[str], task_type: str) -> list[list[float]]:
        url = "https://generativelanguage.googleapis.com/v1beta/models/"
        url += f"{self.model}:batchEmbedContents"
        requests = [
            {
                "model": f"models/{self.model}",
                "content": {"parts": [{"text": text}]},
                "taskType": task_type,
                "outputDimensionality": self.dimensions,
            }
            for text in texts
        ]
        last_error = ""
        for attempt in range(1, MAX_ATTEMPTS + 1):
            response = httpx.post(
                url,
                params={"key": self.api_key},
                json={"requests": requests},
                timeout=120,
            )
            if response.status_code == 429 or response.status_code >= 500:
                last_error = response.text[:300]
                time.sleep(2 * attempt)
                continue
            response.raise_for_status()
            embeddings = response.json()["embeddings"]
            vectors = [item["values"] for item in embeddings]
            for vector in vectors:
                if len(vector) != self.dimensions:
                    raise RuntimeError(
                        f"El embedding llegó con {len(vector)} dims, "
                        f"se esperaban {self.dimensions}."
                    )
            return vectors
        raise RuntimeError(f"Gemini rechazó el lote de embeddings: {last_error}")


def get_embeddings() -> Embeddings:
    if EMBEDDING_PROVIDER == "ollama":
        return OllamaEmbeddings(model=OLLAMA_EMBED_MODEL, base_url=OLLAMA_BASE_URL)
    if EMBEDDING_PROVIDER == "openai":
        require_env("OPENAI_API_KEY")
        return OpenAIEmbeddings(model=EMBEDDING_MODEL, dimensions=1536)
    if EMBEDDING_PROVIDER == "google":
        require_env("GOOGLE_API_KEY")
        return GeminiEmbeddings(
            api_key=os.environ["GOOGLE_API_KEY"],
            model=EMBEDDING_MODEL,
            dimensions=1536,
        )
    raise RuntimeError(
        "EMBEDDING_PROVIDER debe ser 'ollama', 'google' o 'openai'. "
        f"Valor actual: {EMBEDDING_PROVIDER!r}."
    )
