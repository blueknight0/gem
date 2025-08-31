

# **AI 첫걸음: 비전공자를 위한 LLM 이론부터 코딩 맛보기까지 4시간 완성 과정**

## **과정 전체 목표**

이 4시간 과정이 끝날 때까지, 참가자들은 인공지능(AI), 머신러닝(ML), 거대 언어 모델(LLM)의 기본 개념을 설명하고, 최신 AI 모델들의 유형을 비교할 수 있게 됩니다. 또한, AI 어시스턴트가 어떻게 프로그래밍의 진입 장벽을 낮추는지 직접 체험함으로써, 기술에 대한 두려움 대신 자신감과 호기심을 갖게 되는 것을 목표로 합니다.

---

## **1장: 우리 일상 속의 AI: 보이지 않는 혁명 (예상 소요 시간: 60분)**

**목표:** AI의 핵심 개념을 친숙한 사례를 통해 소개하고, 공통의 어휘를 정립하며, 현재의 AI 붐에 대한 흥미로운 역사적 맥락을 제공합니다.

### **1.1. AI와의 첫 만남: 이미 당신의 일상 파트너입니다 (15분)**

강사 가이드:  
AI가 먼 미래의 공상 과학 기술이라는 오해를 불식시키는 것으로 강의를 시작합니다. AI는 우리가 매일 사용하는 강력하고 종종 눈에 보이지 않는 도구임을 강조해야 합니다. 참가자들이 이미 경험한 것을 바탕으로 추상적인 AI 개념을 구체화하는 것이 이 섹션의 핵심입니다.  
활동: "내 안의 AI 찾기" (참여형 토론)  
참가자들에게 다음과 같은 질문을 던져 토론을 유도합니다. "어젯밤 넷플릭스에서 무엇을 볼지 어떻게 결정하셨나요?" 또는 "오늘 아침 이곳으로 오는 길에 교통체증이 있다는 것을 구글맵은 어떻게 알았을까요?"  
이러한 질문을 시작으로, 세 가지 핵심 사례를 통해 AI의 역할을 쉬운 용어로 설명합니다.

* **넷플릭스/스포티파이 추천 시스템:** 넷플릭스의 추천 시스템은 단순히 인기 있는 콘텐츠를 보여주는 것이 아닙니다. AI는 사용자의 시청 기록을 분석하고, 이를 비슷한 취향을 가진 수백만 명의 다른 사용자 데이터와 비교합니다. 이 방식을 '협업 필터링(collaborative filtering)'이라고 부릅니다.1 동시에 AI는 콘텐츠 자체의 특징, 예를 들어 장르, 출연 배우, 감독 등의 정보를 분석하기도 하는데, 이를 '콘텐츠 기반 필터링(content-based filtering)'이라고 합니다.3 결국 넷플릭스의 AI는 모든 영화를 다 보고 모든 사람의 취향을 완벽하게 파악하고 있는 영화광 친구처럼 작동하는 셈입니다.4  
* **내비게이션 앱 (구글맵/웨이즈):** 구글맵과 같은 내비게이션 앱은 정적인 지도가 아닙니다. 이 앱들은 수많은 사용자들의 스마트폰에서 전송되는 실시간 위치 데이터를 AI로 분석하여 교통 상황을 예측하고, 가장 빠른 경로와 도착 예정 시간을 계산합니다.6 즉, AI는 도시 전체의 혈관처럼 도로망을 실시간으로 모니터링하며 학습하는 살아있는 시스템입니다.8  
* **이메일 스팸 필터:** 지메일(Gmail)과 같은 이메일 서비스는 AI를 활용하여 받은 편지함을 깨끗하게 유지합니다. AI는 사용자들이 '스팸'으로 신고한 수십억 개의 이메일에서 공통적인 패턴(특정 단어, 발신자 주소, 링크 구조 등)을 학습합니다.4 이를 통해 새로운 이메일이 도착했을 때, 그것이 스팸일 확률을 계산하여 자동으로 분류해 줍니다. 이는 받은 편지함을 지키는 똑똑한 경비원과 같습니다.

이러한 일상적인 예시들은 AI 기술이 어떻게 대규모의 데이터를 처리하여 각 개인에게 맞춤화된 경험을 제공하는지를 보여줍니다. 넷플릭스는 사용자마다 다른 홈 화면을 보여주고, 구글맵은 현재 위치와 시간에 따라 최적의 경로를 제시하며, 스팸 필터는 각자가 원치 않는 메일을 학습합니다. 수십억 명의 사용자에게 이처럼 개별적인 서비스를 제공하는 것은 인간의 힘으로는 불가능합니다. 따라서 이 기술의 핵심은 단순히 '똑똑한 컴퓨터'를 넘어, '대규모 개인화(personalization at scale)'를 자동화하는 능력에 있습니다. 이는 현대 비즈니스의 핵심 동력이자 우리가 기술과 상호작용하는 방식의 근본적인 변화를 의미합니다.4

### **1.2. AI의 위대한 여정: 이야기로 만나는 역사 (20분)**

강사 가이드:  
AI의 역사를 딱딱한 연대기 나열이 아닌, '생각하는 기계를 만들려는 인류의 장대한 탐험'이라는 이야기 형식으로 구성합니다. 이 이야기의 흐름을 보여주는 네 가지 결정적인 순간을 짚어봅니다.

