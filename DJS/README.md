# 🎯 DJS (Data-based Junction Search)

**오픈이노베이션 연구협력 네트워크 분석 시스템**

DJS는 네이버 검색 API와 Gemini-2.5-flash-lite를 활용하여 기업의 오픈이노베이션 관련 뉴스를 검색하고, 협력 관계를 자동으로 추출하여 네트워크 시각화하는 시스템입니다.

## 🚀 주요 기능

- **🔍 뉴스 검색**: 네이버 검색 API를 활용한 오픈이노베이션 뉴스 검색
- **🧠 중복 제거**: Gemini 임베딩을 활용한 뉴스 중복 자동 제거
- **🤖 관계 추출**: Gemini-2.5-flash-lite 기반 협력 관계 자동 추출 및 분류
- **🔄 라운드 기반 조사**: 기업 조사 라운드 관리 및 재귀적 검색
- **✅ Human-in-the-loop 검토**: 추출된 관계 검토 및 수정 기능
- **📊 네트워크 시각화**: 기업 간 협력 관계 네트워크 시각화
- **📈 히스토리 관리**: 관계 변경 추적 및 버전 관리
- **⏰ 스케줄러**: 자동화된 조사 스케줄링

## 🏗️ 시스템 아키텍처

```
DJS System Architecture
├── Frontend (React/Vue.js) - 사용자 인터페이스
├── Backend (FastAPI) - API 서버
│   ├── Search API - 뉴스 검색
│   ├── Embedding API - 중복 제거
│   ├── Extractor API - 관계 추출
│   └── Database - SQLite/PostgreSQL
└── Data Processing
    ├── Naver Search API - 뉴스 수집
    ├── Sentence Transformers - 텍스트 임베딩
    ├── Gemini-2.5-flash-lite - 관계 추출
    └── NetworkX - 그래프 분석
```

## 📋 지원하는 협력 관계 유형

- **MOU**: 업무협약, 양해각서 체결
- **공동연구**: 공동 연구 프로젝트
- **투자**: 투자 유치 또는 투자
- **M&A**: 인수합병
- **기술이전**: 기술 이전 및 라이선싱
- **파트너십**: 전략적 파트너십
- **협업**: 일반 협업 관계
- **펀딩**: 연구비 지원

## 🛠️ 설치 및 실행

### Windows 배치 파일 사용 (권장)

```bash
# 1. 초기 설정 (최초 1회만 실행)
setup.bat

# 2. 데이터베이스 초기화 (최초 1회만 실행)
init_db.bat

# 3. 서버 실행
run_server.bat

# 4. 개발 모드 (코드 변경시 자동 재시작)
run_dev.bat
```

### 수동 설치 (고급 사용자용)

#### 1. 환경 설정

```bash
# 리포지토리 클론
git clone https://github.com/your-repo/djs.git
cd djs

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

#### 2. 설정 파일 준비

```bash
# 설정 파일 복사
cp config.example.yaml config.yaml

# config.yaml 파일을 열어 다음 정보를 설정:
# - Gemini API Key
# - 네이버 검색 API Client ID/Secret
```

### 3. 데이터베이스 초기화

```bash
# 데이터베이스 및 테이블 생성
python -c "from backend.core.database import create_tables; create_tables()"
```

### 4. 서버 실행

```bash
# 개발 서버 실행
python backend/main.py

# 또는 uvicorn으로 실행
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

서버가 실행되면 다음 URL에서 접근 가능:
- **메인 페이지**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs
- **대안 API 문서**: http://localhost:8000/redoc

## 📖 사용 방법

### 1. 뉴스 검색

```python
import requests

# 기업 뉴스 검색
response = requests.post(
    "http://localhost:8000/api/search/news",
    params={
        "company_name": "삼성전자",
        "max_results": 50,
        "save_to_db": True
    }
)
```

### 2. 관계 추출

```python
# 뉴스에서 관계 추출
response = requests.post(
    "http://localhost:8000/api/extractor/extract-from-news",
    params={
        "news_ids": [1, 2, 3],
        "save_to_db": True
    }
)
```

### 3. 중복 제거

```python
# 뉴스 중복 처리
response = requests.post(
    "http://localhost:8000/api/embedding/deduplicate",
    params={
        "batch_size": 100
    }
)
```

## 🔧 API 엔드포인트

### 뉴스 검색 API
- `POST /api/search/news` - 기업 뉴스 검색
- `GET /api/search/news` - 저장된 뉴스 목록 조회
- `PUT /api/search/credentials` - API 키 설정

### 임베딩 API
- `POST /api/embedding/deduplicate` - 중복 제거
- `GET /api/embedding/similarity/{id1}/{id2}` - 뉴스 유사도 계산
- `POST /api/embedding/generate-embeddings` - 임베딩 생성

### 관계 추출 API
- `POST /api/extractor/extract-from-news` - 뉴스에서 관계 추출
- `POST /api/extractor/extract-single` - 단일 텍스트에서 관계 추출
- `PUT /api/extractor/api-key` - OpenAI API 키 설정

