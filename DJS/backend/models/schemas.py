"""
DJS Pydantic Schemas
API 요청/응답 데이터 검증 및 직렬화
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal


# 사용자 스키마
class UserBase(BaseModel):
    email: str = Field(..., max_length=255)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128)


class UserLogin(BaseModel):
    email: str
    password: str


class User(UserBase):
    id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# 회사 스키마
class CompanyBase(BaseModel):
    name: str = Field(..., max_length=255)
    representative_name: Optional[str] = Field(None, max_length=100)
    industry: Optional[str] = Field(None, max_length=100)
    website: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    representative_name: Optional[str] = Field(None, max_length=100)
    industry: Optional[str] = Field(None, max_length=100)
    website: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None


class Company(CompanyBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# 대학 스키마
class UniversityBase(BaseModel):
    name: str = Field(..., max_length=255)
    website: Optional[str] = Field(None, max_length=255)
    location: Optional[str] = Field(None, max_length=100)


class UniversityCreate(UniversityBase):
    pass


class UniversityUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    website: Optional[str] = Field(None, max_length=255)
    location: Optional[str] = Field(None, max_length=100)


class University(UniversityBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# 교수 스키마
class ProfessorBase(BaseModel):
    name: str = Field(..., max_length=100)
    university_id: Optional[int] = None
    department: Optional[str] = Field(None, max_length=100)
    email: Optional[str] = Field(None, max_length=255)
    research_field: Optional[str] = Field(None, max_length=255)


class ProfessorCreate(ProfessorBase):
    pass


class ProfessorUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    university_id: Optional[int] = None
    department: Optional[str] = Field(None, max_length=100)
    email: Optional[str] = Field(None, max_length=255)
    research_field: Optional[str] = Field(None, max_length=255)


class Professor(ProfessorBase):
    id: int
    created_at: datetime
    updated_at: datetime
    university: Optional[University] = None

    class Config:
        from_attributes = True


# 뉴스 스키마
class NewsBase(BaseModel):
    title: str = Field(..., max_length=500)
    content: str
    url: str = Field(..., max_length=1000)
    source: Optional[str] = Field(None, max_length=100)
    published_date: Optional[date] = None
    search_keyword: Optional[str] = Field(None, max_length=255)


class NewsCreate(NewsBase):
    pass


class NewsUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=500)
    content: Optional[str] = None
    url: Optional[str] = Field(None, max_length=1000)
    source: Optional[str] = Field(None, max_length=100)
    published_date: Optional[date] = None
    search_keyword: Optional[str] = Field(None, max_length=255)
    is_duplicate: Optional[bool] = None
    duplicate_of: Optional[int] = None


class News(NewsBase):
    id: int
    is_duplicate: bool
    duplicate_of: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# 라운드 스키마
class RoundBase(BaseModel):
    round_number: int
    target_company: str = Field(..., max_length=255)
    search_date: date


class RoundCreate(RoundBase):
    pass


class RoundUpdate(BaseModel):
    round_number: Optional[int] = None
    target_company: Optional[str] = Field(None, max_length=255)
    search_date: Optional[date] = None
    total_news_found: Optional[int] = None
    total_relations_extracted: Optional[int] = None
    status: Optional[str] = Field(None, max_length=50)
    approved_by: Optional[str] = Field(None, max_length=100)
    approved_at: Optional[datetime] = None


class Round(RoundBase):
    id: int
    total_news_found: int
    total_relations_extracted: int
    status: str
    approved_by: Optional[str]
    approved_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# 관계 스키마
class RelationBase(BaseModel):
    round_id: int
    news_id: int
    company_a_id: Optional[int] = None
    company_b_id: Optional[int] = None
    university_id: Optional[int] = None
    professor_id: Optional[int] = None
    relation_type: str = Field(..., max_length=50)
    relation_content: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    confidence_score: Optional[Decimal] = Field(None, ge=0, le=1)


class RelationCreate(RelationBase):
    pass


class RelationUpdate(BaseModel):
    round_id: Optional[int] = None
    news_id: Optional[int] = None
    company_a_id: Optional[int] = None
    company_b_id: Optional[int] = None
    university_id: Optional[int] = None
    professor_id: Optional[int] = None
    relation_type: Optional[str] = Field(None, max_length=50)
    relation_content: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[str] = Field(None, max_length=50)
    confidence_score: Optional[Decimal] = Field(None, ge=0, le=1)


class Relation(RelationBase):
    id: int
    status: str
    created_at: datetime
    updated_at: datetime
    round: Optional[Round] = None
    news: Optional[News] = None
    company_a: Optional[Company] = None
    company_b: Optional[Company] = None
    university: Optional[University] = None
    professor: Optional[Professor] = None

    class Config:
        from_attributes = True


# 관계 히스토리 스키마
class RelationHistoryBase(BaseModel):
    relation_id: int
    change_type: str = Field(..., max_length=50)
    old_relation_type: Optional[str] = Field(None, max_length=50)
    new_relation_type: Optional[str] = Field(None, max_length=50)
    old_content: Optional[str] = None
    new_content: Optional[str] = None
    old_status: Optional[str] = Field(None, max_length=50)
    new_status: Optional[str] = Field(None, max_length=50)
    changed_by: Optional[str] = Field(None, max_length=100)
    change_reason: Optional[str] = None


class RelationHistoryCreate(RelationHistoryBase):
    pass


class RelationHistory(RelationHistoryBase):
    id: int
    changed_at: datetime

    class Config:
        from_attributes = True


# 관계 타입 스키마
class RelationTypeBase(BaseModel):
    type_code: str = Field(..., max_length=50)
    type_name: str = Field(..., max_length=100)
    description: Optional[str] = None
    color: Optional[str] = Field(None, max_length=20)
    icon: Optional[str] = Field(None, max_length=50)


class RelationTypeCreate(RelationTypeBase):
    pass


class RelationTypeUpdate(BaseModel):
    type_code: Optional[str] = Field(None, max_length=50)
    type_name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    color: Optional[str] = Field(None, max_length=20)
    icon: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None


class RelationType(RelationTypeBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# 시스템 설정 스키마
class SystemConfigBase(BaseModel):
    config_key: str = Field(..., max_length=100)
    config_value: Optional[str] = None
    config_type: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None


class SystemConfigCreate(SystemConfigBase):
    pass


class SystemConfigUpdate(BaseModel):
    config_value: Optional[str] = None
    config_type: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None


class SystemConfig(SystemConfigBase):
    id: int
    updated_at: datetime

    class Config:
        from_attributes = True


# API 응답을 위한 범용 스키마
class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None


class PaginatedResponse(BaseModel):
    items: List[dict]
    total: int
    page: int
    size: int
    pages: int


# 네트워크 시각화용 스키마
class NetworkNode(BaseModel):
    id: str
    label: str
    type: str  # company, university, professor
    properties: dict = {}


class NetworkEdge(BaseModel):
    source: str
    target: str
    type: str
    properties: dict = {}


class NetworkData(BaseModel):
    nodes: List[NetworkNode]
    edges: List[NetworkEdge]