* **꿈의 시작: 튜링 테스트 (1950년):** '컴퓨터 과학의 아버지' 앨런 튜링을 소개합니다. 그가 고안한 '튜링 테스트' 또는 '이미테이션 게임'을 간단히 설명합니다. 즉, 심사관이 컴퓨터와 사람의 대화를 문자로만 보고 어느 쪽이 컴퓨터인지 구분할 수 없다면, 그 컴퓨터는 지능을 가졌다고 볼 수 있다는 개념입니다.10 이 테스트는 AI가 추구해야 할 철학적 목표를 제시했습니다.10  
* **이름의 탄생: 다트머스 회의 (1956년):** 이 사건을 'AI 어벤져스 팀의 결성'으로 비유합니다. 존 매카시를 비롯한 여러 분야의 과학자들이 여름 워크숍에 모여 '인공지능(Artificial Intelligence)'이라는 용어를 공식적으로 만들고, 하나의 학문 분야로서 연구를 시작했습니다.10  
* **인간 대 기계, 1라운드: 딥블루 대 카스파로프 (1997년):** AI가 대중에게 강력한 인상을 남긴 역사적 사건입니다. IBM의 슈퍼컴퓨터 '딥블루'가 체스 세계 챔피언을 이긴 사건을 설명합니다. 여기서 중요한 점은 딥블루가 인간처럼 '생각'해서 이긴 것이 아니라, 초당 2억 개의 체스판 상황을 계산하는 압도적인 '계산 능력(brute-force)'으로 승리했다는 것입니다.10 이는 인간이 정해준 규칙에 따라 움직이는 '규칙 기반 AI'의 정점을 보여준 사례입니다.10  
* **인간 대 기계, 2라운드: 알파고 대 이세돌 (2016년):** AI 역사의 결정적인 전환점입니다. 바둑은 체스보다 경우의 수가 우주에 있는 원자 수보다 많아 딥블루와 같은 방식으로는 정복이 불가능했습니다. 알파고는 수많은 기보를 '학습'하고 스스로 대국하며 실력을 키우는 '머신러닝'과 '딥러닝' 방식을 사용했습니다.10 알파고가 보여준 인간 기사들이 '창의적'이라고 평가한 수는 AI가 단순히 계산만 하는 기계가 아니라, 데이터로부터 스스로 전략을 터득할 수 있음을 증명한 순간이었습니다. 이 승리는 오늘날 우리가 사용하는 AI 기술의 서막을 열었습니다.10

### **1.3. AI 가족 관계도: AI, 머신러닝, 딥러닝 (15분)**

강사 가이드:  
세 용어는 종종 혼용되지만, 그 관계를 이해하는 것은 AI를 제대로 파악하는 데 매우 중요합니다. 이를 위해 간단하고 기억하기 쉬운 시각적 비유를 사용합니다.  
마트료시카 인형 비유:  
러시아 전통 인형인 마트료시카 이미지를 보여주며 설명합니다.16

* **가장 큰 인형 (인공지능, AI):** 튜링 시대부터 시작된 가장 큰 꿈, 즉 인간의 지능을 어떤 방식으로든 흉내 내는 기계를 만들려는 모든 개념과 시도를 포함합니다.19 여기에는 딥블루와 같은 '구식' 규칙 기반 시스템도 포함됩니다.15  
* **중간 인형 (머신러닝, ML):** AI를 구현하기 위한 '접근법' 중 하나입니다. 모든 상황에 대한 규칙을 인간이 일일이 프로그래밍하는 대신, 기계가 데이터로부터 '스스로 학습'하게 만드는 방식입니다.22 이는 AI 개발 패러다임의 근본적인 전환을 의미하며, 현대 AI의 대부분이 머신러닝에 기반합니다. 학습 방식에는 '정답지'를 주고 배우는 \*\*지도 학습(Supervised Learning)\*\*과 정답 없이 데이터 속에서 패턴을 찾는  
  **비지도 학습(Unsupervised Learning)** 등이 있습니다.19  
* **가장 작은 인형 (딥러닝, DL):** 머신러닝의 여러 '기술' 중 하나로, 현재 가장 강력한 성능을 보여주는 기술입니다. 인간의 뇌 구조에서 영감을 받은 '인공 신경망(Artificial Neural Networks)'을 여러 겹으로 깊게 쌓아 올린 구조를 사용합니다.19 알파고의 승리를 이끌었으며, 이미지 인식, 음성 인식, 그리고 오늘날의 거대 언어 모델(LLM)을 가능하게 한 핵심 기술입니다.27

**시각 자료:** 각 인형에 '인공지능', '머신러닝', '딥러닝'이라고 적힌 간단한 인포그래픽을 활용하면 효과적입니다.

### **1.4. 새로운 물결: 생성형 AI와 LLM이란 무엇인가? (10분)**

강사 가이드:  
앞선 내용들을 종합하여 현재 AI 기술의 최전선을 소개합니다. 딥러닝 기술의 발전이 '생성형 AI'라는 새로운 시대를 열었음을 설명합니다.

* **생성형 AI(Generative AI) 정의:** 이전의 AI가 주로 주어진 데이터를 '분석'하고 '분류'하는 역할(예: 이미지가 고양이인지 개인지 판별)을 했다면, 생성형 AI는 기존에 없던 새로운 콘텐츠를 '창조'하는 AI입니다. 텍스트, 이미지, 음악, 심지어 코드까지 만들어낼 수 있습니다.26  
* **거대 언어 모델(LLM) 소개:** 챗GPT(ChatGPT)와 같이 현재 가장 유명한 생성형 AI 도구들의 핵심 엔진이 바로 '거대 언어 모델(Large Language Model, LLM)'임을 설명합니다. 다음 장에서는 이 놀라운 모델이 실제로 어떻게 작동하는지 그 비밀을 파헤쳐 볼 것임을 예고하며 1장을 마무리합니다.

---

## **2장: LLM의 비밀을 풀다 (예상 소요 시간: 60분)**

**목표:** LLM이 '다음 단어 예측'이라는 핵심 원리로 작동함을 직관적으로 이해시키고, 효과적인 '프롬프트' 작성법이라는 실용적인 기술을 습득하게 합니다.

### **2.1. 핵심 원리: 세상에서 가장 정교한 '다음 단어 맞히기' 게임 (20분)**

강사 가이드:  
"거대 언어 모델의 작동 원리는 놀라울 정도로 단순합니다. LLM의 핵심 임무는 주어진 문맥에서 가장 확률이 높은 다음 단어를 예측하는 것, 단 하나입니다." 이 문장으로 시작하여 LLM에 대한 신비감을 걷어내는 것이 중요합니다.

* **간단한 예시:**  
  * "하늘은 높고 말은 살찌는 천고..." (참가자들이 "마비\!"라고 외칠 것입니다.)  
  * "백설공주를 도와준 일곱..." (참가자들이 "난쟁이\!"라고 답할 것입니다.) 28  
* **작동 원리 설명:** LLM도 이와 똑같은 일을 하지만, 그 규모가 상상을 초월한다고 설명합니다. LLM은 인터넷의 방대한 텍스트와 수많은 책을 학습했습니다. 사용자가 프롬프트를 입력하면, 그 뒤에 올 수 있는 모든 단어에 대한 확률을 계산하고, 그중 가장 가능성이 높은 단어들을 선택하여 문장을 이어 나갑니다.28  
* **시각 자료:** 간단한 다이어그램을 통해 시각적으로 설명합니다.  
  * **입력:** "내가 가장 좋아하는 색은"  
  * **출력 (확률 분포):** 화살표들이 여러 단어를 가리키며 각각의 확률을 표시합니다. 파란색 (45%), 초록색 (20%), 빨간색 (15%), ... 토스터기 (0.0001%)  
