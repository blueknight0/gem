"""
라운드 기반 조사 시스템
기업 검색 라운드를 관리하고 새로운 기업 발견 시 재귀적 검색 수행
"""

import logging
import asyncio
from typing import List, Dict, Optional, Set
from datetime import date, datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from backend.core.database import get_db
from backend.models.models import (
    Round,
    Company,
    University,
    Professor,
    News,
    Relation,
    SystemConfig,
)
from backend.services.naver_search import naver_search_service
from backend.services.llm_extractor import llm_extractor
from backend.services.embedding_service import embedding_service

logger = logging.getLogger(__name__)


class RoundManager:
    """라운드 기반 조사 관리 클래스"""

    def __init__(self):
        self.max_rounds = 5  # 최대 라운드 수
        self.max_companies_per_round = 10  # 라운드당 최대 기업 수
        self.min_confidence_threshold = 0.6  # 최소 신뢰도 임계값

    def _get_config_value(self, config_key: str, default_value: any = None) -> any:
        """시스템 설정 값 조회"""
        try:
            db = next(get_db())
            config = (
                db.query(SystemConfig)
                .filter(SystemConfig.config_key == config_key)
                .first()
            )
            if config:
                if config.config_type == "integer":
                    return int(config.config_value)
                elif config.config_type == "boolean":
                    return config.config_value.lower() == "true"
                else:
                    return config.config_value
            return default_value
        except Exception:
            return default_value

    async def start_investigation_round(
        self,
        target_company: str,
        max_rounds: Optional[int] = None,
        db: Optional[Session] = None,
    ) -> Dict:
        """
        기업 조사 라운드 시작

        Args:
            target_company: 조사할 대상 기업명
            max_rounds: 최대 라운드 수 (기본값: 설정값)
            db: 데이터베이스 세션

        Returns:
            조사 결과 요약
        """
        if max_rounds is None:
            max_rounds = self._get_config_value("max_rounds", 5)

        if db is None:
            db = next(get_db())

        logger.info(f"기업 '{target_company}' 조사 시작 (최대 {max_rounds} 라운드)")

        # 초기 라운드 생성
        initial_round = Round(
            round_number=1,
            target_company=target_company,
            search_date=date.today(),
            status="in_progress",
        )
        db.add(initial_round)
        db.commit()

        # 조사할 기업들 추적
        investigated_companies = {target_company}
        all_rounds = [initial_round]

        try:
            for round_num in range(1, max_rounds + 1):
                logger.info(f"=== 라운드 {round_num} 시작 ===")

                current_round = all_rounds[-1]
                current_targets = []

                if round_num == 1:
                    # 첫 번째 라운드: 지정된 기업 검색
                    current_targets = [target_company]
                else:
                    # 이후 라운드: 이전 라운드에서 발견된 새로운 기업들 검색
                    current_targets = self._get_new_companies_for_round(
                        db, target_company, round_num - 1, investigated_companies
                    )

                if not current_targets:
                    logger.info(f"라운드 {round_num}: 검색할 새로운 기업이 없습니다.")
                    break

                # 현재 라운드 업데이트
                current_round.total_news_found = 0
                current_round.total_relations_extracted = 0

                # 각 대상 기업에 대해 검색 수행
                for company_name in current_targets[: self.max_companies_per_round]:
                    logger.info(f"기업 '{company_name}' 검색 시작")

                    try:
                        # 뉴스 검색
                        search_result = await self._perform_company_search(company_name)
                        if search_result["news_found"] > 0:
                            current_round.total_news_found += search_result[
                                "news_found"
                            ]

                        # 저장 직후 임베딩 생성 및 중복 제거 (자동 워크플로우)
                        if search_result["news_ids"]:
                            try:
                                dedup_stats = (
                                    embedding_service.batch_process_duplicates(
                                        news_ids=search_result["news_ids"],
                                        batch_size=100,
                                    )
                                )
                                logger.info(
                                    f"자동 중복 제거 완료: 처리 {dedup_stats.get('processed', 0)} / 중복 {dedup_stats.get('duplicates_found', 0)} / 표시 {dedup_stats.get('duplicates_marked', 0)}"
                                )
                            except Exception as dedup_err:
                                logger.warning(f"자동 중복 제거 실패: {dedup_err}")

                        # 관계 추출 (대상 기업 고정)
                        if search_result["news_ids"]:
                            extraction_result = await self._perform_relation_extraction(
                                search_result["news_ids"], target_company=company_name
                            )
                            if extraction_result["relations_extracted"] > 0:
                                current_round.total_relations_extracted += (
                                    extraction_result["relations_extracted"]
                                )

                        # 새로운 기업들 추적
                        new_companies = search_result.get("new_companies", [])
                        investigated_companies.update(new_companies)

                    except Exception as e:
                        logger.error(f"기업 '{company_name}' 검색 실패: {e}")
                        continue

                # 라운드 완료 처리
                current_round.status = "completed"
                current_round.updated_at = datetime.now()
                db.commit()

                logger.info(
                    f"라운드 {round_num} 완료: {current_round.total_news_found}개 뉴스, {current_round.total_relations_extracted}개 관계"
                )

                # 다음 라운드를 위한 준비
                if round_num < max_rounds:
                    next_round = Round(
                        round_number=round_num + 1,
                        target_company=target_company,
                        search_date=date.today(),
                        status="pending",
                    )
                    db.add(next_round)
                    all_rounds.append(next_round)
                    db.commit()

            # 전체 조사 완료
            final_result = self._generate_investigation_summary(db, target_company)
            logger.info(
                f"기업 '{target_company}' 조사 완료: 총 {final_result['total_rounds']} 라운드"
            )

            return final_result

        except Exception as e:
            logger.error(f"조사 실패: {e}")
            # 실패 시 현재 라운드 상태 업데이트
            if all_rounds:
                all_rounds[-1].status = "failed"
                db.commit()
            raise

    async def _perform_company_search(self, company_name: str) -> Dict:
        """
        기업 뉴스 검색 수행

        Args:
            company_name: 검색할 기업명

        Returns:
            검색 결과 요약
        """
        try:
            # 뉴스 검색 수행
            search_results = await naver_search_service.search_news(
                company_name=company_name, max_results=50
            )

            if not search_results:
                return {"news_found": 0, "news_ids": [], "new_companies": []}

            # 검색 결과를 데이터베이스에 저장
            db = next(get_db())
            saved_news = []
            existing_news_ids = []
            new_companies = set()

            for result in search_results:
                # 중복 체크
                existing = db.query(News).filter(News.url == result["link"]).first()
                if existing:
                    existing_news_ids.append(existing.id)
                    continue

                # 뉴스 저장
                news = News(
                    title=result["title"],
                    content=result["full_content"],
                    url=result["link"],
                    source=result["source"],
                    published_date=result["pubDate"],
                    search_keyword=company_name,
                )
                db.add(news)
                saved_news.append(news)

                # 뉴스 내용에서 새로운 기업명 추출 시도
                extracted_companies = self._extract_companies_from_text(
                    result["full_content"]
                )
                new_companies.update(extracted_companies)

            db.commit()
            news_ids = [news.id for news in saved_news]
            all_relevant_news_ids = news_ids + existing_news_ids

            logger.info(
                f"기업 '{company_name}': {len(saved_news)}개 신규 뉴스 저장, "
                f"{len(existing_news_ids)}개 기존 뉴스 발견. "
                f"{len(new_companies)}개 새로운 기업 후보 발견"
            )

            return {
                "news_found": len(saved_news),
                "news_ids": all_relevant_news_ids,
                "new_companies": list(new_companies),
            }

        except Exception as e:
            logger.error(f"기업 검색 실패: {e}")
            return {"news_found": 0, "news_ids": [], "new_companies": []}

    async def _perform_relation_extraction(
        self, news_ids: List[int], target_company: Optional[str] = None
    ) -> Dict:
        """
        뉴스에서 관계 추출 수행

        Args:
            news_ids: 관계 추출할 뉴스 ID 리스트

        Returns:
            추출 결과 요약
        """
        try:
            # 뉴스 데이터 조회
            db = next(get_db())
            news_items = []
            for news_id in news_ids:
                news = db.query(News).filter(News.id == news_id).first()
                if news:
                    news_items.append(
                        {"id": news.id, "title": news.title, "content": news.content}
                    )

            if not news_items:
                return {"relations_extracted": 0}

            # 관계 추출 수행 (비동기 병렬)
            extracted_relations = await llm_extractor.batch_extract_relations_async(
                news_items, target_company=target_company
            )

            if not extracted_relations:
                return {"relations_extracted": 0}

            # 관계 저장
            saved_relations = self._save_extracted_relations(db, extracted_relations)

            logger.info(
                f"{len(news_ids)}개 뉴스에서 {len(saved_relations)}개 관계 추출 (대상 기업: {target_company})"
            )

            return {"relations_extracted": len(saved_relations)}

        except Exception as e:
            logger.error(f"관계 추출 실패: {e}")
            return {"relations_extracted": 0}

    def _save_extracted_relations(
        self, db: Session, extracted_relations: List[Dict]
    ) -> List[Relation]:
        """추출된 관계를 데이터베이스에 저장"""
        saved_relations = []

        for relation_data in extracted_relations:
            try:
                # 기업 정보 조회 또는 생성
                company_a_id = self._get_or_create_company(
                    db, relation_data.get("company_a")
                )
                company_b_id = self._get_or_create_company(
                    db, relation_data.get("company_b")
                )
                university_id = self._get_or_create_university(
                    db, relation_data.get("university")
                )
                professor_id = self._get_or_create_professor(
                    db, relation_data.get("professor"), university_id
                )

                # 관계 객체 생성
                relation = Relation(
                    round_id=relation_data.get("round_id", 1),
                    news_id=relation_data["news_id"],
                    company_a_id=company_a_id,
                    company_b_id=company_b_id,
                    university_id=university_id,
                    professor_id=professor_id,
                    relation_type=relation_data["relation_type"],
                    relation_content=relation_data["relation_content"],
                    start_date=relation_data.get("start_date"),
                    end_date=relation_data.get("end_date"),
                    confidence_score=relation_data.get("confidence", 0.5),
                )

                db.add(relation)
                saved_relations.append(relation)

            except Exception as e:
                logger.warning(f"관계 저장 실패: {e}")
                continue

        db.commit()
        return saved_relations

    def _get_or_create_company(
        self, db: Session, company_name: Optional[str]
    ) -> Optional[int]:
        """기업 조회 또는 생성"""
        if not company_name:
            return None

        company = db.query(Company).filter(Company.name == company_name).first()
        if not company:
            company = Company(name=company_name)
            db.add(company)
            db.commit()

        return company.id

    def _get_or_create_university(
        self, db: Session, university_name: Optional[str]
    ) -> Optional[int]:
        """대학 조회 또는 생성"""
        if not university_name:
            return None

        university = (
            db.query(University).filter(University.name == university_name).first()
        )
        if not university:
            university = University(name=university_name)
            db.add(university)
            db.commit()

        return university.id

    def _get_or_create_professor(
        self, db: Session, professor_name: Optional[str], university_id: Optional[int]
    ) -> Optional[int]:
        """교수 조회 또는 생성"""
        if not professor_name or not university_id:
            return None

        from backend.models.models import Professor

        professor = (
            db.query(Professor)
            .filter(
                Professor.name == professor_name,
                Professor.university_id == university_id,
            )
            .first()
        )

        if not professor:
            professor = Professor(name=professor_name, university_id=university_id)
            db.add(professor)
            db.commit()

        return professor.id

    def _extract_companies_from_text(self, text: str) -> Set[str]:
        """텍스트에서 기업명 추출 (단순 패턴 매칭)"""
        import re

        # 기업명 패턴 (개선 필요)
        company_patterns = [
            r"([가-힣a-zA-Z]+(?:주식회사|㈜|주|회사|그룹|홀딩스|산업|테크|랩스?))",
            r"([A-Za-z]+(?:Inc\.?|Corp\.?|Ltd\.?|Co\.?))",
        ]

        companies = set()
        for pattern in company_patterns:
            matches = re.findall(pattern, text)
            companies.update(matches)

        # 너무 짧거나 긴 이름 필터링
        filtered_companies = {
            company
            for company in companies
            if 2 <= len(company) <= 30
            and not any(
                skip in company.lower() for skip in ["기자", "보도", "the", "and"]
            )
        }

        return filtered_companies

    def _get_new_companies_for_round(
        self,
        db: Session,
        target_company: str,
        prev_round_num: int,
        investigated: Set[str],
    ) -> List[str]:
        """다음 라운드에서 조사할 새로운 기업들 조회"""
        try:
            # 이전 라운드에서 추출된 관계들 조회
            prev_round_relations = (
                db.query(Relation)
                .join(Round)
                .filter(
                    Round.round_number == prev_round_num,
                    Round.target_company == target_company,
                    Relation.confidence_score >= self.min_confidence_threshold,
                )
                .all()
            )

            new_companies = set()

            for relation in prev_round_relations:
                # 관계에서 새로운 기업들 추출
                if relation.company_a and relation.company_a.name not in investigated:
                    new_companies.add(relation.company_a.name)
                if relation.company_b and relation.company_b.name not in investigated:
                    new_companies.add(relation.company_b.name)

            return list(new_companies)[: self.max_companies_per_round]

        except Exception as e:
            logger.error(f"새로운 기업 조회 실패: {e}")
            return []

    def _generate_investigation_summary(self, db: Session, target_company: str) -> Dict:
        """조사 결과 요약 생성"""
        try:
            # 모든 라운드 조회
            rounds = (
                db.query(Round)
                .filter(Round.target_company == target_company)
                .order_by(Round.round_number)
                .all()
            )

            total_news = sum(round.total_news_found for round in rounds)
            total_relations = sum(round.total_relations_extracted for round in rounds)

            # 기업별 관계 통계
            company_stats = (
                db.query(Company.name, func.count(Relation.id).label("relation_count"))
                .join(
                    Relation,
                    or_(
                        Company.id == Relation.company_a_id,
                        Company.id == Relation.company_b_id,
                    ),
                )
                .group_by(Company.name)
                .all()
            )

            company_stats_dict = {
                stat.name: stat.relation_count for stat in company_stats
            }

            return {
                "target_company": target_company,
                "total_rounds": len(rounds),
                "total_news_found": total_news,
                "total_relations_extracted": total_relations,
                "company_statistics": company_stats_dict,
                "rounds_summary": [
                    {
                        "round_number": round.round_number,
                        "status": round.status,
                        "news_found": round.total_news_found,
                        "relations_extracted": round.total_relations_extracted,
                        "search_date": round.search_date.isoformat(),
                    }
                    for round in rounds
                ],
            }

        except Exception as e:
            logger.error(f"조사 요약 생성 실패: {e}")
            return {
                "target_company": target_company,
                "error": str(e),
                "total_rounds": 0,
                "total_news_found": 0,
                "total_relations_extracted": 0,
            }

    def approve_round(
        self, round_id: int, approved_by: str, db: Optional[Session] = None
    ) -> bool:
        """라운드 승인"""
        if db is None:
            db = next(get_db())

        try:
            round_obj = db.query(Round).filter(Round.id == round_id).first()
            if round_obj:
                round_obj.status = "approved"
                round_obj.approved_by = approved_by
                round_obj.approved_at = datetime.now()
                db.commit()
                logger.info(f"라운드 {round_id} 승인 완료")
                return True
            return False
        except Exception as e:
            logger.error(f"라운드 승인 실패: {e}")
            db.rollback()
            return False

    def reject_round(
        self, round_id: int, approved_by: str, db: Optional[Session] = None
    ) -> bool:
        """라운드 거부"""
        if db is None:
            db = next(get_db())

        try:
            round_obj = db.query(Round).filter(Round.id == round_id).first()
            if round_obj:
                round_obj.status = "rejected"
                round_obj.approved_by = approved_by
                round_obj.approved_at = datetime.now()
                db.commit()
                logger.info(f"라운드 {round_id} 거부 완료")
                return True
            return False
        except Exception as e:
            logger.error(f"라운드 거부 실패: {e}")
            db.rollback()
            return False


# 싱글톤 인스턴스
round_manager = RoundManager()
