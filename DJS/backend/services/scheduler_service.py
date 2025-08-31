"""
스케줄러 서비스 모듈
기업 조사 자동화 및 주기적 작업 관리
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, date, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session
from backend.core.database import get_db
from backend.services.round_manager import round_manager
from backend.services.naver_search import naver_search_service
from backend.services.llm_extractor import llm_extractor
from backend.services.embedding_service import embedding_service
from backend.models.models import SystemConfig, Company, Round, ScheduledJob

logger = logging.getLogger(__name__)


class SchedulerService:
    """스케줄러 서비스 클래스"""

    def __init__(self):
        self.scheduler = None
        self._initialize_scheduler()
        self.active_jobs = {}

    def _initialize_scheduler(self):
        """스케줄러 초기화"""
        jobstores = {"default": MemoryJobStore()}
        executors = {"default": AsyncIOExecutor()}
        job_defaults = {
            "coalesce": True,  # 중복 작업 병합
            "max_instances": 1,  # 최대 인스턴스 수
            "misfire_grace_time": 30,  # 작업 지연 허용 시간 (초)
        }

        self.scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone="Asia/Seoul",
        )

        logger.info("스케줄러 초기화 완료")

    async def start_scheduler(self):
        """스케줄러 시작"""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("스케줄러 시작됨")

            # 저장된 작업들 복원
            await self._restore_scheduled_jobs()

    async def stop_scheduler(self):
        """스케줄러 중지"""
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown(wait=True)
            logger.info("스케줄러 중지됨")

    def _get_config_value(self, config_key: str, default_value: Any = None) -> Any:
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

    async def schedule_company_investigation(
        self,
        company_name: str,
        cron_expression: Optional[str] = None,
        interval_days: Optional[int] = None,
        max_rounds: int = 3,
        job_name: Optional[str] = None,
    ) -> str:
        """
        기업 조사 작업 스케줄링

        Args:
            company_name: 조사할 기업명
            cron_expression: Cron 표현식 (예: "0 9 * * 1" - 매주 월요일 9시)
            interval_days: 간격 일수
            max_rounds: 최대 라운드 수
            job_name: 작업명 (미지정시 자동 생성)

        Returns:
            작업 ID
        """
        if not job_name:
            job_name = f"investigation_{company_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 트리거 설정
        if cron_expression:
            trigger = CronTrigger.from_crontab(cron_expression)
        elif interval_days:
            trigger = IntervalTrigger(days=interval_days)
        else:
            # 기본값: 매주 월요일 9시
            trigger = CronTrigger.from_crontab("0 9 * * 1")

        # 작업 추가
        job = self.scheduler.add_job(
            func=self._run_company_investigation,
            trigger=trigger,
            args=[company_name, max_rounds],
            id=job_name,
            name=f"기업 조사: {company_name}",
            replace_existing=True,
        )

        # 작업 정보 저장
        self.active_jobs[job.id] = {
            "job_id": job.id,
            "company_name": company_name,
            "max_rounds": max_rounds,
            "trigger": str(trigger),
            "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
        }

        # 데이터베이스에 작업 정보 저장
        await self._save_scheduled_job(job.id, company_name, trigger, max_rounds)

        logger.info(f"기업 조사 작업 스케줄링 완료: {job_name}")
        return job.id

    async def _run_company_investigation(self, company_name: str, max_rounds: int):
        """기업 조사 작업 실행"""
        try:
            logger.info(f"스케줄된 기업 조사 시작: {company_name}")

            db = next(get_db())

            # 기업 조사 실행
            result = await round_manager.start_investigation_round(
                company_name, max_rounds, db
            )

            logger.info(f"스케줄된 기업 조사 완료: {company_name} - {result}")

        except Exception as e:
            logger.error(f"스케줄된 기업 조사 실패 ({company_name}): {e}")

    async def schedule_news_update(
        self,
        search_keywords: List[str],
        cron_expression: str = "0 */6 * * *",  # 6시간마다
        max_results: int = 50,
    ) -> str:
        """
        뉴스 업데이트 작업 스케줄링

        Args:
            search_keywords: 검색 키워드들
            cron_expression: Cron 표현식
            max_results: 최대 결과 수

        Returns:
            작업 ID
        """
        job_name = f"news_update_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        trigger = CronTrigger.from_crontab(cron_expression)

        job = self.scheduler.add_job(
            func=self._run_news_update,
            trigger=trigger,
            args=[search_keywords, max_results],
            id=job_name,
            name="뉴스 업데이트",
            replace_existing=True,
        )

        self.active_jobs[job.id] = {
            "job_id": job.id,
            "type": "news_update",
            "keywords": search_keywords,
            "max_results": max_results,
            "trigger": str(trigger),
            "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
        }

        logger.info(f"뉴스 업데이트 작업 스케줄링 완료: {job_name}")
        return job.id

    async def _run_news_update(self, search_keywords: List[str], max_results: int):
        """뉴스 업데이트 작업 실행"""
        try:
            logger.info(f"스케줄된 뉴스 업데이트 시작: {search_keywords}")

            for keyword in search_keywords:
                try:
                    # 뉴스 검색 및 저장
                    search_results = await naver_search_service.search_news(
                        company_name=keyword, max_results=max_results
                    )

                    if search_results:
                        logger.info(
                            f"키워드 '{keyword}': {len(search_results)}개 뉴스 발견"
                        )

                except Exception as e:
                    logger.warning(f"키워드 '{keyword}' 뉴스 업데이트 실패: {e}")

            logger.info("스케줄된 뉴스 업데이트 완료")

        except Exception as e:
            logger.error(f"스케줄된 뉴스 업데이트 실패: {e}")

    async def schedule_relation_extraction(
        self,
        batch_size: int = 10,
        cron_expression: str = "0 */2 * * *",  # 2시간마다
        min_confidence: float = 0.5,
    ) -> str:
        """
        관계 추출 작업 스케줄링

        Args:
            batch_size: 배치 크기
            cron_expression: Cron 표현식
            min_confidence: 최소 신뢰도

        Returns:
            작업 ID
        """
        job_name = f"relation_extraction_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        trigger = CronTrigger.from_crontab(cron_expression)

        job = self.scheduler.add_job(
            func=self._run_relation_extraction,
            trigger=trigger,
            args=[batch_size, min_confidence],
            id=job_name,
            name="관계 추출",
            replace_existing=True,
        )

        self.active_jobs[job.id] = {
            "job_id": job.id,
            "type": "relation_extraction",
            "batch_size": batch_size,
            "min_confidence": min_confidence,
            "trigger": str(trigger),
            "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
        }

        logger.info(f"관계 추출 작업 스케줄링 완료: {job_name}")
        return job.id

    async def _run_relation_extraction(self, batch_size: int, min_confidence: float):
        """관계 추출 작업 실행"""
        try:
            logger.info("스케줄된 관계 추출 시작")

            db = next(get_db())

            # 추출되지 않은 뉴스 조회
            from backend.models.models import News

            unprocessed_news = (
                db.query(News)
                .filter(
                    News.content.isnot(None),
                    ~News.relations.any(),  # 관계가 없는 뉴스만
                )
                .limit(batch_size)
                .all()
            )

            if not unprocessed_news:
                logger.info("처리할 뉴스가 없습니다.")
                return

            # 뉴스 아이템 포맷팅
            news_items = []
            for news in unprocessed_news:
                news_items.append(
                    {"id": news.id, "title": news.title, "content": news.content}
                )

            # 관계 추출 실행
            extracted_relations = llm_extractor.batch_extract_relations(
                news_items, batch_size=batch_size
            )

            # 신뢰도 필터링
            filtered_relations = [
                relation
                for relation in extracted_relations
                if relation.get("confidence", 0) >= min_confidence
            ]

            logger.info(
                f"스케줄된 관계 추출 완료: {len(filtered_relations)}/{len(extracted_relations)}개 관계 추출"
            )

        except Exception as e:
            logger.error(f"스케줄된 관계 추출 실패: {e}")

    async def schedule_duplicate_detection(
        self,
        cron_expression: str = "0 2 * * *",  # 매일 2시
        similarity_threshold: float = 0.85,
    ) -> str:
        """
        중복 뉴스 탐지 작업 스케줄링

        Args:
            cron_expression: Cron 표현식
            similarity_threshold: 유사도 임계값

        Returns:
            작업 ID
        """
        job_name = f"duplicate_detection_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        trigger = CronTrigger.from_crontab(cron_expression)

        job = self.scheduler.add_job(
            func=self._run_duplicate_detection,
            trigger=trigger,
            args=[similarity_threshold],
            id=job_name,
            name="중복 뉴스 탐지",
            replace_existing=True,
        )

        self.active_jobs[job.id] = {
            "job_id": job.id,
            "type": "duplicate_detection",
            "similarity_threshold": similarity_threshold,
            "trigger": str(trigger),
            "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
        }

        logger.info(f"중복 뉴스 탐지 작업 스케줄링 완료: {job_name}")
        return job.id

    async def _run_duplicate_detection(self, similarity_threshold: float):
        """중복 뉴스 탐지 작업 실행"""
        try:
            logger.info("스케줄된 중복 뉴스 탐지 시작")

            db = next(get_db())

            # 중복 탐지되지 않은 뉴스 조회
            from backend.models.models import News

            news_items = (
                db.query(News)
                .filter(News.is_duplicate.is_(None) | (News.is_duplicate == False))
                .all()
            )

            if not news_items:
                logger.info("처리할 뉴스가 없습니다.")
                return

            # 임베딩 생성
            texts = [f"{news.title} {news.content}" for news in news_items]
            embeddings = embedding_service.encode_texts(texts)

            # 중복 탐지 실행
            duplicate_pairs = embedding_service.find_duplicates(
                embeddings, threshold=similarity_threshold
            )

            # 중복 표시 업데이트
            for i, j in duplicate_pairs:
                if news_items[i].id != news_items[j].id:
                    # 중복 관계 설정
                    news_items[j].is_duplicate = True
                    news_items[j].duplicate_of = news_items[i].id

            db.commit()

            logger.info(
                f"스케줄된 중복 뉴스 탐지 완료: {len(duplicate_pairs)}개 중복쌍 발견"
            )

        except Exception as e:
            logger.error(f"스케줄된 중복 뉴스 탐지 실패: {e}")

    def remove_job(self, job_id: str) -> bool:
        """스케줄된 작업 제거"""
        try:
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
                if job_id in self.active_jobs:
                    del self.active_jobs[job_id]

                # 데이터베이스에서 작업 정보 제거
                self._remove_scheduled_job(job_id)

                logger.info(f"스케줄된 작업 제거됨: {job_id}")
                return True
            else:
                logger.warning(f"작업을 찾을 수 없습니다: {job_id}")
                return False

        except Exception as e:
            logger.error(f"작업 제거 실패: {e}")
            return False

    def get_scheduled_jobs(self) -> Dict[str, Dict]:
        """스케줄된 작업 목록 조회"""
        jobs_info = {}

        for job in self.scheduler.get_jobs():
            job_info = {
                "job_id": job.id,
                "name": job.name,
                "next_run": (
                    job.next_run_time.isoformat() if job.next_run_time else None
                ),
                "trigger": str(job.trigger),
                "active": True,
            }
            jobs_info[job.id] = job_info

        return jobs_info

    def pause_job(self, job_id: str) -> bool:
        """작업 일시 중지"""
        try:
            self.scheduler.pause_job(job_id)
            logger.info(f"작업 일시 중지됨: {job_id}")
            return True
        except Exception as e:
            logger.error(f"작업 일시 중지 실패: {e}")
            return False

    def resume_job(self, job_id: str) -> bool:
        """작업 재개"""
        try:
            self.scheduler.resume_job(job_id)
            logger.info(f"작업 재개됨: {job_id}")
            return True
        except Exception as e:
            logger.error(f"작업 재개 실패: {e}")
            return False

    async def _save_scheduled_job(
        self, job_id: str, company_name: str, trigger: Any, max_rounds: int
    ):
        """스케줄된 작업 정보 데이터베이스에 저장"""
        try:
            db = next(get_db())

            # 기존 작업 정보 확인
            existing_job = (
                db.query(ScheduledJob).filter(ScheduledJob.job_id == job_id).first()
            )

            if existing_job:
                # 업데이트
                existing_job.company_name = company_name
                existing_job.trigger_expression = str(trigger)
                existing_job.max_rounds = max_rounds
                existing_job.updated_at = datetime.now()
            else:
                # 새로 생성
                scheduled_job = ScheduledJob(
                    job_id=job_id,
                    job_type="investigation",
                    company_name=company_name,
                    trigger_expression=str(trigger),
                    max_rounds=max_rounds,
                    is_active=True,
                )
                db.add(scheduled_job)

            db.commit()

        except Exception as e:
            logger.error(f"스케줄된 작업 정보 저장 실패: {e}")

    def _remove_scheduled_job(self, job_id: str):
        """스케줄된 작업 정보 데이터베이스에서 제거"""
        try:
            db = next(get_db())
            db.query(ScheduledJob).filter(ScheduledJob.job_id == job_id).delete()
            db.commit()

        except Exception as e:
            logger.error(f"스케줄된 작업 정보 제거 실패: {e}")

    async def _restore_scheduled_jobs(self):
        """저장된 작업들 복원"""
        try:
            db = next(get_db())
            saved_jobs = (
                db.query(ScheduledJob).filter(ScheduledJob.is_active == True).all()
            )

            for saved_job in saved_jobs:
                try:
                    # 작업 재등록
                    if saved_job.job_type == "investigation":
                        await self.schedule_company_investigation(
                            company_name=saved_job.company_name,
                            cron_expression=saved_job.trigger_expression,
                            max_rounds=saved_job.max_rounds,
                            job_name=saved_job.job_id,
                        )
                    logger.info(f"스케줄된 작업 복원됨: {saved_job.job_id}")

                except Exception as e:
                    logger.warning(f"작업 복원 실패: {saved_job.job_id} - {e}")

        except Exception as e:
            logger.error(f"스케줄된 작업 복원 실패: {e}")

    def get_scheduler_status(self) -> Dict:
        """스케줄러 상태 정보"""
        return {
            "running": self.scheduler.running if self.scheduler else False,
            "active_jobs_count": len(self.active_jobs),
            "jobs": list(self.active_jobs.keys()),
        }


# 싱글톤 인스턴스
scheduler_service = SchedulerService()
