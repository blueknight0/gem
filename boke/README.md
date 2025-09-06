# Boke Image Tool

간단한 보케(ボケ) 시나리오 생성 + 이미지 생성(제미나이 프록시) + 한 줄 유머 오버레이 도구.

## 실행

1) 의존성 설치
```bash
npm i
```

2) 환경변수 파일 생성
```bash
copy .env.example .env
# .env 파일에 GEMINI_API_KEY=... 입력
```

3) 개발 서버 실행
```bash
npm run dev
```

## 스크립트
- `npm run dev`: 정적 페이지와 API 서버 동시 실행(단일 Express)

## 구조
- `public/index.html`: UI, 캔버스 렌더링 및 다운로드
- `src/boke/scenario.ts`: 보케 시나리오 리스트/빌더/영문 프롬프트
- `src/server.ts`: API 엔드포인트(헬스/시나리오/이미지 프록시)

## Gemini 이미지 프록시
현재 `/api/generate`는 placeholder(1x1 PNG 베이스64)입니다. Google AI Images API 공개 베타/정식 명세에 맞춰 `src/server.ts`의 해당 구간을 실제 호출로 교체하세요.

> API 키는 `.env`에만 보관되고, 클라이언트로 전달되지 않습니다.


