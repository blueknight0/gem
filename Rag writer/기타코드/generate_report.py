import os
import google.generativeai as genai
from google.generativeai import types
from dotenv import load_dotenv
import re
import json
from datetime import datetime
import argparse

# =============================================================================
# 모델 설정 구성 (테스트/프로덕션 환경에 따라 조정)
# =============================================================================

# 저렴한 모델들로 테스트할 때 사용
TEST_MODELS = {
    "outline_generation": "gemini-2.5-flash-lite-preview-06-17",  # 개요 생성
    "content_analysis": "gemini-2.5-flash-lite-preview-06-17",  # 콘텐츠 분석 (중복 검사 등)
    "draft_generation": "gemini-2.5-flash-lite-preview-06-17",  # 초안 생성
    "editorial_review": "gemini-2.5-flash-lite-preview-06-17",  # 편집장 검토
    "quality_check": "gemini-2.5-flash-lite-preview-06-17",  # 품질 검사
    "reference_extraction": "gemini-2.5-flash-lite-preview-06-17",  # 참고문헌 추출
}

# 프로덕션에서 사용할 고급 모델들
PRODUCTION_MODELS = {
    "outline_generation": "gemini-2.5-pro",
    "content_analysis": "gemini-2.5-pro",
    "draft_generation": "gemini-2.5-pro",
    "editorial_review": "gemini-2.5-pro",
    "quality_check": "gemini-2.5-pro",
    "reference_extraction": "gemini-2.5-pro",
}

# =============================================================================
# Thinking Budget 설정
# =============================================================================

# 테스트 모드에서는 모든 작업에 thinking_budget을 0으로 설정
TEST_THINKING_BUDGETS = {
    "outline_generation": 0,
    "content_analysis": 0,
    "draft_generation": 0,
    "editorial_review": 0,
    "quality_check": 0,
    "reference_extraction": 0,
}

# 프로덕션 모드에서는 편집장 검토와 품질 검사를 제외하고 0으로 설정
PRODUCTION_THINKING_BUDGETS = {
    "outline_generation": 0,
    "content_analysis": 0,
    "draft_generation": 0,
    "editorial_review": 8192,  # None은 기본값을 사용하도록 함
    "quality_check": 8192,  # None은 기본값을 사용하도록 함
    "reference_extraction": 0,
}

# 사용할 모델 세트 선택 (True: 프로덕션, False: 테스트)
USE_PRODUCTION_MODELS = True

# 현재 사용할 모델 및 예산 설정
CURRENT_MODELS = PRODUCTION_MODELS if USE_PRODUCTION_MODELS else TEST_MODELS
CURRENT_BUDGETS = (
    PRODUCTION_THINKING_BUDGETS if USE_PRODUCTION_MODELS else TEST_THINKING_BUDGETS
)

# 개별 작업별 모델 오버라이드 (필요시 특정 작업만 다른 모델 사용)
MODEL_OVERRIDES = {
    # 예: 'outline_generation': 'gemini-2.5-pro',  # 개요 생성만 고급 모델 사용
    # 예: 'quality_check': 'gemini-2.5-pro',       # 품질 검사만 고급 모델 사용
}

# 최종 모델 설정 (오버라이드 적용)
MODELS = {**CURRENT_MODELS, **MODEL_OVERRIDES}
THINKING_BUDGETS = {**CURRENT_BUDGETS}

