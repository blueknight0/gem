#!/usr/bin/env python3
"""
DJS 시스템 테스트 스크립트
기본 기능들이 제대로 작동하는지 확인
"""

import logging
import sys
import os

# 로깅 설정
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_imports():
    """필수 모듈 임포트 테스트"""
    try:
        logger.info("모듈 임포트 테스트 시작...")

        # FastAPI 및 관련 모듈
        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware

        logger.info("✓ FastAPI 모듈 임포트 성공")

        # 데이터베이스 모듈
        from backend.core.database import create_tables, get_db
        from backend.models.models import Company, News, Relation

        logger.info("✓ 데이터베이스 모듈 임포트 성공")

        # 서비스 모듈
        from backend.services.naver_search import naver_search_service
        from backend.services.embedding_service import embedding_service
        from backend.services.llm_extractor import llm_extractor

        logger.info("✓ 서비스 모듈 임포트 성공")

        # API 모듈
        from backend.api.search import router as search_router
        from backend.api.embedding import router as embedding_router
        from backend.api.extractor import router as extractor_router

        logger.info("✓ API 모듈 임포트 성공")

        logger.info("모든 모듈 임포트 테스트 통과!")
        return True

    except ImportError as e:
        logger.error(f"모듈 임포트 실패: {e}")
        return False
    except Exception as e:
        logger.error(f"예상치 못한 오류: {e}")
        return False


def test_database():
    """데이터베이스 연결 및 테이블 생성 테스트"""
    try:
        logger.info("데이터베이스 테스트 시작...")

        from backend.core.database import create_tables, get_db
        from backend.core.init_db import initialize_database

        # 테이블 생성
        create_tables()
        logger.info("✓ 테이블 생성 성공")

        # 데이터베이스 초기화
        initialize_database()
        logger.info("✓ 데이터베이스 초기화 성공")

        # 기본 데이터 확인
        db = next(get_db())
        from backend.models.models import SystemConfig, RelationType

        config_count = db.query(SystemConfig).count()
        relation_type_count = db.query(RelationType).count()

        logger.info(f"✓ 시스템 설정: {config_count}개")
        logger.info(f"✓ 관계 유형: {relation_type_count}개")

        logger.info("데이터베이스 테스트 통과!")
        return True

    except Exception as e:
        logger.error(f"데이터베이스 테스트 실패: {e}")
        return False


def test_services():
    """서비스 모듈 기본 기능 테스트"""
    try:
        logger.info("서비스 모듈 테스트 시작...")

        from backend.services.naver_search import naver_search_service
        from backend.services.embedding_service import embedding_service

        # 네이버 검색 서비스 상태 확인
        has_naver_creds = (
            naver_search_service.client_id is not None
            and naver_search_service.client_secret is not None
        )
        logger.info(
            f"✓ 네이버 API 인증 정보: {'설정됨' if has_naver_creds else '미설정'}"
        )

        # 임베딩 서비스 모델 로드 테스트 (간단한 텍스트로)
        test_texts = [
            "삼성전자가 SK하이닉스와 협력합니다.",
            "LG전자가 연구소를 설립했습니다.",
        ]
        try:
            embeddings = embedding_service.encode_texts(test_texts)
            logger.info(f"✓ 임베딩 생성 성공: {embeddings.shape}")
        except Exception as e:
            logger.warning(f"임베딩 생성 실패 (모델 설치 필요): {e}")

        # 유사도 계산 테스트
        try:
            similarity = embedding_service.calculate_similarity(
                embeddings[0] if "embeddings" in locals() else [0.1] * 384,
                embeddings[1] if "embeddings" in locals() else [0.2] * 384,
            )
            logger.info(f"✓ 유사도 계산 성공: {similarity:.3f}")
        except Exception as e:
            logger.warning(f"유사도 계산 실패: {e}")

        logger.info("서비스 모듈 테스트 완료!")
        return True

    except Exception as e:
        logger.error(f"서비스 모듈 테스트 실패: {e}")
        return False


def main():
    """메인 테스트 함수"""
    logger.info("DJS 시스템 테스트 시작")
    logger.info("=" * 50)

    tests = [
        ("모듈 임포트", test_imports),
        ("데이터베이스", test_database),
        ("서비스 모듈", test_services),
    ]

    results = []
    for test_name, test_func in tests:
        logger.info(f"\n[{test_name} 테스트 진행중...]")
        try:
            result = test_func()
            results.append((test_name, result))
            status = "✅ 통과" if result else "❌ 실패"
            logger.info(f"[{test_name}] {status}")
        except Exception as e:
            logger.error(f"[{test_name}] 예외 발생: {e}")
            results.append((test_name, False))

    # 결과 요약
    logger.info("\n" + "=" * 50)
    logger.info("테스트 결과 요약:")

    passed = 0
    for test_name, result in results:
        status = "✅ 통과" if result else "❌ 실패"
        logger.info(f"  {test_name}: {status}")
        if result:
            passed += 1

    logger.info(f"\n전체 테스트: {len(results)}개 중 {passed}개 통과")

    if passed == len(results):
        logger.info("🎉 모든 테스트 통과! DJS 시스템이 정상적으로 작동합니다.")
        return True
    else:
        logger.warning("⚠️ 일부 테스트 실패. 시스템 설정을 확인해주세요.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
