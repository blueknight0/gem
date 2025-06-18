# 다그닥 다그닥 그랑프리 🐎

Flutter로 제작된 재미있는 경마 게임입니다!

## 📱 게임 소개

**다그닥 다그닥 그랑프리**는 참가자들이 가상의 말을 타고 경주를 벌이는 재미있는 게임입니다. 
원래 JavaScript로 만들어진 웹 게임을 Flutter로 포팅하여 모바일에서도 즐길 수 있습니다.

### 🎮 게임 특징

- **간단한 설정**: 대회 이름과 참가자만 입력하면 바로 시작
- **실시간 경주**: 말들이 실시간으로 달리는 모습을 시각적으로 확인
- **랜덤 부스터**: 경주 중 랜덤하게 발생하는 부스터 효과
- **실시간 해설**: 경주 상황에 맞는 실시간 해설
- **시상대 시스템**: 1, 2, 3등 시상대와 Confetti 효과
- **사운드 설정**: 사운드 ON/OFF 기능

## 🚀 Flutter 개발 환경 설정

### 1. Flutter SDK 설치

1. [Flutter 공식 사이트](https://flutter.dev/docs/get-started/install/windows)에서 Flutter SDK 다운로드
2. 다운로드한 zip 파일을 `C:\flutter`에 압축 해제
3. 시스템 환경 변수 PATH에 `C:\flutter\bin` 추가

### 2. 개발 도구 설치

```bash
# Android Studio 설치 (권장)
# 또는 VS Code + Flutter 확장 프로그램

# Flutter doctor 실행하여 설치 확인
flutter doctor
```

### 3. 안드로이드 설정

```bash
# Android Studio에서 Android SDK 설치
# Android 라이센스 동의
flutter doctor --android-licenses
```

## 🛠️ 프로젝트 설정 및 실행

### 1. 프로젝트 생성 및 이동

```bash
# 새 Flutter 프로젝트 생성
flutter create horse_racing_game
cd horse_racing_game

# 또는 기존 프로젝트 폴더 사용
cd flutter_horse_racing
```

### 2. 의존성 설치

```bash
# pubspec.yaml의 의존성 설치
flutter pub get
```

### 3. 앱 실행

```bash
# 연결된 디바이스 확인
flutter devices

# 앱 실행 (디버그 모드)
flutter run

# 또는 특정 디바이스에서 실행
flutter run -d chrome  # 웹 브라우저
flutter run -d windows # Windows 데스크톱
```

## 📁 프로젝트 구조

```
flutter_horse_racing/
├── lib/
│   ├── main.dart                 # 앱 엔트리 포인트
│   ├── models/
│   │   └── participant.dart      # 참가자 모델
│   ├── providers/
│   │   └── race_provider.dart    # 게임 상태 관리
│   ├── screens/
│   │   └── home_screen.dart      # 메인 화면
│   └── widgets/
│       ├── setup_widget.dart     # 게임 설정 화면
│       ├── race_widget.dart      # 경주 화면
│       └── result_widget.dart    # 결과 화면
├── pubspec.yaml                  # 프로젝트 설정 및 의존성
└── README.md                     # 이 파일
```

## 🎯 사용법

### 1. 게임 설정
- **대회 이름**: 원하는 대회 이름 입력
- **참가자 명단**: 한 줄에 한 명씩 참가자 이름 입력 (최소 2명, 최대 8명)

### 2. 경주 진행
- **경주 준비** 버튼을 눌러 게임 준비
- **경주 시작** 버튼을 눌러 경주 시작
- 실시간으로 말들의 위치와 순위 확인

### 3. 결과 확인
- 경주 종료 후 1, 2, 3등 시상대 확인
- 전체 순위 리스트 확인
- **다시하기** 버튼으로 새 게임 시작

## 🔧 주요 기능 설명

### State Management (Provider)
- `RaceProvider`를 통한 게임 상태 관리
- 참가자 정보, 경주 진행 상황, 순위 등을 실시간 업데이트

### 애니메이션
- Timer를 사용한 실시간 위치 업데이트
- 부스터 효과 시각화
- Confetti 라이브러리를 이용한 축하 효과

### 반응형 UI
- 다양한 화면 크기에 대응하는 반응형 레이아웃
- Material Design 가이드라인 준수

## 🎨 커스터마이징

### 게임 설정 변경
```dart
// race_provider.dart에서 설정 변경 가능
final double _raceDistance = 500.0; // 경주 거리 (픽셀)
double _remainingDistance = 2000.0; // 표시용 거리 (미터)
```

### 부스터 확률 조정
```dart
// _randomBoost() 함수에서 확률 조정
if (_participants.isNotEmpty && Random().nextDouble() < 0.3) {
  // 0.3 = 30% 확률, 원하는 확률로 변경 가능
}
```

### 색상 테마 변경
```dart
// 각 위젯에서 Color 값 수정
const Color(0xFF005A9C) // 메인 블루 색상
const Color(0xFF007BFF) // 버튼 색상
```

## 🚨 문제 해결

### Flutter 설치 오류
```bash
# PATH 설정 확인
echo $PATH  # macOS/Linux
echo %PATH% # Windows

# Flutter doctor로 문제 진단
flutter doctor -v
```

### 의존성 충돌
```bash
# pub cache 정리
flutter pub cache clean
flutter pub get
```

### 빌드 오류
```bash
# 클린 빌드
flutter clean
flutter pub get
flutter run
```

## 📝 개발 팁

### 초보자를 위한 Flutter 학습 순서
1. **Dart 기초 문법** 학습
2. **Widget 개념** 이해 (StatelessWidget, StatefulWidget)
3. **State Management** 이해 (Provider 패턴)
4. **Layout과 UI** 구성 방법
5. **애니메이션과 상호작용** 구현

### 유용한 Flutter 명령어
```bash
flutter create my_app        # 새 프로젝트 생성
flutter run                  # 앱 실행
flutter build apk           # Android APK 빌드
flutter build web           # 웹 빌드
flutter doctor              # 환경 설정 확인
flutter clean               # 빌드 캐시 정리
```

### 추천 확장 기능 (VS Code)
- Flutter
- Dart
- Flutter Widget Snippets
- Awesome Flutter Snippets

## 🎯 향후 개발 계획

- [ ] 사운드 효과 추가
- [ ] 다양한 말 캐릭터 추가
- [ ] 토너먼트 모드 구현
- [ ] 통계 및 기록 저장
- [ ] 멀티플레이어 기능
- [ ] 베팅 시스템 추가

## 📄 라이센스

이 프로젝트는 교육 목적으로 만들어졌습니다. 자유롭게 수정하고 배포할 수 있습니다.

## 🤝 기여하기

버그 발견이나 기능 개선 제안이 있으시면 언제든지 알려주세요!

---

**즐거운 경마 게임 되세요! 🐎🏁** 