# =============================================================================
# 프롬프트 템플릿 상수
# =============================================================================
# 다른 프로젝트에서도 재활용할 수 있도록, 개요 생성을 위한 프롬프트를
# 별도의 상수로 분리합니다. `{content}` 플레이스홀더에 통합 문서 내용이
# 삽입됩니다.
OUTLINE_PROMPT_TEMPLATE = """
다음은 '사내 변호사의 비밀유지권'에 대한 여러 리서치 보고서를 합친 내용입니다.
이 전체 내용을 기반으로, 하나의 일관된 흐름을 갖는 종합 보고서를 작성하려고 합니다.
보고서의 새로운 핵심 주제는 "사내 변호사를 위한 ACP의 국내 도입을 위한 유럽 사례 연구조사" 입니다.

**지시사항:**
1.  **유럽 중심 재구성:** 보고서의 전체 구조를 유럽의 사례(EU, 독일, 프랑스 등)를 중심으로 재구성해주세요.
2.  **포괄성 및 내용 보존:** **가장 중요한 점입니다.** 원본 문서의 모든 핵심적인 내용(다른 국가, 이론적 배경 등)이 최종 보고서에서 절대 소실되지 않도록 해야 합니다. 유럽 외 국가의 정보는 유럽 사례와 비교/대조하거나, 이론적 배경, 또는 국내 도입 논의를 위한 참고 자료로서 반드시 목차에 포함시켜주세요. 어떤 정보도 누락해서는 안 됩니다.
3.  **최종 목표:** 최종적으로 이 보고서는 한국에 사내 변호사 ACP를 도입하기 위한 법적, 정책적 시사점을 도출하는 것을 목표로 합니다.

위 지시사항에 따라, 논리적이고 체계적인 보고서 목차(개요)를 마크다운 형식으로 생성해주세요.
서론, 본론(유럽 사례 중심의 여러 장과 절 포함), 결론(국내 도입을 위한 제언)이 포함되어야 합니다.

--- 통합 문서 내용 ---
{content}
"""

# =============================================================================
# 기존 함수들
# =============================================================================


def get_model_for_task(task_name):
    """
    특정 작업에 사용할 모델을 반환합니다.
    """
    model_name = MODELS.get(task_name, "gemini-1.5-flash")  # 기본값
    print(f"[{task_name}] 모델: {model_name}")

    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    return genai.GenerativeModel(model_name)


def configure_genai():
    """API 키를 로드하고 genai를 설정합니다."""
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY가 .env 파일에 설정되지 않았습니다.")


