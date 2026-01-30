# OCR Vector DB

A document processing and semantic search system that parses documents (PDFs, Markdown, plain text), creates semantic embeddings, and stores them in PostgreSQL with pgvector for similarity search.

## Features

- **Multi-format parsing**: PDF (with OCR fallback), Markdown, plain text
- **Semantic segmentation**: Intelligent grouping of text, code, and images
- **Multi-view embeddings**: Separate embeddings for text, code, images, tables
- **Parent-child hierarchy**: Context-aware retrieval with parent documents
- **RAG support**: LLM-powered question answering over your documents
- **PostgreSQL + pgvector**: Scalable vector storage with HNSW indexing

## Installation

### From PyPI

```bash
pip install ocr-vector-db
```

### Using uv (recommended)

```bash
uv add ocr-vector-db
```

### Prerequisites

- Python 3.12+
- PostgreSQL with pgvector extension
- Google API key (for Gemini embeddings/LLM) or Voyage API key

### Database Setup

Start PostgreSQL with pgvector using Docker:

```bash
docker run -d \
  --name pgvector \
  -e POSTGRES_USER=langchain \
  -e POSTGRES_PASSWORD=langchain \
  -e POSTGRES_DB=vectordb \
  -p 5432:5432 \
  pgvector/pgvector:pg16
```

Or use docker-compose (if provided in the repository).

## Quick Start

### 1. Configure Environment

Create a `.env` file:

```bash
# Required
PG_CONN=postgresql+psycopg://langchain:langchain@localhost:5432/vectordb
COLLECTION_NAME=my_documents
GOOGLE_API_KEY=your-api-key-here
EMBEDDING_PROVIDER=gemini
```

### 2. Ingest Documents

```bash
# Ingest PDF files
myrag ingest documents/*.pdf

# Ingest with dry-run (parse only)
myrag ingest report.pdf --dry-run
```

### 3. Search

```bash
# Direct search
myrag search "vector database optimization"

# Search with filters
myrag search "async function" --view code --language javascript

# JSON output
myrag search "machine learning" --json
```

### 4. RAG (Question Answering)

```bash
# Ask a question
myrag rag "What is the main topic of this document?"

# With sources
myrag rag "How does the authentication work?" --sources
```

### 5. Interactive REPL

```bash
# Start search REPL
myrag

# Start RAG REPL
myrag --rag
```

## CLI Commands

### `myrag` (default)

Start the interactive REPL for search or RAG queries.

```bash
myrag              # Search mode
myrag --rag        # RAG mode (LLM-powered)
myrag --view code  # Default filter
```

### `myrag search`

Run a single search query.

```bash
myrag search "query" [options]

Options:
  --view {text,code,image,caption,table,figure}  Filter by content type
  --language LANG       Filter by programming language
  --top-k N, -k N       Number of results (default: 5)
  --no-context          Disable parent context expansion
  --json                Output JSON format
  --verbose, -v         Enable verbose logging
```

### `myrag ingest`

Ingest documents into the vector database.

```bash
myrag ingest FILE [FILE ...] [options]

Options:
  --dry-run      Parse only, no database writes
  --no-cache     Disable OCR cache (re-process all pages)
```

### `myrag rag`

Ask a question using RAG (Retrieval-Augmented Generation).

```bash
myrag rag "question" [options]

Options:
  --view {text,code,image,caption,table,figure}  Filter by content type
  --language LANG       Filter by programming language
  --top-k N, -k N       Number of context documents (default: 5)
  --sources             Show source documents in response
  --verbose, -v         Enable verbose logging
```

### `myrag quality`

Inspect data quality and statistics.

```bash
myrag quality
```

Output includes:
- Document/concept/fragment/embedding counts
- View distribution
- Orphan entity check

## Configuration

All settings are configured via environment variables. See `.env.example` for the complete list.

### Key Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `PG_CONN` | PostgreSQL connection string | (required) |
| `COLLECTION_NAME` | Vector store collection name | (required) |
| `EMBEDDING_PROVIDER` | `gemini` or `voyage` | `voyage` |
| `GOOGLE_API_KEY` | Google API key for Gemini | - |
| `VOYAGE_API_KEY` | Voyage AI API key | - |
| `EMBEDDING_DIM` | Embedding dimension | 768 |
| `PARENT_MODE` | Grouping mode: `unit`, `page`, `section`, `page_section` | `unit` |
| `ENABLE_IMAGE_OCR` | Enable Gemini Vision OCR for PDFs | `true` |

## Architecture

```
Document -> Concept -> Fragment -> Embedding
```

- **Document**: Source file (PDF, Markdown, text)
- **Concept**: Semantic unit (related paragraphs, code blocks)
- **Fragment**: Individual piece of content (text paragraph, code block, image)
- **Embedding**: Vector representation for similarity search

### Multi-View Strategy

Documents are segmented into distinct views:
- `text`: Natural language paragraphs
- `code`: Code blocks with language detection
- `image`: Image references with alt text
- `caption`: Figure/table captions
- `table`, `figure`: Structured content

Each view can be filtered during search for targeted retrieval.

## Development

### Install from Source (uv)

```bash
git clone https://github.com/ocr-vector-db/ocr-vector-db.git
cd ocr-vector-db

# Install with uv (recommended)
uv sync --all-extras

# Or with pip
pip install -e ".[dev,test]"
```

### Build Package

```bash
# Using uv
uv build

# Or using pip
python -m build
```

### Run CLI (development)

```bash
# Using uv
uv run myrag --help
uv run myrag search "query"
uv run myrag ingest docs/*.pdf

# Or after pip install -e .
myrag --help
```

### Run Tests

```bash
uv run pytest
# or
pytest
```

### Sync Lock File

```bash
uv lock
```

## License

MIT License - see [LICENSE](LICENSE) for details.
