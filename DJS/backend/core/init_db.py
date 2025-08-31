"""
DJS 데이터베이스 초기화 스크립트
기본 데이터 및 시스템 설정 초기화
"""

import os
import yaml
import logging
from pathlib import Path
from backend.core.database import get_db, create_tables
from backend.models.models import (
    SystemConfig,
    RelationType,
    Company,
    University,
    Professor,
    User,
)

logger = logging.getLogger(__name__)


def load_config_from_yaml():
    """config.yaml에서 설정을 로드하여 SystemConfig 테이블에 저장"""
    try:
        config_path = Path(__file__).parent.parent.parent / "config.yaml"
        if not config_path.exists():
            logger.warning(f"설정 파일이 존재하지 않습니다: {config_path}")
            return

        logger.info(f"설정 파일 로드 중: {config_path}")

        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        db = next(get_db())

        # Gemini 설정 저장
        if "gemini" in config:
            gemini_config = config["gemini"]
            if "api_key" in gemini_config:
                save_config_to_db(
                    db,
                    "gemini_api_key",
                    gemini_config["api_key"],
                    "string",
                    "Gemini API Key",
                )
            if "model" in gemini_config:
                save_config_to_db(
                    db, "llm_model", gemini_config["model"], "string", "Gemini LLM 모델"
                )

        # 네이버 검색 API 설정 저장
        if "naver" in config:
            naver_config = config["naver"]
            if "client_id" in naver_config:
                save_config_to_db(
                    db,
                    "naver_api_client_id",
                    naver_config["client_id"],
                    "string",
                    "네이버 검색 API Client ID",
                )
            if "client_secret" in naver_config:
                save_config_to_db(
                    db,
                    "naver_api_client_secret",
                    naver_config["client_secret"],
                    "string",
                    "네이버 검색 API Client Secret",
                )

        # 임베딩 설정 저장
        if "embedding" in config:
            embedding_config = config["embedding"]
            if "model" in embedding_config:
                save_config_to_db(
                    db,
                    "embedding_model",
                    embedding_config["model"],
                    "string",
                    "임베딩 모델",
                )
            if "similarity_threshold" in embedding_config:
                save_config_to_db(
                    db,
                    "similarity_threshold",
                    str(embedding_config["similarity_threshold"]),
                    "string",
                    "중복 판별 유사도 임계값",
                )

        # 검색 설정 저장
        if "search" in config:
            search_config = config["search"]
            if "max_news_per_search" in search_config:
                save_config_to_db(
                    db,
                    "max_news_per_search",
                    str(search_config["max_news_per_search"]),
                    "integer",
                    "검색당 최대 뉴스 수",
                )

        # 스케줄러 설정 저장
        if "scheduler" in config:
            scheduler_config = config["scheduler"]
            if "interval_days" in scheduler_config:
                save_config_to_db(
                    db,
                    "scheduler_interval_days",
                    str(scheduler_config["interval_days"]),
                    "integer",
                    "스케줄러 실행 간격 (일)",
                )
            if "auto_approve_threshold" in scheduler_config:
                save_config_to_db(
                    db,
                    "auto_approve_threshold",
                    str(scheduler_config["auto_approve_threshold"]),
                    "string",
                    "자동 승인 신뢰도 임계값",
                )

        # JWT 설정 저장 (선택적)
        if "jwt" in config:
            jwt_config = config["jwt"]
            if "secret" in jwt_config:
                save_config_to_db(
                    db,
                    "jwt_secret",
                    jwt_config["secret"],
                    "string",
                    "JWT 시크릿 키",
                )
            if "algorithm" in jwt_config:
                save_config_to_db(
                    db,
                    "jwt_algorithm",
                    jwt_config["algorithm"],
                    "string",
                    "JWT 알고리즘",
                )
            if "expire_minutes" in jwt_config:
                save_config_to_db(
                    db,
                    "jwt_expire_minutes",
                    str(jwt_config["expire_minutes"]),
                    "integer",
                    "JWT 만료(분)",
                )

        db.commit()
        logger.info("설정 파일 로드 및 저장 완료")

    except Exception as e:
        logger.error(f"설정 파일 로드 실패: {e}")


