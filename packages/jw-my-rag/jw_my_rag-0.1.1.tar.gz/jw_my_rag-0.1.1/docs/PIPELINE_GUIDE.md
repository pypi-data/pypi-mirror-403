# OCR Vector DB 파이프라인 가이드

> **대상 독자**: 프로젝트에 새로 참가하는 개발자
> **목적**: 시스템의 실행 파이프라인을 상세히 이해하고, 핵심 메서드의 동작 원리를 파악

---

## 목차

1. [개요](#1-개요)
2. [핵심 개념](#2-핵심-개념)
3. [수집 파이프라인 (Ingestion)](#3-수집-파이프라인-ingestion)
4. [임베딩 검증 및 저장](#4-임베딩-검증-및-저장)
5. [검색 파이프라인 (Retrieval)](#5-검색-파이프라인-retrieval)
6. [RAG 생성 파이프라인 (Generation)](#6-rag-생성-파이프라인-generation)
7. [주요 클래스 참조표](#7-주요-클래스-참조표)
8. [설정 가이드](#8-설정-가이드)
9. [디버깅 팁](#9-디버깅-팁)

---

## 1. 개요

### 1.1 프로젝트 목적

OCR Vector DB는 문서(PDF, Markdown, 텍스트)를 처리하여 검색 가능한 벡터 데이터베이스를 구축하는 시스템입니다.

**핵심 기능:**
- 다양한 문서 형식 파싱 (PDF OCR 포함)
- 지능형 의미 단위 분할
- 부모-자식 계층 구조로 컨텍스트 유지
- pgvector 기반 벡터 유사도 검색
- RAG(Retrieval-Augmented Generation) 지원

### 1.2 전체 아키텍처 다이어그램

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              전체 파이프라인 흐름                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │   파일 입력   │ →  │    파싱     │ →  │  세그먼테이션 │ →  │  의미단위화  │  │
│  │  (PDF/MD/TXT)│    │  (Parsers)  │    │ (RawSegment) │    │ (Unitizer)  │  │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘  │
│                                                                    │        │
│                                                                    ▼        │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │  벡터 저장   │ ←  │ 임베딩 생성  │ ←  │  임베딩 검증  │ ←  │ 엔티티 생성  │  │
│  │  (PGVector) │    │ (Voyage/   │    │ (Validator) │    │ (Concept/   │  │
│  │             │    │  Gemini)   │    │             │    │  Fragment)  │  │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘  │
│         │                                                                   │
│         ▼                                                                   │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │  벡터 검색   │ →  │ 컨텍스트 확장│ →  │  RAG 생성   │ →  │   응답 반환  │  │
│  │ (Retrieval) │    │ (Expander)  │    │(Generation) │    │             │  │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.3 패키지 구조

```
ocr_vector_db/
├── api/                    # CLI, REST 엔드포인트
│   ├── cli/               # 명령줄 인터페이스
│   └── use_cases/         # 유스케이스 오케스트레이션
├── domain/                 # 순수 도메인 엔티티 (인프라 의존성 없음)
├── ingestion/              # 파일 파싱, 세그먼테이션
│   ├── parsers/           # PDF, Markdown, OCR 파서
│   └── ...
├── embedding/              # 벡터 생성, 검증
├── retrieval/              # 검색 파이프라인
├── generation/             # RAG 생성
├── storage/                # 데이터베이스 연산
└── shared/                 # 공통 유틸리티
```

---

## 2. 핵심 개념

### 2.1 엔티티 계층 구조

```
Document (문서)
    │
    └── Concept (개념/의미 단위)
            │
            └── Fragment (조각/청크)
                    │
                    └── Embedding (벡터 표현)
```

**핵심 원칙:**
- 모든 엔티티는 반드시 부모를 가져야 함 (고아 엔티티 금지)
- 부모 ID는 생성 시점에 설정되며 불변
- Fragment가 검색 대상, Concept가 컨텍스트 제공자

### 2.2 도메인 엔티티 상세 설명

**파일 위치**: `domain/entities.py`

#### Document (문서)
```python
@dataclass
class Document:
    """최상위 입력 단위 - 파일 하나를 표현"""
    id: str              # MD5(file_path) - 결정론적 ID
    source_path: str     # 원본 파일 경로
    created_at: datetime # 생성 시각
    metadata: dict       # 추가 메타데이터
```

#### Concept (개념)
```python
@dataclass
class Concept:
    """의미적으로 응집된 정보 단위 (Semantic Parent)"""
    id: str              # MD5(document.id | unit_id)[:16]
    document_id: str     # 부모 Document ID (불변, HIER-002)
    order: int           # 문서 내 순서
    content: str         # 부모 문서 컨텐츠 (컨텍스트용)
    metadata: dict       # 메타데이터
    fragments: List[Fragment]  # 자식 Fragment 목록
```

#### Fragment (조각)
```python
@dataclass
class Fragment:
    """Concept 내의 개별 정보 청크 - 검색 대상"""
    id: str              # f"{concept_id[:12]}-{order}-{content_hash}"
    concept_id: str      # 부모 Concept ID (불변, FRAG-IMMUT-001)
    content: str         # 실제 텍스트 내용
    view: View           # text, code, image 등
    language: str        # 프로그래밍 언어 (코드인 경우)
    order: int           # Concept 내 순서
    metadata: dict       # 메타데이터
```

#### View (뷰 타입)
```python
class View(Enum):
    TEXT = "text"      # 일반 텍스트
    CODE = "code"      # 코드 블록
    IMAGE = "image"    # 이미지 참조
    TABLE = "table"    # 테이블
    FIGURE = "figure"  # 그림/차트
```

### 2.3 의미 단위 (Semantic Unit) 개념

의미 단위는 관련된 콘텐츠를 그룹화하는 핵심 개념입니다.

**예시:**
```
[텍스트] "다음은 리스트 컴프리헨션 예제입니다."  ─┐
[코드]   squares = [x**2 for x in range(10)]    ├─ 하나의 의미 단위
[텍스트] "위 코드는 0부터 9까지의 제곱을 계산합니다." ─┘
```

**의미 단위의 이점:**
- 설명 텍스트와 코드가 함께 검색됨
- 컨텍스트가 보존되어 RAG 품질 향상
- 중복 없이 관련 정보 제공

### 2.4 결정론적 ID 생성

모든 ID는 콘텐츠 기반 해시로 생성되어 **멱등성**을 보장합니다:

| 엔티티 | ID 생성 공식 | 예시 |
|--------|-------------|------|
| Document | `MD5(file_path)` | `a1b2c3d4e5f6...` |
| Concept | `MD5(document.id \| unit_id)[:16]` | `f7e8d9c0b1a2...` |
| Fragment | `{concept_id[:12]}-{order}-{content_hash}` | `f7e8d9c0b1a2-0-abc123` |
| Embedding doc_id | `MD5(concept_id + view + lang + content)` | `doc:xyz789...` |

**장점:**
- 같은 파일 재수집 시 동일한 ID 생성
- 중복 데이터 자동 방지
- 업데이트/삭제 용이

---

## 3. 수집 파이프라인 (Ingestion)

### 3.1 CLI 사용법

```bash
# 기본 수집
python -m api.cli ingest file1.txt file2.pdf

# 글로브 패턴 사용
python -m api.cli ingest "documents/*.md"

# PDF OCR 강제 실행
python -m api.cli ingest document.pdf --force-ocr

# 캐시 비활성화
python -m api.cli ingest document.pdf --no-cache
```

### 3.2 IngestUseCase.execute() 라인별 상세 분석

**파일**: `api/use_cases/ingest.py` (127-210줄)
**역할**: 전체 수집 파이프라인을 조율하는 메인 오케스트레이터

```python
def execute(self, file_paths: List[str]) -> IngestResult:
    """Execute ingestion pipeline."""
```

#### 라인 136-138: 통계 변수 초기화
```python
    total_concepts = 0      # 생성된 Concept 수
    total_fragments = 0     # 생성된 Fragment 수
    total_embeddings = 0    # 생성된 Embedding 수
```
**설명**: 파이프라인 실행 결과를 추적할 카운터를 초기화합니다.

#### 라인 140-145: 파일별 파싱 루프 시작
```python
    for file_path in file_paths:
        print(f"[ingest] Processing: {file_path}")

        # 1. Parse file based on extension
        segments = self._parse_file(file_path)
        print(f"[ingest] Parsed {len(segments)} segments")
```
**설명**:
- 각 파일을 순회하며 처리
- `_parse_file()`은 파일 확장자에 따라 적절한 파서 선택
  - `.md` → `MarkdownParser`
  - `.pdf` → `PyMuPdfParser` 또는 `PdfParser`
  - 기타 → `OcrParser`
- 반환값: `List[RawSegment]` (종류, 내용, 언어, 순서 포함)

#### 라인 147-154: Document ID 생성 및 기존 데이터 정리
```python
        # 2. Create Document entity with deterministic ID
        doc_id = hashlib.md5(file_path.encode("utf-8")).hexdigest()

        # 2a. Delete existing document data before re-ingest (CASCADE-001)
        print(f"[ingest] Cleaning up existing data for doc_id: {doc_id[:8]}...")
        self.cascade_deleter.delete_document(doc_id)
```
**설명**:
- **결정론적 ID**: 같은 파일 경로는 항상 같은 ID 생성 → 재수집 시 업데이트 가능
- **CASCADE 삭제**: 재수집 전에 기존 데이터(Concept, Fragment, Embedding) 모두 삭제
- 이 패턴이 없으면 오래된 임베딩이 누적되어 검색 품질 저하

#### 라인 156-161: Document 엔티티 생성 및 저장
```python
        document = Document(
            id=doc_id,
            source_path=file_path,
            metadata={"filename": os.path.basename(file_path)},
        )
        self.doc_repo.save(document)
```
**설명**:
- Document 엔티티 인스턴스 생성
- 메타데이터에 파일명 저장 (검색 필터링에 활용)
- `DocumentRepository.save()`로 데이터베이스에 저장

#### 라인 163-165: 세그먼트 단위화
```python
        # 3. Unitize segments (group related content)
        unitized = self.unitizer.unitize(segments)
        print(f"[ingest] Created {len(unitized)} semantic units")
```
**설명**:
- `SegmentUnitizer.unitize()`가 관련 세그먼트를 그룹화
- 입력: `List[RawSegment]`
- 출력: `List[UnitizedSegment]` (각각 `unit_id` 할당)
- 상세 동작은 [3.3절](#33-segmentunitizerunitize-라인별-상세-분석) 참조

#### 라인 167-169: Concept/Fragment 빌드
```python
        # 4. Build Concepts and Fragments
        concepts = self.concept_builder.build(
            unitized, document, os.path.basename(file_path)
        )
        print(f"[ingest] Built {len(concepts)} concepts")
```
**설명**:
- `ConceptBuilder.build()`가 도메인 엔티티 생성
- UnitizedSegment → Concept + Fragment 변환
- 상세 동작은 [3.4절](#34-conceptbuilderbuild-라인별-상세-분석) 참조

#### 라인 172-200: Concept별 저장 및 임베딩 루프
```python
        # 5. Save Concepts, Fragments, and Embeddings
        for concept in concepts:
            self.concept_repo.save(concept)      # Concept 저장
            total_concepts += 1

            # Save parent document for context expansion
            self._save_parent(concept)           # 부모 문서 저장

            docs_to_embed = []  # 임베딩할 문서 수집

            for fragment in concept.fragments:
                # Validate fragment (FRAG-LEN-001, etc.)
                if not self.validator.is_eligible(fragment):
                    print(f"[skip] Fragment filtered: {fragment.content[:50]}...")
                    continue

                self.fragment_repo.save(fragment)  # Fragment 저장
                total_fragments += 1

                # Convert to LangChain Document
                doc_id = fragment.compute_doc_id()
                lc_doc = self.adapter.fragment_to_document(fragment, doc_id)
                docs_to_embed.append(lc_doc)

            # Batch embed and store to PGVector
            if docs_to_embed:
                embedded = self.vector_writer.upsert_batch(
                    self.vector_store, docs_to_embed
                )
                total_embeddings += embedded
```
**설명**:
1. **Concept 저장**: `ConceptRepository.save()`
2. **부모 문서 저장**: `_save_parent()`가 컨텍스트 확장용 부모 콘텐츠 저장
3. **Fragment 검증**: `EmbeddingValidator.is_eligible()`로 임베딩 자격 확인
4. **Fragment 저장**: 검증 통과 시 `FragmentRepository.save()`
5. **LangChain 변환**: `LangChainAdapter.fragment_to_document()`
6. **벡터 저장**: `VectorStoreWriter.upsert_batch()`로 PGVector에 배치 업로드

#### 라인 203: 인덱스 생성
```python
    # Ensure indexes after all data is inserted
    self.schema_manager.ensure_indexes()
```
**설명**:
- 모든 데이터 삽입 후 인덱스 생성/갱신
- HNSW 벡터 인덱스, JSONB GIN 인덱스, BTREE 인덱스

#### 라인 205-210: 결과 반환
```python
    return IngestResult(
        documents_processed=len(file_paths),
        concepts_created=total_concepts,
        fragments_created=total_fragments,
        embeddings_generated=total_embeddings,
    )
```

### 3.3 SegmentUnitizer.unitize() 라인별 상세 분석

**파일**: `ingestion/segmentation.py` (40-146줄)
**역할**: RawSegment를 의미 단위로 그룹화

```python
def unitize(self, segments: List[RawSegment]) -> List[UnitizedSegment]:
```

#### 라인 50-53: 초기화
```python
    output: List[UnitizedSegment] = []    # 결과 리스트
    text_buffer: List[RawSegment] = []    # 텍스트 버퍼 (코드 전 텍스트 축적)
    text_buffer_chars = 0                  # 버퍼 내 문자 수
    i, total = 0, len(segments)           # 인덱스, 총 세그먼트 수
```
**설명**:
- `text_buffer`: Python 코드 블록 앞의 설명 텍스트를 임시 저장
- 코드 블록 발견 시 버퍼의 텍스트를 해당 코드와 같은 unit_id로 그룹화

#### 라인 55-74: 텍스트 세그먼트 버퍼링
```python
    while i < total:
        segment = segments[i]
        if segment.kind == "text":
            text_buffer.append(segment)
            text_buffer_chars += len(segment.content)

            # 버퍼가 max_pre_text_chars 초과 시 처리
            while text_buffer_chars > self.max_pre_text_chars and text_buffer:
                if text_buffer_chars >= self.text_unit_threshold:
                    # 충분한 텍스트면 텍스트 전용 의미 단위 생성
                    text_unit_id = self._generate_text_unit_id(text_buffer)
                    for buffered in text_buffer:
                        output.append(UnitizedSegment(text_unit_id, "text_unit", buffered))
                    text_buffer.clear()
                    text_buffer_chars = 0
                else:
                    # 아니면 오래된 텍스트를 고아로 내보냄
                    old = text_buffer.pop(0)
                    text_buffer_chars -= len(old.content)
                    output.append(UnitizedSegment(None, "other", old))
            i += 1
            continue
```
**설명**:
- 텍스트 세그먼트는 바로 출력하지 않고 버퍼에 축적
- 버퍼가 `max_pre_text_chars`(기본 4000자) 초과 시:
  - `text_unit_threshold`(기본 500자) 이상이면 텍스트 전용 의미 단위 생성
  - 미만이면 고아 세그먼트로 처리

#### 라인 76-91: Python 코드 감지 시 의미 단위 생성
```python
        if segment.kind == "code" and segment.language == "python":
            # 결정론적 unit_id 생성
            unit_id = self._generate_unit_id(
                segment,
                text_buffer if self.attach_pre_text else []
            )

            # 버퍼의 텍스트를 pre_text로 같은 unit에 포함
            if self.attach_pre_text and text_buffer:
                for buffered in text_buffer:
                    output.append(UnitizedSegment(unit_id, "pre_text", buffered))
                text_buffer.clear()
                text_buffer_chars = 0
            else:
                # 버퍼 비우기 (고아로 처리)
                while text_buffer:
                    output.append(UnitizedSegment(None, "other", text_buffer.pop(0)))
                text_buffer_chars = 0

            # 연속된 Python 코드 블록 모두 같은 unit에 포함
            while i < total and segments[i].kind == "code" and segments[i].language == "python":
                output.append(UnitizedSegment(unit_id, "python", segments[i]))
                i += 1
```
**설명**:
- **핵심 로직**: Python 코드 발견 시 앞의 텍스트와 함께 의미 단위 형성
- `_generate_unit_id()`: pre_text + code 내용으로 결정론적 해시 생성
- 연속된 Python 코드 블록은 모두 같은 unit_id 공유

#### 라인 93-101: bridge_text 처리
```python
            # 브리지 텍스트: Python과 JavaScript 사이의 짧은 텍스트
            bridged = 0
            while (
                bridged < self.bridge_text_max
                and i < total
                and segments[i].kind == "text"
            ):
                output.append(UnitizedSegment(unit_id, "bridge_text", segments[i]))
                i += 1
                bridged += 1
```
**설명**:
- Python 코드와 JavaScript 코드 사이에 있는 짧은 텍스트
- `bridge_text_max`(기본 0)개까지 같은 unit에 포함

#### 라인 103-120: JavaScript 코드 및 post_text 처리
```python
            # JavaScript 코드가 바로 뒤따르면 같은 unit에 포함
            if i < total and segments[i].kind == "code" and segments[i].language == "javascript":
                while i < total and segments[i].kind == "code" and segments[i].language == "javascript":
                    output.append(UnitizedSegment(unit_id, "javascript", segments[i]))
                    i += 1

                # post_text 처리 (JavaScript 코드 뒤의 텍스트)
                if self.attach_post_text:
                    while i < total and segments[i].kind == "text":
                        # 다음에 Python 코드가 오면 버퍼로 이동
                        if (
                            i + 1 < total
                            and segments[i + 1].kind == "code"
                            and segments[i + 1].language == "python"
                        ):
                            text_buffer.append(segments[i])
                            text_buffer_chars += len(segments[i].content)
                            i += 1
                            break
                        output.append(UnitizedSegment(unit_id, "post_text", segments[i]))
                        i += 1
            continue
```
**설명**:
- Python + JavaScript 조합 패턴 지원 (프론트엔드-백엔드 예제 문서)
- `attach_post_text` 활성화 시 JavaScript 뒤의 텍스트도 같은 unit에 포함

#### 라인 137-146: 잔여 버퍼 처리
```python
    # 루프 종료 후 남은 텍스트 버퍼 처리
    if text_buffer:
        if text_buffer_chars >= self.text_unit_threshold:
            text_unit_id = self._generate_text_unit_id(text_buffer)
            for buffered in text_buffer:
                output.append(UnitizedSegment(text_unit_id, "text_unit", buffered))
        else:
            for buffered in text_buffer:
                output.append(UnitizedSegment(None, "other", buffered))
    return output
```

#### unit_id 생성 함수 (라인 148-168)
```python
def _generate_unit_id(self, code_segment: RawSegment, pre_text_segments: List[RawSegment]) -> str:
    """결정론적 unit_id 생성"""
    # 마지막 2개 pre_text 세그먼트의 앞 100자씩 사용
    pre_text = "".join(s.content[:100] for s in pre_text_segments[-2:])
    # 코드 앞 500자와 결합
    content = f"{pre_text}|{code_segment.content[:500]}"
    # MD5 해시의 앞 16자
    return hashlib.md5(content.encode("utf-8", errors="ignore")).hexdigest()[:16]
```

### 3.4 ConceptBuilder.build() 라인별 상세 분석

**파일**: `ingestion/concept_builder.py` (26-82줄)
**역할**: UnitizedSegment를 도메인 Concept/Fragment로 변환

```python
def build(
    self,
    unitized: List[UnitizedSegment],
    document: Document,
    source_basename: str,
) -> List[Concept]:
```

#### 라인 47-56: unit_id별 그룹화
```python
    # unit_id별로 세그먼트 그룹화
    unit_groups: Dict[str, List[UnitizedSegment]] = {}
    orphan_segments: List[UnitizedSegment] = []  # unit_id가 None인 세그먼트

    for unit_seg in unitized:
        if unit_seg.unit_id:
            if unit_seg.unit_id not in unit_groups:
                unit_groups[unit_seg.unit_id] = []
            unit_groups[unit_seg.unit_id].append(unit_seg)
        else:
            orphan_segments.append(unit_seg)
```
**설명**:
- `unit_id`가 있는 세그먼트: 해당 unit_id로 그룹화
- `unit_id`가 None인 세그먼트: 고아 세그먼트 리스트에 추가

#### 라인 58-70: 그룹화된 unit별 Concept 생성
```python
    concepts: List[Concept] = []
    order = 0

    for unit_id, segments in unit_groups.items():
        concept = self._create_concept_from_unit(
            unit_id=unit_id,
            segments=segments,
            document=document,
            order=order,
        )
        concepts.append(concept)
        order += 1
```
**설명**:
- 각 unit_id 그룹에서 하나의 Concept 생성
- `_create_concept_from_unit()`이 Concept + 소속 Fragment들 생성

#### 라인 73-80: 고아 세그먼트 Concept 생성
```python
    # 고아 세그먼트들을 모아서 하나의 Concept 생성
    if orphan_segments:
        concept = self._create_concept_from_orphans(
            orphan_segments=orphan_segments,
            document=document,
            source_basename=source_basename,
            order=order,
        )
        concepts.append(concept)

    return concepts
```
**설명**:
- 고아 세그먼트들은 하나의 Concept로 묶음
- 내부에서 `TextChunker`로 청킹하여 적절한 크기의 Fragment 생성

#### _create_concept_from_unit() 상세 (라인 84-116)
```python
def _create_concept_from_unit(self, unit_id, segments, document, order) -> Concept:
    # 문서 범위 내에서 고유한 concept_id 생성
    scoped_id = hashlib.md5(f"{document.id}|{unit_id}".encode("utf-8")).hexdigest()[:16]

    concept = Concept(
        id=scoped_id,
        document_id=document.id,  # 부모 참조 (HIER-002)
        order=order,
        metadata={"unit_type": "semantic_unit", "original_unit_id": unit_id},
    )
    concept.validate()  # HIER-002 검증: document_id 필수

    # 각 세그먼트에서 Fragment 생성
    fragments = []
    for idx, unit_seg in enumerate(segments):
        fragment = self._create_fragment(
            concept_id=concept.id,
            segment=unit_seg,
            order=idx,
        )
        fragment.validate()  # HIER-003 검증: concept_id 필수
        fragments.append(fragment)

    concept.fragments = fragments
    return concept
```

#### _create_fragment() 상세 (라인 193-231)
```python
def _create_fragment(self, concept_id, segment, order) -> Fragment:
    # View 매핑: "text" → View.TEXT, "code" → View.CODE
    view = self._map_kind_to_view(segment.segment.kind)

    # 결정론적 Fragment ID 생성
    content_hash = hashlib.md5(
        segment.segment.content[:200].encode("utf-8", errors="ignore")
    ).hexdigest()[:8]
    fragment_id = f"{concept_id[:12]}-{order}-{content_hash}"

    fragment = Fragment(
        id=fragment_id,
        concept_id=concept_id,    # 부모 참조 (FRAG-IMMUT-001)
        content=segment.segment.content,
        view=view,
        language=segment.segment.language,
        order=order,
        metadata={
            "unit_role": segment.role,      # pre_text, python, post_text 등
            "original_kind": segment.segment.kind,
        },
    )
    return fragment
```

### 3.5 MarkdownParser.parse_text() 상세 분석

**파일**: `ingestion/parsers/markdown.py` (30-108줄)
**역할**: Markdown 텍스트를 RawSegment로 파싱

```python
def parse_text(self, raw: str) -> List[RawSegment]:
```

#### 주요 정규식 패턴
```python
MD_FENCE_RE = re.compile(r"^\s*```\s*([A-Za-z0-9_+-]*)\s*$")  # 코드 펜스
MD_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")          # 이미지 링크
```

#### 핵심 로직 흐름
```
1. 각 라인을 순회
2. 코드 펜스(```) 발견 시:
   - 펜스 시작: 이전 텍스트 버퍼 플러시, 코드 버퍼 시작
   - 펜스 종료: 코드 세그먼트 생성 (언어 태그 포함)
3. 텍스트 라인:
   - 텍스트 버퍼에 축적
   - 이미지 링크(![alt](url)) 추출하여 별도 세그먼트 생성
4. 언어 태그 정규화: py/python3 → python, js/jsx/ts → javascript
```

---

## 4. 임베딩 검증 및 저장

### 4.1 EmbeddingValidator.is_eligible() 라인별 상세 분석

**파일**: `embedding/validators.py` (83-105줄)
**역할**: Fragment가 임베딩 대상인지 검증

```python
def is_eligible(self, fragment: Fragment) -> bool:
    """
    Check if fragment meets all requirements for embedding.
    """
```

#### 라인 94-95: 최소 길이 검증 (FRAG-LEN-001)
```python
    # FRAG-LEN-001: Minimum length check
    if len(fragment.content) < self.MIN_LENGTH:  # MIN_LENGTH = 10
        return False
```
**설명**:
- 10자 미만의 Fragment는 임베딩 가치가 없음
- 예: 페이지 번호, 단순 구분자 등 필터링

#### 라인 97-99: 보일러플레이트 검증 (EMBED-BAN-003)
```python
    # EMBED-BAN-003: Reject boilerplate
    if self._is_boilerplate(fragment.content):
        return False
```
**설명**:
- 저작권 문구, 페이지 번호, 헤더/푸터 등 검출
- 패턴 기반 + 반복 라인 검출

#### `_is_boilerplate()` 상세 (라인 107-125)
```python
def _is_boilerplate(self, content: str) -> bool:
    # 정규식 패턴 매칭 (저작권, 페이지 번호, 참조 문구 등)
    if self._boilerplate_re.search(content):
        return True

    # 반복 라인 검출: 모든 라인이 동일하면 보일러플레이트
    lines = content.strip().split("\n")
    if len(lines) > 0:
        unique_lines = set(line.strip() for line in lines if line.strip())
        if len(unique_lines) == 1 and len(lines) > 2:
            return True

    return False
```

#### 라인 101-103: 순수 참조 텍스트 검증 (EMBED-BAN-006)
```python
    # EMBED-BAN-006: Reject pure reference text
    if self._is_pure_reference(fragment.content):
        return False
```
**설명**:
- "그림 3 참조", "See Figure 1" 같은 단순 참조 문구 필터링
- 15자 미만 텍스트에서만 검사 (긴 텍스트는 참조 외 내용 포함 가능)

#### `_is_pure_reference()` 상세 (라인 127-154)
```python
def _is_pure_reference(self, content: str) -> bool:
    content_stripped = content.strip()

    # 15자 미만만 검사
    if len(content_stripped) < 15:
        content_lower = content_stripped.lower()

        # 영어: 동사(see, refer) + 대상(figure, table) 모두 있어야 필터링
        has_en_verb = any(v in content_lower for v in ["see", "refer", "reference"])
        has_en_target = any(t in content_lower for t in ["figure", "table", "section"])
        if has_en_verb and has_en_target:
            return True

        # 한글: 동사(참조, 참고) + 대상(그림, 표) 모두 있어야 필터링
        has_ko_verb = any(v in content_stripped for v in ["참조", "참고", "보기"])
        has_ko_target = any(t in content_stripped for t in ["그림", "표", "도표"])
        if has_ko_verb and has_ko_target:
            return True

    return False
```

### 4.2 VectorStoreWriter.upsert_batch() 라인별 상세 분석

**파일**: `storage/vector_store.py` (47-139줄)
**역할**: PGVector에 배치로 임베딩 업로드

```python
def upsert_batch(
    self,
    store: PGVector,
    docs: List[Document],
    batch_size: int = 64,
) -> int:
```

#### 라인 68-69: 빈 입력 처리
```python
    if not docs:
        return 0
```

#### 라인 71-78: doc_id 기반 중복 제거
```python
    # 1. Deduplicate by doc_id
    unique: dict[str, Document] = {}
    for doc in docs:
        doc_id = doc.metadata.get("doc_id")
        if not doc_id:
            raise ValueError("Document missing doc_id in metadata")
        unique.setdefault(doc_id, doc)  # 첫 번째만 유지
    deduped = list(unique.values())
```
**설명**:
- 같은 `doc_id`를 가진 문서는 하나만 유지
- 결정론적 ID 덕분에 중복 자동 처리

#### 라인 80-91: 문자 예산 기반 배치 분할
```python
    # 2. Character-budget-aware batching
    char_budget = self.config.max_chars_per_request if self.config.max_chars_per_request > 0 else 0
    max_items = self.config.max_items_per_request if self.config.max_items_per_request > 0 else batch_size

    groups = list(iter_by_char_budget(
        deduped,
        char_budget=char_budget,        # 요청당 최대 문자 수
        max_batch_size=batch_size,      # 배치당 최대 문서 수
        max_items_per_request=max_items, # 요청당 최대 항목 수
    ))
    if not groups:
        return 0
```
**설명**:
- 임베딩 API의 토큰 제한을 고려한 배치 분할
- `iter_by_char_budget()`: 문자 수 기준으로 배치 크기 자동 조절

#### 라인 94-97: 비율 제한 설정
```python
    # 3. Rate limiting setup
    interval = (60.0 / self.config.rate_limit_rpm) if self.config.rate_limit_rpm > 0 else 0.0
    total_groups = len(groups)
    total_written = 0
```
**설명**:
- `rate_limit_rpm`: 분당 요청 수 제한
- 예: 60 RPM → 배치 간 1초 대기

#### 라인 100-137: 배치별 업로드 (재시도 로직)
```python
    # 4. Process batches with retry logic
    for index, batch in enumerate(groups, 1):
        print(f"[upsert_batch] storing batch {index}/{total_groups} ({len(batch)} docs)")
        ids = [doc.metadata["doc_id"] for doc in batch]
        attempt = 0
        max_attempts = 6
        backoff = max(20.0, interval) or 20.0

        while True:
            try:
                # PGVector에 문서 추가
                try:
                    store.add_documents(batch, ids=ids)
                except TypeError:
                    # 구버전 LangChain 호환성
                    store.add_documents(batch)
                print(f"[upsert_batch] batch {index}/{total_groups} inserted {len(batch)} docs")
                break
            except Exception as exc:
                message = str(exc).lower()
                # 비율 제한 에러 감지
                rate_limited = any(
                    token in message for token in ("ratelimit", "rate limit", "rpm", "tpm")
                )
                if not rate_limited or attempt >= max_attempts - 1:
                    print(f"[upsert_batch] batch {index}/{total_groups} failed: {exc}")
                    raise

                # 지수 백오프 재시도
                attempt += 1
                sleep_for = backoff * (1.5**attempt)  # 20s → 30s → 45s → ...
                print(f"[rate-limit] retry {attempt}/{max_attempts} in {int(sleep_for)}s")
                time.sleep(sleep_for)

        total_written += len(batch)

        # 배치 간 대기
        if interval > 0 and index < total_groups:
            time.sleep(interval)

    return total_written
```
**설명**:
- **지수 백오프**: 비율 제한 시 대기 시간을 점점 늘림 (20초 → 30초 → 45초...)
- **최대 6번 재시도** 후 실패 시 예외 발생
- 비율 제한이 아닌 다른 에러는 즉시 예외 발생

### 4.3 Fragment.compute_doc_id() 결정론적 ID 생성

**파일**: `domain/entities.py` (113-128줄)

```python
def compute_doc_id(self) -> str:
    """
    Generate deterministic doc_id for this fragment.

    Rule: EMBED-ID-002 - doc_id = hash(parent_id + view + lang + content)
    """
    content_hash = ContentHash.compute(
        parent_id=self.concept_id,    # 부모 Concept ID
        view=self.view,               # text, code, image
        lang=self.language,           # python, javascript, None
        content=self.content,         # 실제 텍스트
    )
    return content_hash.to_doc_id()   # "doc:{hash}" 형식
```

**ContentHash.compute() 내부 동작:**
```python
# domain/value_objects.py
@staticmethod
def compute(parent_id: str, view: View, lang: Optional[str], content: str) -> "ContentHash":
    # 모든 요소를 파이프로 연결
    raw = f"{parent_id}|{view.value}|{lang or ''}|{content}"
    # MD5 해시 생성
    hash_value = hashlib.md5(raw.encode("utf-8", errors="ignore")).hexdigest()
    return ContentHash(hash_value)

def to_doc_id(self) -> str:
    return f"doc:{self.value}"
```

**결정론적 ID의 장점:**
1. 같은 Fragment는 항상 같은 doc_id 생성
2. 재수집 시 기존 임베딩 자동 업데이트 (덮어쓰기)
3. 중복 임베딩 방지

---

## 5. 검색 파이프라인 (Retrieval)

### 5.1 RetrievalPipeline.retrieve() 라인별 상세 분석

**파일**: `retrieval/pipeline.py` (90-181줄)
**역할**: 전체 검색 파이프라인 조율

```python
def retrieve(
    self,
    query: str,
    view: Optional[str] = None,
    language: Optional[str] = None,
    top_k: int = 10,
    expand_context: bool = True,
    deduplicate: bool = True,
    use_self_query: bool = True,
) -> List[ExpandedResult]:
```

#### 라인 114-136: SelfQueryRetriever 경로 (권장)
```python
    # Stage 0: SelfQueryRetriever path (auto-extracts filters from query)
    if use_self_query and self.self_query_retriever:
        try:
            # 쿼리에서 자동으로 메타데이터 필터 추출
            # 예: "Python 데코레이터 코드만 보여줘" → view="code", lang="python"
            self_query_results = self.self_query_retriever.retrieve(query, k=top_k)

            if self_query_results:
                print(f"[self_query] Retrieved {len(self_query_results)} results with auto-filters")

                # SelfQueryResult → SearchResult 변환
                search_results = self._convert_self_query_results(self_query_results)

                # 중복 제거
                if deduplicate:
                    search_results = self.grouper.deduplicate_by_content(search_results)

                # 컨텍스트 확장
                if expand_context:
                    return self.context_expander.expand(search_results)
                else:
                    return [ExpandedResult(result=r) for r in search_results]
        except Exception as e:
            print(f"[self_query] Falling back to standard search: {e}")
```
**설명**:
- **SelfQueryRetriever**: LangChain의 자연어 쿼리 → 메타데이터 필터 자동 변환 기능
- 사용자가 "Python 코드만 보여줘" 입력 시 자동으로 `view="code"`, `lang="python"` 필터 적용
- 실패 시 레거시 경로로 폴백

#### 라인 138-158: 레거시 QueryOptimizer 경로
```python
    # Legacy path: QueryOptimizer or direct search
    search_query = query
    optimized_view = view
    optimized_language = language

    # Stage 0 (legacy): Query optimization
    if self.query_optimizer:
        try:
            optimized = self.query_optimizer.optimize(query)
            search_query = optimized.rewritten      # 재작성된 쿼리

            # 힌트가 있으면 사용
            if not view and optimized.view_hint:
                optimized_view = optimized.view_hint
            if not language and optimized.language_hint:
                optimized_language = optimized.language_hint

            print(f"[optimize] '{query}' -> '{search_query}'")
            if optimized.keywords:
                print(f"[optimize] Keywords: {optimized.keywords}")
        except Exception as e:
            print(f"[optimize] Fallback to original query: {e}")
```
**설명**:
- 구버전 호환용 QueryOptimizer
- LLM을 사용해 쿼리 재작성 및 키워드/필터 힌트 추출

#### 라인 160-166: 쿼리 해석 (QueryInterpreter)
```python
    # Stage 1: Query interpretation
    query_plan = self.query_interpreter.interpret(
        query=search_query,
        view=optimized_view,
        language=optimized_language,
        top_k=top_k,
    )
```
**설명**:
- `QueryInterpreter.interpret()`:
  1. 쿼리 텍스트를 임베딩 벡터로 변환
  2. 필터 조건 (view, language) 포함
- 반환: `QueryPlan` (query_text, query_embedding, filters, top_k)

#### 라인 168-169: 벡터 유사도 검색
```python
    # Stage 2: Vector similarity search
    search_results = self.search_engine.search(query_plan)
```
**설명**:
- `VectorSearchEngine.search()`:
  1. PGVector에서 코사인 유사도 검색
  2. 필터 조건 적용 (view, language)
  3. top_k개 결과 반환
- 반환: `List[SearchResult]` (fragment_id, content, similarity, metadata)

#### 라인 171-173: 중복 제거
```python
    # Optional: Deduplicate
    if deduplicate:
        search_results = self.grouper.deduplicate_by_content(search_results)
```
**설명**:
- 동일하거나 유사한 내용의 결과 제거
- 콘텐츠 해시 기반 중복 감지

#### 라인 175-179: 컨텍스트 확장
```python
    # Stage 3: Context expansion
    if expand_context:
        expanded_results = self.context_expander.expand(search_results)
    else:
        expanded_results = [ExpandedResult(result=r) for r in search_results]

    return expanded_results
```
**설명**:
- `ContextExpander.expand()`:
  1. 각 SearchResult의 `parent_id` (= concept_id)로 부모 문서 조회
  2. 부모 문서의 전체 콘텐츠를 컨텍스트로 추가
- 반환: `List[ExpandedResult]` (검색 결과 + 부모 컨텍스트)

### 5.2 SelfQueryRetriever 자동 필터 추출 원리

```python
# retrieval/self_query.py
def create_self_query_retriever(config, embeddings_client, llm, verbose):
    """
    LangChain SelfQueryRetriever 생성.

    동작 원리:
    1. 사용자 쿼리를 LLM에 전달
    2. LLM이 쿼리를 분석하여 메타데이터 필터 추출
    3. 추출된 필터로 PGVector 검색 실행
    """
```

**메타데이터 스키마 정의:**
```python
metadata_field_info = [
    AttributeInfo(
        name="view",
        description="Content type: text, code, image",
        type="string",
    ),
    AttributeInfo(
        name="lang",
        description="Programming language: python, javascript, etc.",
        type="string",
    ),
]
```

**예시 변환:**
| 사용자 쿼리 | 추출된 필터 |
|------------|-----------|
| "Python 리스트 컴프리헨션 코드" | `view="code"`, `lang="python"` |
| "JavaScript 함수 설명" | `view="text"`, `lang="javascript"` |
| "이미지 관련 내용" | `view="image"` |

### 5.3 컨텍스트 확장 메커니즘

```python
# retrieval/context.py
class ContextExpander:
    def expand(self, results: List[SearchResult]) -> List[ExpandedResult]:
        """
        검색 결과에 부모 문서 컨텍스트 추가.

        검색 대상 (Fragment) != 컨텍스트 제공자 (Concept)
        """
        expanded = []
        for result in results:
            # parent_id로 부모 문서 조회
            parent = self.parent_store.get_parent(result.parent_id)

            expanded.append(ExpandedResult(
                result=result,                    # 검색된 Fragment
                parent_content=parent.content,    # 부모 Concept의 전체 내용
                parent_metadata=parent.metadata,
            ))
        return expanded
```

**장점:**
- Fragment만 검색해도 전체 컨텍스트 (pre_text + code + post_text) 제공
- RAG 품질 향상: LLM이 더 완전한 정보로 응답 생성

---

## 6. RAG 생성 파이프라인 (Generation)

### 6.1 GenerationPipeline.generate() 흐름

**파일**: `generation/pipeline.py`

```python
def generate(
    self,
    query: str,
    results: List[ExpandedResult],
    conversation: Optional[Conversation] = None,
    optimized_query: Optional[str] = None,
) -> GeneratedResponse:
```

#### Stage 1: 컨텍스트 조립
```python
    # 검색 결과를 텍스트로 변환
    context = PromptTemplate.build_context(results)
```

`build_context()` 내부:
```python
def build_context(results: List[ExpandedResult]) -> str:
    parts = []
    for i, r in enumerate(results, 1):
        parts.append(f"[{i}] {r.parent_content or r.result.content}")
    return "\n\n".join(parts)
```

#### Stage 2: 프롬프트 구성
```python
    prompt = PromptTemplate.format_rag_prompt(query, context)

    # 대화 기록이 있으면 추가
    if conversation and conversation.turns:
        history = conversation.get_history_context()
        prompt = f"=== Previous Conversation ===\n{history}\n\n=== Current Question ===\n{prompt}"
```

#### Stage 3: LLM 생성
```python
    llm_response = self.llm_client.generate(
        prompt=prompt,
        system_prompt=PromptTemplate.SYSTEM_PROMPT,
        temperature=self.temperature,
        max_tokens=self.max_tokens,
    )
```

#### Stage 4: 응답 반환
```python
    return GeneratedResponse(
        query=query,
        answer=llm_response.content,
        sources=results,              # 참조한 검색 결과
        model=llm_response.model,
        optimized_query=optimized_query,
    )
```

---

## 7. 주요 클래스 참조표

### 7.1 패키지별 핵심 클래스

| 패키지 | 클래스 | 역할 | 주요 메서드 |
|--------|-------|------|-----------|
| **api/use_cases** | `IngestUseCase` | 수집 오케스트레이션 | `execute(file_paths)` |
| | `SearchUseCase` | 검색 오케스트레이션 | `execute(query, ...)` |
| **domain** | `Document` | 문서 엔티티 | `validate()` |
| | `Concept` | 의미 단위 엔티티 | `validate()` |
| | `Fragment` | 검색 대상 엔티티 | `validate()`, `compute_doc_id()` |
| | `View` | 뷰 타입 열거형 | TEXT, CODE, IMAGE |
| **ingestion** | `SegmentUnitizer` | 세그먼트 그룹화 | `unitize(segments)` |
| | `ConceptBuilder` | 엔티티 생성 | `build(unitized, doc, ...)` |
| | `MarkdownParser` | Markdown 파싱 | `parse(path)`, `parse_text(raw)` |
| | `PyMuPdfParser` | PDF 파싱 | `parse(path)` |
| | `OcrParser` | 텍스트 파싱 | `parse(path)` |
| **embedding** | `EmbeddingValidator` | 임베딩 자격 검증 | `is_eligible(fragment)` |
| | `EmbeddingProviderFactory` | 임베딩 클라이언트 생성 | `create(config)` |
| **retrieval** | `RetrievalPipeline` | 검색 오케스트레이션 | `retrieve(query, ...)` |
| | `QueryInterpreter` | 쿼리 해석 | `interpret(query, ...)` |
| | `VectorSearchEngine` | 벡터 검색 | `search(query_plan)` |
| | `ContextExpander` | 컨텍스트 확장 | `expand(results)` |
| **generation** | `GenerationPipeline` | RAG 생성 | `generate(query, results, ...)` |
| | `LLMClient` | LLM 호출 | `generate(prompt, ...)` |
| **storage** | `VectorStoreWriter` | PGVector 저장 | `upsert_batch(store, docs)` |
| | `ParentDocumentStore` | 부모 문서 저장 | `upsert_parent(id, content, ...)` |
| | `DocumentRepository` | Document CRUD | `save(doc)`, `find(id)` |
| | `ConceptRepository` | Concept CRUD | `save(concept)`, `find(id)` |
| | `FragmentRepository` | Fragment CRUD | `save(fragment)`, `find(id)` |

### 7.2 데이터 흐름 요약

```
파일 경로
    │
    ▼ (파서)
List[RawSegment]
    │
    ▼ (SegmentUnitizer)
List[UnitizedSegment]
    │
    ▼ (ConceptBuilder)
List[Concept] (각각 List[Fragment] 포함)
    │
    ▼ (EmbeddingValidator 필터링)
    │
    ▼ (LangChainAdapter 변환)
List[LangChain Document]
    │
    ▼ (VectorStoreWriter)
PGVector 저장
```

---

## 8. 설정 가이드

### 8.1 환경변수 (.env)

#### 필수 설정
```env
# 데이터베이스 연결
PG_CONN=postgresql+psycopg://langchain:langchain@localhost:5432/vectordb

# 임베딩 API (택1)
VOYAGE_API_KEY=your-voyage-api-key
# 또는
GOOGLE_API_KEY=your-google-api-key

# 컬렉션 이름
COLLECTION_NAME=langchain_book_ocr
```

#### 임베딩 설정
```env
# 임베딩 제공자: voyage 또는 gemini
EMBEDDING_PROVIDER=voyage

# 모델 설정
EMBEDDING_MODEL=voyage-3
GEMINI_EMBED_MODEL=text-embedding-004

# 임베딩 차원 (모델에 맞게 설정)
EMBEDDING_DIM=1024  # Voyage: 1024, Gemini: 768

# API 비율 제한
RATE_LIMIT_RPM=60
```

#### PDF 파싱 설정 (PyMuPDF)
```env
# OCR 설정
ENABLE_AUTO_OCR=false    # 텍스트 희소 시 자동 OCR
FORCE_OCR=false          # 항상 OCR 실행
ENABLE_IMAGE_OCR=true    # 이미지 블록 OCR (Gemini Vision)
GEMINI_OCR_MODEL=gemini-2.0-flash-exp
```

#### 의미 단위화 설정
```env
# 부모 문서 최대 길이 (RAG 컨텍스트)
PARENT_CONTEXT_LIMIT=8000

# 텍스트 의미 단위 최소 길이
TEXT_UNIT_THRESHOLD=500
```

#### 검색 튜닝
```env
# HNSW 인덱스 파라미터
HNSW_EF_SEARCH=100
HNSW_EF_CONSTRUCTION=200
```

### 8.2 설정 옵션별 영향

| 설정 | 값 | 영향 |
|------|-----|-----|
| `EMBEDDING_DIM` | 768 / 1024 | 벡터 차원 - 모델과 일치해야 함 |
| `RATE_LIMIT_RPM` | 0 / 60 | 0=무제한, 60=분당 60요청 |
| `PARENT_CONTEXT_LIMIT` | 4000 / 8000 | RAG 컨텍스트 길이 - 클수록 정보 많음 |
| `TEXT_UNIT_THRESHOLD` | 300 / 500 | 텍스트 의미 단위 최소 크기 |
| `ENABLE_AUTO_OCR` | true / false | PDF 텍스트 희소 시 자동 OCR |
| `FORCE_OCR` | true / false | 모든 PDF OCR 강제 실행 |

---

## 9. 디버깅 팁

### 9.1 로그 메시지 해석

```
[ingest] Processing: test.pdf              # 파일 처리 시작
[ingest] Parsed 45 segments                # 파싱 완료, 45개 세그먼트
[ingest] Cleaning up existing data...      # 기존 데이터 삭제 (재수집)
[ingest] Created 12 semantic units         # 의미 단위 12개 생성
[ingest] Built 13 concepts                 # Concept 13개 (12 + 1 고아)
[skip] Fragment filtered: ...              # 임베딩 제외된 Fragment
[upsert_batch] storing batch 1/3 (64 docs) # 벡터 저장 배치 진행
[rate-limit] retry 1/6 in 30s              # API 비율 제한, 재시도
[self_query] Retrieved 10 results          # SelfQueryRetriever 결과
```

### 9.2 일반적인 문제 해결

#### 문제: "Document missing doc_id in metadata"
**원인**: Fragment가 `compute_doc_id()` 없이 저장 시도
**해결**: `LangChainAdapter.fragment_to_document()` 호출 시 `doc_id` 전달 확인

#### 문제: "HIER-003: Must belong to a Concept"
**원인**: Fragment 생성 시 `concept_id` 누락
**해결**: `ConceptBuilder._create_fragment()`에서 `concept_id` 전달 확인

#### 문제: 비율 제한 에러 반복
**원인**: API 요청 과다
**해결**:
1. `RATE_LIMIT_RPM` 낮추기 (예: 30)
2. `max_items_per_request` 줄이기

#### 문제: 검색 결과 품질 저하
**원인**: 의미 단위 분할 부적절 또는 컨텍스트 부족
**해결**:
1. `TEXT_UNIT_THRESHOLD` 조정
2. `PARENT_CONTEXT_LIMIT` 늘리기
3. `expand_context=True` 확인

#### 문제: PDF 텍스트 추출 실패
**원인**: 스캔된 PDF (이미지 기반)
**해결**:
1. `--force-ocr` 플래그 사용
2. `ENABLE_AUTO_OCR=true` 설정

### 9.3 디버그 모드 실행

```bash
# 드라이런 (파싱만, DB 저장 안함)
python -m api.cli ingest test.pdf --dry-run

# 상세 로그
python -m api.cli ingest test.pdf --verbose

# 특정 Concept 확인
python -c "
from storage import ConceptRepository
from shared.config import load_config
repo = ConceptRepository(load_config())
concept = repo.find('concept_id_here')
print(concept)
"
```

---

## 부록: 용어 정리

| 용어 | 설명 |
|------|------|
| **RawSegment** | 파싱 직후의 원시 세그먼트 (종류, 내용, 언어, 순서) |
| **UnitizedSegment** | 의미 단위가 할당된 세그먼트 (unit_id, role 추가) |
| **Semantic Unit** | 관련 콘텐츠의 논리적 그룹 (설명 + 코드 등) |
| **View** | 콘텐츠 타입 (text, code, image 등) |
| **Parent Document** | Concept의 전체 콘텐츠 (컨텍스트 제공용) |
| **doc_id** | 임베딩의 결정론적 ID (중복 방지용) |
| **CASCADE 삭제** | Document 삭제 시 관련 Concept, Fragment, Embedding 모두 삭제 |
| **SelfQueryRetriever** | 자연어 쿼리에서 메타데이터 필터 자동 추출 |

---

> **문서 버전**: 1.0
> **최종 수정**: 2025-01-09
> **관련 문서**: `docs/ARCHITECTURE.md`, `docs/DOMAIN_RULES.md`, `docs/PACKAGE_RULES.md`
