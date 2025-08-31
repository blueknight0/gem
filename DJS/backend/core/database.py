"""
DJS Database Configuration
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from pathlib import Path

# 데이터베이스 파일 경로 설정
BASE_DIR = Path(__file__).parent.parent.parent
# 우선순위: ENV DATABASE_URL > 기본 SQLite 경로
DATABASE_URL = os.getenv("DATABASE_URL") or f"sqlite:///{BASE_DIR}/data/djs.db"

# SQLAlchemy 엔진 생성
# 엔진 생성 (SQLite일 때만 check_same_thread 적용)
engine_kwargs = {"echo": False}
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **engine_kwargs)

# 세션 팩토리 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 베이스 클래스
Base = declarative_base()


def get_db():
    """데이터베이스 세션 의존성"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """모든 테이블 생성"""
    Base.metadata.create_all(bind=engine)


def drop_tables():
    """모든 테이블 삭제 (주의: 데이터가 모두 삭제됨)"""
    Base.metadata.drop_all(bind=engine)


if __name__ == "__main__":
    # 테이블 생성 (초기 설정용)
    create_tables()
    print("데이터베이스 테이블이 생성되었습니다.")
