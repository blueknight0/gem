-- DJS (Data-based Junction Search) Database Schema
-- 오픈이노베이션 연구협력 네트워크 분석 시스템

-- 기업 정보 테이블
CREATE TABLE companies (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    representative_name VARCHAR(100),
    industry VARCHAR(100),
    website VARCHAR(255),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 대학 정보 테이블
CREATE TABLE universities (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    website VARCHAR(255),
    location VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 교수 정보 테이블
CREATE TABLE professors (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    university_id INTEGER,
    department VARCHAR(100),
    email VARCHAR(255),
    research_field VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (university_id) REFERENCES universities(id) ON DELETE CASCADE
);

-- 뉴스 기사 테이블
CREATE TABLE news (
    id INTEGER PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    url VARCHAR(1000) NOT NULL UNIQUE,
    source VARCHAR(100),
    published_date DATE,
    search_keyword VARCHAR(255),
    embedding_vector BLOB, -- 텍스트 임베딩 벡터 저장
    is_duplicate BOOLEAN DEFAULT FALSE,
    duplicate_of INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (duplicate_of) REFERENCES news(id) ON DELETE SET NULL
);

-- 검색 라운드 테이블
CREATE TABLE rounds (
    id INTEGER PRIMARY KEY,
    round_number INTEGER NOT NULL,
    target_company VARCHAR(255) NOT NULL,
    search_date DATE NOT NULL,
    total_news_found INTEGER DEFAULT 0,
    total_relations_extracted INTEGER DEFAULT 0,
    status VARCHAR(50) DEFAULT 'pending', -- pending, in_progress, completed, approved
    approved_by VARCHAR(100),
    approved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 협력 관계 테이블
CREATE TABLE relations (
    id INTEGER PRIMARY KEY,
    round_id INTEGER NOT NULL,
    news_id INTEGER NOT NULL,
    company_a_id INTEGER,
    company_b_id INTEGER,
    university_id INTEGER,
    professor_id INTEGER,
    relation_type VARCHAR(50) NOT NULL, -- MOU, 공동연구, 투자, M&A, 기술이전 등
    relation_content TEXT NOT NULL,
    start_date DATE,
    end_date DATE,
    status VARCHAR(50) DEFAULT 'extracted', -- extracted, approved, rejected, modified
    confidence_score REAL, -- LLM 추출 신뢰도 점수 (0.0 ~ 1.0)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (round_id) REFERENCES rounds(id) ON DELETE CASCADE,
    FOREIGN KEY (news_id) REFERENCES news(id) ON DELETE CASCADE,
    FOREIGN KEY (company_a_id) REFERENCES companies(id) ON DELETE CASCADE,
    FOREIGN KEY (company_b_id) REFERENCES companies(id) ON DELETE CASCADE,
    FOREIGN KEY (university_id) REFERENCES universities(id) ON DELETE CASCADE,
    FOREIGN KEY (professor_id) REFERENCES professors(id) ON DELETE CASCADE
);

-- 관계 변경 히스토리 테이블
CREATE TABLE relation_history (
    id INTEGER PRIMARY KEY,
    relation_id INTEGER NOT NULL,
    change_type VARCHAR(50) NOT NULL, -- created, modified, approved, rejected, deleted
    old_relation_type VARCHAR(50),
    new_relation_type VARCHAR(50),
    old_content TEXT,
    new_content TEXT,
    old_status VARCHAR(50),
    new_status VARCHAR(50),
    changed_by VARCHAR(100),
    change_reason TEXT,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (relation_id) REFERENCES relations(id) ON DELETE CASCADE
);

-- 시스템 설정 테이블
CREATE TABLE system_config (
    id INTEGER PRIMARY KEY,
    config_key VARCHAR(100) NOT NULL UNIQUE,
    config_value TEXT,
    config_type VARCHAR(50), -- string, integer, boolean, json
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스 생성
CREATE INDEX idx_news_published_date ON news(published_date);
CREATE INDEX idx_news_search_keyword ON news(search_keyword);
CREATE INDEX idx_news_is_duplicate ON news(is_duplicate);
CREATE INDEX idx_relations_round_id ON relations(round_id);
CREATE INDEX idx_relations_company_a ON relations(company_a_id);
CREATE INDEX idx_relations_company_b ON relations(company_b_id);
CREATE INDEX idx_relations_university ON relations(university_id);
CREATE INDEX idx_relations_type ON relations(relation_type);
CREATE INDEX idx_relations_status ON relations(status);
CREATE INDEX idx_rounds_target_company ON rounds(target_company);
CREATE INDEX idx_rounds_status ON rounds(status);
CREATE INDEX idx_relation_history_relation_id ON relation_history(relation_id);
CREATE INDEX idx_companies_name ON companies(name);
CREATE INDEX idx_universities_name ON universities(name);
CREATE INDEX idx_professors_university ON professors(university_id);

-- 기본 시스템 설정 데이터
INSERT INTO system_config (config_key, config_value, config_type, description) VALUES
('naver_api_client_id', '', 'string', '네이버 검색 API Client ID'),
('naver_api_client_secret', '', 'string', '네이버 검색 API Client Secret'),
('gemini_api_key', '', 'string', 'Gemini API Key'),
('embedding_model', 'models/gemini-embedding-001', 'string', 'Gemini 임베딩 모델'),
('llm_model', 'gemini-2.5-flash-lite', 'string', 'Gemini LLM 모델'),
('similarity_threshold', '0.85', 'string', '중복 판별 유사도 임계값'),
('max_news_per_search', '100', 'integer', '검색당 최대 뉴스 수'),
('scheduler_interval_days', '7', 'integer', '스케줄러 실행 간격 (일)'),
('auto_approve_threshold', '0.8', 'string', '자동 승인 신뢰도 임계값');

-- 기본 협력 관계 타입
CREATE TABLE relation_types (
    id INTEGER PRIMARY KEY,
    type_code VARCHAR(50) NOT NULL UNIQUE,
    type_name VARCHAR(100) NOT NULL,
    description TEXT,
    color VARCHAR(20), -- 시각화 색상
    icon VARCHAR(50), -- 아이콘
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 스케줄된 작업 테이블
CREATE TABLE scheduled_jobs (
    id INTEGER PRIMARY KEY,
    job_id VARCHAR(100) NOT NULL UNIQUE,
    job_type VARCHAR(50) NOT NULL, -- investigation, news_update, relation_extraction, duplicate_detection
    company_name VARCHAR(255),
    trigger_expression VARCHAR(255) NOT NULL,
    max_rounds INTEGER DEFAULT 3,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스 생성
CREATE INDEX idx_scheduled_jobs_job_id ON scheduled_jobs(job_id);
CREATE INDEX idx_scheduled_jobs_type ON scheduled_jobs(job_type);
CREATE INDEX idx_scheduled_jobs_active ON scheduled_jobs(is_active);

INSERT INTO relation_types (type_code, type_name, description, color, icon) VALUES
('MOU', 'MOU 체결', '양해각서 체결', '#4CAF50', 'handshake'),
('JOINT_RESEARCH', '공동연구', '공동 연구 프로젝트', '#2196F3', 'flask'),
('INVESTMENT', '투자', '투자 유치 또는 투자', '#FF9800', 'trending-up'),
('MERGER', 'M&A', '인수합병', '#F44336', 'merge'),
('TECHNOLOGY_TRANSFER', '기술이전', '기술 이전 및 라이선싱', '#9C27B0', 'transfer'),
('PARTNERSHIP', '파트너십', '전략적 파트너십', '#00BCD4', 'users'),
('COLLABORATION', '협업', '일반 협업 관계', '#607D8B', 'link'),
('FUNDING', '펀딩', '연구비 지원', '#4CAF50', 'dollar-sign');
