"""Embedding generation — shared utility for vector operations via LiteLLM Proxy."""
from langchain_openai import OpenAIEmbeddings

from core.config import settings

_embeddings = None


def get_embeddings() -> OpenAIEmbeddings:
    """Get or create embedding model routed through LiteLLM Proxy."""
    global _embeddings
    if _embeddings is None:
        _embeddings = OpenAIEmbeddings(
            model="gemini/text-embedding-004",
            openai_api_key=settings.LITELLM_API_KEY,
            openai_api_base=settings.LITELLM_BASE_URL,
        )
    return _embeddings


async def embed_text(text: str) -> list[float]:
    """Generate embedding vector for a single text."""
    model = get_embeddings()
    return await model.aembed_query(text)


async def embed_texts(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for multiple texts."""
    model = get_embeddings()
    return await model.aembed_documents(texts)
