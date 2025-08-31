#!/usr/bin/env python3
"""데이터베이스 생성 스크립트"""

import sqlite3
import os

# 데이터베이스 파일 경로
db_path = "data/djs.db"

# 데이터베이스 디렉토리가 없으면 생성
os.makedirs("data", exist_ok=True)

try:
    # 데이터베이스 연결
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 기본 테이블 생성
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(255) NOT NULL UNIQUE,
            representative_name VARCHAR(100),
            industry VARCHAR(100),
            website VARCHAR(255),
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title VARCHAR(500) NOT NULL,
            content TEXT NOT NULL,
            url VARCHAR(1000) NOT NULL UNIQUE,
            source VARCHAR(100),
            published_date DATE,
            search_keyword VARCHAR(255),
            embedding_vector BLOB,
            is_duplicate BOOLEAN DEFAULT FALSE,
            duplicate_of INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS relations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            news_id INTEGER NOT NULL,
            company_a_id INTEGER,
            company_b_id INTEGER,
            relation_type VARCHAR(50) NOT NULL,
            relation_content TEXT NOT NULL,
            start_date DATE,
            end_date DATE,
            status VARCHAR(50) DEFAULT 'extracted',
            confidence_score DECIMAL(3,2),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (news_id) REFERENCES news(id),
            FOREIGN KEY (company_a_id) REFERENCES companies(id),
            FOREIGN KEY (company_b_id) REFERENCES companies(id)
        )
    """
    )

    # 기본 데이터 삽입
    cursor.execute(
        "INSERT OR IGNORE INTO companies (name, industry) VALUES (?, ?)",
        ("삼성전자", "전자"),
    )
    cursor.execute(
        "INSERT OR IGNORE INTO companies (name, industry) VALUES (?, ?)",
        ("LG전자", "전자"),
    )
    cursor.execute(
        "INSERT OR IGNORE INTO companies (name, industry) VALUES (?, ?)",
        ("SK하이닉스", "반도체"),
    )

    conn.commit()
    conn.close()

    print(f"✅ 데이터베이스 생성 완료: {db_path}")

    # 결과를 파일에 기록
    with open("db_creation_log.txt", "w", encoding="utf-8") as f:
        f.write(f"✅ 데이터베이스 생성 완료: {db_path}\n")

        # 생성된 파일 확인
        if os.path.exists(db_path):
            size = os.path.getsize(db_path)
            f.write(f"📁 파일 크기: {size} bytes\n")

        # 테이블 확인
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        f.write(f"📋 생성된 테이블: {[t[0] for t in tables]}\n")

        # 데이터 확인
        cursor.execute("SELECT COUNT(*) FROM companies")
        company_count = cursor.fetchone()[0]
        f.write(f"🏢 회사 데이터: {company_count}개\n")

        conn.close()

    print("✅ 데이터베이스 생성 로그가 db_creation_log.txt에 기록되었습니다.")

except Exception as e:
    print(f"❌ 데이터베이스 생성 실패: {e}")
    import traceback

    traceback.print_exc()
    exit(1)