def save_config_to_db(db, config_key, config_value, config_type, description):
    """설정 값을 데이터베이스에 저장"""
    try:
        # 기존 설정 확인
        existing_config = (
            db.query(SystemConfig).filter(SystemConfig.config_key == config_key).first()
        )

        if existing_config:
            # 기존 값과 다를 때만 업데이트
            if existing_config.config_value != config_value:
                existing_config.config_value = config_value
                logger.info(f"설정 업데이트: {config_key} = {config_value}")
        else:
            # 새 설정 추가
            new_config = SystemConfig(
                config_key=config_key,
                config_value=config_value,
                config_type=config_type,
                description=description,
            )
            db.add(new_config)
            logger.info(f"새 설정 추가: {config_key} = {config_value}")

    except Exception as e:
        logger.error(f"설정 저장 실패 ({config_key}): {e}")


def init_system_config():
    """시스템 설정 초기화"""
    db = next(get_db())

    # 기본 시스템 설정
    default_configs = [
        {
            "config_key": "naver_api_client_id",
            "config_value": "",
            "config_type": "string",
            "description": "네이버 검색 API Client ID",
        },
        {
            "config_key": "naver_api_client_secret",
            "config_value": "",
            "config_type": "string",
            "description": "네이버 검색 API Client Secret",
        },
        {
            "config_key": "openai_api_key",
            "config_value": "",
            "config_type": "string",
            "description": "OpenAI API Key",
        },
        {
            "config_key": "embedding_model",
            "config_value": "sentence-transformers/all-MiniLM-L6-v2",
            "config_type": "string",
            "description": "텍스트 임베딩 모델",
        },
        {
            "config_key": "llm_model",
            "config_value": "gemini-2.5-flash-lite",
            "config_type": "string",
            "description": "LLM 모델",
        },
        {
            "config_key": "similarity_threshold",
            "config_value": "0.85",
            "config_type": "string",
            "description": "중복 판별 유사도 임계값",
        },
        {
            "config_key": "max_news_per_search",
            "config_value": "100",
            "config_type": "integer",
            "description": "검색당 최대 뉴스 수",
        },
        {
            "config_key": "scheduler_interval_days",
            "config_value": "7",
            "config_type": "integer",
            "description": "스케줄러 실행 간격 (일)",
        },
        {
            "config_key": "auto_approve_threshold",
            "config_value": "0.8",
            "config_type": "string",
            "description": "자동 승인 신뢰도 임계값",
        },
        {
            "config_key": "jwt_secret",
            "config_value": "CHANGE_ME_DEV_SECRET",
            "config_type": "string",
            "description": "JWT 시크릿 키",
        },
        {
            "config_key": "jwt_algorithm",
            "config_value": "HS256",
            "config_type": "string",
            "description": "JWT 알고리즘",
        },
        {
            "config_key": "jwt_expire_minutes",
            "config_value": "1440",
            "config_type": "integer",
            "description": "JWT 만료(분)",
        },
    ]

    for config_data in default_configs:
        # 이미 존재하는지 확인
        existing = (
            db.query(SystemConfig)
            .filter(SystemConfig.config_key == config_data["config_key"])
            .first()
        )

        if not existing:
            config = SystemConfig(**config_data)
            db.add(config)
            logger.info(f"시스템 설정 추가: {config_data['config_key']}")

    db.commit()


def init_relation_types():
    """관계 유형 초기화"""
    db = next(get_db())

    relation_types = [
        {
            "type_code": "MOU",
            "type_name": "MOU 체결",
            "description": "업무협약, 양해각서 체결",
            "color": "#4CAF50",
            "icon": "handshake",
        },
        {
            "type_code": "JOINT_RESEARCH",
            "type_name": "공동연구",
            "description": "공동 연구 프로젝트",
            "color": "#2196F3",
            "icon": "flask",
        },
        {
            "type_code": "INVESTMENT",
            "type_name": "투자",
            "description": "투자 유치 또는 투자",
            "color": "#FF9800",
            "icon": "trending-up",
        },
        {
            "type_code": "MERGER",
            "type_name": "M&A",
            "description": "인수합병",
            "color": "#F44336",
            "icon": "merge",
        },
        {
            "type_code": "TECHNOLOGY_TRANSFER",
            "type_name": "기술이전",
            "description": "기술 이전 및 라이선싱",
            "color": "#9C27B0",
            "icon": "transfer",
        },
        {
            "type_code": "PARTNERSHIP",
            "type_name": "파트너십",
            "description": "전략적 파트너십",
            "color": "#00BCD4",
            "icon": "users",
        },
        {
            "type_code": "COLLABORATION",
            "type_name": "협업",
            "description": "일반 협업 관계",
            "color": "#607D8B",
            "icon": "link",
        },
        {
            "type_code": "FUNDING",
            "type_name": "펀딩",
            "description": "연구비 지원",
            "color": "#4CAF50",
            "icon": "dollar-sign",
        },
    ]

    for type_data in relation_types:
        # 이미 존재하는지 확인
        existing = (
            db.query(RelationType)
            .filter(RelationType.type_code == type_data["type_code"])
            .first()
        )

        if not existing:
            relation_type = RelationType(**type_data)
            db.add(relation_type)
            logger.info(f"관계 유형 추가: {type_data['type_code']}")

    db.commit()


