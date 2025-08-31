"""
관계 검토 및 수정 API 엔드포인트
사용자가 추출된 관계를 검토하고 수정할 수 있는 기능 제공
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Body
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
from backend.core.database import get_db
from backend.services.review_service import review_service
from backend.models.schemas import APIResponse
from backend.models.models import Relation
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/review", tags=["review"])


@router.get("/relations", response_model=APIResponse)
def get_relations_for_review(
    status: Optional[str] = Query(None, description="관계 상태 필터"),
    confidence_threshold: Optional[float] = Query(
        None, description="최소 신뢰도", ge=0.0, le=1.0
    ),
    skip: int = Query(0, description="건너뛸 레코드 수", ge=0),
    limit: int = Query(50, description="반환할 레코드 수", ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    검토할 관계들 조회

    - **status**: 관계 상태 필터 (extracted, modified, approved, rejected)
    - **confidence_threshold**: 최소 신뢰도 임계값
    - **skip**: 건너뛸 레코드 수
    - **limit**: 반환할 최대 레코드 수
    """
    try:
        relations = review_service.get_relations_for_review(
            status=status, confidence_threshold=confidence_threshold, limit=limit, db=db
        )

        # 페이징 적용 (메모리에서 처리)
        paginated_relations = relations[skip : skip + limit]

        return APIResponse(
            success=True,
            message=f"{len(paginated_relations)}개의 검토용 관계 조회 완료",
            data={
                "relations": paginated_relations,
                "total": len(relations),
                "skip": skip,
                "limit": limit,
                "has_more": skip + limit < len(relations),
            },
        )

    except Exception as e:
        logger.error(f"관계 검토 조회 실패: {e}")
        raise HTTPException(
            status_code=500, detail="관계 검토 조회 중 오류가 발생했습니다."
        )


@router.get("/relation/{relation_id}", response_model=APIResponse)
def get_relation_detail(relation_id: int, db: Session = Depends(get_db)):
    """특정 관계 상세 정보 조회"""
    try:
        relation = db.query(Relation).filter(Relation.id == relation_id).first()
        if not relation:
            raise HTTPException(status_code=404, detail="관계를 찾을 수 없습니다.")

        # 히스토리 조회
        history = review_service.get_relation_history(relation_id, db)

        relation_detail = review_service._format_relation_for_review(relation)
        relation_detail["history"] = history

        return APIResponse(
            success=True,
            message=f"관계 {relation_id} 상세 정보 조회 완료",
            data={"relation": relation_detail},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"관계 상세 조회 실패: {e}")
        raise HTTPException(
            status_code=500, detail="관계 상세 조회 중 오류가 발생했습니다."
        )


@router.put("/relation/{relation_id}", response_model=APIResponse)
def update_relation(
    relation_id: int,
    updates: Dict[str, Any] = Body(..., description="수정할 필드들"),
    modified_by: str = Query(..., description="수정자 이름"),
    reason: Optional[str] = Query(None, description="수정 사유"),
    db: Session = Depends(get_db),
):
    """
    관계 정보 수정

    - **relation_id**: 수정할 관계 ID
    - **updates**: 수정할 필드들 (JSON)
    - **modified_by**: 수정자 이름
    - **reason**: 수정 사유
    """
    try:
        # 허용되는 수정 필드들
        allowed_fields = [
            "relation_type",
            "relation_content",
            "start_date",
            "end_date",
            "company_a",
            "company_b",
            "university",
            "professor",
            "confidence_score",
        ]

        # 필드 검증
        filtered_updates = {}
        for key, value in updates.items():
            if key in allowed_fields:
                filtered_updates[key] = value
            else:
                logger.warning(f"허용되지 않은 필드 수정 시도: {key}")

        if not filtered_updates:
            raise HTTPException(
                status_code=400, detail="수정할 유효한 필드가 없습니다."
            )

        success = review_service.update_relation(
            relation_id=relation_id,
            updates=filtered_updates,
            modified_by=modified_by,
            reason=reason,
            db=db,
        )

        if success:
            return APIResponse(
                success=True,
                message=f"관계 {relation_id} 수정 완료",
                data={
                    "relation_id": relation_id,
                    "modified_by": modified_by,
                    "modified_fields": list(filtered_updates.keys()),
                    "reason": reason,
                },
            )
        else:
            raise HTTPException(
                status_code=404, detail="관계를 찾을 수 없거나 수정에 실패했습니다."
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"관계 수정 실패: {e}")
        raise HTTPException(status_code=500, detail="관계 수정 중 오류가 발생했습니다.")


