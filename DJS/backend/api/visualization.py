"""
네트워크 시각화 API 엔드포인트
기업 관계 네트워크를 시각화하는 기능 제공
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import date, datetime
import json
import os
from pathlib import Path
from backend.core.database import get_db
from backend.services.network_visualizer import network_visualizer
from backend.models.schemas import APIResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/visualization", tags=["visualization"])


@router.get("/network", response_model=APIResponse)
def get_network_data(
    target_company: Optional[str] = Query(None, description="중심 기업명"),
    max_depth: int = Query(3, description="네트워크 깊이", ge=1, le=5),
    relation_types: Optional[str] = Query(
        None, description="관계 유형들 (콤마로 구분)"
    ),
    start_date: Optional[date] = Query(None, description="시작 날짜"),
    end_date: Optional[date] = Query(None, description="종료 날짜"),
    db: Session = Depends(get_db),
):
    """
    기업 관계 네트워크 데이터 조회

    - **target_company**: 중심 기업명 (미지정시 전체 네트워크)
    - **max_depth**: 네트워크 깊이 제한 (1-5)
    - **relation_types**: 포함할 관계 유형들 (예: MOU,JOINT_RESEARCH)
    - **start_date**: 시작 날짜 필터
    - **end_date**: 종료 날짜 필터
    """
    try:
        # 관계 유형 파싱
        relation_type_list = None
        if relation_types:
            relation_type_list = [rt.strip() for rt in relation_types.split(",")]

        # 네트워크 데이터 생성
        network_data = network_visualizer.generate_network_data(
            target_company=target_company,
            max_depth=max_depth,
            relation_types=relation_type_list,
            start_date=start_date,
            end_date=end_date,
            db=db,
        )

        return APIResponse(
            success=True,
            message=f"네트워크 데이터 생성 완료 ({len(network_data['nodes'])}개 노드, {len(network_data['edges'])}개 관계)",
            data=network_data,
        )

    except Exception as e:
        logger.error(f"네트워크 데이터 생성 실패: {e}")
        raise HTTPException(
            status_code=500, detail="네트워크 데이터 생성 중 오류가 발생했습니다."
        )


@router.get("/network/statistics", response_model=APIResponse)
def get_network_statistics(
    target_company: Optional[str] = Query(None, description="중심 기업명"),
    max_depth: int = Query(3, description="네트워크 깊이", ge=1, le=5),
    relation_types: Optional[str] = Query(
        None, description="관계 유형들 (콤마로 구분)"
    ),
    start_date: Optional[date] = Query(None, description="시작 날짜"),
    end_date: Optional[date] = Query(None, description="종료 날짜"),
    db: Session = Depends(get_db),
):
    """네트워크 통계 정보 조회"""
    try:
        # 관계 유형 파싱
        relation_type_list = None
        if relation_types:
            relation_type_list = [rt.strip() for rt in relation_types.split(",")]

        # 네트워크 데이터 생성
        network_data = network_visualizer.generate_network_data(
            target_company=target_company,
            max_depth=max_depth,
            relation_types=relation_type_list,
            start_date=start_date,
            end_date=end_date,
            db=db,
        )

        # 통계 정보 생성
        statistics = network_visualizer.generate_network_statistics(network_data)

        return APIResponse(
            success=True,
            message="네트워크 통계 조회 완료",
            data={"network": network_data, "statistics": statistics},
        )

    except Exception as e:
        logger.error(f"네트워크 통계 조회 실패: {e}")
        raise HTTPException(
            status_code=500, detail="네트워크 통계 조회 중 오류가 발생했습니다."
        )


@router.get("/network/export", response_model=APIResponse)
def export_network_data(
    target_company: Optional[str] = Query(None, description="중심 기업명"),
    max_depth: int = Query(3, description="네트워크 깊이", ge=1, le=5),
    relation_types: Optional[str] = Query(
        None, description="관계 유형들 (콤마로 구분)"
    ),
    format: str = Query("json", description="내보내기 형식 (json, csv)"),
    db: Session = Depends(get_db),
):
    """
    네트워크 데이터를 파일로 내보내기

    - **format**: 내보내기 형식 (json, csv)
    """
    try:
        # 관계 유형 파싱
        relation_type_list = None
        if relation_types:
            relation_type_list = [rt.strip() for rt in relation_types.split(",")]

        # 네트워크 데이터 생성
        network_data = network_visualizer.generate_network_data(
            target_company=target_company,
            max_depth=max_depth,
            relation_types=relation_type_list,
            db=db,
        )

        # 파일명 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if target_company:
            filename = f"network_{target_company}_{timestamp}.{format}"
        else:
            filename = f"network_full_{timestamp}.{format}"

        # 파일 경로 생성
        export_dir = Path("data/exports")
        export_dir.mkdir(exist_ok=True)
        file_path = export_dir / filename

        if format == "json":
            network_visualizer.export_network_to_json(network_data, str(file_path))
        else:
            # CSV 형식으로 내보내기 (미구현)
            raise HTTPException(
                status_code=400, detail="CSV 형식은 아직 지원되지 않습니다."
            )

        return APIResponse(
            success=True,
            message=f"네트워크 데이터가 {filename}으로 내보내졌습니다.",
            data={
                "filename": filename,
                "file_path": str(file_path),
                "file_size": (
                    os.path.getsize(file_path) if os.path.exists(file_path) else 0
                ),
                "nodes_count": len(network_data["nodes"]),
                "edges_count": len(network_data["edges"]),
            },
        )

    except Exception as e:
        logger.error(f"네트워크 데이터 내보내기 실패: {e}")
        raise HTTPException(
            status_code=500, detail="네트워크 데이터 내보내기 중 오류가 발생했습니다."
        )


@router.get("/network/evolution", response_model=APIResponse)
def get_network_evolution(
    target_company: str = Query(..., description="대상 기업명"),
    periods: str = Query(..., description="분석 기간들 (JSON 형식)"),
    db: Session = Depends(get_db),
):
    """
    시간에 따른 네트워크 진화 추이 분석

    - **target_company**: 분석할 기업명
    - **periods**: 분석 기간들 JSON (예: [[2024-01-01,2024-03-31],[2024-04-01,2024-06-30]])
    """
    try:
        # 기간 파싱
        try:
            periods_list = json.loads(periods)
            time_periods = [
                (date.fromisoformat(start), date.fromisoformat(end))
                for start, end in periods_list
            ]
        except (json.JSONDecodeError, ValueError) as e:
            raise HTTPException(status_code=400, detail=f"기간 형식 오류: {e}")

        # 네트워크 진화 데이터 생성
        evolution_data = network_visualizer.get_network_evolution(
            target_company=target_company, time_periods=time_periods, db=db
        )

        return APIResponse(
            success=True,
            message=f"네트워크 진화 데이터 생성 완료 ({len(evolution_data)}개 기간)",
            data=evolution_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"네트워크 진화 분석 실패: {e}")
        raise HTTPException(
            status_code=500, detail="네트워크 진화 분석 중 오류가 발생했습니다."
        )


@router.get("/network/companies", response_model=APIResponse)
def get_available_companies(db: Session = Depends(get_db)):
    """네트워크 분석에 사용할 수 있는 기업 목록 조회"""
    try:
        from backend.models.models import Company

        companies = (
            db.query(Company)
            .filter(Company.name.isnot(None))
            .order_by(Company.name)
            .all()
        )

        companies_data = []
        for company in companies:
            companies_data.append(
                {
                    "id": company.id,
                    "name": company.name,
                    "industry": company.industry,
                    "website": company.website,
                    "created_at": company.created_at.isoformat(),
                }
            )

        return APIResponse(
            success=True,
            message=f"{len(companies_data)}개 기업 조회 완료",
            data={"companies": companies_data},
        )

    except Exception as e:
        logger.error(f"기업 목록 조회 실패: {e}")
        raise HTTPException(
            status_code=500, detail="기업 목록 조회 중 오류가 발생했습니다."
        )


@router.get("/network/relation-types", response_model=APIResponse)
def get_relation_types(db: Session = Depends(get_db)):
    """사용 가능한 관계 유형 목록 조회"""
    try:
        from backend.models.models import RelationType

        relation_types = (
            db.query(RelationType)
            .filter(RelationType.is_active == True)
            .order_by(RelationType.type_name)
            .all()
        )

        types_data = []
        for rt in relation_types:
            types_data.append(
                {
                    "id": rt.id,
                    "code": rt.type_code,
                    "name": rt.type_name,
                    "description": rt.description,
                    "color": rt.color,
                    "icon": rt.icon,
                }
            )

        return APIResponse(
            success=True,
            message=f"{len(types_data)}개 관계 유형 조회 완료",
            data={"relation_types": types_data},
        )

    except Exception as e:
        logger.error(f"관계 유형 조회 실패: {e}")
        raise HTTPException(
            status_code=500, detail="관계 유형 조회 중 오류가 발생했습니다."
        )


@router.get("/network/templates", response_model=APIResponse)
def get_visualization_templates():
    """시각화 템플릿 목록 조회"""
    try:
        templates = [
            {
                "id": "basic_network",
                "name": "기본 네트워크",
                "description": "기업 간 기본 협력 관계 네트워크",
                "parameters": {
                    "max_depth": 3,
                    "relation_types": ["MOU", "JOINT_RESEARCH", "PARTNERSHIP"],
                },
            },
            {
                "id": "investment_network",
                "name": "투자 네트워크",
                "description": "기업 투자 및 출자 관계 네트워크",
                "parameters": {
                    "max_depth": 2,
                    "relation_types": ["INVESTMENT", "MERGER", "FUNDING"],
                },
            },
            {
                "id": "research_network",
                "name": "연구 협력 네트워크",
                "description": "대학/연구기관과의 협력 네트워크",
                "parameters": {
                    "max_depth": 4,
                    "relation_types": ["JOINT_RESEARCH", "TECHNOLOGY_TRANSFER"],
                },
            },
            {
                "id": "comprehensive_network",
                "name": "종합 네트워크",
                "description": "모든 관계 유형 포함 네트워크",
                "parameters": {"max_depth": 3, "relation_types": None},  # 모든 유형
            },
        ]

        return APIResponse(
            success=True,
            message=f"{len(templates)}개 시각화 템플릿 조회 완료",
            data={"templates": templates},
        )

    except Exception as e:
        logger.error(f"시각화 템플릿 조회 실패: {e}")
        raise HTTPException(
            status_code=500, detail="시각화 템플릿 조회 중 오류가 발생했습니다."
        )


@router.get("/network/download/{filename}")
def download_exported_file(filename: str):
    """내보낸 파일 다운로드"""
    try:
        file_path = Path("data/exports") / filename

        if not file_path.exists():
            raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")

        return FileResponse(
            path=file_path, filename=filename, media_type="application/octet-stream"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"파일 다운로드 실패: {e}")
        raise HTTPException(
            status_code=500, detail="파일 다운로드 중 오류가 발생했습니다."
        )
