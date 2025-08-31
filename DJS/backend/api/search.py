"""
뉴스 검색 API 엔드포인트
네이버 검색 API를 활용한 뉴스 검색 기능 제공
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from datetime import date
from backend.core.database import get_db
from backend.services.naver_search import naver_search_service
from backend.models.schemas import APIResponse, NewsCreate, News
from backend.models.models import News as NewsModel
from sqlalchemy import func
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/search", tags=["search"])


@router.post("/news", response_model=APIResponse)
async def search_company_news(
    company_name: str = Query(..., description="검색할 기업명"),
    keywords: Optional[List[str]] = Query(None, description="추가 검색 키워드"),
    start_date: Optional[date] = Query(None, description="검색 시작일"),
    end_date: Optional[date] = Query(None, description="검색 종료일"),
    max_results: Optional[int] = Query(
        50, description="최대 검색 결과 수", ge=1, le=200
    ),
    save_to_db: bool = Query(True, description="데이터베이스에 저장 여부"),
    db: Session = Depends(get_db),
):
    """
    기업명을 기반으로 오픈이노베이션 관련 뉴스 검색

    - **company_name**: 검색할 기업명 (필수)
    - **keywords**: 추가 검색 키워드 리스트 (선택)
    - **start_date**: 검색 시작일 (선택)
    - **end_date**: 검색 종료일 (선택)
    - **max_results**: 최대 검색 결과 수 (기본: 50, 최대: 200)
    - **save_to_db**: 검색 결과를 데이터베이스에 저장할지 여부 (기본: True)
    """
    try:
        # 뉴스 검색 수행
        search_results = await naver_search_service.search_news(
            company_name=company_name,
            keywords=keywords,
            start_date=start_date,
            end_date=end_date,
            max_results=max_results,
        )

        saved_news = []
        if save_to_db and search_results:
            saved_news = save_search_results_to_db(db, search_results, company_name)

        return APIResponse(
            success=True,
            message=f"{len(search_results)}개의 뉴스 검색 완료",
            data={
                "total_found": len(search_results),
                "total_saved": len(saved_news),
                "search_query": company_name,
                "results": (
                    search_results[:10] if len(search_results) > 10 else search_results
                ),  # 미리보기용
            },
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"뉴스 검색 실패: {e}")
        raise HTTPException(status_code=500, detail="뉴 검색 중 오류가 발생했습니다.")


@router.get("/news/{news_id}", response_model=News)
def get_news_by_id(news_id: int, db: Session = Depends(get_db)):
    """특정 뉴스 조회"""
    news = db.query(NewsModel).filter(NewsModel.id == news_id).first()
    if not news:
        raise HTTPException(status_code=404, detail="뉴스를 찾을 수 없습니다.")

    return news


@router.get("/news", response_model=List[News])
def get_news_list(
    company_name: Optional[str] = Query(None, description="기업명으로 필터링"),
    source: Optional[str] = Query(None, description="언론사로 필터링"),
    start_date: Optional[date] = Query(None, description="시작일"),
    end_date: Optional[date] = Query(None, description="종료일"),
    is_duplicate: Optional[bool] = Query(None, description="중복 여부 필터"),
    skip: int = Query(0, description="건너뛸 레코드 수", ge=0),
    limit: int = Query(100, description="반환할 레코드 수", ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """저장된 뉴스 목록 조회"""
    query = db.query(NewsModel)

    # 필터 적용
    if company_name:
        query = query.filter(NewsModel.search_keyword.contains(company_name))
    if source:
        query = query.filter(NewsModel.source == source)
    if start_date:
        query = query.filter(NewsModel.published_date >= start_date)
    if end_date:
        query = query.filter(NewsModel.published_date <= end_date)
    if is_duplicate is not None:
        query = query.filter(NewsModel.is_duplicate == is_duplicate)

    # 정렬 및 페이징
    news_list = (
        query.order_by(NewsModel.published_date.desc()).offset(skip).limit(limit).all()
    )

    return news_list


@router.get("/last-search-date", response_model=APIResponse)
def get_last_search_date(
    company_name: str = Query(..., description="기업명"),
    db: Session = Depends(get_db),
):
    """해당 기업명으로 저장된 뉴스의 마지막 날짜 정보를 반환"""
    try:
        last_published = (
            db.query(func.max(NewsModel.published_date))
            .filter(NewsModel.search_keyword == company_name)
            .scalar()
        )
        last_created = (
            db.query(func.max(NewsModel.created_at))
            .filter(NewsModel.search_keyword == company_name)
            .scalar()
        )

        return APIResponse(
            success=True,
            message="마지막 검색 날짜 조회 완료",
            data={
                "company_name": company_name,
                "last_published_date": (
                    last_published.isoformat() if last_published else None
                ),
                "last_created_at": last_created.isoformat() if last_created else None,
            },
        )
    except Exception as e:
        logger.error(f"마지막 검색 날짜 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="마지막 검색 날짜 조회 중 오류")


@router.put("/credentials", response_model=APIResponse)
def update_api_credentials(
    client_id: str = Query(..., description="네이버 API Client ID"),
    client_secret: str = Query(..., description="네이버 API Client Secret"),
    db: Session = Depends(get_db),
):
    """네이버 API 인증 정보 업데이트"""
    try:
        naver_search_service.update_api_credentials(client_id, client_secret)

        return APIResponse(
            success=True, message="API 인증 정보가 업데이트되었습니다.", data=None
        )

    except Exception as e:
        logger.error(f"API 인증 정보 업데이트 실패: {e}")
        raise HTTPException(
            status_code=500, detail="API 인증 정보 업데이트 중 오류가 발생했습니다."
        )


@router.get("/credentials/status", response_model=APIResponse)
def check_api_credentials_status():
    """API 인증 정보 상태 확인"""
    has_credentials = (
        naver_search_service.client_id is not None
        and naver_search_service.client_secret is not None
    )

    return APIResponse(
        success=True,
        message="API 인증 정보 상태 확인 완료",
        data={
            "has_credentials": has_credentials,
            "client_id_configured": naver_search_service.client_id is not None,
            "client_secret_configured": naver_search_service.client_secret is not None,
        },
    )


def save_search_results_to_db(
    db: Session, search_results: List[Dict], search_keyword: str
) -> List[NewsModel]:
    """검색 결과를 데이터베이스에 저장"""
    saved_news = []

    for result in search_results:
        try:
            # 중복 체크 (URL 기준)
            existing_news = (
                db.query(NewsModel).filter(NewsModel.url == result["link"]).first()
            )

            if existing_news:
                logger.info(f"중복 뉴스 발견: {result['title']}")
                continue

            # 뉴스 객체 생성
            news_data = NewsCreate(
                title=result["title"],
                content=result["full_content"],
                url=result["link"],
                source=result["source"],
                published_date=result["pubDate"],
                search_keyword=search_keyword,
            )

            # 데이터베이스에 저장
            db_news = NewsModel(**news_data.model_dump())
            db.add(db_news)
            saved_news.append(db_news)

        except Exception as e:
            logger.warning(f"뉴스 저장 실패: {e}")
            continue

    try:
        db.commit()
        logger.info(f"{len(saved_news)}개의 뉴스 저장 완료")
    except Exception as e:
        db.rollback()
        logger.error(f"데이터베이스 커밋 실패: {e}")
        raise

    return saved_news