@router.delete("/relation/{relation_id}", response_model=APIResponse)
def delete_relation(
    relation_id: int,
    db: Session = Depends(get_db),
):
    """관계 삭제"""
    try:
        relation = db.query(Relation).filter(Relation.id == relation_id).first()
        if not relation:
            raise HTTPException(status_code=404, detail="관계를 찾을 수 없습니다.")

        db.delete(relation)
        db.commit()

        return APIResponse(
            success=True, message=f"관계 {relation_id} 삭제 완료", data=None
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"관계 삭제 실패: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="관계 삭제 중 오류가 발생했습니다.")


@router.post("/relations/bulk-delete", response_model=APIResponse)
def bulk_delete_relations(
    relation_ids: List[int] = Body(..., embed=True, description="삭제할 관계 ID 목록"),
    db: Session = Depends(get_db),
):
    """관계 다건 삭제 (현재 목록 등 선택 삭제에 사용)"""
    try:
        if not relation_ids:
            raise HTTPException(status_code=400, detail="삭제할 ID가 없습니다.")

        deleted = (
            db.query(Relation)
            .filter(Relation.id.in_(relation_ids))
            .delete(synchronize_session=False)
        )
        db.commit()
        return APIResponse(
            success=True,
            message=f"관계 {deleted}건 삭제 완료",
            data={"deleted_count": deleted},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"관계 다건 삭제 실패: {e}")
        db.rollback()
        raise HTTPException(
            status_code=500, detail="관계 다건 삭제 중 오류가 발생했습니다."
        )


@router.put("/relation/{relation_id}/approve", response_model=APIResponse)
def approve_relation(
    relation_id: int,
    approved_by: str = Query(..., description="승인자 이름"),
    reason: Optional[str] = Query(None, description="승인 사유"),
    db: Session = Depends(get_db),
):
    """관계 승인"""
    try:
        success = review_service.approve_relation(
            relation_id=relation_id, approved_by=approved_by, reason=reason, db=db
        )

        if success:
            return APIResponse(
                success=True,
                message=f"관계 {relation_id} 승인 완료",
                data={
                    "relation_id": relation_id,
                    "status": "approved",
                    "approved_by": approved_by,
                },
            )
        else:
            raise HTTPException(status_code=404, detail="관계를 찾을 수 없습니다.")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"관계 승인 실패: {e}")
        raise HTTPException(status_code=500, detail="관계 승인 중 오류가 발생했습니다.")


@router.put("/relation/{relation_id}/reject", response_model=APIResponse)
def reject_relation(
    relation_id: int,
    rejected_by: str = Query(..., description="거부자 이름"),
    reason: str = Query(..., description="거부 사유 (필수)"),
    db: Session = Depends(get_db),
):
    """관계 거부"""
    try:
        if not reason or reason.strip() == "":
            raise HTTPException(status_code=400, detail="거부 사유는 필수입니다.")

        success = review_service.reject_relation(
            relation_id=relation_id, rejected_by=rejected_by, reason=reason, db=db
        )

        if success:
            return APIResponse(
                success=True,
                message=f"관계 {relation_id} 거부 완료",
                data={
                    "relation_id": relation_id,
                    "status": "rejected",
                    "rejected_by": rejected_by,
                    "reason": reason,
                },
            )
        else:
            raise HTTPException(status_code=404, detail="관계를 찾을 수 없습니다.")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"관계 거부 실패: {e}")
        raise HTTPException(status_code=500, detail="관계 거부 중 오류가 발생했습니다.")


@router.post("/bulk-update", response_model=APIResponse)
def bulk_update_relations(
    updates: List[Dict[str, Any]] = Body(..., description="수정할 관계들"),
    modified_by: str = Query(..., description="수정자 이름"),
    reason: Optional[str] = Query(None, description="수정 사유"),
    db: Session = Depends(get_db),
):
    """
    관계 일괄 수정

    - **updates**: 수정할 관계들 [{"relation_id": int, "updates": dict}, ...]
    - **modified_by**: 수정자 이름
    - **reason**: 수정 사유
    """
    try:
        # 입력 검증
        if not updates:
            raise HTTPException(status_code=400, detail="수정할 관계가 없습니다.")

        for item in updates:
            if "relation_id" not in item or "updates" not in item:
                raise HTTPException(
                    status_code=400,
                    detail="각 항목은 'relation_id'와 'updates' 필드를 포함해야 합니다.",
                )

        result = review_service.bulk_update_relations(
            updates=updates, modified_by=modified_by, reason=reason, db=db
        )

        return APIResponse(
            success=True,
            message=f"일괄 수정 완료: {result['successful']}/{result['total_processed']}개 성공",
            data=result,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"일괄 수정 실패: {e}")
        raise HTTPException(status_code=500, detail="일괄 수정 중 오류가 발생했습니다.")


