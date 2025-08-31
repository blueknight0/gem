"""
관계 검토 및 수정 서비스 모듈
사용자가 추출된 관계를 검토하고 수정할 수 있는 기능 제공
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from backend.core.database import get_db
from backend.models.models import (
    Relation,
    RelationHistory,
    Company,
    University,
    Professor,
    News,
)

logger = logging.getLogger(__name__)


class ReviewService:
    """관계 검토 및 수정 서비스 클래스"""

    def get_relations_for_review(
        self,
        status: Optional[str] = None,
        confidence_threshold: Optional[float] = None,
        limit: int = 50,
        db: Optional[Session] = None,
    ) -> List[Dict]:
        """
        검토할 관계들 조회

        Args:
            status: 관계 상태 필터 (None이면 extracted, approved, rejected)
            confidence_threshold: 신뢰도 임계값
            limit: 최대 반환 개수
            db: 데이터베이스 세션

        Returns:
            검토할 관계 리스트
        """
        if db is None:
            db = next(get_db())

        try:
            query = db.query(Relation)

            # 상태 필터
            if status:
                query = query.filter(Relation.status == status)
            else:
                # 기본적으로 검토 필요한 상태들
                query = query.filter(Relation.status.in_(["extracted", "modified"]))

            # 신뢰도 필터
            if confidence_threshold is not None:
                query = query.filter(Relation.confidence_score >= confidence_threshold)

            # 정렬 (신뢰도 낮은 순, 최신순)
            relations = (
                query.order_by(
                    Relation.confidence_score.asc(), Relation.created_at.desc()
                )
                .limit(limit)
                .all()
            )

            result = []
            for relation in relations:
                result.append(self._format_relation_for_review(relation))

            logger.info(f"검토용 관계 {len(result)}개 조회 완료")
            return result

        except Exception as e:
            logger.error(f"관계 검토 조회 실패: {e}")
            return []

    def _format_relation_for_review(self, relation: Relation) -> Dict:
        """관계 데이터를 검토용 형식으로 변환"""
        return {
            "id": relation.id,
            "news": {
                "id": relation.news.id,
                "title": relation.news.title,
                "url": relation.news.url,
                "source": relation.news.source,
                "published_date": (
                    relation.news.published_date.isoformat()
                    if relation.news.published_date
                    else None
                ),
            },
            "company_a": (
                {
                    "id": relation.company_a.id if relation.company_a else None,
                    "name": relation.company_a.name if relation.company_a else None,
                }
                if relation.company_a
                else None
            ),
            "company_b": (
                {
                    "id": relation.company_b.id if relation.company_b else None,
                    "name": relation.company_b.name if relation.company_b else None,
                }
                if relation.company_b
                else None
            ),
            "university": (
                {
                    "id": relation.university.id if relation.university else None,
                    "name": relation.university.name if relation.university else None,
                }
                if relation.university
                else None
            ),
            "professor": (
                {
                    "id": relation.professor.id if relation.professor else None,
                    "name": relation.professor.name if relation.professor else None,
                }
                if relation.professor
                else None
            ),
            "relation_type": relation.relation_type,
            "relation_content": relation.relation_content,
            "start_date": (
                relation.start_date.isoformat() if relation.start_date else None
            ),
            "end_date": relation.end_date.isoformat() if relation.end_date else None,
            "confidence_score": relation.confidence_score,
            "status": relation.status,
            "created_at": relation.created_at.isoformat(),
            "updated_at": relation.updated_at.isoformat(),
        }

    def update_relation(
        self,
        relation_id: int,
        updates: Dict,
        modified_by: str,
        reason: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> bool:
        """
        관계 정보 수정

        Args:
            relation_id: 수정할 관계 ID
            updates: 수정할 필드들
            modified_by: 수정자
            reason: 수정 사유
            db: 데이터베이스 세션

        Returns:
            수정 성공 여부
        """
        if db is None:
            db = next(get_db())

        try:
            # 기존 관계 조회
            relation = db.query(Relation).filter(Relation.id == relation_id).first()
            if not relation:
                logger.warning(f"관계 {relation_id}를 찾을 수 없습니다.")
                return False

            # 변경 전 값 저장
            old_values = {
                "relation_type": relation.relation_type,
                "relation_content": relation.relation_content,
                "company_a_id": relation.company_a_id,
                "company_b_id": relation.company_b_id,
                "university_id": relation.university_id,
                "professor_id": relation.professor_id,
                "start_date": relation.start_date,
                "end_date": relation.end_date,
                "status": relation.status,
                "confidence_score": relation.confidence_score,
            }

            # 관계 정보 업데이트
            for key, value in updates.items():
                if hasattr(relation, key):
                    if key in ["company_a", "company_b", "university", "professor"]:
                        # 외래 키 관계 업데이트
                        entity_id = self._get_or_create_entity(db, key, value)
                        setattr(relation, f"{key}_id", entity_id)
                    else:
                        setattr(relation, key, value)

            relation.status = "modified"
            relation.updated_at = datetime.now()

            # 변경 히스토리 기록
            history = RelationHistory(
                relation_id=relation_id,
                change_type="modified",
                old_relation_type=old_values["relation_type"],
                new_relation_type=relation.relation_type,
                old_content=old_values["relation_content"],
                new_content=relation.relation_content,
                old_status=old_values["status"],
                new_status=relation.status,
                changed_by=modified_by,
                change_reason=reason,
            )

            db.add(history)
            db.commit()

            logger.info(f"관계 {relation_id} 수정 완료 (수정자: {modified_by})")
            return True

        except Exception as e:
            logger.error(f"관계 수정 실패: {e}")
            db.rollback()
            return False

    def _get_or_create_entity(
        self, db: Session, entity_type: str, entity_name: str
    ) -> Optional[int]:
        """엔티티 조회 또는 생성"""
        if not entity_name:
            return None

        try:
            if entity_type == "company_a" or entity_type == "company_b":
                # 기업 조회 또는 생성
                entity = db.query(Company).filter(Company.name == entity_name).first()
                if not entity:
                    entity = Company(name=entity_name)
                    db.add(entity)
                    db.flush()  # ID 생성을 위해 flush
                return entity.id

            elif entity_type == "university":
                # 대학 조회 또는 생성
                entity = (
                    db.query(University).filter(University.name == entity_name).first()
                )
                if not entity:
                    entity = University(name=entity_name)
                    db.add(entity)
                    db.flush()
                return entity.id

            elif entity_type == "professor":
                # 교수 조회 (대학 정보가 필요하므로 기본값 사용)
                entity = (
                    db.query(Professor).filter(Professor.name == entity_name).first()
                )
                if not entity:
                    # 기본 대학 ID 사용 (개선 필요)
                    default_university = db.query(University).first()
                    if default_university:
                        entity = Professor(
                            name=entity_name, university_id=default_university.id
                        )
                        db.add(entity)
                        db.flush()
                    else:
                        return None
                return entity.id

        except Exception as e:
            logger.error(f"엔티티 생성 실패 ({entity_type}: {entity_name}): {e}")
            return None

        return None

    def approve_relation(
        self,
        relation_id: int,
        approved_by: str,
        reason: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> bool:
        """
        관계 승인

        Args:
            relation_id: 승인할 관계 ID
            approved_by: 승인자
            reason: 승인 사유
            db: 데이터베이스 세션

        Returns:
            승인 성공 여부
        """
        if db is None:
            db = next(get_db())

        try:
            relation = db.query(Relation).filter(Relation.id == relation_id).first()
            if not relation:
                return False

            old_status = relation.status
            relation.status = "approved"
            relation.updated_at = datetime.now()

            # 승인 히스토리 기록
            history = RelationHistory(
                relation_id=relation_id,
                change_type="approved",
                old_status=old_status,
                new_status="approved",
                changed_by=approved_by,
                change_reason=reason,
            )

            db.add(history)
            db.commit()

            logger.info(f"관계 {relation_id} 승인 완료 (승인자: {approved_by})")
            return True

        except Exception as e:
            logger.error(f"관계 승인 실패: {e}")
            db.rollback()
            return False

    def reject_relation(
        self,
        relation_id: int,
        rejected_by: str,
        reason: str,
        db: Optional[Session] = None,
    ) -> bool:
        """
        관계 거부

        Args:
            relation_id: 거부할 관계 ID
            rejected_by: 거부자
            reason: 거부 사유 (필수)
            db: 데이터베이스 세션

        Returns:
            거부 성공 여부
        """
        if db is None:
            db = next(get_db())

        try:
            relation = db.query(Relation).filter(Relation.id == relation_id).first()
            if not relation:
                return False

            old_status = relation.status
            relation.status = "rejected"
            relation.updated_at = datetime.now()

            # 거부 히스토리 기록
            history = RelationHistory(
                relation_id=relation_id,
                change_type="rejected",
                old_status=old_status,
                new_status="rejected",
                changed_by=rejected_by,
                change_reason=reason,
            )

            db.add(history)
            db.commit()

            logger.info(f"관계 {relation_id} 거부 완료 (거부자: {rejected_by})")
            return True

        except Exception as e:
            logger.error(f"관계 거부 실패: {e}")
            db.rollback()
            return False

    def get_relation_history(
        self, relation_id: int, db: Optional[Session] = None
    ) -> List[Dict]:
        """
        관계 변경 히스토리 조회

        Args:
            relation_id: 관계 ID
            db: 데이터베이스 세션

        Returns:
            변경 히스토리 리스트
        """
        if db is None:
            db = next(get_db())

        try:
            histories = (
                db.query(RelationHistory)
                .filter(RelationHistory.relation_id == relation_id)
                .order_by(RelationHistory.changed_at.desc())
                .all()
            )

            result = []
            for history in histories:
                result.append(
                    {
                        "id": history.id,
                        "change_type": history.change_type,
                        "old_relation_type": history.old_relation_type,
                        "new_relation_type": history.new_relation_type,
                        "old_content": history.old_content,
                        "new_content": history.new_content,
                        "old_status": history.old_status,
                        "new_status": history.new_status,
                        "changed_by": history.changed_by,
                        "change_reason": history.change_reason,
                        "changed_at": history.changed_at.isoformat(),
                    }
                )

            return result

        except Exception as e:
            logger.error(f"관계 히스토리 조회 실패: {e}")
            return []

    def bulk_update_relations(
        self,
        updates: List[Dict],
        modified_by: str,
        reason: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> Dict:
        """
        관계 일괄 수정

        Args:
            updates: 수정할 관계들 [{"relation_id": int, "updates": dict}, ...]
            modified_by: 수정자
            reason: 수정 사유
            db: 데이터베이스 세션

        Returns:
            처리 결과 요약
        """
        if db is None:
            db = next(get_db())

        success_count = 0
        failed_updates = []

        try:
            for update_item in updates:
                relation_id = update_item["relation_id"]
                updates_dict = update_item["updates"]

                success = self.update_relation(
                    relation_id, updates_dict, modified_by, reason, db
                )

                if success:
                    success_count += 1
                else:
                    failed_updates.append(relation_id)

            db.commit()

            result = {
                "total_processed": len(updates),
                "successful": success_count,
                "failed": len(failed_updates),
                "failed_ids": failed_updates,
            }

            logger.info(f"관계 일괄 수정 완료: {result}")
            return result

        except Exception as e:
            logger.error(f"관계 일괄 수정 실패: {e}")
            db.rollback()
            return {
                "total_processed": len(updates),
                "successful": success_count,
                "failed": len(updates) - success_count,
                "error": str(e),
            }

    def get_review_statistics(self, db: Optional[Session] = None) -> Dict:
        """
        검토 통계 조회

        Args:
            db: 데이터베이스 세션

        Returns:
            검토 통계 정보
        """
        if db is None:
            db = next(get_db())

        try:
            # 상태별 관계 수
            status_counts = (
                db.query(Relation.status, db.func.count(Relation.id).label("count"))
                .group_by(Relation.status)
                .all()
            )

            # 신뢰도별 분포
            confidence_ranges = (
                db.query(
                    db.case(
                        (Relation.confidence_score >= 0.8, "high"),
                        (Relation.confidence_score >= 0.6, "medium"),
                        else_="low",
                    ).label("confidence_range"),
                    db.func.count(Relation.id).label("count"),
                )
                .group_by("confidence_range")
                .all()
            )

            # 최근 수정된 관계들
            recent_changes = (
                db.query(Relation)
                .filter(Relation.status.in_(["modified", "approved", "rejected"]))
                .order_by(Relation.updated_at.desc())
                .limit(10)
                .all()
            )

            recent_list = []
            for relation in recent_changes:
                recent_list.append(
                    {
                        "id": relation.id,
                        "relation_type": relation.relation_type,
                        "status": relation.status,
                        "confidence_score": relation.confidence_score,
                        "updated_at": relation.updated_at.isoformat(),
                    }
                )

            return {
                "status_distribution": {
                    status: count for status, count in status_counts
                },
                "confidence_distribution": {
                    range_name: count for range_name, count in confidence_ranges
                },
                "recent_changes": recent_list,
                "total_relations": sum(count for _, count in status_counts),
            }

        except Exception as e:
            logger.error(f"검토 통계 조회 실패: {e}")
            return {}


# 싱글톤 인스턴스
review_service = ReviewService()
