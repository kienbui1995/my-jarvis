"""Embedding generation — shared utility for vector operations."""
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from core.config import settings

_embeddings = None


def get_embeddings() -> GoogleGenerativeAIEmbeddings:
    """Get or create embedding model (direct Google API — embeddings don't route via LiteLLM)."""
    global _embeddings
    if _embeddings is None:
        _embeddings = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001",
            google_api_key=settings.GOOGLE_API_KEY,
            task_type="SEMANTIC_SIMILARITY",
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