### 라운드 조사 API
- `POST /api/rounds/investigate` - 기업 조사 시작
- `GET /api/rounds/status/{company}` - 조사 상태 조회
- `PUT /api/rounds/{round_id}/approve` - 라운드 승인
- `PUT /api/rounds/{round_id}/reject` - 라운드 거부

### 관계 검토 API
- `GET /api/review/relations` - 검토할 관계 조회
- `PUT /api/review/relation/{id}` - 관계 수정
- `PUT /api/review/relation/{id}/approve` - 관계 승인
- `PUT /api/review/relation/{id}/reject` - 관계 거부
- `POST /api/review/bulk-update` - 일괄 수정

### 네트워크 시각화 API
- `GET /api/visualization/network` - 네트워크 데이터 조회
- `GET /api/visualization/network/statistics` - 네트워크 통계
- `GET /api/visualization/network/export` - 네트워크 데이터 내보내기
- `GET /api/visualization/network/evolution` - 시간별 네트워크 진화

### 스케줄러 API
- `POST /api/scheduler/investigation` - 기업 조사 작업 스케줄링
- `POST /api/scheduler/news-update` - 뉴스 업데이트 작업 스케줄링
- `GET /api/scheduler/jobs` - 스케줄된 작업 목록
- `DELETE /api/scheduler/jobs/{id}` - 작업 제거

## 🗃️ 데이터베이스 스키마

### 주요 테이블
- **companies**: 기업 정보
- **universities**: 대학 정보
- **professors**: 교수 정보
- **news**: 뉴스 기사
- **relations**: 협력 관계
- **rounds**: 검색 라운드
- **relation_history**: 관계 변경 히스토리
- **scheduled_jobs**: 스케줄된 작업

## ⚙️ 설정 옵션

### 시스템 설정 (config.yaml)
```yaml
openai:
  api_key: "your-api-key"
  model: "gemini-2.5-flash-lite"
  temperature: 0.3

naver:
  client_id: "your-client-id"
  client_secret: "your-secret"

embedding:
  similarity_threshold: 0.85

search:
  max_news_per_search: 100
```

## 🔍 모니터링 및 로깅

시스템은 다음과 같은 로그를 제공:
- 뉴스 검색 결과
- 관계 추출 진행상황
- 중복 제거 통계
- API 호출 기록

로그 파일: `logs/djs.log`

## 🚀 배포

### Docker를 사용한 배포

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 프로덕션 배포

```bash
# Gunicorn을 사용한 배포
pip install gunicorn
gunicorn backend.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

## 🤝 기여하기

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 라이선스

이 프로젝트는 MIT 라이선스 하에 있습니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 📞 문의

- **이메일**: your-email@example.com
- **GitHub Issues**: 버그 리포트 및 기능 요청

## 🔄 업데이트 내역

### v1.0.0 (2024-01-XX)
- 초기 버전 출시
- 기본 뉴스 검색 기능
- LLM 기반 관계 추출
- 텍스트 임베딩 중복 제거
- FastAPI 기반 REST API

---

**DJS** - 데이터 기반 혁신 네트워크 탐색 시스템

## 문서
- 시스템 구조: [docs/architecture.md](docs/architecture.md)

## 배포 (Docker)

### 1) 환경 변수
- DATABASE_URL: 예) postgresql+psycopg2://user:pass@host/db
- JWT_SECRET: 프로덕션 시 반드시 안전한 값으로 교체
- JWT_ALGORITHM: 기본 HS256
- JWT_EXPIRE_MINUTES: 기본 1440(분)

Windows PowerShell 예시:
```powershell
$env:DATABASE_URL="sqlite:///./data/djs.db"
$env:JWT_SECRET="CHANGE_ME_DEV_SECRET"
$env:JWT_ALGORITHM="HS256"
$env:JWT_EXPIRE_MINUTES="1440"
```

### 2) 컨테이너 빌드/실행
```bash
# 루트에서 실행
docker compose build
docker compose up -d
```
- 브라우저에서 http://localhost 확인
- Nginx(80) → backend(8000) 프록시

### 3) 로그 확인
```bash
docker compose logs -f backend
```

### 4) 종료
```bash
docker compose down
```

## 데이터베이스(PostgreSQL) 전환

### 1) docker-compose로 Postgres 함께 실행
```bash
docker compose up -d db
```
- 기본 접속: postgresql+psycopg2://djs:djs_pw@localhost:5432/djs
- 애플리케이션은 `DATABASE_URL` 환경변수로 연결(미설정 시 compose 기본값 사용)

### 2) 기존 SQLite 데이터 마이그레이션
```bash
# 환경변수 설정 (필요 시)
$env:SQLITE_URL="sqlite:///./data/djs.db"
$env:POSTGRES_URL="postgresql+psycopg2://djs:djs_pw@localhost:5432/djs"

venv\Scripts\python.exe scripts/migrate_sqlite_to_postgres.py
```
- 완료 후 `DATABASE_URL`을 Postgres로 지정하고 서버/컨테이너를 재시작