@router.get("/statistics", response_model=APIResponse)
def get_review_statistics(db: Session = Depends(get_db)):
    """검토 통계 조회"""
    try:
        stats = review_service.get_review_statistics(db=db)

        return APIResponse(success=True, message="검토 통계 조회 완료", data=stats)

    except Exception as e:
        logger.error(f"검토 통계 조회 실패: {e}")
        raise HTTPException(
            status_code=500, detail="검토 통계 조회 중 오류가 발생했습니다."
        )


@router.get("/history/{relation_id}", response_model=APIResponse)
def get_relation_history(relation_id: int, db: Session = Depends(get_db)):
    """관계 변경 히스토리 조회"""
    try:
        history = review_service.get_relation_history(relation_id, db)

        return APIResponse(
            success=True,
            message=f"관계 {relation_id} 변경 히스토리 조회 완료",
            data={
                "relation_id": relation_id,
                "history_count": len(history),
                "history": history,
            },
        )

    except Exception as e:
        logger.error(f"관계 히스토리 조회 실패: {e}")
        raise HTTPException(
            status_code=500, detail="관계 히스토리 조회 중 오류가 발생했습니다."
        )


@router.get("/queue", response_model=APIResponse)
def get_review_queue(
    priority: str = Query(
        "low_confidence", description="우선순위 (low_confidence, recent, all)"
    ),
    limit: int = Query(20, description="반환할 레코드 수", ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    검토 대기열 조회

    - **priority**: 우선순위
      - low_confidence: 신뢰도 낮은 순
      - recent: 최근 생성된 순
      - all: 전체
    - **limit**: 최대 반환 개수
    """
    try:
        if priority == "low_confidence":
            # 신뢰도 낮은 순
            relations = review_service.get_relations_for_review(
                status=None, confidence_threshold=None, limit=limit, db=db
            )
        elif priority == "recent":
            # 최근 생성된 순
            relations = (
                db.query(Relation)
                .filter(Relation.status.in_(["extracted", "modified"]))
                .order_by(Relation.created_at.desc())
                .limit(limit)
                .all()
            )

            relations = [
                review_service._format_relation_for_review(r) for r in relations
            ]
        else:
            # 전체
            relations = review_service.get_relations_for_review(
                status=None, confidence_threshold=None, limit=limit, db=db
            )

        return APIResponse(
            success=True,
            message=f"검토 대기열 조회 완료 ({priority} 우선순위)",
            data={
                "priority": priority,
                "count": len(relations),
                "relations": relations,
            },
        )

    except Exception as e:
        logger.error(f"검토 대기열 조회 실패: {e}")
        raise HTTPException(
            status_code=500, detail="검토 대기열 조회 중 오류가 발생했습니다."
        )


@router.put("/relation/{relation_id}/confidence", response_model=APIResponse)
def update_confidence_score(
    relation_id: int,
    confidence_score: float = Query(
        ..., description="새로운 신뢰도 점수", ge=0.0, le=1.0
    ),
    updated_by: str = Query(..., description="수정자 이름"),
    reason: Optional[str] = Query(None, description="수정 사유"),
    db: Session = Depends(get_db),
):
    """관계 신뢰도 점수 수정"""
    try:
        success = review_service.update_relation(
            relation_id=relation_id,
            updates={"confidence_score": confidence_score},
            modified_by=updated_by,
            reason=f"신뢰도 점수 수정: {reason}" if reason else "신뢰도 점수 수정",
            db=db,
        )

        if success:
            return APIResponse(
                success=True,
                message=f"관계 {relation_id} 신뢰도 점수 수정 완료",
                data={
                    "relation_id": relation_id,
                    "new_confidence_score": confidence_score,
                    "updated_by": updated_by,
                },
            )
        else:
            raise HTTPException(status_code=404, detail="관계를 찾을 수 없습니다.")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"신뢰도 점수 수정 실패: {e}")
        raise HTTPException(
            status_code=500, detail="신뢰도 점수 수정 중 오류가 발생했습니다."
        )
