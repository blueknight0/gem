"""
DJS Database Models
SQLAlchemy ORM 모델 정의
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Date,
    DateTime,
    Boolean,
    ForeignKey,
    DECIMAL,
    LargeBinary,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.core.database import Base


class User(Base):
    """사용자 계정 모델"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, index=True)
    is_superuser = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Company(Base):
    """기업 정보 모델"""

    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    representative_name = Column(String(100))
    industry = Column(String(100))
    website = Column(String(255))
    description = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # 관계
    relations_as_a = relationship(
        "Relation", foreign_keys="Relation.company_a_id", back_populates="company_a"
    )
    relations_as_b = relationship(
        "Relation", foreign_keys="Relation.company_b_id", back_populates="company_b"
    )


class University(Base):
    """대학 정보 모델"""

    __tablename__ = "universities"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    website = Column(String(255))
    location = Column(String(100))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # 관계
    professors = relationship("Professor", back_populates="university")
    relations = relationship("Relation", back_populates="university")


class Professor(Base):
    """교수 정보 모델"""

    __tablename__ = "professors"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    university_id = Column(Integer, ForeignKey("universities.id"), index=True)
    department = Column(String(100))
    email = Column(String(255))
    research_field = Column(String(255))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # 관계
    university = relationship("University", back_populates="professors")
    relations = relationship("Relation", back_populates="professor")


class News(Base):
    """뉴스 기사 모델"""

    __tablename__ = "news"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    url = Column(String(1000), nullable=False, unique=True)
    source = Column(String(100))
    published_date = Column(Date, index=True)
    search_keyword = Column(String(255), index=True)
    embedding_vector = Column(LargeBinary)  # 텍스트 임베딩 벡터
    is_duplicate = Column(Boolean, default=False, index=True)
    duplicate_of = Column(Integer, ForeignKey("news.id"))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # 관계
    relations = relationship("Relation", back_populates="news")
    duplicate_news = relationship("News")  # self-referencing


class Round(Base):
    """검색 라운드 모델"""

    __tablename__ = "rounds"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    round_number = Column(Integer, nullable=False)
    target_company = Column(String(255), nullable=False, index=True)
    search_date = Column(Date, nullable=False)
    total_news_found = Column(Integer, default=0)
    total_relations_extracted = Column(Integer, default=0)
    status = Column(
        String(50), default="pending", index=True
    )  # pending, in_progress, completed, approved
    approved_by = Column(String(100))
    approved_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # 관계
    relations = relationship("Relation", back_populates="round")


class Relation(Base):
    """협력 관계 모델"""

    __tablename__ = "relations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    round_id = Column(Integer, ForeignKey("rounds.id"), nullable=False, index=True)
    news_id = Column(Integer, ForeignKey("news.id"), nullable=False)
    company_a_id = Column(Integer, ForeignKey("companies.id"), index=True)
    company_b_id = Column(Integer, ForeignKey("companies.id"), index=True)
    university_id = Column(Integer, ForeignKey("universities.id"), index=True)
    professor_id = Column(Integer, ForeignKey("professors.id"), index=True)
    relation_type = Column(
        String(50), nullable=False, index=True
    )  # MOU, 공동연구, 투자 등
    relation_content = Column(Text, nullable=False)
    start_date = Column(Date)
    end_date = Column(Date)
    status = Column(
        String(50), default="extracted", index=True
    )  # extracted, approved, rejected, modified
    confidence_score = Column(DECIMAL(3, 2))  # LLM 추출 신뢰도 점수
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # 관계
    round = relationship("Round", back_populates="relations")
    news = relationship("News", back_populates="relations")
    company_a = relationship(
        "Company", foreign_keys=[company_a_id], back_populates="relations_as_a"
    )
    company_b = relationship(
        "Company", foreign_keys=[company_b_id], back_populates="relations_as_b"
    )
    university = relationship("University", back_populates="relations")
    professor = relationship("Professor", back_populates="relations")
    history = relationship("RelationHistory", back_populates="relation")


class RelationHistory(Base):
    """관계 변경 히스토리 모델"""

    __tablename__ = "relation_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    relation_id = Column(
        Integer, ForeignKey("relations.id"), nullable=False, index=True
    )
    change_type = Column(
        String(50), nullable=False
    )  # created, modified, approved, rejected, deleted
    old_relation_type = Column(String(50))
    new_relation_type = Column(String(50))
    old_content = Column(Text)
    new_content = Column(Text)
    old_status = Column(String(50))
    new_status = Column(String(50))
    changed_by = Column(String(100))
    change_reason = Column(Text)
    changed_at = Column(DateTime, server_default=func.now())

    # 관계
    relation = relationship("Relation", back_populates="history")


class ScheduledJob(Base):
    """스케줄된 작업 모델"""

    __tablename__ = "scheduled_jobs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    job_id = Column(String(100), unique=True, nullable=False)
    job_type = Column(
        String(50), nullable=False
    )  # investigation, news_update, relation_extraction, duplicate_detection
    company_name = Column(String(255))
    trigger_expression = Column(String(255), nullable=False)
    max_rounds = Column(Integer, default=3)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class SystemConfig(Base):
    """시스템 설정 모델"""

    __tablename__ = "system_config"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    config_key = Column(String(100), nullable=False, unique=True)
    config_value = Column(Text)
    config_type = Column(String(50))  # string, integer, boolean, json
    description = Column(Text)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class RelationType(Base):
    """협력 관계 타입 모델"""

    __tablename__ = "relation_types"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    type_code = Column(String(50), nullable=False, unique=True)
    type_name = Column(String(100), nullable=False)
    description = Column(Text)
    color = Column(String(20))  # 시각화 색상
    icon = Column(String(50))  # 아이콘
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
