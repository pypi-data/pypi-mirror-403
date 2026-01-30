# 임베딩 파이프라인 개요

이 문서는 신규 파이프라인 기준으로 **프래그먼트 → 임베딩 생성 → 저장 → 검색**까지 임베딩 레이어가 수행하는 책임을 요약한다. 레거시 `app/` 흐름은 제외한다.

## 책임 범위
- 입력: `ingestion/`이 만든 `domain.Fragment` 목록
- 검증: `embedding/validators.py`의 `EmbeddingValidator`
- 식별자: `embedding/doc_id.py`의 결정적 `doc_id` 생성
- 생성: `embedding/provider.py`에서 프로바이더 클라이언트 생성
- 출력: pgvector 테이블(`langchain_pg_embedding`)에 벡터 + 메타데이터 저장 (`storage/` 레이어가 담당)

## 흐름(요약)
1) **프래그먼트 수신**: `api.cli.ingest`에서 정규화된 Fragment 리스트를 넘겨받음  
2) **적격성 검사** (`EmbeddingValidator.is_eligible`)  
   - 최소 길이: 10자 미만 거부 (FRAG-LEN-001)  
   - 보일러플레이트/페이지 넘버/저작권 패턴 필터 (EMBED-BAN-003/004)  
   - 순수 참조 텍스트 필터 (EMBED-BAN-006)  
3) **doc_id 계산** (`compute_doc_id`)  
   - 해시 입력: `parent_id(concept_id) + view + lang + content`  
   - 출력 포맷: `doc:{32-hex}` (EMBED-ID-002)  
4) **임베딩 생성**  
   - 클라이언트: `EmbeddingProviderFactory.create` (현재 `openai`만 지원, `langchain_openai.OpenAIEmbeddings`)  
   - 구성: `shared.config.EmbeddingConfig`(`embedding_provider`, `embedding_model`, `embedding_dim`)  
   - 차원 확인: `validate_embedding_dimension`가 샘플 호출로 기대 차원과 불일치 시 워닝  
5) **저장**  
   - `storage/` 리포지토리에서 pgvector `langchain_pg_embedding` 테이블에 벡터/메타데이터 업서트  
   - 검색을 위해 HNSW 인덱스 사용 (테이블 정의는 `docs/TECHNICAL_GUIDE.md` 참조)
6) **검색 시 재사용**  
   - `retrieval/`에서 동일 테이블을 코사인 유사도/HNSW로 조회, `view`/`lang` 등의 메타데이터 필터링 적용

## 주요 규칙 & 체크리스트
- **금지**: 파일 파싱(ingestion), 검색 로직(retrieval), 스키마 관리(storage) 수행 금지 (`PKG-EMB-BAN-*`)  
- **의존성**: `domain`, `shared`, `storage` 인터페이스만 import 허용 (`DEP-EMB-ALLOW-*`)  
- **중복/결정성**: 동일 `parent_id+view+lang+content`는 동일 `doc_id`를 생성해야 함 (중복 임베딩 방지)  
- **언어 지원**: 한국어/영어 패턴 모두 필터링 지원

## 실행 진입점
- **적재**: `python -m api.cli.ingest docs/*.md pdf_data/*.pdf` → 임베딩 생성·저장까지 수행
- **검색**: `python -m api.cli.search "query text" --view text --top-k 5` → 저장된 임베딩 재사용

## 빠른 참조 파일
- `embedding/validators.py` — 적격성 검사 규칙
- `embedding/doc_id.py` — 결정적 `doc_id` 해시 로직
- `embedding/provider.py` — 임베딩 클라이언트 생성 및 차원 검증
- `shared/config.py` — 임베딩 설정 스키마 (`EmbeddingConfig`)
