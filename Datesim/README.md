# DateSim

이상형을 설정하고, AI가 제시하는 3가지 선택지 중 하나를 골라 데이트 상황을 이어가는 미니 게임. 3번의 선택마다 장면을 반영해 이미지를 다시 생성하며, 앞선 대화 이력을 바탕으로 연결성 있게 진행됩니다.

## 실행

1) 의존성 설치 (Datesim 디렉터리)
```bash
npm i
```

2) 환경변수 파일 생성
```bash
copy .env.example .env
# .env 파일에 GEMINI_API_KEY=... 입력
```

3) 개발 서버 실행 (기본 포트: 5174)
```bash
npm run dev
# 또는 nodemon 대신 node로 실행
npm start
```

## 스크립트
- `npm run dev`: 정적 페이지와 API 서버 동시 실행(단일 Express)
  - 접속: `http://localhost:5174`

## 구조
- `public/index.html`: UI, 이상형 설정/리롤/확정/선택지 루프, 캔버스 미리보기
- `server.js`: API 엔드포인트(헬스/방문자/DateSim 흐름/이미지 생성)

## 모델/이미지
- 텍스트 형성: 기본값 `gemini-2.5-flash-lite` (환경변수 `GENAI_TEXT_MODEL`로 덮어쓰기 가능)
- 이미지 생성: 기본값 `gemini-2.5-flash-image-preview` (환경변수 `GENAI_IMAGE_MODEL`)

> API 키는 `.env`의 `GEMINI_API_KEY`에만 보관되고, 클라이언트로 전달되지 않습니다.

## 게임 규칙
- 이상형 설정: 2D/3D, 이름, 종족, 인종, 성별, 기타 요청사항
- 리롤: 최종 확정 전 최대 2회 미리보기 재생성 가능
- 진행: 매 턴 3가지 선택지 제공, 3번째 선택마다 이미지 재생성
- 정책 실패 시: 설정을 변경하도록 안내 후 재시도


