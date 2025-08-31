"""
라운드 기반 조사 API 엔드포인트
기업 조사 라운드를 관리하는 API 제공
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from backend.core.database import get_db
from backend.services.round_manager import round_manager
from backend.models.schemas import APIResponse
from backend.models.models import Round, Company, Relation
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/rounds", tags=["rounds"])


@router.post("/investigate", response_model=APIResponse)
async def start_company_investigation(
    target_company: str = Query(..., description="조사할 대상 기업명"),
    max_rounds: Optional[int] = Query(5, description="최대 라운드 수", ge=1, le=10),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
):
    """
    기업 조사 라운드 시작

    - **target_company**: 조사할 기업명 (필수)
    - **max_rounds**: 최대 라운드 수 (기본: 5, 최대: 10)
    """
    try:
        # 백그라운드에서 조사 수행
        if background_tasks:
            background_tasks.add_task(
                round_manager.start_investigation_round, target_company, max_rounds, db
            )

            return APIResponse(
                success=True,
                message=f"기업 '{target_company}' 조사 시작 (백그라운드 실행)",
                data={
                    "target_company": target_company,
                    "max_rounds": max_rounds,
                    "status": "running_in_background",
                },
            )
        else:
            # 동기 실행 (개발용)
            result = await round_manager.start_investigation_round(
                target_company, max_rounds, db
            )

            return APIResponse(
                success=True, message=f"기업 '{target_company}' 조사 완료", data=result
            )

    except Exception as e:
        logger.error(f"조사 시작 실패: {e}")
        raise HTTPException(status_code=500, detail="조사 시작 중 오류가 발생했습니다.")


@router.get("/status/{company_name}", response_model=APIResponse)
def get_investigation_status(company_name: str, db: Session = Depends(get_db)):
    """기업 조사 상태 조회"""
    try:
        rounds = (
            db.query(Round)
            .filter(Round.target_company == company_name)
            .order_by(Round.round_number)
            .all()
        )

        if not rounds:
            return APIResponse(
                success=True, message="조사 기록이 없습니다.", data={"rounds": []}
            )

        rounds_data = []
        for round_obj in rounds:
            rounds_data.append(
                {
                    "id": round_obj.id,
                    "round_number": round_obj.round_number,
                    "search_date": round_obj.search_date.isoformat(),
                    "status": round_obj.status,
                    "total_news_found": round_obj.total_news_found,
                    "total_relations_extracted": round_obj.total_relations_extracted,
                    "approved_by": round_obj.approved_by,
                    "approved_at": (
                        round_obj.approved_at.isoformat()
                        if round_obj.approved_at
                        else None
                    ),
                    "created_at": round_obj.created_at.isoformat(),
                    "updated_at": round_obj.updated_at.isoformat(),
                }
            )

        return APIResponse(
            success=True,
            message=f"기업 '{company_name}' 조사 상태 조회 완료",
            data={
                "target_company": company_name,
                "total_rounds": len(rounds),
                "rounds": rounds_data,
            },
        )

    except Exception as e:
        logger.error(f"조사 상태 조회 실패: {e}")
        raise HTTPException(
            status_code=500, detail="조사 상태 조회 중 오류가 발생했습니다."
        )


@router.put("/{round_id}/approve", response_model=APIResponse)
def approve_round(
    round_id: int,
    approved_by: str = Query(..., description="승인자 이름"),
    db: Session = Depends(get_db),
):
    """라운드 승인"""
    try:
        success = round_manager.approve_round(round_id, approved_by, db)

        if success:
            return APIResponse(
                success=True,
                message=f"라운드 {round_id} 승인 완료",
                data={"round_id": round_id, "status": "approved"},
            )
        else:
            raise HTTPException(status_code=404, detail="라운드를 찾을 수 없습니다.")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"라운드 승인 실패: {e}")
        raise HTTPException(
            status_code=500, detail="라운드 승인 중 오류가 발생했습니다."
        )


@router.put("/{round_id}/reject", response_model=APIResponse)
def reject_round(
    round_id: int,
    approved_by: str = Query(..., description="거부자 이름"),
    db: Session = Depends(get_db),
):
    """라운드 거부"""
    try:
        success = round_manager.reject_round(round_id, approved_by, db)

        if success:
            return APIResponse(
                success=True,
                message=f"라운드 {round_id} 거부 완료",
                data={"round_id": round_id, "status": "rejected"},
            )
        else:
            raise HTTPException(status_code=404, detail="라운드를 찾을 수 없습니다.")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"라운드 거부 실패: {e}")
        raise HTTPException(
            status_code=500, detail="라운드 거부 중 오류가 발생했습니다."
        )


@router.get("/pending", response_model=APIResponse)
def get_pending_rounds(
    skip: int = Query(0, description="건너뛸 레코드 수", ge=0),
    limit: int = Query(50, description="반환할 레코드 수", ge=1, le=100),
    db: Session = Depends(get_db),
):
    """승인 대기 중인 라운드 목록 조회"""
    try:
        pending_rounds = (
            db.query(Round)
            .filter(Round.status == "completed")
            .order_by(Round.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        rounds_data = []
        for round_obj in pending_rounds:
            rounds_data.append(
                {
                    "id": round_obj.id,
                    "round_number": round_obj.round_number,
                    "target_company": round_obj.target_company,
                    "search_date": round_obj.search_date.isoformat(),
                    "total_news_found": round_obj.total_news_found,
                    "total_relations_extracted": round_obj.total_relations_extracted,
                    "created_at": round_obj.created_at.isoformat(),
                }
            )

        return APIResponse(
            success=True,
            message=f"{len(rounds_data)}개의 승인 대기 라운드 조회 완료",
            data={
                "pending_rounds": rounds_data,
                "total": len(rounds_data),
                "skip": skip,
                "limit": limit,
            },
        )

    except Exception as e:
        logger.error(f"승인 대기 라운드 조회 실패: {e}")
        raise HTTPException(
            status_code=500, detail="승인 대기 라운드 조회 중 오류가 발생했습니다."
        )


@router.get("/companies/{round_id}", response_model=APIResponse)
def get_companies_from_round(round_id: int, db: Session = Depends(get_db)):
    """특정 라운드에서 발견된 기업들 조회"""
    try:
        # 라운드 조회
        round_obj = db.query(Round).filter(Round.id == round_id).first()
        if not round_obj:
            raise HTTPException(status_code=404, detail="라운드를 찾을 수 없습니다.")

        # 해당 라운드의 관계들에서 기업들 추출
        relations = db.query(Relation).filter(Relation.round_id == round_id).all()

        companies = set()
        for relation in relations:
            if relation.company_a:
                companies.add(relation.company_a)
            if relation.company_b:
                companies.add(relation.company_b)

        companies_data = []
        for company in companies:
            companies_data.append(
                {
                    "id": company.id,
                    "name": company.name,
                    "industry": company.industry,
                    "website": company.website,
                    "description": company.description,
                    "created_at": company.created_at.isoformat(),
                }
            )

        return APIResponse(
            success=True,
            message=f"라운드 {round_id}에서 {len(companies_data)}개 기업 발견",
            data={
                "round_id": round_id,
                "round_number": round_obj.round_number,
                "target_company": round_obj.target_company,
                "companies": companies_data,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"라운드 기업 조회 실패: {e}")
        raise HTTPException(
            status_code=500, detail="라운드 기업 조회 중 오류가 발생했습니다."
        )


@router.get("/statistics", response_model=APIResponse)
def get_round_statistics(db: Session = Depends(get_db)):
    """라운드 기반 조사 통계"""
    try:
        # 전체 라운드 수
        total_rounds = db.query(Round).count()

        # 상태별 라운드 수
        status_counts = (
            db.query(Round.status, db.func.count(Round.id).label("count"))
            .group_by(Round.status)
            .all()
        )

        status_stats = {status: count for status, count in status_counts}

        # 기업별 조사된 라운드 수
        company_rounds = (
            db.query(
                Round.target_company,
                db.func.count(Round.id).label("round_count"),
                db.func.max(Round.round_number).label("max_round"),
            )
            .group_by(Round.target_company)
            .all()
        )

        company_stats = []
        for company, round_count, max_round in company_rounds:
            company_stats.append(
                {
                    "company": company,
                    "total_rounds": round_count,
                    "max_round_reached": max_round,
                }
            )

        # 최근 라운드들
        recent_rounds = (
            db.query(Round).order_by(Round.updated_at.desc()).limit(10).all()
        )

        recent_data = []
        for round_obj in recent_rounds:
            recent_data.append(
                {
                    "id": round_obj.id,
                    "target_company": round_obj.target_company,
                    "round_number": round_obj.round_number,
                    "status": round_obj.status,
                    "total_news_found": round_obj.total_news_found,
                    "total_relations_extracted": round_obj.total_relations_extracted,
                    "updated_at": round_obj.updated_at.isoformat(),
                }
            )

        return APIResponse(
            success=True,
            message="라운드 조사 통계 조회 완료",
            data={
                "total_rounds": total_rounds,
                "status_statistics": status_stats,
                "company_statistics": company_stats,
                "recent_rounds": recent_data,
            },
        )

    except Exception as e:
        logger.error(f"라운드 통계 조회 실패: {e}")
        raise HTTPException(
            status_code=500, detail="라운드 통계 조회 중 오류가 발생했습니다."
        )


@router.delete("/{round_id}", response_model=APIResponse)
def delete_round(round_id: int, db: Session = Depends(get_db)):
    """라운드 삭제 (주의: 관련 데이터도 모두 삭제됨)"""
    try:
        # 라운드 존재 확인
        round_obj = db.query(Round).filter(Round.id == round_id).first()
        if not round_obj:
            raise HTTPException(status_code=404, detail="라운드를 찾을 수 없습니다.")

        # 관련 관계들 삭제 (외래 키 제약으로 인해)
        relations_deleted = (
            db.query(Relation).filter(Relation.round_id == round_id).delete()
        )

        # 라운드 삭제
        db.delete(round_obj)
        db.commit()

        return APIResponse(
            success=True,
            message=f"라운드 {round_id} 및 관련 데이터 삭제 완료",
            data={"round_id": round_id, "relations_deleted": relations_deleted},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"라운드 삭제 실패: {e}")
        db.rollback()
        raise HTTPException(
            status_code=500, detail="라운드 삭제 중 오류가 발생했습니다."
        )