* **반복의 마법:** LLM이 '파란색'이라는 단어를 예측하고 나면, 그 단어를 원래 문장에 덧붙여 "내가 가장 좋아하는 색은 파란색"이라는 새로운 문맥을 만듭니다. 그리고 이 새로운 문맥을 기반으로 다시 다음 단어를 예측하는 과정을 무한히 반복함으로써, 단어 하나하나가 모여 완전한 문장과 문단을 생성하게 됩니다.29

이처럼 '다음 단어 예측'이라는 단순한 작업 원리가 어떻게 복잡한 결과로 이어지는지 이해하는 것이 중요합니다. LLM은 인터넷 규모의 방대한 데이터로 훈련됩니다. "프랑스 혁명의 주요 원인은 무엇이었나?"와 같은 복잡한 질문에 대한 다음 단어를 정확하게 예측하려면, 모델은 '왕정', '세금', '사회적 불만'과 같은 개념들 사이의 관계를 훈련 데이터로부터 이미 학습했어야 합니다.28 따라서 우리가 '이해'나 '추론'이라고 인식하는 능력은, 사실 이 단순한 예측 과제를 방대하고 복잡한 데이터셋 위에서 최적으로 수행한 결과로 나타나는 '창발적 속성(emergent properties)'입니다. 이는 직관적이지는 않지만, LLM의 능력을 이해하는 핵심적인 개념입니다.28

### **2.2. 대화의 기술: 프롬프트 엔지니어링 101 (25분)**

강사 가이드:  
"AI와 대화하는 것은 하나의 기술입니다. 내가 얻는 결과물의 품질은 내가 던지는 질문의 품질에 정비례합니다. 이것을 '프롬프트 엔지니어링(Prompt Engineering)'이라고 부르며, 현대 직장인에게 가장 가치 있는 새로운 기술 중 하나입니다."  
활동: 좋은 프롬프트 vs. 나쁜 프롬프트 (사례 비교)  
슬라이드에 여러 예시를 제시하며, 왜 '좋은 프롬프트'가 더 나은 결과를 만드는지 참가자들과 함께 토론합니다.

* 모호함 vs. 구체성 33:  
  * **나쁜 프롬프트:** AI에 대해 알려줘.  
  * **좋은 프롬프트:** 머신러닝의 개념을 고등학생이 이해할 수 있도록 세 개의 간단한 문단으로 설명해줘.  
* 맥락 없음 vs. 맥락 제공 35:  
  * **나쁜 프롬프트:** 마케팅 이메일 써줘.  
  * **좋은 프롬프트:** 친환경 원두 커피 브랜드를 새로 런칭했어. 도시 지역에 거주하는 20-30대를 타겟으로 하는 마케팅 이메일을 작성해줘. 톤앤매너는 유머러스하고 캐주얼하게.  
* 역할 미지정 vs. 역할 부여 34:  
  * **나쁜 프롬프트:** 여행 계획 좀 짜줘.  
  * **좋은 프롬프트:** 당신은 최고의 여행 전문가입니다. 4인 가족이 처음으로 도쿄를 방문하는 7일간의 여행 일정을 짜주세요. 문화 체험과 아이들이 좋아할 만한 활동에 초점을 맞춰주세요. 예상 경비도 포함해주세요.  
* 형식 미지정 vs. 기대 결과 명시 35:  
  * **나쁜 프롬프트:** 이 기사 요약해줘.  
  * **좋은 프롬프트:** 이 기사의 핵심 내용을 5개의 불렛 포인트로 요약해줘.

### **2.3. LLM의 두 가지 맛: 상업용 vs. 오픈소스 (15분)**

강사 가이드:  
LLM이 무엇인지 알았으니, 이제 LLM이 개발되고 배포되는 두 가지 주요 방식을 알아봅니다. 이는 AI 업계의 생태계를 이해하는 데 매우 중요한 구분입니다.  
**자동차 비유:**

* 상업용/독점 모델 (Commercial/Proprietary Models) 37:  
  "이 모델들은 잘 만들어진 최신 자동차를 사는 것과 같습니다. 세련된 디자인, 고성능, 그리고 바로 운전할 수 있는 완제품이죠. 고객 지원과 최신 기능을 제공받지만, 비용을 지불해야 하고 엔진을 마음대로 뜯어고칠 수는 없습니다. 대표적인 예로 OpenAI의 GPT 시리즈, 구글의 Gemini, 앤스로픽의 Claude가 있습니다."  
* 오픈소스 모델 (Open-Source Models) 37:  
  "이 모델들은 고성능 컴퓨터 조립 키트와 같습니다. 핵심 부품(소스 코드, 모델 가중치)을 무료로 얻을 수 있습니다. 이를 바탕으로 내 필요에 맞게 자유롭게 커스터마이징하고, 튜닝하고, 개선할 수 있습니다. 하지만 조립하고 유지보수하려면 기술적인 전문 지식이 필요합니다. 대표적인 예로 메타의 Llama, 미스트랄 AI의 모델들이 있습니다."

**핵심:** 어떤 것이 절대적으로 '더 좋다'의 문제가 아니라, 주어진 상황에 어떤 것이 '더 적합한가'의 문제입니다. 사용하기 쉬운 최첨단 도구가 필요한가요, 아니면 완벽한 통제와 맞춤화가 필요한가요? 이것이 바로 선택의 기준이 됩니다.38

---

## **3장: 현대 AI의 격전장: 주요 플레이어와 우리의 미래 (예상 소요 시간: 60분)**

**목표:** 현재 LLM 시장의 구도를 개괄적으로 이해하고, 상업용과 오픈소스 모델의 차이를 실제 사례를 통해 명확히 하며, AI가 가져올 미래에 대한 긍정적이고 발전적인 시각을 제시합니다.

### **3.1. 상업용 모델의 거인들: Who's Who (20분)**

강사 가이드:  
뉴스에서 자주 접하게 될 주요 기업들을 소개합니다. 각 모델의 기술적 사양보다는 '성격'이나 '강점'에 초점을 맞춰 설명합니다.

