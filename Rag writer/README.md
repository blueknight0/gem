# 🏛️ RAG Writer v4 - 지능형 법률 보고서 생성기

> Tkinter GUI와 LangGraph 기반의 자가 교정(self-correcting) 워크플로우를 통해 유럽 사내변호사 비밀유지특권(ACP)에 대한 전문 연구 보고서를 자동으로 생성하는 지능형 시스템입니다.

## 📋 프로젝트 개요

본 시스템은 RAG(Retrieval-Augmented Generation) 기법과 LangGraph의 에이전트 워크플로우를 결합하여, 복잡하고 전문적인 법률 연구 보고서 생성 과정을 완전히 자동화합니다. 사용자는 간단한 GUI를 통해 'Production', 'Test', **'Extreme(익스트림)'** 모드를 선택하고 주제를 입력하기만 하면, 시스템이 스스로 초안 작성, 편집장 검토, 섹션 재작성, 최종 서식 정리, 시각적 분석 대시보드 생성까지 모든 과정을 수행합니다.

### 🎯 연구 주제
- **사내변호사 비밀유지특권(Attorney-Client Privilege, ACP)**
- **유럽 대륙법계 국가별 제도 비교 분석**
- **한국 도입을 위한 정책 제언**

## ⚡ 주요 기능

- **🖥️ 사용자 친화적 GUI**: Tkinter로 제작된 간단한 인터페이스를 통해 보고서 주제 입력 및 생성 모드(Production/Test/Extreme) 선택이 가능합니다.
- **🧠 지능형 워크플로우 (LangGraph)**: '편집장 검토' 노드를 중심으로 자가 교정(self-correcting) 루프를 구현했습니다. 초안 품질이 기준에 미달할 경우, AI가 스스로 문제점을 분석하고 해당 섹션을 자동으로 재작성하여 보고서의 완성도를 높입니다.
- **🚀 익스트림 모드**: Google Search Grounding 기능과 FAISS 벡터 DB의 방대한 자료를 최대한 활용하여, 한 번에 30,000자 이상의 고품질 보고서를 생성하는 극한 성능 모드입니다.
- **📊 자동 분석 대시보드**: Matplotlib와 Seaborn을 사용하여 보고서 생성 파이프라인의 모든 과정을 시각화합니다. 작업별 소요 시간, 보고서 품질 지표, 참고문헌 통계, 로그 분포 등을 포함한 종합 대시보드와 개별 차트를 생성하여 프로세스 투명성을 확보합니다.
- **🗂️ 체계적인 결과물 관리**: 모든 생성물(보고서, 로그, 시각화 자료)은 `results_{mode}_{timestamp}` 형식의 타임스탬프 폴더에 체계적으로 저장되어 이력 관리가 용이합니다.
- **⚙️ 동적 모델 선택**: GUI에서 Production 모드(고품질 `gemini-2.5-pro`), Test 모드(비용 효율적 `gemini-2.5-flash-lite`), Extreme 모드(극한 성능 `gemini-2.5-pro` + Search Grounding)를 선택하여, 목적에 맞는 AI 모델을 유연하게 활용할 수 있습니다.
- **📚 FAISS 기반 벡터 DB**: 효율적인 문서 검색을 위해 FAISS 벡터 데이터베이스를 활용합니다.

## 📁 프로젝트 구조

```
Rag writer/
├── 📄 generate_report_v3.py       # GUI 보고서 생성 애플리케이션
├── 📄 README.md                   # 프로젝트 설명서 (이 파일)
├── 📁 sources/                    # 원본 연구 자료 (json, md, pdf...)
├── 📁 results_{mode}_{timestamp}/ # 생성 결과 폴더
│   ├── 📄 final_report_{timestamp}.md
│   ├── 📄 editorial_review_log_{timestamp}.md
│   ├── 📁 logs/
│   │   ├── 📄 pipeline_log_{timestamp}.md
│   │   └── 📄 node_{node_name}_log_{timestamp}.md
│   └── 📁 visualizations/
│       ├── 📄 dashboard_{timestamp}.png
│       └── 📄 *.png (개별 분석 차트)
├── 📄 vector_db.faiss             # Faiss 인덱스
└── 📄 vector_db_data.json         # 벡터 데이터
```

## 🚀 사용 방법

1.  **필수 라이브러리 설치**: `generate_report_v3.py` 스크립트가 처음 실행될 때 필요한 라이브러리를 자동으로 감지하고 설치를 시도합니다. 만약 수동 설치가 필요하다면 아래 명령어를 사용하세요.
    ```bash
    pip install google-generativeai python-dotenv faiss-cpu numpy scikit-learn langgraph matplotlib seaborn pandas Pillow
    ```
2.  **환경 변수 설정**: 프로젝트 루트 디렉토리에 `.env` 파일을 생성하고 Google Gemini API 키를 추가합니다.
    ```
    GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
    ```
3.  **애플리케이션 실행**: 아래 명령어로 GUI 애플리케이션을 실행합니다.
    ```bash
    python generate_report_v3.py
    ```
4.  **보고서 생성**: GUI 창에서 보고서 주제를 입력하고, 'Production', 'Test' 또는 'Extreme' 모드를 선택한 후 '리포트 생성 시작' 버튼을 클릭합니다.

## 🤖 AI 모델 설정

GUI를 통해 세 가지 실행 모드를 선택할 수 있습니다.

- **Production 모드**: 고품질 결과물을 위한 설정 (`gemini-2.5-pro` 사용)
- **Test 모드**: 빠른 프로토타이핑 및 비용 절약을 위한 설정 (`gemini-2.5-flash-lite` 사용)
- **Extreme 모드**: 극한 성능을 위한 특별 설정 (`gemini-2.5-pro` + Google Search Grounding 사용)

