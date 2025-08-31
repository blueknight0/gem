"""
네이버 검색 API 통합 모듈
오픈이노베이션 관련 뉴스 검색 기능 구현
"""

import httpx
import json
import asyncio
from typing import List, Dict, Optional
import re
from datetime import datetime, date
from urllib.parse import quote
import logging
from backend.core.database import get_db
from backend.models.models import News, SystemConfig

logger = logging.getLogger(__name__)


class NaverSearchService:
    """네이버 검색 API 서비스 클래스"""

    def __init__(self):
        self.base_url = "https://openapi.naver.com/v1/search/news.json"
        self.client_id = None
        self.client_secret = None
        self.max_results = 100
        self._load_api_credentials()

    def _load_api_credentials(self):
        """시스템 설정에서 API 인증 정보를 로드"""
        try:
            db = next(get_db())
            client_id_config = (
                db.query(SystemConfig)
                .filter(SystemConfig.config_key == "naver_api_client_id")
                .first()
            )
            client_secret_config = (
                db.query(SystemConfig)
                .filter(SystemConfig.config_key == "naver_api_client_secret")
                .first()
            )

            if client_id_config and client_secret_config:
                self.client_id = client_id_config.config_value
                self.client_secret = client_secret_config.config_value
                logger.info("네이버 API 인증 정보 로드 완료")
            else:
                logger.warning("네이버 API 인증 정보가 설정되지 않았습니다.")
        except Exception as e:
            logger.error(f"API 인증 정보 로드 실패: {e}")

    async def search_news(
        self,
        company_name: str,
        keywords: List[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        max_results: int = None,
    ) -> List[Dict]:
        """
        기업명을 검색어로 뉴스 검색 수행

        Args:
            company_name: 검색할 기업명
            keywords: 추가 검색 키워드 리스트
            start_date: 검색 시작일
            end_date: 검색 종료일
            max_results: 최대 검색 결과 수

        Returns:
            뉴스 검색 결과 리스트
        """
        if not self.client_id or not self.client_secret:
            raise ValueError("네이버 API 인증 정보가 설정되지 않았습니다.")

        # 검색어 구성
        search_query = self._build_search_query(company_name, keywords)

        # 검색 파라미터 구성
        params = self._build_search_params(
            search_query, start_date, end_date, max_results
        )

        try:
            results = []
            start = 1

            while len(results) < (max_results or self.max_results):
                params["start"] = start
                batch_results = await self._execute_search_request(params)

                if not batch_results:
                    logger.info(
                        f"네이버 검색 빈 결과: start={start}, params.display={params.get('display')} query={search_query}"
                    )
                    break

                results.extend(batch_results)
                start += len(batch_results)

                # 네이버 API 제한: 한 번에 최대 100개, 총 1000개
                if start > 1000:
                    break

            logger.info(f"총 {len(results)}개의 뉴스 검색 결과 수집 완료")
            return results[:max_results] if max_results else results

        except Exception as e:
            logger.error(f"뉴스 검색 실패: {e}")
            raise

    def _build_search_query(self, company_name: str, keywords: List[str] = None) -> str:
        """검색 쿼리 구성"""
        # 기본 검색어: 기업명
        query_parts = [f'"{company_name}"']

        # 오픈이노베이션 관련 키워드 추가
        innovation_keywords = [
            "오픈이노베이션",
            "개방형혁신",
            "공동연구",
            "협력연구",
            "기술협력",
            "연구협력",
            "MOU",
            "양해각서",
            "투자",
            "기술이전",
            "라이선싱",
            "협업",
            "파트너십",
            "공동개발",
            "R&D",
            "연구개발",
            "산학협력",
            "산학연협력",
        ]

        # 추가 키워드가 있는 경우
        if keywords:
            innovation_keywords.extend(keywords)

        # OR 조건으로 키워드 추가 (네이버 검색은 | 연산을 지원)
        if innovation_keywords:
            keyword_query = " | ".join(f'"{kw}"' for kw in innovation_keywords)
            query_parts.append(f"({keyword_query})")

        return " ".join(query_parts)

    def _build_search_params(
        self,
        query: str,
        start_date: Optional[date],
        end_date: Optional[date],
        max_results: Optional[int],
    ) -> Dict:
        """검색 파라미터 구성"""
        params = {
            "query": query,
            "display": min(100, max_results or self.max_results),  # 한 번에 최대 100개
            "sort": "date",  # 날짜순 정렬
        }

        # 날짜 필터링
        if start_date:
            params["startDate"] = start_date.strftime("%Y%m%d")
        if end_date:
            params["endDate"] = end_date.strftime("%Y%m%d")

        return params

    async def _execute_search_request(self, params: Dict) -> List[Dict]:
        """네이버 API 검색 요청 실행"""
        headers = {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret,
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.base_url, headers=headers, params=params, timeout=30
            )

            if response.status_code != 200:
                logger.error(
                    f"네이버 API 요청 실패: {response.status_code} - {response.text}"
                )
                return []

            data = response.json()
            total = data.get("total")
            start_val = data.get("start")
            display_val = data.get("display")
            logger.info(
                f"네이버 API 응답: total={total}, start={start_val}, display={display_val}"
            )

            # 검색 결과 파싱
            return self._parse_search_results(data.get("items", []))

    def _parse_search_results(self, items: List[Dict]) -> List[Dict]:
        """네이버 검색 결과를 구조화된 형태로 파싱"""
        parsed_results = []

        for item in items:
            try:
                parsed_item = {
                    "title": self._clean_html(item.get("title", "")),
                    "description": self._clean_html(item.get("description", "")),
                    "link": item.get("link", ""),
                    "originallink": item.get("originallink", ""),
                    "pubDate": self._parse_pubdate(item.get("pubDate", "")),
                    "source": self._extract_source(item.get("title", "")),
                    "search_date": datetime.now().date(),
                }

                # 제목과 설명을 결합하여 전체 내용 구성
                full_content = f"{parsed_item['title']}\n\n{parsed_item['description']}"

                parsed_item["full_content"] = full_content
                parsed_results.append(parsed_item)

            except Exception as e:
                logger.warning(f"검색 결과 파싱 실패: {e}")
                continue

        return parsed_results

    def _clean_html(self, text: str) -> str:
        """HTML 태그 제거 및 텍스트 정리"""
        import re

        # HTML 태그 제거
        text = re.sub(r"<[^>]+>", "", text)

        # 특수 문자 디코딩
        text = text.replace("&lt;", "<").replace("&gt;", ">")
        text = text.replace("&amp;", "&").replace("&quot;", '"')
        text = text.replace("&apos;", "'").replace("&#39;", "'")

        # 연속된 공백 제거
        text = re.sub(r"\s+", " ", text).strip()

        return text

    def _parse_pubdate(self, pubdate_str: str) -> Optional[date]:
        """발행일 파싱"""
        from dateutil import parser

        try:
            if not pubdate_str:
                return None

            parsed_date = parser.parse(pubdate_str)
            return parsed_date.date()
        except Exception:
            return None

    def _extract_source(self, title: str) -> Optional[str]:
        """제목에서 언론사 추출"""
        # 일반적인 언론사 패턴
        patterns = [
            r"\[([^\]]+)\]",  # [언론사]
            r"\(([^\)]+)\)",  # (언론사)
            r"\|([^\|]+)$",  # |언론사
        ]

        for pattern in patterns:
            match = re.search(pattern, title)
            if match:
                source = match.group(1).strip()
                # 너무 짧거나 긴 이름 필터링
                if 2 <= len(source) <= 20:
                    return source

        return None

    async def get_news_content(self, url: str) -> Optional[str]:
        """
        뉴스 URL에서 실제 내용 추출
        (네이버 검색 API는 요약만 제공하므로 필요시 구현)
        """
        # TODO: 실제 뉴스 내용 크롤링 구현
        # 보안 및 정책상 실제 구현시 주의 필요
        return None

    def update_api_credentials(self, client_id: str, client_secret: str):
        """API 인증 정보 업데이트"""
        self.client_id = client_id
        self.client_secret = client_secret

        # 데이터베이스에도 업데이트
        try:
            db = next(get_db())

            # Client ID 업데이트
            client_id_config = (
                db.query(SystemConfig)
                .filter(SystemConfig.config_key == "naver_api_client_id")
                .first()
            )
            if client_id_config:
                client_id_config.config_value = client_id
            else:
                client_id_config = SystemConfig(
                    config_key="naver_api_client_id",
                    config_value=client_id,
                    config_type="string",
                    description="네이버 검색 API Client ID",
                )
                db.add(client_id_config)

            # Client Secret 업데이트
            client_secret_config = (
                db.query(SystemConfig)
                .filter(SystemConfig.config_key == "naver_api_client_secret")
                .first()
            )
            if client_secret_config:
                client_secret_config.config_value = client_secret
            else:
                client_secret_config = SystemConfig(
                    config_key="naver_api_client_secret",
                    config_value=client_secret,
                    config_type="string",
                    description="네이버 검색 API Client Secret",
                )
                db.add(client_secret_config)

            db.commit()
            logger.info("네이버 API 인증 정보 업데이트 완료")

        except Exception as e:
            logger.error(f"API 인증 정보 업데이트 실패: {e}")
            db.rollback()
            raise


# 싱글톤 인스턴스
naver_search_service = NaverSearchService()
