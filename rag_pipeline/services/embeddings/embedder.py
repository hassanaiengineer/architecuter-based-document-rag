from __future__ import annotations

import numpy as np
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from construction_rag.core.errors import ConfigError


def _l2_normalize(matrix: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return matrix / norms


class Embedder:
    """
    OpenAI embeddings client.

    Uses cosine similarity via FAISS IP index by L2-normalizing vectors.
    """

    def __init__(self, *, api_key: str, model: str):
        if not api_key:
            raise ConfigError("OPENAI_API_KEY is required to generate embeddings.")
        if not model:
            raise ConfigError("EMBEDDING_MODEL must be set.")
        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model

    @property
    def model(self) -> str:
        return self._model

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, min=0.5, max=4))
    async def embed_texts(self, texts: list[str]) -> np.ndarray:
        resp = await self._client.embeddings.create(model=self._model, input=texts)
        vectors = [d.embedding for d in resp.data]
        arr = np.asarray(vectors, dtype=np.float32)
        return _l2_normalize(arr)

    async def embed_query(self, text: str) -> np.ndarray:
        arr = await self.embed_texts([text])
        return arr[0]

