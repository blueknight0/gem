"""
텍스트 임베딩 서비스 모듈
Gemini 임베딩을 활용한 텍스트 유사도 계산 및 중복 제거
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
import google.genai as genai
import yaml
import pickle
import os
from pathlib import Path
import logging
from sklearn.metrics.pairwise import cosine_similarity
from backend.core.database import get_db
from backend.models.models import News, SystemConfig

logger = logging.getLogger(__name__)


class EmbeddingService:
    """텍스트 임베딩 서비스 클래스"""

    def __init__(self):
        self.model = None
        self.model_name = "models/gemini-embedding-001"  # Gemini 임베딩 모델
        self.similarity_threshold = 0.85  # 유사도 임계값
        self.embedding_cache = {}  # 임베딩 캐시
        self._load_model_config()

    def _load_model_config(self):
        """시스템 설정에서 모델 설정 로드"""
        try:
            db = next(get_db())

            # 모델명 설정
            model_config = (
                db.query(SystemConfig)
                .filter(SystemConfig.config_key == "embedding_model")
                .first()
            )
            if model_config and model_config.config_value:
                self.model_name = model_config.config_value

            # 유사도 임계값 설정
            threshold_config = (
                db.query(SystemConfig)
                .filter(SystemConfig.config_key == "similarity_threshold")
                .first()
            )
            if threshold_config and threshold_config.config_value:
                try:
                    self.similarity_threshold = float(threshold_config.config_value)
                except ValueError:
                    logger.warning("유사도 임계값 파싱 실패, 기본값 사용")

            # Gemini API 키 설정 (임베딩에도 필요) - config.yaml에서 직접 로드
            try:
                config_path = Path(__file__).parent.parent.parent / "config.yaml"
                if config_path.exists():
                    with open(config_path, "r", encoding="utf-8") as f:
                        config = yaml.safe_load(f)

                    if "gemini" in config and "api_key" in config["gemini"]:
                        api_key = config["gemini"]["api_key"]
                        if api_key and api_key.strip():
                            import os

                            os.environ["GOOGLE_API_KEY"] = api_key.strip()
                            logger.info("Gemini 임베딩 API 키 설정 완료")
                        else:
                            logger.warning("Gemini API 키가 비어있습니다.")
                    else:
                        logger.warning(
                            "config.yaml에서 Gemini 설정을 찾을 수 없습니다."
                        )
                else:
                    logger.warning(f"설정 파일이 존재하지 않습니다: {config_path}")
            except Exception as e:
                logger.warning(f"Gemini API 키 설정 실패: {e}")

            logger.info(
                f"임베딩 모델 설정 로드 완료: {self.model_name}, 임계값: {self.similarity_threshold}"
            )

        except Exception as e:
            logger.warning(f"모델 설정 로드 실패, 기본값 사용: {e}")

    def _load_model(self):
        """Gemini 임베딩 모델 초기화"""
        if self.model is None:
            try:
                logger.info(f"Gemini 임베딩 모델 초기화 중: {self.model_name}")
                # Gemini 임베딩 모델은 별도 초기화가 필요하지 않음
                # API 키는 이미 설정되어 있어야 함
                self.model = True  # 초기화 완료 표시
                logger.info("Gemini 임베딩 모델 초기화 완료")
            except Exception as e:
                logger.error(f"Gemini 임베딩 모델 초기화 실패: {e}")
                raise

    def encode_texts(self, texts: List[str]) -> np.ndarray:
        """
        텍스트 리스트를 Gemini 임베딩 벡터로 변환

        Args:
            texts: 임베딩할 텍스트 리스트

        Returns:
            임베딩 벡터 배열 (shape: [len(texts), embedding_dim])
        """
        self._load_model()

        try:
            embeddings = []
            # 최신 SDK: Client 사용
            client = genai.Client()
            response = client.models.embed_content(
                model=self.model_name,
                contents=texts,
            )
            # EmbedContentResponse.embeddings -> list[ContentEmbedding]
            for emb in response.embeddings or []:
                embeddings.append(np.array(emb.values, dtype=float))

            embeddings_array = np.array(embeddings)
            logger.info(f"{len(texts)}개 텍스트 Gemini 임베딩 생성 완료")
            return embeddings_array

        except Exception as e:
            logger.error(f"Gemini 텍스트 임베딩 생성 실패: {e}")
            raise

    def calculate_similarity(
        self, embedding1: np.ndarray, embedding2: np.ndarray
    ) -> float:
        """
        두 임베딩 벡터 간 코사인 유사도 계산

        Args:
            embedding1: 첫 번째 임베딩 벡터
            embedding2: 두 번째 임베딩 벡터

        Returns:
            코사인 유사도 (0.0 ~ 1.0)
        """
        try:
            similarity = cosine_similarity(
                embedding1.reshape(1, -1), embedding2.reshape(1, -1)
            )[0][0]

            # 유사도를 0-1 범위로 정규화
            similarity = max(0.0, min(1.0, similarity))
            return similarity

        except Exception as e:
            logger.error(f"유사도 계산 실패: {e}")
            return 0.0

    def find_duplicates(
        self, texts: List[str], threshold: Optional[float] = None
    ) -> List[Tuple[int, int, float]]:
        """
        텍스트 리스트에서 중복 항목 찾기

        Args:
            texts: 검사할 텍스트 리스트
            threshold: 유사도 임계값 (기본값: 설정값)

        Returns:
            중복 쌍 리스트 [(index1, index2, similarity), ...]
        """
        if threshold is None:
            threshold = self.similarity_threshold

        if len(texts) < 2:
            return []

        try:
            # 모든 텍스트 임베딩 계산
            embeddings = self.encode_texts(texts)

            duplicates = []

            # 모든 쌍에 대해 유사도 계산
            for i in range(len(texts)):
                for j in range(i + 1, len(texts)):
                    similarity = self.calculate_similarity(embeddings[i], embeddings[j])

                    if similarity >= threshold:
                        duplicates.append((i, j, similarity))

            logger.info(f"중복 검사 완료: {len(duplicates)}개 중복 발견")
            return duplicates

        except Exception as e:
            logger.error(f"중복 검사 실패: {e}")
            return []

    def deduplicate_news_batch(
        self, news_items: List[Dict], threshold: Optional[float] = None
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        뉴스 기사 배치에서 중복 제거

        Args:
            news_items: 뉴스 기사 리스트
            threshold: 유사도 임계값

        Returns:
            (유일한 뉴스 리스트, 중복 뉴스 리스트)
        """
        if not news_items:
            return [], []

        try:
            # 뉴스 제목과 내용 결합하여 텍스트 생성
            texts = []
            for item in news_items:
                text = f"{item.get('title', '')} {item.get('description', '')}".strip()
                texts.append(text)

            # 중복 찾기
            duplicates = self.find_duplicates(texts, threshold)

            if not duplicates:
                return news_items, []

            # 중복 그룹화
            duplicate_groups = self._group_duplicates(duplicates, len(news_items))

            # 각 그룹에서 대표 뉴스 선택 (가장 긴 내용의 뉴스)
            unique_news = []
            duplicate_news = []

            for group in duplicate_groups:
                if len(group) == 1:
                    unique_news.append(news_items[group[0]])
                else:
                    # 그룹 내에서 가장 긴 내용을 가진 뉴스를 대표로 선택
                    representative_idx = max(group, key=lambda i: len(texts[i]))
                    unique_news.append(news_items[representative_idx])

                    # 나머지는 중복으로 처리
                    for idx in group:
                        if idx != representative_idx:
                            duplicate_news.append(
                                {
                                    **news_items[idx],
                                    "duplicate_of": representative_idx,
                                    "similarity_score": max(
                                        sim
                                        for i, j, sim in duplicates
                                        if (i == representative_idx and j == idx)
                                        or (i == idx and j == representative_idx)
                                    ),
                                }
                            )

            logger.info(
                f"중복 제거 완료: {len(unique_news)}개 유일, {len(duplicate_news)}개 중복"
            )
            return unique_news, duplicate_news

        except Exception as e:
            logger.error(f"뉴스 중복 제거 실패: {e}")
            return news_items, []

    def _group_duplicates(
        self, duplicates: List[Tuple[int, int, float]], total_items: int
    ) -> List[List[int]]:
        """중복 쌍을 그룹으로 묶기"""
        # Union-Find 알고리즘으로 연결된 그룹 찾기
        parent = list(range(total_items))

        def find(x):
            if parent[x] != x:
                parent[x] = find(parent[x])
            return parent[x]

        def union(x, y):
            px, py = find(x), find(y)
            if px != py:
                parent[px] = py

        # 중복 쌍으로 연결
        for i, j, _ in duplicates:
            union(i, j)

        # 그룹화
        groups = {}
        for i in range(total_items):
            root = find(i)
            if root not in groups:
                groups[root] = []
            groups[root].append(i)

        return list(groups.values())

    def save_embeddings_to_db(self, news_items: List[Dict]) -> List[Dict]:
        """
        뉴스 임베딩을 계산하여 데이터베이스에 저장

        Args:
            news_items: 임베딩을 계산할 뉴스 리스트

        Returns:
            임베딩이 추가된 뉴스 리스트
        """
        if not news_items:
            return news_items

        try:
            # 임베딩할 텍스트 준비
            texts = []
            for item in news_items:
                text = f"{item.get('title', '')} {item.get('description', '')}".strip()
                texts.append(text)

            # 임베딩 계산
            embeddings = self.encode_texts(texts)

            # 뉴스 항목에 임베딩 추가
            for i, item in enumerate(news_items):
                item["embedding_vector"] = pickle.dumps(
                    embeddings[i].astype(np.float32)
                )

            logger.info(f"{len(news_items)}개 뉴스의 임베딩 저장 준비 완료")
            return news_items

        except Exception as e:
            logger.error(f"임베딩 저장 준비 실패: {e}")
            return news_items

    def compare_news_similarity(self, news_id1: int, news_id2: int) -> Optional[float]:
        """
        두 뉴스 간 유사도 계산

        Args:
            news_id1: 첫 번째 뉴스 ID
            news_id2: 두 번째 뉴스 ID

        Returns:
            유사도 점수 (없으면 None)
        """
        try:
            db = next(get_db())

            news1 = db.query(News).filter(News.id == news_id1).first()
            news2 = db.query(News).filter(News.id == news_id2).first()

            if (
                not news1
                or not news2
                or not news1.embedding_vector
                or not news2.embedding_vector
            ):
                return None

            # 임베딩 벡터 로드
            embedding1 = pickle.loads(news1.embedding_vector)
            embedding2 = pickle.loads(news2.embedding_vector)

            return self.calculate_similarity(embedding1, embedding2)

        except Exception as e:
            logger.error(f"뉴스 유사도 계산 실패: {e}")
            return None

    def batch_process_duplicates(
        self, news_ids: List[int] = None, batch_size: int = 100
    ) -> Dict:
        """
        데이터베이스의 뉴스 중복 일괄 처리

        Args:
            news_ids: 처리할 뉴스 ID 리스트 (None이면 전체)
            batch_size: 배치 크기

        Returns:
            처리 결과 통계
        """
        try:
            db = next(get_db())

            # 처리할 뉴스 쿼리
            query = db.query(News)
            if news_ids:
                query = query.filter(News.id.in_(news_ids))

            # 임베딩이 있는 뉴스만 선택
            news_with_embeddings = query.filter(
                News.embedding_vector.isnot(None), News.is_duplicate == False
            ).all()

            if len(news_with_embeddings) < 2:
                return {"processed": 0, "duplicates_found": 0, "duplicates_marked": 0}

            # 배치 처리
            total_processed = 0
            total_duplicates = 0
            total_marked = 0

            for i in range(0, len(news_with_embeddings), batch_size):
                batch = news_with_embeddings[i : i + batch_size]
                batch_texts = [
                    f"{news.title} {news.content[:500]}".strip() for news in batch
                ]

                # 중복 찾기
                duplicates = self.find_duplicates(batch_texts)

                if duplicates:
                    # 중복 표시
                    for idx1, idx2, similarity in duplicates:
                        news1 = batch[idx1]
                        news2 = batch[idx2]

                        # 이미 중복 표시된 뉴스는 건너뜀
                        if news2.is_duplicate:
                            continue

                        news2.is_duplicate = True
                        news2.duplicate_of = news1.id
                        total_marked += 1

                total_processed += len(batch)
                total_duplicates += len(duplicates)

            db.commit()

            result = {
                "processed": total_processed,
                "duplicates_found": total_duplicates,
                "duplicates_marked": total_marked,
                "batch_size": batch_size,
            }

            logger.info(f"중복 일괄 처리 완료: {result}")
            return result

        except Exception as e:
            logger.error(f"중복 일괄 처리 실패: {e}")
            db.rollback()
            return {"error": str(e)}


# 싱글톤 인스턴스
embedding_service = EmbeddingService()
