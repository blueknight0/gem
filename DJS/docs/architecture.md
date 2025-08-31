# DJS 시스템 구조

본 문서는 DJS(Data-based Junction Search) 서비스의 전체 구조를 요약합니다.

## 개요
- 백엔드: FastAPI 기반 모놀리식 앱(`backend/`), JWT 인증, SQLAlchemy ORM
- 데이터베이스: SQLite/PostgreSQL(환경에 따라 `DATABASE_URL`로 전환)
- 프론트: FastAPI에서 서빙하는 HTML/JS(로그인 모달/워크플로우 UI)
- 배포: Docker(Gunicorn+Uvicorn), Nginx 리버스 프록시, docker-compose

## 전체 아키텍처
```mermaid
graph TD
    U[사용자 브라우저] --> N[Nginx (80)]
    N --> A[FastAPI (Gunicorn+Uvicorn) :8000]
    A -->|/api/auth| AUTH[Auth Router]
    A -->|/api/search| SEARCH[Search Router]
    A -->|/api/embedding| EMBED[Embedding Router]
    A -->|/api/extractor| EXTR[Extractor Router]
    A -->|/api/rounds| ROUNDS[Rounds Router]
    A -->|/api/review| REVIEW[Review Router]
    A -->|/api/visualization| VIZ[Visualization Router]
    A -->|/api/scheduler| SCHED[Scheduler Router]

    subgraph Services
        NS[Naver Search]
        ES[Embedding Service]
        LE[LLM Extractor]
        RM[Round Manager]
        RSV[Review Service]
        NV[Network Visualizer]
        SS[Scheduler Service]
    end

    AUTH --> DB[(PostgreSQL/SQLite)]
    SEARCH --> NS
    EMBED --> ES
    EXTR --> LE
    ROUNDS --> RM
    REVIEW --> RSV
    VIZ --> NV
    SCHED --> SS

    ES --> DB
    LE --> DB
    RM --> DB
    RSV --> DB
    NV --> DB
    SS --> DB
```

## 디렉터리 구조(핵심)
- `backend/main.py`: 앱 부트스트랩, 라우터 포함, 정적 HTML/JS 서빙(로그인/워크플로우 모달)
- `backend/api/`: 기능별 API 라우터
  - `auth.py`: 회원가입(`/register`), 로그인(`/token`), 내정보(`/me`), 보호 예시(`/protected`)
  - `search.py`, `embedding.py`, `extractor.py`, `rounds.py`, `review.py`, `visualization.py`, `scheduler.py`
- `backend/services/`: 비즈니스 로직 (네이버 검색, 임베딩, LLM 추출, 라운드/리뷰 관리, 시각화, 스케줄러)
- `backend/models/`: ORM 모델/스키마
  - 주요 테이블: `User`, `Company`, `University`, `Professor`, `News(embedding_vector: LargeBinary)`, `Round`, `Relation`, `RelationHistory`, `ScheduledJob`, `SystemConfig`, `RelationType`
- `backend/core/database.py`: DB 연결(`DATABASE_URL` ENV 우선, SQLite 시 `check_same_thread=False` 설정), 세션/베이스
- `backend/core/init_db.py`: 테이블 생성 및 `config.yaml`→`SystemConfig` 로드, 기본값 초기화, 샘플 데이터
- `backend/utils/security.py`: 비밀번호 해싱(bcrypt), JWT 생성/검증
- `scripts/migrate_sqlite_to_postgres.py`: SQLite→Postgres 데이터 복제(ORM 레벨)

## 인증(로그인)
- 비밀번호 해싱: passlib[bcrypt]
- 토큰: JWT(기본 HS256), 페이로드 `sub = 사용자 이메일`, 만료 기본 1440분
- 설정 우선순위: ENV(`JWT_SECRET`, `JWT_ALGORITHM`, `JWT_EXPIRE_MINUTES`) > `SystemConfig` > 기본값
- 프론트: `main.py`의 HTML/JS에서 로그인 모달 제공, `localStorage`에 토큰 저장, 전역 `fetch`에 `Authorization: Bearer <token>` 자동 주입

```mermaid
graph LR
    UI[로그인 모달] -->|username/password| AUTH[/api/auth/token]
    AUTH -->|JWT access_token| UI
    UI -->|Authorization: Bearer| PROT[/api/auth/protected]
```

## 설정과 환경변수
- 파일: `config.yaml` (또는 `config.example.yaml` 참고)
  - `gemini`, `naver`, `embedding`, `search`, `scheduler`, `logging`, `server`, `jwt`
- DB 연결: `DATABASE_URL` (예: `postgresql+psycopg2://user:pass@host:5432/db`)
- JWT: `JWT_SECRET`, `JWT_ALGORITHM`, `JWT_EXPIRE_MINUTES`

## 배포
- `Dockerfile.backend`: Python 3.11-slim, `requirements.txt` 설치, `gunicorn` 실행
- `Dockerfile.frontend` + `nginx.conf`: Nginx 리버스 프록시(80→backend:8000)
- `docker-compose.yml`:
  - `db`(Postgres 16), `backend`, `nginx` 서비스
  - ENV로 DB/JWT 설정 주입, `./data`, `./logs` 볼륨 마운트

```mermaid
graph TD
    C[Client] --> N[Nginx]
    N --> B[Backend (Gunicorn/Uvicorn)]
    B --> P[(PostgreSQL)]
```

## 데이터 흐름(요약)
1. 기업 조사 시작 → `rounds` 라우터가 라운드 생성 → 뉴스 수집(`search`/네이버 API) → 임베딩/중복 제거(`embedding`) → LLM 관계 추출(`extractor`) → `relations` 저장
2. 검토/승인 → `review` 라우터에서 관계 상태 변경 및 히스토리 기록
3. 시각화 → `visualization` 라우터에서 네트워크 데이터 제공

## 마이그레이션
- Postgres 실행: `docker compose up -d db`
- 데이터 이전: `scripts/migrate_sqlite_to_postgres.py` 실행(환경변수 `SQLITE_URL`, `POSTGRES_URL`)
- 앱의 `DATABASE_URL`을 Postgres로 지정 후 재시작

## 로그/디렉터리
- 데이터: `data/embeddings`, `data/raw_news`, `data/processed_relations`
- 로그: `logs/` (Nginx/Backend 로그는 컨테이너 로그로 확인 가능)

## 보안/운영 참고
- 프로덕션에서는 반드시 강력한 `JWT_SECRET` 사용, HTTPS 적용(L4/L7에서 TLS 종단, 예: Cloud, LB, 또는 Nginx+Certbot)
- SQLite는 단일/개발용, 운영은 Postgres 권장
- 민감정보는 코드가 아닌 환경변수로 주입

