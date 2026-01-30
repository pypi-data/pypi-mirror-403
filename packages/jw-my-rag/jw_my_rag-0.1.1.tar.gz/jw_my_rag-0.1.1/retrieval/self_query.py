"""Self-query retrieval using LangChain SelfQueryRetriever.

Automatically extracts metadata filters from natural language queries.

Rules:
- PKG-RET-001: Search pipeline orchestration (MUST)
- DEP-RET-ALLOW-001~004: MAY import domain, storage, embedding, shared
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any

# LangChain 1.x imports (using langchain_classic for chains/retrievers)
from langchain_classic.chains.query_constructor.base import AttributeInfo
from langchain_classic.retrievers.self_query.base import SelfQueryRetriever
from langchain_core.documents import Document
from langchain_postgres import PGVector

from shared.config import EmbeddingConfig


# Metadata schema definition for LangChain SelfQueryRetriever
METADATA_FIELD_INFO = [
    AttributeInfo(
        name="view",
        description="Content type: 'text' for explanatory documentation, 'code' for code snippets and examples",
        type="string",
    ),
    AttributeInfo(
        name="lang",
        description="Programming language of code content: 'python', 'javascript', 'java', 'typescript', 'go', etc. Only applicable when view is 'code'",
        type="string",
    ),
]

DOCUMENT_CONTENT_DESCRIPTION = """
Technical documentation and code examples from OCR-processed PDFs.
Contains explanatory text about programming concepts and code snippets in various languages.
"""


@dataclass
class ExtractedQuery:
    """LLM이 추출한 쿼리 정보.

    Attributes:
        rewritten_query: LLM이 재작성한 쿼리 (없으면 원본 사용)
        filters: 추출된 메타데이터 필터
    """
    rewritten_query: Optional[str]
    filters: Optional[Dict[str, Any]]


@dataclass
class SelfQueryResult:
    """Result from self-query retrieval.

    Attributes:
        content: Document content
        metadata: Document metadata including view, lang, parent_id
        score: Relevance score (cosine similarity)
        rewritten_query: LLM이 재작성한 검색 쿼리 (디버깅/투명성용)
    """
    content: str
    metadata: dict
    score: Optional[float] = None
    rewritten_query: Optional[str] = None


class SelfQueryRetrieverWrapper:
    """LangChain SelfQueryRetriever integration for automatic metadata filtering.
    
    Hybrid approach:
    1. Use SelfQueryRetriever to extract metadata filters from natural language
    2. Use similarity_search_with_score for actual search with real scores
    
    Example:
        >>> wrapper = SelfQueryRetrieverWrapper(vectorstore, llm)
        >>> results = wrapper.retrieve("Python 데코레이터 코드 예제")
        # Automatically applies: view="code", lang="python"
        # Returns actual similarity scores
    """
    
    def __init__(
        self,
        vectorstore: PGVector,
        llm,
        *,
        enable_limit: bool = True,
        verbose: bool = False,
    ):
        """Initialize SelfQueryRetriever wrapper.
        
        Args:
            vectorstore: LangChain PGVector instance
            llm: LangChain-compatible LLM (e.g., ChatGoogleGenerativeAI)
            enable_limit: Allow LLM to specify result limit
            verbose: Print debug information
        """
        self.vectorstore = vectorstore
        self.llm = llm
        self.verbose = verbose
        
        self.retriever = SelfQueryRetriever.from_llm(
            llm=llm,
            vectorstore=vectorstore,
            document_contents=DOCUMENT_CONTENT_DESCRIPTION.strip(),
            metadata_field_info=METADATA_FIELD_INFO,
            enable_limit=enable_limit,
            verbose=verbose,
        )
    
    def _extract_query_and_filters(self, query: str) -> ExtractedQuery:
        """Extract rewritten query and metadata filters using SelfQueryRetriever's query_constructor.

        LangChain의 StructuredQuery에서 query(LLM이 재작성한 쿼리)와 filter를 모두 추출.

        Args:
            query: Natural language query

        Returns:
            ExtractedQuery with rewritten_query and filters
        """
        try:
            # Use the query_constructor to get structured query
            structured_query = self.retriever.query_constructor.invoke({"query": query})

            if self.verbose:
                print(f"[self_query] Structured query: {structured_query}")

            # Extract rewritten query (LLM이 최적화한 검색어)
            rewritten_query = None
            if structured_query and hasattr(structured_query, "query"):
                rewritten_query = structured_query.query
                if rewritten_query and rewritten_query.strip():
                    rewritten_query = rewritten_query.strip()
                else:
                    rewritten_query = None

            # Extract filter from structured query
            filters = None
            if (
                structured_query
                and hasattr(structured_query, "filter")
                and structured_query.filter
            ):
                filters = self._convert_filter_to_dict(structured_query.filter)

            return ExtractedQuery(rewritten_query=rewritten_query, filters=filters)

        except Exception as e:
            if self.verbose:
                print(f"[self_query] Query/filter extraction failed: {e}")
            return ExtractedQuery(rewritten_query=None, filters=None)
    
    def _convert_filter_to_dict(self, filter_obj) -> Dict[str, Any]:
        """Convert LangChain filter object to dictionary for PGVector.
        
        Args:
            filter_obj: LangChain filter object (Comparison, Operation, etc.)
            
        Returns:
            Dictionary suitable for PGVector filtering
        """
        # Handle different filter types from langchain_core.structured_query
        filter_dict = {}
        
        try:
            # Simple Comparison (e.g., view == "code")
            if hasattr(filter_obj, 'attribute') and hasattr(filter_obj, 'value'):
                filter_dict[filter_obj.attribute] = filter_obj.value
                return filter_dict
            
            # Operation with multiple comparisons (AND, OR)
            if hasattr(filter_obj, 'arguments'):
                for arg in filter_obj.arguments:
                    if hasattr(arg, 'attribute') and hasattr(arg, 'value'):
                        filter_dict[arg.attribute] = arg.value
                return filter_dict
                
        except Exception as e:
            if self.verbose:
                print(f"[self_query] Filter conversion error: {e}")
        
        return filter_dict
    
    def retrieve(
        self,
        query: str,
        k: int = 10,
    ) -> List[SelfQueryResult]:
        """Retrieve documents using hybrid approach.

        1. Extract rewritten query and filters from query using LLM (SelfQueryRetriever)
        2. Search with actual similarity scores using rewritten query (or original if unavailable)

        Args:
            query: Natural language query (may contain filter hints)
            k: Maximum number of results to return

        Returns:
            List of SelfQueryResult with content, metadata, ACTUAL scores, and rewritten_query
        """
        try:
            # Step 1: Extract rewritten query and filters using query constructor
            extracted = self._extract_query_and_filters(query)

            if self.verbose:
                if extracted.rewritten_query:
                    print(f"[self_query] Rewritten query: '{extracted.rewritten_query}' (original: '{query}')")
                if extracted.filters:
                    print(f"[self_query] Extracted filters: {extracted.filters}")

            # Step 2: Determine search query (rewritten or original)
            search_query = extracted.rewritten_query if extracted.rewritten_query else query

            # Step 3: Search with filters and get actual similarity scores
            if extracted.filters:
                # Use filtered search with scores
                docs_with_scores = self.vectorstore.similarity_search_with_score(
                    search_query,
                    k=k,
                    filter=extracted.filters,
                )
            else:
                # No filters extracted, just similarity search
                docs_with_scores = self.vectorstore.similarity_search_with_score(
                    search_query,
                    k=k,
                )

            if self.verbose:
                print(f"[self_query] Retrieved {len(docs_with_scores)} documents with scores")

            # Convert to SelfQueryResult with actual scores and rewritten_query
            return [
                SelfQueryResult(
                    content=doc.page_content,
                    metadata=doc.metadata,
                    score=1.0 - float(score),  # Convert distance to similarity
                    rewritten_query=extracted.rewritten_query,
                )
                for doc, score in docs_with_scores
            ]

        except Exception as e:
            print(f"[self_query] Error: {e}")
            # Fallback to simple similarity search without filters
            return self._fallback_search(query, k)
    
    def _fallback_search(
        self,
        query: str,
        k: int,
    ) -> List[SelfQueryResult]:
        """Fallback to simple similarity search on error.
        
        Args:
            query: Search query
            k: Number of results
            
        Returns:
            List of SelfQueryResult from basic similarity search
        """
        try:
            # Use similarity_search_with_score to get actual scores
            docs_with_scores = self.vectorstore.similarity_search_with_score(query, k=k)
            return [
                SelfQueryResult(
                    content=doc.page_content,
                    metadata=doc.metadata,
                    score=1.0 - float(score),  # Convert distance to similarity
                )
                for doc, score in docs_with_scores
            ]
        except Exception as e:
            print(f"[self_query] Fallback search also failed: {e}")
            return []


def create_self_query_retriever(
    config: EmbeddingConfig,
    embeddings_client,
    llm=None,
    verbose: bool = False,
) -> SelfQueryRetrieverWrapper:
    """Factory function to create SelfQueryRetrieverWrapper.
    
    Args:
        config: Embedding configuration with PG connection
        embeddings_client: Embedding provider (Gemini or Voyage AI)
        llm: Optional LangChain-compatible LLM (creates default if None)
        verbose: Enable verbose logging
        
    Returns:
        Configured SelfQueryRetrieverWrapper
    """
    # Create PGVector store
    vectorstore = PGVector(
        connection=config.pg_conn,
        embeddings=embeddings_client,
        collection_name=config.collection_name,
        distance_strategy="cosine",  # lowercase required by langchain-postgres
        use_jsonb=True,
        embedding_length=config.embedding_dim,
    )

    
    # Create LLM if not provided
    if llm is None:
        import os
        from langchain_google_genai import ChatGoogleGenerativeAI
        
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("GOOGLE_API_KEY required for SelfQueryRetriever LLM")
        
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=api_key,
            temperature=0.0,  # Deterministic for query parsing
        )
    
    return SelfQueryRetrieverWrapper(
        vectorstore=vectorstore,
        llm=llm,
        verbose=verbose,
    )


__all__ = [
    "SelfQueryRetrieverWrapper",
    "SelfQueryResult",
    "ExtractedQuery",
    "create_self_query_retriever",
    "METADATA_FIELD_INFO",
]
