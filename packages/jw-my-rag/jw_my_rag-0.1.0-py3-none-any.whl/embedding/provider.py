"""Embedding provider abstraction for OpenAI backend."""

from typing import Optional

from shared.config import EmbeddingConfig


class EmbeddingProviderFactory:
    """Factory for producing embedding clients based on configuration."""

    @staticmethod
    def create(config: EmbeddingConfig):
        """
        Create embedding client based on config.

        Args:
            config: EmbeddingConfig with provider settings

        Returns:
            OpenAIEmbeddings client

        Raises:
            ValueError: If embedding_provider is not 'openai'
        """
        if config.embedding_provider != "openai":
            raise ValueError(
                f"Unsupported embedding provider: {config.embedding_provider}. "
                "Only 'openai' is supported."
            )

        from langchain_openai import OpenAIEmbeddings  # type: ignore

        return OpenAIEmbeddings(
            model=config.embedding_model,
            dimensions=config.embedding_dim,
        )


def validate_embedding_dimension(
    embeddings,
    expected: int,
    *,
    provider: Optional[str] = None,
    model: Optional[str] = None,
) -> None:
    """
    Validate that embedding dimensions match expected configuration.

    Args:
        embeddings: Embedding client
        expected: Expected dimension
        provider: Provider name for error messages
        model: Model name for error messages
    """
    label_parts = []
    if provider:
        label_parts.append(provider)
    if model:
        label_parts.append(model)
    label = ":".join(label_parts) if label_parts else "embedding-provider"
    try:
        vectors = embeddings.embed_documents(["__dim_check__"])
        if not vectors or not isinstance(vectors, list) or not isinstance(vectors[0], (list, tuple)):
            print("[warn] Unable to validate embedding dimension (unexpected response)")
            return
        actual = len(vectors[0])
        if actual != expected:
            print(
                f"[WARN] EMBEDDING_DIM mismatch for {label}: expected {expected}, received {actual}"
            )
    except Exception as exc:
        print(f"[warn] Skipping dimension validation for {label}: {exc}")


__all__ = ["EmbeddingProviderFactory", "validate_embedding_dimension"]
