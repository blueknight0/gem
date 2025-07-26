# 게임 아트워크 가이드

## 이미지 파일 사용 방법

### 1. 이미지 파일 준비
다음 경로에 이미지 파일들을 추가하세요:

```
public/images/characters/
├── beginner.png      # 초급자 캐릭터
├── intermediate.png  # 중급자 캐릭터  
├── advanced.png      # 고급자 캐릭터
└── elite.png         # 엘리트 캐릭터
```

### 2. 권장 이미지 사양
- **크기**: 120x150px (또는 비율 유지)
- **포맷**: PNG (투명 배경 지원)
- **스타일**: 픽셀 아트 또는 2D 일러스트
- **색상**: 체형별로 구분되는 색상 사용

### 3. 체형별 디자인 가이드

#### Beginner (초급자)
- 색상: 회색 계열 (#95a5a6)
- 체형: 일반적인 체형
- 특징: 기본적인 모습

#### Intermediate (중급자)  
- 색상: 파란색 계열 (#3498db)
- 체형: 약간 근육질
- 특징: 운동복 착용

#### Advanced (고급자)
- 색상: 주황색 계열 (#e67e22) 
- 체형: 근육질 체형
- 특징: 운동 장비 착용

#### Elite (엘리트)
- 색상: 금색 계열 (#f1c40f)
- 체형: 매우 근육질
- 특징: 후광 효과, 트로피 등

## 아트 스타일 옵션

### 1. 이미지 스프라이트 (CharacterSprite)
- 실제 이미지 파일 사용
- 가장 고품질 그래픽
- 파일 크기 고려 필요

### 2. SVG 아트워크 (SVGCharacter)  
- 벡터 그래픽으로 확대/축소 자유
- 애니메이션 효과 쉬움
- 파일 크기 작음

### 3. CSS 아트워크 (CSSCharacter)
- 순수 CSS로 구현
- 이미지 파일 불필요
- 커스터마이징 쉬움

### 4. 픽셀 아트 (기본)
- 간단한 픽셀 스타일
- 레트로 게임 느낌
- 가장 가벼움

## 커스터마이징 방법

### 새로운 아트 스타일 추가
1. `src/components/` 에 새 컴포넌트 생성
2. `CharacterDisplay.js`에 옵션 추가
3. 스타일 선택 버튼에 추가

### 애니메이션 추가
- CSS 애니메이션 사용
- `animated` prop으로 제어
- 체형별 다른 애니메이션 가능

## 성능 최적화

### 이미지 최적화
- WebP 포맷 사용 고려
- 이미지 압축 도구 사용
- 스프라이트 시트 활용

### 로딩 최적화  
- 이미지 preload
- lazy loading 적용
- 폴백 시스템 구현

## 예시 코드

```jsx
// 커스텀 캐릭터 컴포넌트
function MyCharacter({ character }) {
  return (
    <div className="my-character">
      <img 
        src={`/images/characters/${character.bodyType}.png`}
        alt={character.bodyType}
        onError={handleImageError}
      />
    </div>
  );
}
```

## 추천 도구

### 이미지 편집
- Aseprite (픽셀 아트)
- Photoshop
- GIMP (무료)

### 최적화
- TinyPNG (압축)
- ImageOptim
- Squoosh (Google)

### 애니메이션
- CSS 애니메이션
- Lottie (복잡한 애니메이션)
- GreenSock (GSAP)