* **OpenAI (GPT 시리즈):** 시장을 개척하고 선도하는 기업입니다. GPT 모델들은 뛰어난 창의성과 다재다능함으로 유명합니다. '만능 해결사'라고 할 수 있습니다. 챗GPT와 마이크로소프트의 코파일럿(Copilot)의 엔진으로 사용됩니다.41  
* **Google (Gemini 시리즈):** OpenAI의 가장 강력한 경쟁자입니다. 구글 검색, 워크스페이스, 안드로이드 등 자사 생태계와의 깊은 통합이 최대 강점입니다. 또한, 한 번에 매우 긴 문서를 처리할 수 있는 방대한 컨텍스트 창(context window)을 자랑합니다. '통합의 거인'으로 비유할 수 있습니다.37  
* **Anthropic (Claude 시리즈):** OpenAI 출신 연구원들이 설립한 회사입니다. AI의 안전성, 윤리, 그리고 신뢰할 수 있고 '무해한(harmless)' 결과물을 만드는 데 중점을 둡니다. 특히 기업 고객 응대나 고객 서비스 분야에서 탁월한 성능을 보입니다. '양심적인 대화가'로 부를 수 있습니다.41

### **3.2. 오픈소스의 혁명가들 (15분)**

강사 가이드:  
강력한 AI 기술을 모두에게 공개함으로써 새로운 혁신의 물결을 이끌고 있는 모델들을 소개합니다.

* **Meta (Llama 시리즈):** 고성능 오픈소스 LLM 시대를 본격적으로 연 모델입니다. 메타가 Llama를 공개함으로써 수많은 연구자와 스타트업이 이 기술을 바탕으로 새로운 서비스를 개발할 수 있게 되었습니다. '게임 체인저'로 평가받습니다.41  
* **Mistral AI:** 프랑스 파리에 기반을 둔 스타트업으로, 작은 크기에도 불구하고 훨씬 큰 모델들과 대등한 성능을 내는 효율적인 모델들을 발표하며 시장에 큰 충격을 주었습니다. 빠른 속도와 비용 효율성으로 유명합니다. '효율적인 강자'로 불립니다.43

### **3.3. 한눈에 보기: 전략적 선택 가이드 (15분)**

강사 가이드:  
지금까지 논의한 상업용 모델과 오픈소스 모델의 핵심적인 차이점을 간단한 표로 정리하여 제공합니다. 이 표는 기업이나 개발자가 어떤 상황에서 어떤 유형의 모델을 선택해야 하는지 이해하는 데 도움을 줄 것입니다. 이 비교는 기술적 사양보다는 비즈니스 관점에서 실용적인 의미(비용, 사용 편의성, 통제권 등)에 초점을 맞춥니다.  
**표: 상업용 LLM vs. 오픈소스 LLM \- 전략적 선택**

| 특징 | 상업용 모델 (예: GPT-4o, Gemini 2.5, Claude 4\) | 오픈소스 모델 (예: Llama 4, Mistral) |
| :---- | :---- | :---- |
| **접근성 및 비용** | 유료 API 또는 구독을 통해 접근. 시작은 쉽지만 사용량에 따라 비용이 증가할 수 있음.39 | 무료로 다운로드 및 사용 가능. 모델을 구동하기 위한 고성능 하드웨어(GPU) 비용이 발생함.39 |
| **사용 편의성** | 매우 높음. 풍부한 문서와 기술 지원이 제공되는 '플러그 앤 플레이' 방식의 완제품.37 | 설치, 유지보수, 최적화를 위해 상당한 기술 전문성(DevOps, ML 엔지니어)이 필요함.40 |
| **맞춤화 및 통제권** | 제한적. 프롬프트를 통해 유도할 수는 있지만, 핵심 모델을 변경할 수는 없음. 데이터 프라이버시가 우려될 수 있음.39 | 완벽한 통제권. 자체 데이터로 모델을 미세 조정(fine-tuning)하고, 자체 서버에서 운영하여 보안을 극대화할 수 있음.39 |
| **성능** | 출시 직후에는 가장 강력한 '최첨단(state-of-the-art)' 성능을 보이는 경우가 많음.41 | 성능 격차가 빠르게 좁혀지고 있으며, 특정 작업에 맞게 미세 조정했을 경우 상업용 모델을 능가할 수 있음.39 |
| **이상적인 사용자** | 빠르고 안정적인 솔루션을 원하는 기업, 비기술적 사용자, 빠른 프로토타이핑이 필요한 경우.38 | 연구자, 독창적인 제품을 개발하는 스타트업, 엄격한 데이터 보안 정책을 가진 기업, 고도로 특화된 작업이 필요한 경우.38 |

### **3.4. 미래는 협업이다: 우리의 일과 삶은 어떻게 변할까 (10분)**

강사 가이드:  
영감을 주는 비전으로 3장을 마무리합니다. AI는 인간을 대체하기 위해 온 것이 아니라, 인간의 능력을 증강시키기 위해 존재합니다. 계산기나 컴퓨터처럼, 우리의 능력을 증폭시켜 줄 새로운 도구라는 점을 강조합니다.  
**토론 주제:**

* 모든 직업에 'AI 부조종사(Co-pilot)'가 등장할 것입니다. 글쓰기, 데이터 분석뿐만 아니라, 다음 장에서 우리가 직접 경험할 코딩 분야에서도 마찬가지입니다.  
* 단순 반복적인 작업에서 벗어나, 창의적이고 전략적인 사고에 더 많은 시간을 할애하게 될 것입니다.  
* 평생 학습과 적응력의 중요성이 커집니다. 미래의 핵심 역량은 이 새로운 도구들과 '함께' 일하는 법을 배우는 것입니다.

---

## **4장: AI 부조종사와 함께하는 코딩 맛보기 (예상 소요 시간: 60분)**

**목표:** 코딩에 대한 두려움 없이 즐겁게 참여할 수 있는 실습 환경을 제공합니다. AI 어시스턴트가 어떻게 기술의 진입 장벽을 낮추고, 창작 과정에서 유용한 파트너가 되는지 직접 체험하게 합니다.

### **4.1. 워크숍 준비: 디지털 작업대 설정하기 (5분)**

강사 가이드:  
"우리는 한 시간 만에 프로그래밍 언어를 마스터하려는 것이 아닙니다. 대신, 코딩이 어떤 '느낌'인지 체험하고, AI가 우리가 재미있는 것을 만드는 데 어떻게 도움을 주는지 볼 것입니다. VS Code를 '코드를 위한 워드 문서'라고 생각하고, Gemini를 대부분의 힘든 일을 대신해 줄 전문가 조수라고 생각하세요."  
**설치 가이드 (사전 배포 및 화면 공유):**