def init_sample_data():
    """샘플 데이터 초기화 (개발용)"""
    db = next(get_db())

    # 샘플 기업 데이터
    sample_companies = [
        {"name": "삼성전자", "industry": "전자", "description": "글로벌 전자 기업"},
        {"name": "LG전자", "industry": "전자", "description": "글로벌 전자 기업"},
        {
            "name": "SK하이닉스",
            "industry": "반도체",
            "description": "메모리 반도체 기업",
        },
        {"name": "현대자동차", "industry": "자동차", "description": "자동차 제조 기업"},
        {"name": "포스코", "industry": "철강", "description": "철강 제조 기업"},
    ]

    for company_data in sample_companies:
        existing = (
            db.query(Company).filter(Company.name == company_data["name"]).first()
        )

        if not existing:
            company = Company(**company_data)
            db.add(company)
            logger.info(f"샘플 기업 추가: {company_data['name']}")

    # 샘플 대학 데이터
    sample_universities = [
        {"name": "서울대학교", "location": "서울", "website": "https://www.snu.ac.kr"},
        {"name": "카이스트", "location": "대전", "website": "https://www.kaist.ac.kr"},
        {
            "name": "포항공과대학교",
            "location": "포항",
            "website": "https://www.postech.ac.kr",
        },
        {
            "name": "연세대학교",
            "location": "서울",
            "website": "https://www.yonsei.ac.kr",
        },
        {
            "name": "고려대학교",
            "location": "서울",
            "website": "https://www.korea.ac.kr",
        },
    ]

    for university_data in sample_universities:
        existing = (
            db.query(University)
            .filter(University.name == university_data["name"])
            .first()
        )

        if not existing:
            university = University(**university_data)
            db.add(university)
            logger.info(f"샘플 대학 추가: {university_data['name']}")

    db.commit()


def initialize_database():
    """데이터베이스 전체 초기화"""
    try:
        logger.info("데이터베이스 초기화 시작...")

        # 테이블 생성
        create_tables()
        logger.info("테이블 생성 완료")

        # config.yaml에서 설정 로드
        load_config_from_yaml()
        logger.info("설정 파일 로드 완료")

        # 시스템 설정 초기화 (기본값 설정)
        init_system_config()
        logger.info("시스템 설정 초기화 완료")

        # 관계 유형 초기화
        init_relation_types()
        logger.info("관계 유형 초기화 완료")

        # 샘플 데이터 초기화
        init_sample_data()
        logger.info("샘플 데이터 초기화 완료")

        # 기본 사용자 계정 초기화 (비공개 시스템)
        try:
            db = next(get_db())
            default_users = [
                ("heedo@lghnh.com", "heedo1234", True, True),
                ("test", "testtesttest", True, False),
            ]
            from backend.utils.security import hash_password

            for email, pw, is_active, is_super in default_users:
                if not db.query(User).filter(User.email == email).first():
                    db.add(
                        User(
                            email=email,
                            hashed_password=hash_password(pw),
                            is_active=is_active,
                            is_superuser=is_super,
                        )
                    )
                    logger.info(f"기본 사용자 생성: {email}")
            db.commit()
        except Exception as e:
            logger.error(f"기본 사용자 초기화 실패: {e}")

        logger.info("데이터베이스 초기화 완료!")

    except Exception as e:
        logger.error(f"데이터베이스 초기화 실패: {e}")
        raise


if __name__ == "__main__":
    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    initialize_database()
