"""
스케줄러 API 엔드포인트
자동화된 작업 스케줄링 및 관리 기능 제공
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
from backend.core.database import get_db
from backend.services.scheduler_service import scheduler_service
from backend.models.schemas import APIResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/scheduler", tags=["scheduler"])


@router.post("/investigation", response_model=APIResponse)
async def schedule_investigation(
    company_name: str = Query(..., description="조사할 기업명"),
    cron_expression: Optional[str] = Query(
        None, description="Cron 표현식 (예: '0 9 * * 1')"
    ),
    interval_days: Optional[int] = Query(None, description="반복 간격 (일)"),
    max_rounds: int = Query(3, description="최대 라운드 수", ge=1, le=10),
    job_name: Optional[str] = Query(None, description="작업명"),
    background_tasks: BackgroundTasks = None,
):
    """
    기업 조사 작업 스케줄링

    - **company_name**: 조사할 기업명 (필수)
    - **cron_expression**: Cron 표현식 (예: "0 9 * * 1" - 매주 월요일 9시)
    - **interval_days**: 반복 간격 일수 (cron_expression과 함께 사용 불가)
    - **max_rounds**: 최대 라운드 수 (1-10)
    - **job_name**: 작업명 (미지정시 자동 생성)
    """
    try:
        # 스케줄러 시작 확인
        if background_tasks:
            background_tasks.add_task(scheduler_service.start_scheduler)

        # 작업 스케줄링
        job_id = await scheduler_service.schedule_company_investigation(
            company_name=company_name,
            cron_expression=cron_expression,
            interval_days=interval_days,
            max_rounds=max_rounds,
            job_name=job_name,
        )

        return APIResponse(
            success=True,
            message=f"기업 조사 작업이 스케줄링되었습니다: {job_id}",
            data={
                "job_id": job_id,
                "company_name": company_name,
                "max_rounds": max_rounds,
                "cron_expression": cron_expression,
                "interval_days": interval_days,
            },
        )

    except Exception as e:
        logger.error(f"기업 조사 작업 스케줄링 실패: {e}")
        raise HTTPException(
            status_code=500, detail="기업 조사 작업 스케줄링 중 오류가 발생했습니다."
        )


@router.post("/news-update", response_model=APIResponse)
async def schedule_news_update(
    search_keywords: str = Query(..., description="검색 키워드들 (콤마로 구분)"),
    cron_expression: str = Query(
        "0 */6 * * *", description="Cron 표현식 (기본: 6시간마다)"
    ),
    max_results: int = Query(50, description="최대 결과 수", ge=1, le=200),
    background_tasks: BackgroundTasks = None,
):
    """
    뉴스 업데이트 작업 스케줄링

    - **search_keywords**: 검색 키워드들 (콤마로 구분)
    - **cron_expression**: Cron 표현식 (기본: 6시간마다)
    - **max_results**: 최대 뉴스 수
    """
    try:
        # 스케줄러 시작 확인
        if background_tasks:
            background_tasks.add_task(scheduler_service.start_scheduler)

        # 키워드 파싱
        keywords_list = [kw.strip() for kw in search_keywords.split(",") if kw.strip()]

        if not keywords_list:
            raise HTTPException(status_code=400, detail="검색 키워드를 입력해주세요.")

        # 작업 스케줄링
        job_id = await scheduler_service.schedule_news_update(
            search_keywords=keywords_list,
            cron_expression=cron_expression,
            max_results=max_results,
        )

        return APIResponse(
            success=True,
            message=f"뉴스 업데이트 작업이 스케줄링되었습니다: {job_id}",
            data={
                "job_id": job_id,
                "keywords": keywords_list,
                "cron_expression": cron_expression,
                "max_results": max_results,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"뉴스 업데이트 작업 스케줄링 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail="뉴스 업데이트 작업 스케줄링 중 오류가 발생했습니다.",
        )


@router.post("/relation-extraction", response_model=APIResponse)
async def schedule_relation_extraction(
    batch_size: int = Query(10, description="배치 크기", ge=1, le=50),
    cron_expression: str = Query(
        "0 */2 * * *", description="Cron 표현식 (기본: 2시간마다)"
    ),
    min_confidence: float = Query(0.5, description="최소 신뢰도", ge=0.0, le=1.0),
    background_tasks: BackgroundTasks = None,
):
    """
    관계 추출 작업 스케줄링

    - **batch_size**: 배치 크기 (1-50)
    - **cron_expression**: Cron 표현식 (기본: 2시간마다)
    - **min_confidence**: 최소 신뢰도 (0.0-1.0)
    """
    try:
        # 스케줄러 시작 확인
        if background_tasks:
            background_tasks.add_task(scheduler_service.start_scheduler)

        # 작업 스케줄링
        job_id = await scheduler_service.schedule_relation_extraction(
            batch_size=batch_size,
            cron_expression=cron_expression,
            min_confidence=min_confidence,
        )

        return APIResponse(
            success=True,
            message=f"관계 추출 작업이 스케줄링되었습니다: {job_id}",
            data={
                "job_id": job_id,
                "batch_size": batch_size,
                "cron_expression": cron_expression,
                "min_confidence": min_confidence,
            },
        )

    except Exception as e:
        logger.error(f"관계 추출 작업 스케줄링 실패: {e}")
        raise HTTPException(
            status_code=500, detail="관계 추출 작업 스케줄링 중 오류가 발생했습니다."
        )


@router.post("/duplicate-detection", response_model=APIResponse)
async def schedule_duplicate_detection(
    cron_expression: str = Query(
        "0 2 * * *", description="Cron 표현식 (기본: 매일 2시)"
    ),
    similarity_threshold: float = Query(
        0.85, description="유사도 임계값", ge=0.0, le=1.0
    ),
    background_tasks: BackgroundTasks = None,
):
    """
    중복 뉴스 탐지 작업 스케줄링

    - **cron_expression**: Cron 표현식 (기본: 매일 2시)
    - **similarity_threshold**: 유사도 임계값 (0.0-1.0)
    """
    try:
        # 스케줄러 시작 확인
        if background_tasks:
            background_tasks.add_task(scheduler_service.start_scheduler)

        # 작업 스케줄링
        job_id = await scheduler_service.schedule_duplicate_detection(
            cron_expression=cron_expression, similarity_threshold=similarity_threshold
        )

        return APIResponse(
            success=True,
            message=f"중복 뉴스 탐지 작업이 스케줄링되었습니다: {job_id}",
            data={
                "job_id": job_id,
                "cron_expression": cron_expression,
                "similarity_threshold": similarity_threshold,
            },
        )

    except Exception as e:
        logger.error(f"중복 뉴스 탐지 작업 스케줄링 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail="중복 뉴스 탐지 작업 스케줄링 중 오류가 발생했습니다.",
        )


@router.get("/jobs", response_model=APIResponse)
def get_scheduled_jobs():
    """스케줄된 작업 목록 조회"""
    try:
        jobs = scheduler_service.get_scheduled_jobs()

        return APIResponse(
            success=True,
            message=f"{len(jobs)}개 스케줄된 작업 조회 완료",
            data={
                "jobs": jobs,
                "scheduler_status": scheduler_service.get_scheduler_status(),
            },
        )

    except Exception as e:
        logger.error(f"스케줄된 작업 목록 조회 실패: {e}")
        raise HTTPException(
            status_code=500, detail="스케줄된 작업 목록 조회 중 오류가 발생했습니다."
        )


@router.delete("/jobs/{job_id}", response_model=APIResponse)
def remove_scheduled_job(job_id: str):
    """스케줄된 작업 제거"""
    try:
        success = scheduler_service.remove_job(job_id)

        if success:
            return APIResponse(
                success=True,
                message=f"스케줄된 작업이 제거되었습니다: {job_id}",
                data={"job_id": job_id},
            )
        else:
            raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다.")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"스케줄된 작업 제거 실패: {e}")
        raise HTTPException(
            status_code=500, detail="스케줄된 작업 제거 중 오류가 발생했습니다."
        )


@router.put("/jobs/{job_id}/pause", response_model=APIResponse)
def pause_scheduled_job(job_id: str):
    """스케줄된 작업 일시 중지"""
    try:
        success = scheduler_service.pause_job(job_id)

        if success:
            return APIResponse(
                success=True,
                message=f"작업이 일시 중지되었습니다: {job_id}",
                data={"job_id": job_id, "status": "paused"},
            )
        else:
            raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다.")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"작업 일시 중지 실패: {e}")
        raise HTTPException(
            status_code=500, detail="작업 일시 중지 중 오류가 발생했습니다."
        )


@router.put("/jobs/{job_id}/resume", response_model=APIResponse)
def resume_scheduled_job(job_id: str):
    """스케줄된 작업 재개"""
    try:
        success = scheduler_service.resume_job(job_id)

        if success:
            return APIResponse(
                success=True,
                message=f"작업이 재개되었습니다: {job_id}",
                data={"job_id": job_id, "status": "resumed"},
            )
        else:
            raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다.")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"작업 재개 실패: {e}")
        raise HTTPException(status_code=500, detail="작업 재개 중 오류가 발생했습니다.")


@router.post("/start", response_model=APIResponse)
async def start_scheduler(background_tasks: BackgroundTasks = None):
    """스케줄러 시작"""
    try:
        if background_tasks:
            background_tasks.add_task(scheduler_service.start_scheduler)
        else:
            await scheduler_service.start_scheduler()

        return APIResponse(
            success=True,
            message="스케줄러가 시작되었습니다.",
            data={"status": "running"},
        )

    except Exception as e:
        logger.error(f"스케줄러 시작 실패: {e}")
        raise HTTPException(
            status_code=500, detail="스케줄러 시작 중 오류가 발생했습니다."
        )


@router.post("/stop", response_model=APIResponse)
async def stop_scheduler():
    """스케줄러 중지"""
    try:
        await scheduler_service.stop_scheduler()

        return APIResponse(
            success=True,
            message="스케줄러가 중지되었습니다.",
            data={"status": "stopped"},
        )

    except Exception as e:
        logger.error(f"스케줄러 중지 실패: {e}")
        raise HTTPException(
            status_code=500, detail="스케줄러 중지 중 오류가 발생했습니다."
        )


@router.get("/status", response_model=APIResponse)
def get_scheduler_status():
    """스케줄러 상태 조회"""
    try:
        status = scheduler_service.get_scheduler_status()

        return APIResponse(success=True, message="스케줄러 상태 조회 완료", data=status)

    except Exception as e:
        logger.error(f"스케줄러 상태 조회 실패: {e}")
        raise HTTPException(
            status_code=500, detail="스케줄러 상태 조회 중 오류가 발생했습니다."
        )


@router.get("/templates", response_model=APIResponse)
def get_scheduler_templates():
    """스케줄러 템플릿 목록 조회"""
    try:
        templates = [
            {
                "id": "daily_investigation",
                "name": "일일 기업 조사",
                "description": "매일 아침 9시에 기업 조사 실행",
                "cron_expression": "0 9 * * *",
                "type": "investigation",
            },
            {
                "id": "weekly_investigation",
                "name": "주간 기업 조사",
                "description": "매주 월요일 아침 9시에 기업 조사 실행",
                "cron_expression": "0 9 * * 1",
                "type": "investigation",
            },
            {
                "id": "frequent_news_update",
                "name": "빈번한 뉴스 업데이트",
                "description": "3시간마다 뉴스 업데이트",
                "cron_expression": "0 */3 * * *",
                "type": "news_update",
            },
            {
                "id": "standard_news_update",
                "name": "표준 뉴스 업데이트",
                "description": "6시간마다 뉴스 업데이트",
                "cron_expression": "0 */6 * * *",
                "type": "news_update",
            },
            {
                "id": "frequent_relation_extraction",
                "name": "빈번한 관계 추출",
                "description": "2시간마다 관계 추출",
                "cron_expression": "0 */2 * * *",
                "type": "relation_extraction",
            },
            {
                "id": "daily_relation_extraction",
                "name": "일일 관계 추출",
                "description": "매일 새벽 3시에 관계 추출",
                "cron_expression": "0 3 * * *",
                "type": "relation_extraction",
            },
            {
                "id": "nightly_duplicate_detection",
                "name": "야간 중복 탐지",
                "description": "매일 밤 2시에 중복 뉴스 탐지",
                "cron_expression": "0 2 * * *",
                "type": "duplicate_detection",
            },
        ]

        return APIResponse(
            success=True,
            message=f"{len(templates)}개 스케줄러 템플릿 조회 완료",
            data={"templates": templates},
        )

    except Exception as e:
        logger.error(f"스케줄러 템플릿 조회 실패: {e}")
        raise HTTPException(
            status_code=500, detail="스케줄러 템플릿 조회 중 오류가 발생했습니다."
        )
