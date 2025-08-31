"""
임베딩 및 중복 제거 API 엔드포인트
텍스트 임베딩을 활용한 뉴스 중복 제거 기능 제공
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.core.database import get_db
from backend.services.embedding_service import embedding_service
from backend.models.schemas import APIResponse
from backend.models.models import News
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/embedding", tags=["embedding"])


@router.post("/deduplicate", response_model=APIResponse)
def deduplicate_news_batch(
    news_ids: Optional[List[int]] = Query(
        None, description="중복 제거할 뉴스 ID 리스트 (None이면 전체)"
    ),
    threshold: Optional[float] = Query(
        None, description="유사도 임계값", ge=0.0, le=1.0
    ),
    batch_size: int = Query(100, description="배치 크기", ge=10, le=1000),
    db: Session = Depends(get_db),
):
    """
    뉴스 중복 일괄 제거

    - **news_ids**: 특정 뉴스 ID 리스트만 처리 (선택)
    - **threshold**: 유사도 임계값 (선택, 기본값: 시스템 설정값)
    - **batch_size**: 배치 처리 크기 (기본: 100)
    """
    try:
        result = embedding_service.batch_process_duplicates(news_ids, batch_size)

        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        return APIResponse(success=True, message="중복 제거 처리 완료", data=result)

    except Exception as e:
        logger.error(f"중복 제거 실패: {e}")
        raise HTTPException(status_code=500, detail="중복 제거 중 오류가 발생했습니다.")


@router.get("/similarity/{news_id1}/{news_id2}", response_model=APIResponse)
def get_news_similarity(news_id1: int, news_id2: int):
    """
    두 뉴스 간 유사도 계산

    - **news_id1**: 첫 번째 뉴스 ID
    - **news_id2**: 두 번째 뉴스 ID
    """
    try:
        similarity = embedding_service.compare_news_similarity(news_id1, news_id2)

        if similarity is None:
            raise HTTPException(
                status_code=404, detail="뉴스를 찾을 수 없거나 임베딩이 없습니다."
            )

        return APIResponse(
            success=True,
            message="유사도 계산 완료",
            data={
                "news_id1": news_id1,
                "news_id2": news_id2,
                "similarity": similarity,
                "is_similar": similarity >= embedding_service.similarity_threshold,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"유사도 계산 실패: {e}")
        raise HTTPException(
            status_code=500, detail="유사도 계산 중 오류가 발생했습니다."
        )


@router.get("/duplicates", response_model=APIResponse)
def get_duplicate_news_list(
    skip: int = Query(0, description="건너뛸 레코드 수", ge=0),
    limit: int = Query(100, description="반환할 레코드 수", ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """중복으로 표시된 뉴스 목록 조회"""
    try:
        duplicates = (
            db.query(News)
            .filter(News.is_duplicate == True)
            .offset(skip)
            .limit(limit)
            .all()
        )

        duplicate_list = []
        for news in duplicates:
            original_news = None
            if news.duplicate_of:
                original_news = (
                    db.query(News).filter(News.id == news.duplicate_of).first()
                )

            duplicate_list.append(
                {
                    "id": news.id,
                    "title": news.title,
                    "url": news.url,
                    "source": news.source,
                    "published_date": news.published_date,
                    "duplicate_of": news.duplicate_of,
                    "original_title": original_news.title if original_news else None,
                    "created_at": news.created_at,
                }
            )

        return APIResponse(
            success=True,
            message=f"{len(duplicate_list)}개의 중복 뉴스 조회 완료",
            data={
                "duplicates": duplicate_list,
                "total": len(duplicate_list),
                "skip": skip,
                "limit": limit,
            },
        )

    except Exception as e:
        logger.error(f"중복 뉴스 목록 조회 실패: {e}")
        raise HTTPException(
            status_code=500, detail="중복 뉴스 목록 조회 중 오류가 발생했습니다."
        )


@router.delete("/duplicates", response_model=APIResponse)
def delete_duplicate_news(
    permanently: bool = Query(
        False, description="영구 삭제 여부 (False면 duplicate 플래그만 제거)"
    ),
    db: Session = Depends(get_db),
):
    """중복 뉴스 정리 (삭제 또는 플래그 제거)"""
    try:
        duplicate_news = db.query(News).filter(News.is_duplicate == True).all()

        if not duplicate_news:
            return APIResponse(
                success=True,
                message="삭제할 중복 뉴스가 없습니다.",
                data={"deleted_count": 0},
            )

        if permanently:
            # 영구 삭제
            for news in duplicate_news:
                db.delete(news)
            deleted_count = len(duplicate_news)
            message = f"{deleted_count}개의 중복 뉴스 영구 삭제 완료"
        else:
            # 플래그만 제거
            for news in duplicate_news:
                news.is_duplicate = False
                news.duplicate_of = None
            deleted_count = len(duplicate_news)
            message = f"{deleted_count}개의 뉴스 중복 플래그 제거 완료"

        db.commit()

        return APIResponse(
            success=True, message=message, data={"processed_count": deleted_count}
        )

    except Exception as e:
        logger.error(f"중복 뉴스 정리 실패: {e}")
        db.rollback()
        raise HTTPException(
            status_code=500, detail="중복 뉴스 정리 중 오류가 발생했습니다."
        )


@router.get("/stats", response_model=APIResponse)
def get_embedding_stats(db: Session = Depends(get_db)):
    """임베딩 관련 통계 정보"""
    try:
        total_news = db.query(News).count()
        news_with_embeddings = (
            db.query(News).filter(News.embedding_vector.isnot(None)).count()
        )
        duplicate_news = db.query(News).filter(News.is_duplicate == True).count()

        # 최근 중복 처리된 뉴스
        recent_duplicates = (
            db.query(News)
            .filter(News.is_duplicate == True)
            .order_by(News.updated_at.desc())
            .limit(5)
            .all()
        )

        recent_duplicate_list = []
        for news in recent_duplicates:
            recent_duplicate_list.append(
                {"id": news.id, "title": news.title, "updated_at": news.updated_at}
            )

        return APIResponse(
            success=True,
            message="임베딩 통계 조회 완료",
            data={
                "total_news": total_news,
                "news_with_embeddings": news_with_embeddings,
                "embedding_coverage": (
                    news_with_embeddings / total_news if total_news > 0 else 0
                ),
                "duplicate_news": duplicate_news,
                "duplicate_ratio": duplicate_news / total_news if total_news > 0 else 0,
                "recent_duplicates": recent_duplicate_list,
                "similarity_threshold": embedding_service.similarity_threshold,
            },
        )

    except Exception as e:
        logger.error(f"임베딩 통계 조회 실패: {e}")
        raise HTTPException(
            status_code=500, detail="임베딩 통계 조회 중 오류가 발생했습니다."
        )


@router.post("/generate-embeddings", response_model=APIResponse)
def generate_embeddings_for_news(
    news_ids: Optional[List[int]] = Query(
        None,
        description="임베딩을 생성할 뉴스 ID 리스트 (None이면 임베딩 없는 뉴스 전체)",
    ),
    batch_size: int = Query(50, description="배치 크기", ge=10, le=200),
    db: Session = Depends(get_db),
):
    """
    뉴스에 대한 임베딩 벡터 생성 및 저장

    - **news_ids**: 특정 뉴스 ID 리스트 (선택)
    - **batch_size**: 배치 처리 크기 (기본: 50)
    """
    try:
        # 처리할 뉴스 선택
        query = db.query(News)
        if news_ids:
            query = query.filter(News.id.in_(news_ids))
        else:
            query = query.filter(News.embedding_vector.is_(None))

        news_without_embeddings = query.all()

        if not news_without_embeddings:
            return APIResponse(
                success=True,
                message="임베딩이 필요한 뉴스가 없습니다.",
                data={"processed_count": 0},
            )

        processed_count = 0

        # 배치 처리
        for i in range(0, len(news_without_embeddings), batch_size):
            batch = news_without_embeddings[i : i + batch_size]

            # 뉴스 데이터를 딕셔너리 형태로 변환
            news_data = []
            for news in batch:
                news_data.append(
                    {
                        "title": news.title,
                        "description": news.content[
                            :1000
                        ],  # 내용이 너무 길면 잘라서 사용
                    }
                )

            # 임베딩 생성 및 저장 준비
            news_with_embeddings = embedding_service.save_embeddings_to_db(news_data)

            # 데이터베이스에 저장
            for j, news in enumerate(batch):
                if (
                    j < len(news_with_embeddings)
                    and "embedding_vector" in news_with_embeddings[j]
                ):
                    news.embedding_vector = news_with_embeddings[j]["embedding_vector"]

            processed_count += len(batch)

        db.commit()

        return APIResponse(
            success=True,
            message=f"{processed_count}개 뉴스의 임베딩 생성 완료",
            data={
                "processed_count": processed_count,
                "batch_size": batch_size,
                "total_without_embeddings": len(news_without_embeddings),
            },
        )

    except Exception as e:
        logger.error(f"임베딩 생성 실패: {e}")
        db.rollback()
        raise HTTPException(
            status_code=500, detail="임베딩 생성 중 오류가 발생했습니다."
        )