* Visual Studio Code(VS Code) 설치 과정을 담은 간단하고 시각적인 단계별 안내서를 제공합니다.  
* VS Code 내에서 '확장 프로그램(Extensions)' 마켓플레이스를 찾아 'Gemini Code Assist'를 검색하고 '설치(Install)' 버튼을 누르는 과정을 시각적으로 안내합니다.50  
* 최초 1회 구글 계정 로그인 과정을 안내합니다.

### **4.2. AI 코딩 파트너를 만나보세요: 라이브 데모 (15분)**

강사 가이드:  
"우리의 AI 조수가 무엇을 할 수 있는지 직접 보여드리겠습니다. 빈 파이썬 파일(game.py)을 열고, AI에게 도움을 요청해 보겠습니다."  
**주요 기능 시연:**

* 주석으로 코드 생성하기 53:  
  * 코드 파일에 주석을 입력합니다: \# 사용자의 이름을 받아 인사하는 파이썬 함수를 만들어줘  
  * 코드 생성 단축키(Ctrl+Enter 또는 Control+Return)를 누릅니다.  
  * 화면에 나타나는 '고스트 텍스트(ghost text)'를 참가자들에게 보여주며 AI가 코드를 제안하는 모습을 시연합니다.  
* 코드 자동 완성 53:  
  * def say\_hello( 라고 입력하기 시작합니다.  
  * Gemini가 함수 전체를 자동으로 제안하는 것을 보여줍니다.  
  * "이제 Tab 키만 누르면 이 코드가 완성됩니다. 제가 직접 모든 코드를 입력할 필요가 없었죠." 라고 강조하며 AI의 편리함을 보여줍니다.  
* 채팅으로 코드 설명 요청하기 54:  
  * 방금 생성된 함수 전체를 마우스로 선택합니다.  
  * 화면 옆의 Gemini 채팅 사이드바를 엽니다.  
  * 이 코드를 10살 아이도 이해할 수 있게 설명해줘. 라는 프롬프트를 입력합니다.  
  * AI가 생성한 쉬운 설명을 참가자들에게 큰 소리로 읽어줍니다. 이는 AI가 단순히 코드를 작성하는 도구가 아니라, 학습을 돕는 튜터 역할도 할 수 있음을 보여주는 중요한 과정입니다.

### **4.3. 실습: 숫자 맞히기 게임 만들기 (35분)**

강사 가이드:  
"이제 여러분 차례입니다\! 우리 모두 함께 고전적인 '숫자 맞히기' 게임을 만들어 볼 겁니다. 걱정하지 마세요, 거의 모든 코드는 Gemini가 작성해 줄 겁니다."

* **1단계: 마법의 프롬프트 (10분):**  
  * 모든 참가자에게 my\_game.py라는 새 파일을 만들도록 안내합니다.  
  * 아래의 '마법 프롬프트'를 파일 최상단에 주석으로 입력하도록 지시합니다. 이 프롬프트는 AI에게 명확한 목표, 맥락, 역할, 그리고 기대 결과를 모두 제공하는 좋은 프롬프트의 종합 예시입니다.

  Python  
    \# 당신은 친절한 파이썬 프로그래밍 조수입니다.  
    \# 지금부터 간단한 명령줄(command-line) 숫자 맞히기 게임을 처음부터 끝까지 완전한 코드로 작성해주세요.  
    \# 게임 규칙은 다음과 같습니다:  
    \# 1\. 컴퓨터는 1부터 100 사이의 임의의 숫자를 하나 선택합니다.  
    \# 2\. 사용자는 제한된 횟수(예: 7번) 안에 그 숫자를 맞춰야 합니다.  
    \# 3\. 사용자가 숫자를 입력할 때마다, 프로그램은 사용자의 추측이 정답보다 '너무 높음' 또는 '너무 낮음'인지 알려줘야 합니다.  
    \# 4\. 사용자가 정답을 맞히면, 승리 메시지를 출력하고 게임이 종료됩니다.  
    \# 5\. 사용자가 모든 기회를 사용해도 정답을 맞히지 못하면, 패배 메시지와 함께 정답이 무엇이었는지 알려주고 게임이 종료됩니다.  
    \# 6\. 초보자도 이해할 수 있도록 코드의 각 부분에 주석을 달아 설명해주세요.

  * 참가자들에게 코드 생성 단축키를 눌러 AI가 전체 게임 코드를 생성하도록 안내합니다.56  
* **2단계: 코드 이해하고 실행하기 (15분):**  
  * VS Code의 '파이썬 파일 실행' 버튼을 눌러 각자 만든 게임을 실행하고 몇 분간 플레이하도록 합니다.  
  * Gemini를 활용하여 코드의 의미를 파악하도록 유도합니다. 특정 코드 라인을 선택하고 채팅창에 다음과 같이 질문하게 합니다.  
    * 'import random'은 무슨 뜻인가요?  
    * 'while loop'는 무엇을 하는 건가요?  
    * 이 'if/elif/else' 부분은 어떻게 작동하는지 설명해주세요.  
  * 이 상호작용 기반의 탐구 과정이 이번 실습의 핵심 학습 경험입니다.  
* **3단계: 수정하고 실험하기 (10분):**  
  * 참가자들에게 간단한 '도전 과제'를 제시하여 코드 수정을 유도합니다. 이는 AI 조수에게 새로운 지시를 내리는 경험을 제공합니다.  
  * **도전 과제 1:** "숫자 범위가 너무 쉬운 것 같네요. Gemini에게 물어보세요: 숫자 범위를 1에서 500 사이로 바꾸려면 어떻게 해야 하나요?"  
  * **도전 과제 2:** "기회를 더 줍시다. Gemini에게 물어보세요: 주어지는 기회를 10번으로 늘리려면 어떻게 수정해야 하나요?"  
  * **도전 과제 3:** "승리 메시지를 바꿔봅시다. Gemini에게 물어보세요: 승리 메시지를 좀 더 멋지고 화려하게 바꾸려면 어떻게 해야 하나요?"

### **4.4. 마무리 및 질의응답 (5분)**

강사 가이드:  
"축하합니다\! 여러분 모두 방금 첫 파이썬 프로그램을 직접 작성하고 수정해 보셨습니다\! 우리가 세미콜론이나 복잡한 문법에 대해 걱정하는 대신, 게임의 '논리'를 생각하는 데 더 많은 시간을 썼다는 점을 주목해 주세요. 이것이 바로 코딩의 미래입니다. 인간의 아이디어와 AI의 실행력이 결합된 창의적인 파트너십이죠."  
마지막 메시지:  
AI는 기술적 능력의 진입 장벽을 낮추어 누구나 자신의 아이디어를 현실로 만들 수 있게 돕는 강력한 도구임을 다시 한번 강조합니다. 마지막으로 전체 과정에 대한 질의응답 시간을 갖습니다.

#### **참고 자료**

1. How Netflix's Personalize Recommendation Algorithm Works? \- Attract Group, 8월 9, 2025에 액세스, [https://attractgroup.com/blog/how-netflixs-personalize-recommendation-algorithm-works/](https://attractgroup.com/blog/how-netflixs-personalize-recommendation-algorithm-works/)  
2. Netflix Recommendation System: Inside the Algorithm | by Michael Scognamiglio \- Medium, 8월 9, 2025에 액세스, [https://mikescogs20.medium.com/netflix-recommendation-system-inside-the-algorithm-55edc1712748](https://mikescogs20.medium.com/netflix-recommendation-system-inside-the-algorithm-55edc1712748)  
3. A Deep Dive Into Recommendation Algorithms With Netflix Case Study and NVIDIA Deep Learning Technology \- DZone, 8월 9, 2025에 액세스, [https://dzone.com/articles/a-deep-dive-into-recommendation-algorithms-with-ne](https://dzone.com/articles/a-deep-dive-into-recommendation-algorithms-with-ne)  
4. 15 Everyday Examples of Artificial Intelligence You Didn't Know About \- InvoiceOnline.com, 8월 9, 2025에 액세스, [https://www.invoiceonline.com/business-newsletter/technology-and-innovation/15-everyday-examples-of-artificial-intelligence-you-didnt-know-about](https://www.invoiceonline.com/business-newsletter/technology-and-innovation/15-everyday-examples-of-artificial-intelligence-you-didnt-know-about)  
5. Examples of Artificial Intelligence: Everyday Applications \- Blog Pareto, 8월 9, 2025에 액세스, [https://blog.pareto.io/en/examples-of-artificial-intelligence/](https://blog.pareto.io/en/examples-of-artificial-intelligence/)  
6. 20 Uses of Artificial Intelligence in Day-to-Day Life \- Daffodil Software, 8월 9, 2025에 액세스, [https://insights.daffodilsw.com/blog/20-uses-of-artificial-intelligence-in-day-to-day-life](https://insights.daffodilsw.com/blog/20-uses-of-artificial-intelligence-in-day-to-day-life)  
7. 15 Non-Obvious AI Examples In Your Daily Life \- Litslink, 8월 9, 2025에 액세스, [https://litslink.com/blog/non-obvious-ai-examples-in-your-daily-life](https://litslink.com/blog/non-obvious-ai-examples-in-your-daily-life)  
8. Everyday examples and applications of artificial intelligence (AI) \- Tableau, 8월 9, 2025에 액세스, [https://www.tableau.com/data-insights/ai/examples](https://www.tableau.com/data-insights/ai/examples)  
9. AI Examples & Business Use Cases \- IBM, 8월 9, 2025에 액세스, [https://www.ibm.com/think/topics/artificial-intelligence-business-use-cases](https://www.ibm.com/think/topics/artificial-intelligence-business-use-cases)  
10. The Most Significant AI Milestones So Far | Bernard Marr, 8월 9, 2025에 액세스, [https://bernardmarr.com/the-most-significant-ai-milestones-so-far/](https://bernardmarr.com/the-most-significant-ai-milestones-so-far/)  
11. The History of AI: A Timeline of Artificial Intelligence | Coursera, 8월 9, 2025에 액세스, [https://www.coursera.org/articles/history-of-ai](https://www.coursera.org/articles/history-of-ai)  
12. History of Artificial Intelligence: Milestones, Inventions, Trends, Predictions | Clay, 8월 9, 2025에 액세스, [https://clay.global/blog/ai-guide/timeline-of-ai](https://clay.global/blog/ai-guide/timeline-of-ai)  
13. History of artificial intelligence \- Wikipedia, 8월 9, 2025에 액세스, [https://en.wikipedia.org/wiki/History\_of\_artificial\_intelligence](https://en.wikipedia.org/wiki/History_of_artificial_intelligence)  
14. Appendix I: A Short History of AI | One Hundred Year Study on Artificial Intelligence (AI100), 8월 9, 2025에 액세스, [https://ai100.stanford.edu/2016-report/appendix-i-short-history-ai](https://ai100.stanford.edu/2016-report/appendix-i-short-history-ai)  
15. Deep Learning vs. Machine Learning: A Beginner's Guide \- Coursera, 8월 9, 2025에 액세스, [https://www.coursera.org/articles/ai-vs-deep-learning-vs-machine-learning-beginners-guide](https://www.coursera.org/articles/ai-vs-deep-learning-vs-machine-learning-beginners-guide)  
16. Machine-Learning/Matryoshka Representation Learning with Python.md at main \- GitHub, 8월 9, 2025에 액세스, [https://github.com/xbeat/Machine-Learning/blob/main/Matryoshka%20Representation%20Learning%20with%20Python.md](https://github.com/xbeat/Machine-Learning/blob/main/Matryoshka%20Representation%20Learning%20with%20Python.md)  
17. Matryoshka Representation Learning \- YouTube, 8월 9, 2025에 액세스, [https://m.youtube.com/shorts/VQosEgOw84s](https://m.youtube.com/shorts/VQosEgOw84s)  
18. Matryoshka Representation Learning: Nesting Embeddings for Efficiency and Accuracy | by Nayan Shah | Medium, 8월 9, 2025에 액세스, [https://medium.com/@snayan06/mrl-mastering-adaptable-representation-learning-460223c08f8b](https://medium.com/@snayan06/mrl-mastering-adaptable-representation-learning-460223c08f8b)  
19. 인공지능·머신러닝·딥러닝 차이점은?ㅣ개념부터 차이점까지 총 정리, 8월 9, 2025에 액세스, [https://www.codestates.com/blog/content/%EB%A8%B8%EC%8B%A0%EB%9F%AC%EB%8B%9D-%EB%94%A5%EB%9F%AC%EB%8B%9D%EA%B0%9C%EB%85%90](https://www.codestates.com/blog/content/%EB%A8%B8%EC%8B%A0%EB%9F%AC%EB%8B%9D-%EB%94%A5%EB%9F%AC%EB%8B%9D%EA%B0%9C%EB%85%90)  
20. \[AI란 무엇인가\] 인공지능 머신러닝 딥러닝 차이점 총정리 \- 혼공학습단, 8월 9, 2025에 액세스, [https://hongong.hanbit.co.kr/ai-%EB%AC%B4%EC%97%87%EC%9D%B8%EA%B0%80-%EC%9D%B8%EA%B3%B5%EC%A7%80%EB%8A%A5-%EB%A8%B8%EC%8B%A0%EB%9F%AC%EB%8B%9D-%EB%94%A5%EB%9F%AC%EB%8B%9D-%EC%B0%A8%EC%9D%B4%EC%A0%90-%EC%B4%9D%EC%A0%95%EB%A6%AC/](https://hongong.hanbit.co.kr/ai-%EB%AC%B4%EC%97%87%EC%9D%B8%EA%B0%80-%EC%9D%B8%EA%B3%B5%EC%A7%80%EB%8A%A5-%EB%A8%B8%EC%8B%A0%EB%9F%AC%EB%8B%9D-%EB%94%A5%EB%9F%AC%EB%8B%9D-%EC%B0%A8%EC%9D%B4%EC%A0%90-%EC%B4%9D%EC%A0%95%EB%A6%AC/)  
21. 딥 러닝과 머신 러닝의 비교: 차이는 무엇일까요? \- Zendesk, 8월 9, 2025에 액세스, [https://www.zendesk.kr/blog/machine-learning-and-deep-learning/](https://www.zendesk.kr/blog/machine-learning-and-deep-learning/)  
22. What Is Machine Learning (ML)? \- IBM, 8월 9, 2025에 액세스, [https://www.ibm.com/think/topics/machine-learning](https://www.ibm.com/think/topics/machine-learning)  
23. Machine Learning Tutorial \- GeeksforGeeks, 8월 9, 2025에 액세스, [https://www.geeksforgeeks.org/machine-learning/machine-learning/](https://www.geeksforgeeks.org/machine-learning/machine-learning/)  
24. 딥 러닝, 머신러닝, 인공지능의 차이점은 무엇인가요? \- Google Cloud, 8월 9, 2025에 액세스, [https://cloud.google.com/discover/deep-learning-vs-machine-learning?hl=ko](https://cloud.google.com/discover/deep-learning-vs-machine-learning?hl=ko)  
25. What Is Artificial Intelligence (AI)? | Google Cloud, 8월 9, 2025에 액세스, [https://cloud.google.com/learn/what-is-artificial-intelligence](https://cloud.google.com/learn/what-is-artificial-intelligence)  
26. What is deep learning in AI? \- AWS, 8월 9, 2025에 액세스, [https://aws.amazon.com/what-is/deep-learning/](https://aws.amazon.com/what-is/deep-learning/)  
27. Deep Learning Tutorial \- GeeksforGeeks, 8월 9, 2025에 액세스, [https://www.geeksforgeeks.org/deep-learning/deep-learning-tutorial/](https://www.geeksforgeeks.org/deep-learning/deep-learning-tutorial/)  
28. The Surprising Power of Next Word Prediction: Large Language Models Explained, Part 1 | Center for Security and Emerging Technology \- CSET, 8월 9, 2025에 액세스, [https://cset.georgetown.edu/article/the-surprising-power-of-next-word-prediction-large-language-models-explained-part-1/](https://cset.georgetown.edu/article/the-surprising-power-of-next-word-prediction-large-language-models-explained-part-1/)  
29. LLMs are next-word predictors \- YouTube, 8월 9, 2025에 액세스, [https://www.youtube.com/shorts/KHEtJUlpqcg](https://www.youtube.com/shorts/KHEtJUlpqcg)  
30. How Large Language Models Predict the Next Word (and Why That's Powerful) \- Medium, 8월 9, 2025에 액세스, [https://medium.com/@sybrandwildeboer/how-large-language-models-predict-the-next-word-and-why-thats-powerful-b1ac78995e74](https://medium.com/@sybrandwildeboer/how-large-language-models-predict-the-next-word-and-why-thats-powerful-b1ac78995e74)  
31. LLMs Do Not Predict the Next Word \- Harys Dalvi, 8월 9, 2025에 액세스, [https://www.harysdalvi.com/blog/llms-dont-predict-next-word/](https://www.harysdalvi.com/blog/llms-dont-predict-next-word/)  
32. Visualization \- How LLMs Just Predict The Next Word : r/LocalLLaMA \- Reddit, 8월 9, 2025에 액세스, [https://www.reddit.com/r/LocalLLaMA/comments/1ml14kw/visualization\_how\_llms\_just\_predict\_the\_next\_word/](https://www.reddit.com/r/LocalLLaMA/comments/1ml14kw/visualization_how_llms_just_predict_the_next_word/)  
33. Examples of Good vs. Bad Prompts \- WordPress.com, 8월 9, 2025에 액세스, [https://wordpress.com/learn/courses/unlocking-the-power-of-ai/examples-of-good-vs-bad-prompts/](https://wordpress.com/learn/courses/unlocking-the-power-of-ai/examples-of-good-vs-bad-prompts/)  
34. Getting started with prompts for text-based Generative AI tools | Harvard University Information Technology, 8월 9, 2025에 액세스, [https://www.huit.harvard.edu/news/ai-prompts](https://www.huit.harvard.edu/news/ai-prompts)  
35. Good Prompts vs. Bad Prompts with Copilot \- Changing Social, 8월 9, 2025에 액세스, [https://www.changingsocial.com/blog/good-prompts-vs-bad-prompts-copilot/](https://www.changingsocial.com/blog/good-prompts-vs-bad-prompts-copilot/)  
36. AI Prompting Tips from a Power User: How to Get Way Better Responses \- Reddit, 8월 9, 2025에 액세스, [https://www.reddit.com/r/PromptEngineering/comments/1j5ymik/ai\_prompting\_tips\_from\_a\_power\_user\_how\_to\_get/](https://www.reddit.com/r/PromptEngineering/comments/1j5ymik/ai_prompting_tips_from_a_power_user_how_to_get/)  
37. Top LLMs To Use in 2025: Our Best Picks | Splunk, 8월 9, 2025에 액세스, [https://www.splunk.com/en\_us/blog/learn/llms-best-to-use.html](https://www.splunk.com/en_us/blog/learn/llms-best-to-use.html)  
38. Open Source vs. Commercial LLMs: Which for Your Enterprise Needs? \- ContextClue, 8월 9, 2025에 액세스, [https://context-clue.com/blog/open-source-vs-commercial-llms/](https://context-clue.com/blog/open-source-vs-commercial-llms/)  
39. Open-Source vs. Commercial LLMs – Which Fits You Best? \- Zencoder, 8월 9, 2025에 액세스, [https://zencoder.ai/blog/open-source-vs-commercial-llms](https://zencoder.ai/blog/open-source-vs-commercial-llms)  
40. Open vs. Closed LLMs in 2025: Strategic Tradeoffs for Enterprise AI \- Medium, 8월 9, 2025에 액세스, [https://medium.com/data-science-collective/open-vs-closed-llms-in-2025-strategic-tradeoffs-for-enterprise-ai-668af30bffa0](https://medium.com/data-science-collective/open-vs-closed-llms-in-2025-strategic-tradeoffs-for-enterprise-ai-668af30bffa0)  
41. Top LLMs in 2025: Comparing Claude, Gemini, and GPT-4 LLaMA \- FastBots.ai, 8월 9, 2025에 액세스, [https://fastbots.ai/blog/top-llms-in-2025-comparing-claude-gemini-and-gpt-4-llama](https://fastbots.ai/blog/top-llms-in-2025-comparing-claude-gemini-and-gpt-4-llama)  
42. Most powerful LLMs (Large Language Models) in 2025 \- Codingscape, 8월 9, 2025에 액세스, [https://codingscape.com/blog/most-powerful-llms-large-language-models](https://codingscape.com/blog/most-powerful-llms-large-language-models)  
43. Top 7 LLMs Ranked in 2025: GPT-4o, Gemini, Claude & More \- Whistler Billboards, 8월 9, 2025에 액세스, [https://www.whistlerbillboards.com/friday-feature/ranking-the-top-7-llms-in-2025/](https://www.whistlerbillboards.com/friday-feature/ranking-the-top-7-llms-in-2025/)  
44. The best large language models (LLMs) in 2025 \- Zapier, 8월 9, 2025에 액세스, [https://zapier.com/blog/best-llm/](https://zapier.com/blog/best-llm/)  
45. Claude vs. GPT-4.5 vs. Gemini: A Comprehensive Comparison \- Evolution AI, 8월 9, 2025에 액세스, [https://www.evolution.ai/post/claude-vs-gpt-4o-vs-gemini](https://www.evolution.ai/post/claude-vs-gpt-4o-vs-gemini)  
46. The 11 best open-source LLMs for 2025 \- n8n Blog, 8월 9, 2025에 액세스, [https://blog.n8n.io/open-source-llm/](https://blog.n8n.io/open-source-llm/)  
47. Top 5 open-source LLMs to watch out for in 2024 \- Upstage AI, 8월 9, 2025에 액세스, [https://www.upstage.ai/blog/en/top-open-source-llms-2024](https://www.upstage.ai/blog/en/top-open-source-llms-2024)  
48. Top 8 Open-Source LLMs for Coding \- E2E Networks, 8월 9, 2025에 액세스, [https://www.e2enetworks.com/blog/top-8-open-source-llms-for-coding](https://www.e2enetworks.com/blog/top-8-open-source-llms-for-coding)  
49. Best LLMs for Business in 2025: Use-Case Comparison \- Tech Research Online, 8월 9, 2025에 액세스, [https://techresearchonline.com/blog/best-llm-for-business-use-case-comparison/](https://techresearchonline.com/blog/best-llm-for-business-use-case-comparison/)  
50. 개인을 위한 Gemini Code Assist 설정하기, 8월 9, 2025에 액세스, [https://developers.google.com/gemini-code-assist/docs/set-up-gemini?hl=ko](https://developers.google.com/gemini-code-assist/docs/set-up-gemini?hl=ko)  
51. Gemini Code Assist \- Educative.io, 8월 9, 2025에 액세스, [https://www.educative.io/blog/gemini-code-assist](https://www.educative.io/blog/gemini-code-assist)  
52. Set up Gemini Code Assist for individuals \- Google for Developers, 8월 9, 2025에 액세스, [https://developers.google.com/gemini-code-assist/docs/set-up-gemini](https://developers.google.com/gemini-code-assist/docs/set-up-gemini)  
53. 개인을 위한 Gemini Code Assist로 코딩 | Google for Developers, 8월 9, 2025에 액세스, [https://developers.google.com/gemini-code-assist/docs/write-code-gemini?hl=ko](https://developers.google.com/gemini-code-assist/docs/write-code-gemini?hl=ko)  
54. Gemini Code Assist를 사용한 코드 \- Google Cloud, 8월 9, 2025에 액세스, [https://cloud.google.com/code/docs/vscode/write-code-gemini?hl=ko](https://cloud.google.com/code/docs/vscode/write-code-gemini?hl=ko)  
55. 24화 VS Code에서 Gemini 이용하기 \- 브런치, 8월 9, 2025에 액세스, [https://brunch.co.kr/@@kEJ/210](https://brunch.co.kr/@@kEJ/210)  
56. How to make a simple guessing game in Python \- SheCodes, 8월 9, 2025에 액세스, [https://www.shecodes.io/athena/39028-how-to-make-a-simple-guessing-game-in-python](https://www.shecodes.io/athena/39028-how-to-make-a-simple-guessing-game-in-python)  
57. How To Code a Simple Number Guessing Game in Python \- DEV Community, 8월 9, 2025에 액세스, [https://dev.to/balapriya/how-to-code-a-simple-number-guessing-game-in-python-4jai](https://dev.to/balapriya/how-to-code-a-simple-number-guessing-game-in-python-4jai)  
58. Build a Fun Number Guessing Game in Python: A Guide for Beginners \- Medium, 8월 9, 2025에 액세스, [https://medium.com/@awaleedpk/build-a-fun-number-guessing-game-in-python-a-guide-for-beginners-aff6cd74fde3](https://medium.com/@awaleedpk/build-a-fun-number-guessing-game-in-python-a-guide-for-beginners-aff6cd74fde3)