"""
LLM 관계 추출 API 엔드포인트
Gemini 모델을 활용한 뉴스 기사 관계 추출 기능 제공
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from backend.core.database import get_db
from backend.services.llm_extractor import llm_extractor
from backend.models.schemas import APIResponse
from backend.models.models import News, Relation
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/extractor", tags=["extractor"])


@router.post("/extract-from-news", response_model=APIResponse)
def extract_relations_from_news(
    news_ids: List[int] = Query(..., description="관계 추출할 뉴스 ID 리스트"),
    batch_size: int = Query(5, description="배치 크기", ge=1, le=20),
    save_to_db: bool = Query(True, description="데이터베이스에 저장 여부"),
    db: Session = Depends(get_db),
):
    """
    뉴스 기사에서 관계 추출

    - **news_ids**: 관계 추출할 뉴스 ID 리스트
    - **batch_size**: 배치 처리 크기 (기본: 5)
    - **save_to_db**: 추출 결과를 데이터베이스에 저장할지 여부 (기본: True)
    """
    try:
        # 뉴스 데이터 조회
        news_items = db.query(News).filter(News.id.in_(news_ids)).all()

        if not news_items:
            raise HTTPException(
                status_code=404, detail="지정된 뉴스를 찾을 수 없습니다."
            )

        # 뉴스 데이터를 딕셔너리 형태로 변환
        news_data = []
        for news in news_items:
            news_data.append(
                {
                    "id": news.id,
                    "title": news.title,
                    "content": news.content,
                    "url": news.url,
                }
            )

        # 관계 추출
        extracted_relations = llm_extractor.batch_extract_relations(
            news_data, batch_size
        )

        if not extracted_relations:
            return APIResponse(
                success=True,
                message="추출된 관계가 없습니다.",
                data={"extracted_count": 0, "relations": []},
            )

        saved_relations = []
        if save_to_db:
            saved_relations = save_relations_to_db(db, extracted_relations)

        return APIResponse(
            success=True,
            message=f"{len(extracted_relations)}개 관계 추출 완료",
            data={
                "extracted_count": len(extracted_relations),
                "saved_count": len(saved_relations),
                "relations": extracted_relations,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"관계 추출 실패: {e}")
        raise HTTPException(status_code=500, detail="관계 추출 중 오류가 발생했습니다.")


@router.post("/extract-single", response_model=APIResponse)
def extract_relations_from_text(
    text: str = Query(..., description="관계 추출할 텍스트"),
    title: Optional[str] = Query(None, description="텍스트 제목"),
):
    """
    단일 텍스트에서 관계 추출

    - **text**: 관계 추출할 텍스트 내용
    - **title**: 텍스트 제목 (선택)
    """
    try:
        # 관계 추출
        relations = llm_extractor.extract_relations_from_news(text)

        return APIResponse(
            success=True,
            message=f"{len(relations)}개 관계 추출 완료",
            data={
                "title": title,
                "text_length": len(text),
                "extracted_relations": relations,
            },
        )

    except Exception as e:
        logger.error(f"단일 텍스트 관계 추출 실패: {e}")
        raise HTTPException(
            status_code=500, detail="텍스트 관계 추출 중 오류가 발생했습니다."
        )


@router.post("/classify-relation", response_model=APIResponse)
def classify_relation_type(content: str = Query(..., description="분류할 관계 내용")):
    """
    관계 내용 기반 관계 유형 분류

    - **content**: 분류할 관계 내용
    """
    try:
        relation_type, confidence = llm_extractor.classify_relation_type(content)

        return APIResponse(
            success=True,
            message="관계 유형 분류 완료",
            data={
                "content": content,
                "relation_type": relation_type,
                "confidence": confidence,
            },
        )

    except Exception as e:
        logger.error(f"관계 유형 분류 실패: {e}")
        raise HTTPException(
            status_code=500, detail="관계 유형 분류 중 오류가 발생했습니다."
        )


@router.put("/api-key", response_model=APIResponse)
def update_gemini_api_key(api_key: str = Query(..., description="Gemini API Key")):
    """Gemini API 키 업데이트"""
    try:
        llm_extractor.update_api_key(api_key)

        return APIResponse(
            success=True, message="Gemini API 키가 업데이트되었습니다.", data=None
        )

    except Exception as e:
        logger.error(f"API 키 업데이트 실패: {e}")
        raise HTTPException(
            status_code=500, detail="API 키 업데이트 중 오류가 발생했습니다."
        )


@router.get("/api-key/status", response_model=APIResponse)
def check_api_key_status():
    """Gemini API 키 상태 확인"""
    try:
        # API 키 존재 여부 확인
        has_api_key = llm_extractor._get_api_key_from_config() is not None

        return APIResponse(
            success=True,
            message="API 키 상태 확인 완료",
            data={"has_api_key": has_api_key, "model_name": llm_extractor.model_name},
        )

    except Exception as e:
        logger.error(f"API 키 상태 확인 실패: {e}")
        raise HTTPException(
            status_code=500, detail="API 키 상태 확인 중 오류가 발생했습니다."
        )


@router.get("/stats", response_model=APIResponse)
def get_extraction_stats(db: Session = Depends(get_db)):
    """관계 추출 통계 정보"""
    try:
        # 전체 관계 수
        total_relations = db.query(Relation).count()

        # 관계 유형별 통계
        relation_type_stats = (
            db.query(Relation.relation_type, db.func.count(Relation.id).label("count"))
            .group_by(Relation.relation_type)
            .all()
        )

        type_stats_dict = {
            stat.relation_type: stat.count for stat in relation_type_stats
        }

        # 신뢰도별 통계
        confidence_ranges = (
            db.query(
                db.case(
                    (Relation.confidence_score >= 0.8, "high"),
                    (Relation.confidence_score >= 0.6, "medium"),
                    else_="low",
                ).label("confidence_range"),
                db.func.count(Relation.id).label("count"),
            )
            .group_by("confidence_range")
            .all()
        )

        confidence_stats = {
            stat.confidence_range: stat.count for stat in confidence_ranges
        }

        # 최근 추출된 관계
        recent_relations = (
            db.query(Relation).order_by(Relation.created_at.desc()).limit(10).all()
        )

        recent_list = []
        for relation in recent_relations:
            recent_list.append(
                {
                    "id": relation.id,
                    "relation_type": relation.relation_type,
                    "relation_content": (
                        relation.relation_content[:50] + "..."
                        if len(relation.relation_content) > 50
                        else relation.relation_content
                    ),
                    "confidence_score": relation.confidence_score,
                    "created_at": relation.created_at,
                }
            )

        return APIResponse(
            success=True,
            message="관계 추출 통계 조회 완료",
            data={
                "total_relations": total_relations,
                "relation_type_stats": type_stats_dict,
                "confidence_stats": confidence_stats,
                "recent_relations": recent_list,
            },
        )

    except Exception as e:
        logger.error(f"관계 추출 통계 조회 실패: {e}")
        raise HTTPException(
            status_code=500, detail="관계 추출 통계 조회 중 오류가 발생했습니다."
        )


@router.get("/relations/{news_id}", response_model=APIResponse)
def get_relations_by_news(news_id: int, db: Session = Depends(get_db)):
    """특정 뉴스에서 추출된 관계 조회"""
    try:
        relations = db.query(Relation).filter(Relation.news_id == news_id).all()

        if not relations:
            return APIResponse(
                success=True,
                message="해당 뉴스에서 추출된 관계가 없습니다.",
                data={"relations": []},
            )

        relation_list = []
        for relation in relations:
            relation_list.append(
                {
                    "id": relation.id,
                    "company_a": (
                        relation.company_a.name if relation.company_a else None
                    ),
                    "company_b": (
                        relation.company_b.name if relation.company_b else None
                    ),
                    "university": (
                        relation.university.name if relation.university else None
                    ),
                    "professor": (
                        relation.professor.name if relation.professor else None
                    ),
                    "relation_type": relation.relation_type,
                    "relation_content": relation.relation_content,
                    "start_date": relation.start_date,
                    "end_date": relation.end_date,
                    "status": relation.status,
                    "confidence_score": relation.confidence_score,
                    "created_at": relation.created_at,
                }
            )

        return APIResponse(
            success=True,
            message=f"{len(relation_list)}개 관계 조회 완료",
            data={"relations": relation_list},
        )

    except Exception as e:
        logger.error(f"뉴스 관계 조회 실패: {e}")
        raise HTTPException(
            status_code=500, detail="뉴스 관계 조회 중 오류가 발생했습니다."
        )


def save_relations_to_db(
    db: Session, extracted_relations: List[Dict]
) -> List[Relation]:
    """추출된 관계를 데이터베이스에 저장"""
    from backend.models.models import Company, University, Professor

    saved_relations = []

    for relation_data in extracted_relations:
        try:
            # 기업 정보 조회 또는 생성
            company_a = None
            company_b = None
            university = None
            professor = None

            if relation_data.get("company_a"):
                company_a = (
                    db.query(Company)
                    .filter(Company.name == relation_data["company_a"])
                    .first()
                )
                if not company_a:
                    company_a = Company(name=relation_data["company_a"])
                    db.add(company_a)

            if relation_data.get("company_b"):
                company_b = (
                    db.query(Company)
                    .filter(Company.name == relation_data["company_b"])
                    .first()
                )
                if not company_b:
                    company_b = Company(name=relation_data["company_b"])
                    db.add(company_b)

            if relation_data.get("university"):
                university = (
                    db.query(University)
                    .filter(University.name == relation_data["university"])
                    .first()
                )
                if not university:
                    university = University(name=relation_data["university"])
                    db.add(university)

            if relation_data.get("professor") and university:
                professor = (
                    db.query(Professor)
                    .filter(
                        Professor.name == relation_data["professor"],
                        Professor.university_id == university.id,
                    )
                    .first()
                )
                if not professor:
                    professor = Professor(
                        name=relation_data["professor"], university_id=university.id
                    )
                    db.add(professor)

            # 관계 객체 생성
            db_relation = Relation(
                round_id=1,  # TODO: 실제 라운드 ID로 변경
                news_id=relation_data["news_id"],
                company_a_id=company_a.id if company_a else None,
                company_b_id=company_b.id if company_b else None,
                university_id=university.id if university else None,
                professor_id=professor.id if professor else None,
                relation_type=relation_data["relation_type"],
                relation_content=relation_data["relation_content"],
                start_date=relation_data.get("start_date"),
                end_date=relation_data.get("end_date"),
                confidence_score=relation_data.get("confidence", 0.5),
            )

            db.add(db_relation)
            saved_relations.append(db_relation)

        except Exception as e:
            logger.warning(f"관계 저장 실패: {e}")
            continue

    try:
        db.commit()
        logger.info(f"{len(saved_relations)}개 관계 저장 완료")
    except Exception as e:
        db.rollback()
        logger.error(f"데이터베이스 커밋 실패: {e}")
        raise

    return saved_relations