def generate_content(model, prompt):
    """
    모델을 사용하여 콘텐츠를 생성합니다.
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"콘텐츠 생성 중 오류 발생: {e}")
        return None


def print_model_configuration():
    """
    현재 모델 설정을 출력합니다.
    """
    mode = "프로덕션" if USE_PRODUCTION_MODELS else "테스트"
    print(f"\n=== 모델 설정 ({mode} 모드) ===")
    for task, model in MODELS.items():
        budget = THINKING_BUDGETS.get(task)
        budget_str = (
            f" (Thinking Budget: {budget})"
            if budget is not None
            else " (Thinking Budget: 기본값)"
        )
        print(f"  {task}: {model}{budget_str}")
    print("=" * 50)


def read_all_source_files(source_dir="sources"):
    """
    source_dir 내의 모든 .md 파일 내용을 읽어 하나의 문자열로 합칩니다.
    각 파일 내용 사이에는 구분선을 추가합니다.
    """
    all_content = []
    try:
        file_names = [f for f in os.listdir(source_dir) if f.endswith(".md")]
        print(f"총 {len(file_names)}개의 파일을 읽습니다.")

        for file_name in sorted(file_names):  # 일관된 순서를 위해 정렬
            file_path = os.path.join(source_dir, file_name)
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                all_content.append(
                    f"--- 문서 시작: {file_name} ---\n\n{content}\n\n--- 문서 끝: {file_name} ---\n\n"
                )

        print("모든 파일 내용을 성공적으로 읽었습니다.")
        return "\n".join(all_content)

    except FileNotFoundError:
        print(f"오류: '{source_dir}' 폴더를 찾을 수 없습니다.")
        return None
    except Exception as e:
        print(f"파일을 읽는 중 오류가 발생했습니다: {e}")
        return None


def extract_and_consolidate_references(content):
    """
    AI를 사용하여 소스 콘텐츠에서 각주와 참고문헌을 추출하고 통합합니다.
    AI가 더 안정적으로 처리할 수 있도록 JSON 대신 마크다운 형식을 사용합니다.
    """
    print("\n참고문헌 및 각주 추출 및 통합 시작...")

    model = get_model_for_task("reference_extraction")
    ai_extracted_data = None
    last_response = ""
    last_error = None

    for attempt in range(3):  # 최대 3번 시도
        print(f"AI 기반 추출 시도 ({attempt + 1}/3)...")

        prompt = ""
        if last_error:
            prompt = f"""
            이전 시도에서 응답 처리 중 오류가 발생했습니다: {last_error}
            아래 텍스트를 수정하여 유효한 마크다운 형식을 생성해주세요.

            --- 오류 발생 텍스트 ---
            {last_response}
            --- 끝 ---
            
            **출력 형식 (오직 아래 마크다운 형식만 출력):**
            ## 각주
            [1] 각주 내용 1
            
            ---
            
            ## 참고문헌
            - 참고문헌 1 (출처)
            """
        else:
            prompt = f"""
            당신은 법률 보고서의 참고문헌을 전문적으로 추출하는 AI입니다.
            아래 통합 문서에서 '참고문헌' 섹션만 식별하고, 그 안의 출처 목록을 추출해주세요. 각주 정보는 무시합니다.

            **정의:**
            - **참고문헌 (Bibliography/References):** 보고서 작성에 사용된 자료의 출처 목록입니다. '참고문헌', 'References', '참고 자료', 'Bibliography' 등 다양한 제목으로 존재할 수 있습니다.

            --- 통합 문서 시작 ---
            {content}
            --- 통합 문서 끝 ---

            **작업 요청:**
            1.  '참고문헌', 'References', '참고 자료' 등과 같은 제목 아래 있는 모든 출처 목록을 찾아서 목록으로 만드세요. **설명 내용이 아닌, 출처 자체를 추출해야 합니다.**
            2.  아래 지정된 마크다운 형식에 맞춰 **참고문헌**만 출력하세요.

            **출력 형식 (오직 마크다운만 출력):**
            ## 참고문헌

            - 출처 1 (예: OOO 저, "논문 제목", 2023)
            - 출처 2 (예: https://example.com/article)
            """

        response_text = generate_content(model, prompt)
        last_response = response_text

        if not response_text:
            last_error = "AI 모델로부터 응답을 받지 못했습니다."
            continue

        try:
            footnotes = {}
            references = []

            # 각주와 참고문헌 섹션을 분리
            parts = response_text.split("---")
            footnote_part = ""
            reference_part = ""

            if len(parts) >= 2:
                footnote_part = parts[0]
                reference_part = parts[1]
            elif "## 각주" in response_text:
                footnote_part = (
                    response_text.split("## 참고문헌")[0]
                    if "## 참고문헌" in response_text
                    else response_text
                )
            elif "## 참고문헌" in response_text:
                reference_part = response_text

            # 각주 파싱
            if "## 각주" in footnote_part:
                fn_content = footnote_part.split("## 각주")[1].strip()
                fn_matches = re.finditer(r"\[(\d+)\]\s*(.*)", fn_content)
                for match in fn_matches:
                    footnotes[int(match.group(1))] = match.group(2).strip()

            # 참고문헌 파싱
            if "## 참고문헌" in reference_part:
                ref_content = reference_part.split("## 참고문헌")[1].strip()
                references = [
                    line.strip().lstrip("- ").strip()
                    for line in ref_content.split("\n")
                    if line.strip()
                ]

            if not footnotes and not references:
                raise ValueError("AI 응답에서 각주나 참고문헌을 파싱하지 못했습니다.")

            # 참고문헌에 번호를 붙여 딕셔너리로 변환
            final_references = {
                i + 1: ref for i, ref in enumerate(sorted(list(set(references))))
            }

            ai_extracted_data = {"footnotes": footnotes, "references": final_references}
            print("AI 기반 추출 및 파싱 성공.")
            break
        except Exception as e:
            print(f"AI 응답 처리 중 오류 발생: {e}")
            last_error = str(e)
            ai_extracted_data = None

    if not ai_extracted_data:
        print("AI를 통한 추출에 최종 실패했습니다. 빈 데이터를 반환합니다.")
        return {"footnotes": {}, "references": {}}

    print(
        f"각주 {len(ai_extracted_data['footnotes'])}개, 참고문헌 {len(ai_extracted_data['references'])}개 추출 완료"
    )
    return ai_extracted_data


def analyze_content_overlap(content):
    """
    콘텐츠의 중복 부분을 분석하고 핵심 정보를 추출합니다.
    """
    print("\n콘텐츠 중복 분석 시작...")
    model = get_model_for_task("content_analysis")

    prompt = f"""
    아래는 여러 문서의 내용을 합친 통합 문서입니다.
    --- 통합 문서 시작 ---
    {content}
    --- 통합 문서 끝 ---
    
    **분석 요청사항:**
    위 통합 문서 내용 전체를 바탕으로 다음 항목들을 분석하고 추출해주세요.
    1. 여러 문서에 걸쳐 중복적으로 나타나는 주제 또는 내용을 식별해주세요.
    2. 각 문서만이 가지고 있는 고유한 정보나 관점을 추출해주세요.
    3. 정보의 중요도와 신뢰도를 평가하여, 보고서 작성 시 우선적으로 반영해야 할 핵심 정보를 선별해주세요.
    4. 현재 정보에서 누락되었거나 더 보강이 필요한 부분이 있다면 '콘텐츠 갭'으로 정리해주세요.
    
    **출력 형식:**
    반드시 다음 JSON 형식에 맞춰서 출력해주세요.
    ```json
    {{
        "duplicate_topics": ["중복 주제1", "중복 주제2"],
        "unique_insights": ["고유 인사이트1", "고유 인사이트2"],
        "priority_information": ["우선순위 정보1", "우선순위 정보2"],
        "content_gaps": ["누락된 정보1", "누락된 정보2"]
    }}
    ```
    """

    try:
        response_text = generate_content(model, prompt)
        if not response_text:
            return {}

        json_text = response_text.strip()
        if json_text.startswith("```json"):
            json_text = json_text[7:-3]
        elif json_text.startswith("```"):
            json_text = json_text[3:-3]

        analysis_data = json.loads(json_text)
        print("콘텐츠 분석 완료")
        return analysis_data
    except Exception as e:
        print(f"콘텐츠 분석 중 오류 발생: {e}")
        return {}


def generate_outline(content):
    """LLM을 사용하여 콘텐츠의 개요를 생성합니다."""
    print("\nLLM에게 보고서 개요 생성을 요청합니다...")
    try:
        configure_genai()
        model = get_model_for_task("outline_generation")

        # 글로벌 템플릿에 통합 문서 내용을 삽입
        prompt = OUTLINE_PROMPT_TEMPLATE.format(content=content)

        response_text = generate_content(model, prompt)
        print("개요 생성을 완료했습니다.")
        return response_text

    except Exception as e:
        print(f"LLM 요청 중 오류 발생: {e}")
        return None


def generate_draft_report(outline, full_content):
    """개요와 전체 내용을 바탕으로 보고서 초안을 생성합니다."""
    print("\n\n--- 보고서 초안 생성을 시작합니다 ---")
    model = get_model_for_task("draft_generation")

    prompt = f"""
    당신은 법률 보고서 전문 작성자입니다. 주어진 '개요'와 '전체 내용'을 바탕으로, 상세하고 긴 보고서 본문을 작성해주세요.

    **⚠️ 중요한 요구사항 (반드시 준수):**
    1.  **최소 분량:** 한국어 기준 최소 20,000자 이상, 8,000단어 이상이 되도록 충분히 상세하게 작성하세요.
    2.  **개요 완전 준수:** '개요'의 모든 장·절을 빠짐없이 작성하고, 각 절마다 최소 5-10개 문단으로 충분히 서술하세요.
    3.  **심층 분석:** 단순한 사실 나열이 아닌, 깊이 있는 분석과 논증을 포함하세요.
    4.  **구체적 사례:** 각 국가별 사례, 판례, 법조문 등을 상세히 설명하세요.
    5.  **비교 분석:** 국가 간 제도 비교, 장단점 분석을 포함하세요.

    **지시사항:**
    - **목차 생성 금지:** 목차나 TOC는 작성하지 말고, 바로 본문 내용부터 시작하세요.
    - **각주 사용 금지:** 각주 대신 본문에 괄호나 문장으로 정보를 포함하세요.
    - **참고문헌 포함 금지:** 참고문헌 목록은 별도로 추가될 예정이므로 포함하지 마세요.
    - **완전한 문서:** 서론부터 결론까지 완전한 보고서를 작성하세요.

    **분량 검증:** 작성 후 내용이 최소 20,000자가 되는지 확인하세요. 부족하면 각 섹션을 더 자세히 확장하세요.

    --- 전체 내용 (참고 자료) ---
    {full_content}
    --- 끝 ---

    --- 작성할 보고서 개요 ---
    {outline}
    --- 끝 ---

    이제 위 요구사항을 반드시 준수하여 상세하고 긴 보고서 본문을 작성해주세요.
    """

    generation_config = {
        "temperature": 0.7,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 8192,  # 최대 출력 토큰 수 증가
    }

    draft = model.generate_content(prompt, generation_config=generation_config).text

    # 생성된 초안의 길이 확인
    char_count = len(draft)
    word_count = len(draft.split())
    print(f"생성된 초안 길이: {char_count:,}자, {word_count:,}단어")

    if char_count < 10000:
        print(
            "⚠️ 경고: 생성된 초안이 너무 짧습니다. 더 긴 내용을 생성하도록 재시도합니다."
        )
        # 재시도 프롬프트
        retry_prompt = f"""
        이전에 생성한 초안이 너무 짧습니다 ({char_count:,}자).
        다시 한 번 최소 20,000자 이상의 매우 상세하고 긴 보고서를 작성해주세요.
        
        각 섹션마다 다음을 포함하세요:
        - 상세한 배경 설명
        - 구체적인 사례와 예시
        - 비교 분석
        - 법적 논증
        - 시사점과 함의
        
        --- 이전 초안 ---
        {draft}
        --- 끝 ---
        
        위 초안을 기반으로 각 섹션을 3-5배 확장하여 매우 상세하고 긴 보고서를 작성해주세요.
        """

        extended_draft = model.generate_content(
            retry_prompt, generation_config=generation_config
        ).text
        if len(extended_draft) > len(draft):
            draft = extended_draft
            print(f"확장된 초안 길이: {len(draft):,}자, {len(draft.split()):,}단어")

    print("보고서 초안 생성 완료.")
    return draft


def editorial_review(draft, full_content, references_data):
    """
    편집장 AI가 초안을 검토하고 개선합니다.
    """
    print("\n편집장 AI 검토 시작...")
    model = get_model_for_task("editorial_review")

    prompt = f"""
    당신은 법률 보고서 전문 편집장입니다.
    당신의 임무는 아래 '검토할 초안'을 '원본 자료'와 '참고문헌 데이터'를 참고하여 수정·개선해 완성된 보고서 본문을 만드는 것입니다.

    **가장 중요한 규칙: 출력은 오직 최종적으로 완성된 보고서의 본문 내용이어야 합니다.**
    절대로 검토 의견, 수정 과정, 원본과의 비교, 또는 각주·참고문헌 목록 등 기타 부연 설명을 포함해서는 안 됩니다.
    각주는 사용하지 않으므로, 원본 각주에 포함된 정보가 필요하다면 본문 속에 자연스럽게 녹여주세요.
    
    --- 원본 자료 (전체 내용) ---
    {full_content}
    --- 끝 ---
    
    --- 참고문헌 데이터 ---
    {json.dumps(references_data.get('references', {}), ensure_ascii=False, indent=2)}
    --- 끝 ---

    --- 검토할 초안 ---
    {draft}
    --- 끝 ---

    **개선 지시사항:**
    1.  **논리적 흐름 및 일관성:** 전체적인 논리가 명확하고, 용어나 주장이 일관되도록 다듬어주세요.
    2.  **내용 중복 처리:** 중복되는 내용은 가장 포괄적이고 정확한 버전으로 통합하되, 정보가 소실되지 않도록 신중하게 처리해주세요.
    3.  **정보 보강 및 심층 분석:** '검토할 초안'의 내용이 부족하다고 판단되면, '원본 자료'를 참고하여 적극적으로 내용을 확장하고 보강해주세요. 단순 사실 나열을 넘어, 설득력 있는 논증과 깊이 있는 분석이 되도록 문체를 강화해주세요.
    4.  **표현 및 가독성:** 전문적인 용어를 사용하되, 독자가 이해하기 쉽도록 명확하고 간결한 문장으로 다듬어주세요.

    **최종 출력물은 반드시 보고서 제목으로 시작해야 하며, 오직 완성된 보고서 본문만 포함해야 합니다. 다른 어떤 내용도 포함하지 마세요.**
    
    **출력 형식:**
    # 사내 변호사를 위한 ACP의 국내 도입을 위한 유럽 사례 연구조사

    [여기에 보고서 본문 내용을 작성]
    """

    generation_config = {"temperature": 0.7, "top_p": 0.95, "top_k": 40}

    response = model.generate_content(prompt, generation_config=generation_config).text

    # AI가 지시를 어기고 구분자나 메타 정보를 포함하는 경우를 처리
    final_report = response.strip()

    # 제목을 기준으로 본문 시작 부분 찾기
    title_str = "사내 변호사를 위한 ACP의 국내 도입을 위한 유럽 사례 연구조사"

    # 제목이 여러 번 나타나는 경우 첫 번째 제목만 사용
    title_positions = []
    start_pos = 0
    while True:
        pos = final_report.find(title_str, start_pos)
        if pos == -1:
            break
        title_positions.append(pos)
        start_pos = pos + len(title_str)

    if title_positions:
        # 첫 번째 제목부터 시작
        final_report = final_report[title_positions[0] :]

        # 만약 제목이 중복으로 나타나면 첫 번째 제목 이후 두 번째 제목 전까지만 사용
        if len(title_positions) > 1:
            second_title_pos = title_positions[1] - title_positions[0]
            final_report = final_report[:second_title_pos]

    # "---" 구분자 뒤의 내용은 제거하여 본문만 남기기
    if "---" in final_report:
        final_report = final_report.split("---")[0].strip()

    # 최소한의 내용 검증
    if len(final_report.split()) < 100:  # 단어 수가 너무 적은 경우
        print("경고: 생성된 보고서 본문이 너무 짧습니다. 초안을 그대로 사용합니다.")
        final_report = draft

    print("편집장 AI 검토 완료.")
    return final_report


def final_quality_check(report, outline, references_data):
    """
    최종 품질 검사 및 사실 확인
    """
    print("\n최종 품질 검사 시작...")
    model = get_model_for_task("quality_check")

    prompt = f"""
    당신은 최종 품질 검사관입니다. 아래 제공되는 자료들을 바탕으로 보고서의 최종 품질을 검사하고, 검토 의견을 작성해주세요.
    
    --- 원본 개요 ---
    {outline}
    --- 끝 ---

    --- 참고문헌 데이터 ---
    {json.dumps(references_data.get('references', {}), ensure_ascii=False, indent=2)}
    --- 끝 ---

    --- 최종 검토할 보고서 ---
    {report}
    --- 끝 ---
    
    **검토 지시사항:**
    위 자료들을 종합적으로 참고하여 '최종 검토할 보고서'를 다음 기준에 따라 검토하고, 각 항목별로 구체적인 검토 의견을 작성해주세요.

    1.  **개요 일치성:** 보고서의 구조와 내용이 '원본 개요'와 일치하는지 검토해주세요.
    2.  **참고문헌 연결성:** 본문이 참고문헌 목록에 적절히 근거를 표시하고 있는지 확인해주세요. 각주 사용 여부는 무시하고, 내용과 출처의 매칭을 평가해주세요.
    3.  **정보 정확성:** 국가별 정보 등 사실 관계에 오류가 없는지 검토해주세요.
    4.  **일관성:** 용어나 주장이 보고서 전반에 걸쳐 일관되게 사용되었는지 확인해주세요.

    **출력 형식:**
    # 품질 검사 보고서

    ## 1. 개요 일치성
    - 발견된 문제점:
    - 개선 제안:

    ## 2. 참고문헌 연결성
    - 발견된 문제점:
    - 개선 제안:

    [이하 각 항목별로 동일한 형식으로 작성]
    """

    try:
        review_comments = generate_content(model, prompt)
        print("최종 품질 검사 완료")
        return report, (
            review_comments
            if review_comments
            else (report, "품질 검사 중 오류가 발생했습니다.")
        )
    except Exception as e:
        print(f"최종 품질 검사 중 오류 발생: {e}")
        return (
            report,
            f"품질 검사 중 오류가 발생했습니다: {e}",
        )  # 오류 시 원본과 오류 메시지 반환


def format_references_for_report(references_data):
    """
    추출된 각주와 참고문헌 데이터를 보고서에 추가할 수 있는 마크다운 형식으로 변환합니다.
    """
    markdown_text = ""

    # 참고문헌 포맷 (설명이 아닌 출처 목록)
    if references_data.get("references"):
        markdown_text += "\n\n---\n\n## 참고문헌\n\n"
        try:
            # 키(참고문헌 번호)를 정수로 변환하여 정렬
            sorted_references = sorted(
                references_data["references"].items(), key=lambda item: int(item[0])
            )
            for number, text in sorted_references:
                markdown_text += f"{number}. {text}\n"
        except (ValueError, TypeError) as e:
            print(f"참고문헌 정렬 중 오류 발생: {e}. 원본 순서대로 처리합니다.")
            for number, text in references_data["references"].items():
                markdown_text += f"{number}. {text}\n"

    return markdown_text


def generate_enhanced_report(draft_report, outline, full_content, references_data):
    """주어진 초안을 기반으로 편집장 검토 → 참고자료 삽입 → 품질 검사를 수행합니다."""

    # 5-1단계: 편집장 AI 검토
    print("\n5-1단계: 편집장 AI 검토")
    reviewed_report = editorial_review(draft_report, full_content, references_data)
    if not reviewed_report:
        print("경고: 편집장 검토에 실패했습니다. 초안을 그대로 사용합니다.")
        reviewed_report = draft_report

    # 5-2단계: 각주 및 참고문헌 추가
    print("\n5-2단계: 각주 및 참고문헌 추가")
    references_markdown = format_references_for_report(references_data)

    # 본문과 참고자료를 구분하는 구분선 추가
    report_with_references = f"{reviewed_report}\n\n{'=' * 80}\n\n{references_markdown}"

    # 5-3단계: 최종 품질 검사
    print("\n5-3단계: 최종 품질 검사")
    final_report, quality_check_report = final_quality_check(
        report_with_references, outline, references_data
    )

    # 최종 검증 – 초안이 충분히 길지 않으면 실패로 간주
    if len(reviewed_report.split()) < 100:
        print("경고: 최종 보고서 본문이 너무 짧습니다. 프로세스를 다시 확인하세요.")
        return None, "보고서 본문 생성 실패"

    return final_report, quality_check_report


def add_generation_info(quality_check_report, generation_info):
    """
    생성 과정의 메타데이터와 품질 검사 보고서를 결합합니다.
    """
    metadata = {
        "generation_date": datetime.now().isoformat(),
        "source_files": generation_info.get("source_files", []),
        "total_references": len(generation_info.get("references", [])),
        "models_used": MODELS,
        "generation_stages": ["outline", "draft", "editorial_review", "quality_check"],
        "production_mode": USE_PRODUCTION_MODELS,
    }

    info_section = f"""# 보고서 생성 정보

- **생성 일시:** {metadata['generation_date']}
- **사용 모델:** {'프로덕션 모드' if metadata['production_mode'] else '테스트 모드'}
- **생성 단계:** {' → '.join(metadata['generation_stages'])}
- **참고문헌 수:** {metadata['total_references']}개

## 모델 상세 정보
"""

    for task, model in metadata["models_used"].items():
        info_section += f"- **{task}:** {model}\n"

    info_section += f"""
---

# 최종 품질 검사 보고서

{quality_check_report}
"""
    return info_section


def get_unique_filename(base_name, date_str, extension=".md"):
    """
    날짜와 시간을 포함한 고유한 파일 이름을 생성합니다.
    이미 존재하는 경우 번호를 추가하여 중복을 방지합니다.
    """
    name_without_ext = os.path.splitext(base_name)[0]
    new_base = f"{name_without_ext}_{date_str}"

    counter = 1
    filename = f"{new_base}{extension}"

    while os.path.exists(filename):
        filename = f"{new_base}_{counter}{extension}"
        counter += 1

    return filename


def main():
    parser = argparse.ArgumentParser(description="ACP 보고서 생성 파이프라인")
    parser.add_argument(
        "--step",
        choices=["draft", "enhance", "all"],
        default="all",
        help="draft: 초안만 생성 / enhance: 기존 초안을 향상 / all: 풀 파이프라인",
    )
    parser.add_argument(
        "--draft-path",
        help="'enhance' 단계에서 사용할 기존 초안 파일 경로",
    )

    args = parser.parse_args()

    # 모델 설정 정보 출력
    print_model_configuration()

    print("\n1단계: 소스 파일 읽기")
    combined_content = read_all_source_files()
    if not combined_content:
        print("소스 파일을 읽는 데 실패했습니다.")
        return

    try:
        configure_genai()
    except ValueError as e:
        print(e)
        return

    # 2단계: 참고문헌 추출 (모든 단계 공통)
    print("\n2단계: 참고문헌 추출")
    references_data = extract_and_consolidate_references(combined_content)

    # 3단계: 개요 생성 (draft, all 단계에서 필요)
    outline = None
    if args.step in ["draft", "all", "enhance"]:
        print("\n3단계: 개요 생성")
        outline = generate_outline(combined_content)
        if not outline:
            print("개요 생성에 실패했습니다.")
            return

    # draft 전용 실행 --------------------------------------------------
    if args.step == "draft":
        print("\n4단계: 초안 생성")
        draft_report = generate_draft_report(outline, combined_content)
        if not draft_report:
            print("초안 생성 실패")
            return

        now = datetime.now()
        date_str = now.strftime("%Y%m%d_%H%M%S")
        draft_filename = get_unique_filename("draft_report", date_str)
        with open(draft_filename, "w", encoding="utf-8") as f:
            f.write(draft_report)
        print(f"🎉 초안 생성 완료: {draft_filename}")
        return

    # enhance 전용 실행 -----------------------------------------------
    if args.step == "enhance":
        if not args.draft_path or not os.path.exists(args.draft_path):
            print("--draft-path 에 유효한 초안 파일을 지정해야 합니다.")
            return
        with open(args.draft_path, "r", encoding="utf-8") as f:
            draft_report = f.read()

        final_report, quality_check_report = generate_enhanced_report(
            draft_report, outline, combined_content, references_data
        )

        now = datetime.now()
        date_str = now.strftime("%Y%m%d_%H%M%S")
        report_filename = get_unique_filename("enhanced_report", date_str)
        with open(report_filename, "w", encoding="utf-8") as f:
            f.write(final_report)
        print(f"🎉 향상된 보고서 생성 완료: {report_filename}")
        return

    # all 단계 (기존 전체 파이프라인) ---------------------------------
    print("\n4단계: 초안 생성")
    draft_report = generate_draft_report(outline, combined_content)
    if not draft_report:
        print("초안 생성에 실패했습니다.")
        return

    print("\n5단계: 향상된 보고서 생성")
    final_report, quality_check_report = generate_enhanced_report(
        draft_report, outline, combined_content, references_data
    )

    print("\n6단계: 파일 저장")
    now = datetime.now()
    date_str = now.strftime("%Y%m%d_%H%M%S")

    report_filename = get_unique_filename("enhanced_report", date_str)
    with open(report_filename, "w", encoding="utf-8") as f:
        f.write(final_report)

    info_filename = get_unique_filename("generation_info", date_str)
    with open(info_filename, "w", encoding="utf-8") as f:
        f.write(quality_check_report)

    print(f"🎉 전체 파이프라인 완료!")
    print(f"📄 결과 파일: {report_filename}")
    print(f"📄 품질 검사 파일: {info_filename}")


if __name__ == "__main__":
    main()
