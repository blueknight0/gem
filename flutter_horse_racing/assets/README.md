# Assets 폴더

이 폴더에는 게임에서 사용하는 리소스 파일들을 저장합니다.

## 폴더 구조

```
assets/
├── images/          # 이미지 파일들
│   ├── horse1.png   # 말 이미지 1
│   ├── horse2.png   # 말 이미지 2
│   └── ...
└── sounds/          # 사운드 파일들
    ├── gallop.mp3   # 말발굽 소리
    ├── boost.mp3    # 부스터 효과음
    └── victory.mp3  # 승리 팡파레
```

## 리소스 추가 방법

1. 해당 폴더에 파일 추가
2. `pubspec.yaml`에서 assets 경로 확인
3. `flutter pub get` 실행

## 지원 파일 형식

### 이미지
- PNG, JPG, JPEG, GIF, WebP

### 사운드
- MP3, WAV, AAC, OGG

현재는 기본 이모지(🐎)를 사용하고 있으며, 필요에 따라 커스텀 이미지를 추가할 수 있습니다. 