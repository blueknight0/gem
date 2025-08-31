"""
LLM 기반 관계 추출 서비스 모듈
Gemini 모델을 활용한 뉴스 기사에서 협력 관계 추출 및 분류
"""

import json
import google.genai as genai
import yaml
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
import logging
import re
from backend.core.database import get_db
from backend.models.models import (
    SystemConfig,
    Company,
    University,
    Professor,
    RelationType,
)

logger = logging.getLogger(__name__)


def load_gemini_api_key():
    """config.yaml에서 Gemini API 키를 직접 로드"""
    try:
        config_path = Path(__file__).parent.parent.parent / "config.yaml"
        if not config_path.exists():
            logger.warning(f"설정 파일이 존재하지 않습니다: {config_path}")
            return None

        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        if "gemini" in config and "api_key" in config["gemini"]:
            api_key = config["gemini"]["api_key"]
            if api_key and api_key.strip():
                return api_key.strip()

        logger.warning("config.yaml에서 Gemini API 키를 찾을 수 없습니다.")
        return None

    except Exception as e:
        logger.error(f"config.yaml 로드 실패: {e}")
        return None


class LLMRelationExtractor:
    """LLM 기반 관계 추출 클래스"""

    def __init__(self):
        self.client = None
        self.model_name = "gemini-2.5-flash"  # 기본 모델
        self.max_tokens = 2000
        self.temperature = 0.3
        # 레이트 리미팅/병렬 처리 설정 (기본 3000 rpm -> 50 rps)
        self.requests_per_minute = 3000
        self.max_requests_per_second = max(1, self.requests_per_minute // 60)
        self._rate_lock = asyncio.Lock()
        self._last_refill_ts = time.monotonic()
        self._available_tokens = self.max_requests_per_second
        self._executor = ThreadPoolExecutor(max_workers=self.max_requests_per_second)
        self._load_model_config()

    def _load_model_config(self):
        """시스템 설정에서 모델 설정 로드"""
        try:
            db = next(get_db())

            # 모델명 설정
            model_config = (
                db.query(SystemConfig)
                .filter(SystemConfig.config_key == "llm_model")
                .first()
            )
            if model_config and model_config.config_value:
                self.model_name = model_config.config_value

            # Gemini API 키 설정 (config.yaml에서 직접 로드)
            api_key = load_gemini_api_key()
            if api_key:
                # 환경변수로 API 키 설정 (최신 SDK 방식)
                import os

                os.environ["GOOGLE_API_KEY"] = api_key
                # 최신 SDK: Client 사용
                self.client = genai.Client()
                logger.info(f"Gemini API 키 설정 완료")
            else:
                logger.warning("Gemini API 키가 설정되지 않았습니다.")

            logger.info(f"LLM 모델 설정 로드 완료: {self.model_name}")

        except Exception as e:
            logger.warning(f"LLM 모델 설정 로드 실패, 기본값 사용: {e}")

    def _get_gemini_client(self):
        """Gemini 클라이언트 초기화"""
        if self.client is None:
            try:
                db = next(get_db())
                # config.yaml에서 API 키 로드
                api_key = load_gemini_api_key()
                if api_key:
                    # 환경변수로 API 키 설정 (최신 SDK 방식)
                    import os

                    os.environ["GOOGLE_API_KEY"] = api_key
                    # 최신 SDK: Client 사용
                    self.client = genai.Client()
                    logger.info("Gemini 클라이언트 초기화 완료")
                else:
                    raise ValueError("Gemini API 키가 설정되지 않았습니다.")
            except Exception as e:
                logger.error(f"Gemini 클라이언트 초기화 실패: {e}")
                raise
        return self.client

    def _get_gemini_api_key_from_config(self) -> Optional[str]:
        """config.yaml에서 Gemini API 키 로드"""
        return load_gemini_api_key()

    def extract_relations_from_news(
        self, news_content: str, target_company: Optional[str] = None
    ) -> List[Dict]:
        """
        뉴스 기사에서 협력 관계 추출

        Args:
            news_content: 뉴스 기사 내용

        Returns:
            추출된 관계 리스트
        """
        try:
            client = self._get_gemini_client()

            # 프롬프트 구성
            prompt = self._build_extraction_prompt(news_content, target_company)

            # 시스템 프롬프트와 사용자 프롬프트 결합
            full_prompt = f"""당신은 뉴스 기사에서 기업 간 협력 관계를 전문적으로 추출하는 AI입니다.

다음 뉴스 기사를 분석하여 기업 간 협력 관계를 JSON 형식으로 추출해주세요:

{prompt}

응답은 반드시 유효한 JSON 형식이어야 합니다."""

            # Gemini API 호출 (최신 SDK)
            response = client.models.generate_content(
                model=self.model_name,
                contents=full_prompt,
                config=genai.types.GenerateContentConfig(
                    temperature=self.temperature,
                    max_output_tokens=self.max_tokens,
                    response_mime_type="application/json",
                ),
            )

            # 응답 파싱
            result_text = response.text
            result_data = json.loads(result_text)

            relations = result_data.get("relations", [])

            # 관계 데이터 검증 및 정제
            validated_relations = []
            for relation in relations:
                validated_relation = self._validate_and_clean_relation(relation)
                if validated_relation:
                    if target_company:
                        tc = target_company.strip()
                        ca = (validated_relation.get("company_a") or "").strip()
                        cb = (validated_relation.get("company_b") or "").strip()
                        # 대상 기업이 company_a 또는 company_b에 포함되어야 함
                        if not (tc and (tc in ca or ca in tc or tc in cb or cb in tc)):
                            continue
                    validated_relations.append(validated_relation)

            logger.info(f"관계 추출 완료: {len(validated_relations)}개 관계 발견")
            return validated_relations

        except Exception as e:
            logger.error(f"관계 추출 실패: {e}")
            return []

    # 내부 동기 호출을 쓰레드에서 실행하기 위한 헬퍼
    def _generate_and_parse_sync(
        self, content: str, target_company: Optional[str] = None
    ) -> List[Dict]:
        client = self._get_gemini_client()
        full_prompt = self._build_extraction_prompt(content, target_company)
        try:
            response = client.models.generate_content(
                model=self.model_name,
                contents=full_prompt,
                config=genai.types.GenerateContentConfig(
                    temperature=self.temperature,
                    max_output_tokens=self.max_tokens,
                    response_mime_type="application/json",
                ),
            )
            result_text = response.text

            # 모델 응답에서 JSON 코드 블록 추출
            json_match = re.search(r"```json\n({.*?})\n```", result_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = result_text

            result_data = json.loads(json_str)
            relations = result_data.get("relations", [])

            validated_relations: List[Dict] = []
            for relation in relations:
                vr = self._validate_and_clean_relation(relation)
                if vr:
                    if target_company:
                        tc = target_company.strip()
                        ca = (vr.get("company_a") or "").strip()
                        cb = (vr.get("company_b") or "").strip()
                        if not (tc and (tc in ca or ca in tc or tc in cb or cb in tc)):
                            continue
                    validated_relations.append(vr)
            return validated_relations
        except json.JSONDecodeError as e:
            logger.error(f"LLM 응답 JSON 파싱 실패: {e}")
            logger.debug(f"원본 LLM 응답: {response.text}")
            return []
        except Exception as e:
            logger.error(f"관계 추출 동기 작업 실패: {e}")
            return []

    async def _acquire_token(self):
        # 간단한 초당 토큰 버킷
        async with self._rate_lock:
            now = time.monotonic()
            elapsed = now - self._last_refill_ts
            # 초당 토큰 리필
            refill = int(elapsed * self.max_requests_per_second)
            if refill > 0:
                self._available_tokens = min(
                    self.max_requests_per_second, self._available_tokens + refill
                )
                self._last_refill_ts = now
            if self._available_tokens == 0:
                # 다음 토큰까지 대기
                await asyncio.sleep(1.0 / self.max_requests_per_second)
                return await self._acquire_token()
            self._available_tokens -= 1

    async def extract_relations_from_news_async(
        self, news_content: str, target_company: Optional[str] = None
    ) -> List[Dict]:
        try:
            await self._acquire_token()
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(
                self._executor,
                self._generate_and_parse_sync,
                news_content,
                target_company,
            )
        except Exception as e:
            logger.error(f"관계 추출 실패(async): {e}")
            return []

    def _build_extraction_prompt(
        self, news_content: str, target_company: Optional[str] = None
    ) -> str:
        """관계 추출을 위한 프롬프트 구성"""
        scope = (
            f"대상 기업은 '{target_company}'입니다. 반드시 대상 기업이 참여한 관계만 추출하고, 대상 기업을 company_a 또는 company_b에 정확히 표기하세요."
            if target_company
            else "대상 기업이 포함된 관계를 우선 추출하세요."
        )
        prompt = f"""
다음 뉴스 기사에서 기업, 대학, 연구기관 간의 협력 관계를 추출해주세요.

기사 내용:
{news_content}

중요 지침: {scope}

다음과 같은 관계 유형을 인식해주세요:
- MOU: 업무협약, 양해각서 체결
- JOINT_RESEARCH: 공동연구, 협동연구
- INVESTMENT: 투자, 출자
- MERGER: 인수합병, M&A
- TECHNOLOGY_TRANSFER: 기술이전, 라이선싱
- PARTNERSHIP: 전략적 파트너십
- COLLABORATION: 일반 협업
- FUNDING: 연구비 지원, 보조금

응답은 다음 JSON 형식으로 해주세요:
{{
    "relations": [
        {{
            "company_a": "기업 A 이름",
            "company_b": "기업 B 이름 (기업 간 관계인 경우)",
            "university": "대학 이름 (대학 관련인 경우)",
            "professor": "교수 이름 (교수 관련인 경우)",
            "relation_type": "관계 유형 코드",
            "relation_content": "관계 내용 요약",
            "start_date": "협력 시작일 (YYYY-MM-DD 형식, 알려지지 않은 경우 null)",
            "end_date": "협력 종료일 (YYYY-MM-DD 형식, 알려지지 않은 경우 null)",
            "confidence": 0.0-1.0 사이의 신뢰도 점수,
            "keywords": ["관련 키워드 배열"]
        }}
    ]
}}

주의사항:
1. 관계가 명확하지 않은 경우 추출하지 마세요
2. 기업, 대학, 교수 이름은 정확히 기재된 대로 추출하세요
3. 관계 유형은 위의 코드 중 하나를 선택하세요
4. 신뢰도는 관계의 명확성과 중요도를 고려하여 0.0-1.0 사이 값으로 설정하세요
5. 관계 내용은 100자 이내로 요약하세요
"""
        return prompt

    def _validate_and_clean_relation(self, relation: Dict) -> Optional[Dict]:
        """추출된 관계 데이터 검증 및 정제"""
        try:
            # 필수 필드 검증
            required_fields = ["relation_type", "relation_content", "confidence"]
            for field in required_fields:
                if field not in relation or not relation[field]:
                    return None

            # 관계 유형 검증
            valid_types = [
                "MOU",
                "JOINT_RESEARCH",
                "INVESTMENT",
                "MERGER",
                "TECHNOLOGY_TRANSFER",
                "PARTNERSHIP",
                "COLLABORATION",
                "FUNDING",
            ]
            if relation["relation_type"] not in valid_types:
                return None

            # 신뢰도 범위 검증
            confidence = float(relation.get("confidence", 0))
            if not 0 <= confidence <= 1:
                confidence = 0.5

            # 날짜 형식 검증 및 변환
            start_date = self._parse_date(relation.get("start_date"))
            end_date = self._parse_date(relation.get("end_date"))

            # 관계 내용 길이 제한
            content = relation["relation_content"]
            if len(content) > 200:
                content = content[:200] + "..."

            # 기업/대학 이름 정제
            company_a = self._clean_entity_name(relation.get("company_a"))
            company_b = self._clean_entity_name(relation.get("company_b"))
            university = self._clean_entity_name(relation.get("university"))
            professor = self._clean_entity_name(relation.get("professor"))

            # 적어도 하나의 참여자가 있어야 함
            if not any([company_a, company_b, university]):
                return None

            return {
                "company_a": company_a,
                "company_b": company_b,
                "university": university,
                "professor": professor,
                "relation_type": relation["relation_type"],
                "relation_content": content,
                "start_date": start_date,
                "end_date": end_date,
                "confidence": confidence,
                "keywords": relation.get("keywords", []),
            }

        except Exception as e:
            logger.warning(f"관계 데이터 정제 실패: {e}")
            return None

    def _parse_date(self, date_str: Optional[str]) -> Optional[str]:
        """날짜 문자열 파싱"""
        if not date_str or date_str.lower() == "null":
            return None

        try:
            # 다양한 날짜 형식 처리
            patterns = [
                r"(\d{4})[./-](\d{1,2})[./-](\d{1,2})",  # YYYY-MM-DD
                r"(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일",  # YYYY년 MM월 DD일
            ]

            for pattern in patterns:
                match = re.search(pattern, date_str)
                if match:
                    year, month, day = match.groups()
                    return "04d"

            return None
        except Exception:
            return None

    def _clean_entity_name(self, name: Optional[str]) -> Optional[str]:
        """기업/대학 이름 정제"""
        if not name or name.lower() == "null":
            return None

        # 불필요한 공백 및 특수문자 제거
        name = re.sub(r"\s+", " ", name.strip())
        name = re.sub(r"[()【】\[\]]", "", name)

        # 너무 짧거나 긴 이름 필터링
        if len(name) < 2 or len(name) > 100:
            return None

        return name

    def batch_extract_relations(
        self, news_items: List[Dict], batch_size: int = 5
    ) -> List[Dict]:
        """
        뉴스 기사 배치에서 관계 추출

        Args:
            news_items: 뉴스 기사 리스트
            batch_size: 배치 크기

        Returns:
            추출된 관계 리스트 (news_id 포함)
        """
        all_relations = []

        for i in range(0, len(news_items), batch_size):
            batch = news_items[i : i + batch_size]

            for news_item in batch:
                try:
                    news_id = news_item.get("id")
                    content = news_item.get("content", "") or news_item.get(
                        "full_content", ""
                    )

                    if not content:
                        continue

                    # 관계 추출
                    relations = self.extract_relations_from_news(content)

                    # news_id 추가
                    for relation in relations:
                        relation["news_id"] = news_id
                        all_relations.append(relation)

                except Exception as e:
                    logger.warning(
                        f"뉴스 관계 추출 실패 (ID: {news_item.get('id')}): {e}"
                    )
                    continue

            logger.info(
                f"배치 처리 진행중: {min(i + batch_size, len(news_items))}/{len(news_items)}"
            )

        logger.info(f"배치 관계 추출 완료: 총 {len(all_relations)}개 관계 추출")
        return all_relations

    async def batch_extract_relations_async(
        self, news_items: List[Dict], target_company: Optional[str] = None
    ) -> List[Dict]:
        """뉴스 리스트에 대해 병렬/레이트리미팅을 적용한 비동기 관계 추출"""
        all_relations: List[Dict] = []
        semaphore = asyncio.Semaphore(self.max_requests_per_second)

        async def process_item(item: Dict):
            async with semaphore:
                news_id = item.get("id")
                content = item.get("content", "") or item.get("full_content", "")
                if not content:
                    return
                rels = await self.extract_relations_from_news_async(
                    content, target_company
                )
                for r in rels:
                    r["news_id"] = news_id
                return rels

        tasks = [process_item(it) for it in news_items]
        for coro in asyncio.as_completed(tasks):
            try:
                res = await coro
                if res:
                    all_relations.extend(res)
            except Exception as e:
                logger.warning(f"뉴스 관계 추출 실패(async): {e}")
                continue

        logger.info(f"비동기 배치 관계 추출 완료: 총 {len(all_relations)}개 관계 추출")
        return all_relations

    def classify_relation_type(self, relation_content: str) -> Tuple[str, float]:
        """
        관계 내용을 기반으로 관계 유형 분류

        Args:
            relation_content: 관계 내용

        Returns:
            (관계 유형, 신뢰도)
        """
        try:
            client = self._get_gemini_client()

            prompt = f"""다음 관계 내용을 분석하여 가장 적합한 관계 유형을 분류해주세요:

관계 내용: {relation_content}

가능한 관계 유형:
- MOU: 업무협약, 양해각서 체결
- JOINT_RESEARCH: 공동연구, 협동연구
- INVESTMENT: 투자, 출자
- MERGER: 인수합병, M&A
- TECHNOLOGY_TRANSFER: 기술이전, 라이선싱
- PARTNERSHIP: 전략적 파트너십
- COLLABORATION: 일반 협업
- FUNDING: 연구비 지원, 보조금

응답 형식:
{{
    "relation_type": "분류된 유형 코드",
    "confidence": 0.0-1.0 신뢰도 점수,
    "reason": "분류 근거 설명"
}}

응답은 반드시 유효한 JSON 형식이어야 합니다."""

            response = client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=genai.types.GenerateContentConfig(
                    temperature=0.2,
                    max_output_tokens=500,
                    response_mime_type="application/json",
                ),
            )

            result_text = response.text
            result_data = json.loads(result_text)

            return result_data.get("relation_type", "COLLABORATION"), result_data.get(
                "confidence", 0.5
            )

        except Exception as e:
            logger.error(f"관계 유형 분류 실패: {e}")
            return "COLLABORATION", 0.5

    def update_api_key(self, api_key: str):
        """Gemini API 키 업데이트"""
        try:
            # 데이터베이스에 저장
            db = next(get_db())
            api_config = (
                db.query(SystemConfig)
                .filter(SystemConfig.config_key == "gemini_api_key")
                .first()
            )

            if api_config:
                api_config.config_value = api_key
            else:
                api_config = SystemConfig(
                    config_key="gemini_api_key",
                    config_value=api_key,
                    config_type="string",
                    description="Gemini API Key",
                )
                db.add(api_config)

            db.commit()

            # 클라이언트 재초기화 (환경변수 방식)
            import os

            os.environ["GOOGLE_API_KEY"] = api_key
            # 최신 SDK: Client 사용
            self.client = genai.Client()

            logger.info("Gemini API 키 업데이트 완료")

        except Exception as e:
            logger.error(f"API 키 업데이트 실패: {e}")
            raise


# 싱글톤 인스턴스
llm_extractor = LLMRelationExtractor()