### 모드별 특징
| 모드 | 모델 | 워크플로우 | 특징 | 목표 길이 |
| :--- | :--- | :--- | :--- | :--- |
| **Production** | `gemini-2.5-pro` | 표준 6단계 LangGraph | 편집장 검토를 통한 고품질 보고서 | 15,000~20,000자 |
| **Test** | `gemini-2.5-flash-lite` | 표준 6단계 LangGraph | 빠른 테스트 및 비용 절약 | 10,000~15,000자 |
| **Extreme** | `gemini-2.5-pro` + Search Grounding | 간소화 2단계 워크플로우 | 방대한 자료 활용 + 웹 검색으로 극한 품질 | 30,000자+ |

### LangGraph 노드별 모델 역할 (Production/Test 모드)
| 노드 (작업) | Production 모델 | Test 모델 | 역할 |
| :--- | :--- | :--- | :--- |
| `generate_outline` | `gemini-2.5-pro` | `gemini-2.5-flash-lite` | 체계적인 보고서 목차 설계 |
| `generate_draft` | `gemini-2.5-pro` | `gemini-2.5-flash-lite` | 참고문헌 기반으로 상세 본문 작성 |
| `editorial_review` | `gemini-2.5-pro` | `gemini-2.5-flash-lite` | 초안 품질 검토 및 개선 지침 생성 |
| `regenerate_sections` | `gemini-2.5-pro` | `gemini-2.5-flash-lite` | 개선 지침에 따라 특정 섹션 재작성 |
| `final_formatting` | `gemini-2.5-pro` | `gemini-2.5-flash-lite` | 최종 보고서 마크다운 서식 정리 |

### Extreme 모드 워크플로우
| 노드 (작업) | 모델 | 역할 |
| :--- | :--- | :--- |
| `generate_outline` | `gemini-2.5-pro` | 체계적인 보고서 목차 설계 |
| `generate_bypassed_report` | `gemini-2.5-pro` + Search Grounding | 벡터 DB 자료 + 웹 검색을 활용한 극한 품질 보고서 한번에 생성 |

## 📊 생성 프로세스 상세 (LangGraph 워크플로우)

1.  **`generate_outline` (개요 생성)**: 사용자가 입력한 주제와 벡터 DB의 핵심 정보를 종합하여 논리적인 보고서 목차를 생성합니다.
2.  **`generate_draft` (초안 생성)**: 생성된 목차의 각 섹션에 대해, 벡터 DB에서 관련 깊은 내용을 검색하여 상세한 초안을 작성합니다.
3.  **`editorial_review` (편집장 검토)**: AI 편집장이 작성된 초안을 전체 목차와 비교하며 논리적 비약, 내용 부실 등을 검토합니다.
    - **(조건 분기)** 검토 결과, 보고서가 기준을 통과하면 다음 단계로 진행합니다. 개선이 필요하다고 판단되면 'regenerate_sections' 노드로 이동합니다. 최대 3회까지 재작성을 시도합니다.
4.  **`regenerate_sections` (섹션 재작성)**: 편집장의 구체적인 개선 지침에 따라 문제가 된 섹션의 본문을 다시 생성합니다. 재작성된 내용은 다시 `editorial_review` 노드로 보내져 재검토를 받습니다.
5.  **`final_formatting` (서식 정리)**: 모든 검토를 통과한 보고서의 가독성을 높이기 위해 마크다운 서식을 정리합니다.
6.  **`finalize_and_save` (최종화 및 저장)**: 본문의 참고문헌 태그(`[CITATION:...]`)를 실제 각주 번호(`[^1]`)로 변환하고, 최종 보고서와 모든 로그 및 시각화 자료를 저장하며 파이프라인을 종료합니다.

## 📄 출력 파일 설명

모든 결과물은 `results_{mode}_{timestamp}` 폴더 내에 저장됩니다.

- **`final_report_{timestamp}.md`**: 최종적으로 생성된 완성본 보고서 파일입니다.
- **`editorial_review_log_{timestamp}.md`**: AI 편집장의 검토 과정 전체 기록입니다. 어떤 섹션이 왜, 어떻게 개선되었는지 확인할 수 있습니다.
- **`/visualizations`**:
  - **`dashboard_{timestamp}.png`**: 파이프라인 전체 현황을 요약한 종합 대시보드 이미지입니다.
  - **개별 차트 이미지들**: 작업별 소요시간, 보고서 품질 지표 등 개별 분석 차트가 저장됩니다.
- **`/logs`**:
  - **`pipeline_log_{timestamp}.md`**: 파이프라인의 모든 이벤트를 기록한 상세 로그입니다.
  - **`node_*.md`**: 각 LangGraph 노드별로 분리된 상세 실행 로그입니다.

## 🔧 기술적 요구사항

- Python 3.8+
- 인터넷 연결 (Google Gemini API 호출)
- **필수 라이브러리**:
  - `google-generativeai`
  - `python-dotenv`
  - `faiss-cpu`
  - `numpy`
  - `scikit-learn`
  - `langgraph`
  - `matplotlib`
  - `seaborn`
  - `pandas`
  - `Pillow`

---

**🔗 관련 링크**
- [Google AI Studio](https://aistudio.google.com/)
- [LangGraph Documentation](https://python.langchain.com/docs/langgraph)

**📧 문의사항**
프로젝트 관련 문의나 개선 제안은 이슈로 등록해 주세요. 