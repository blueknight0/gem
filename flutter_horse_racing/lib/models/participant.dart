class Participant {
  final String name;
  double position;
  double speed;
  bool isBoosting;
  int rank;
  bool isFinished;
  
  Participant({
    required this.name,
    this.position = 0.0,
    this.speed = 1.0,
    this.isBoosting = false,
    this.rank = 0,
    this.isFinished = false,
  });

  void updatePosition(double deltaTime) {
    if (!isFinished) {
      double currentSpeed = speed;
      if (isBoosting) {
        currentSpeed *= 2.0; // 부스터 효과
      }
      position += currentSpeed * deltaTime * 100; // 픽셀 단위로 이동
    }
  }

  void boost() {
    if (!isBoosting) {
      isBoosting = true;
      // 일정 시간 후 부스터 효과 제거 (실제로는 타이머 필요)
    }
  }

  void resetBoost() {
    isBoosting = false;
  }

  Map<String, dynamic> toJson() {
    return {
      'name': name,
      'position': position,
      'speed': speed,
      'isBoosting': isBoosting,
      'rank': rank,
      'isFinished': isFinished,
    };
  }

  factory Participant.fromJson(Map<String, dynamic> json) {
    return Participant(
      name: json['name'],
      position: json['position'],
      speed: json['speed'],
      isBoosting: json['isBoosting'],
      rank: json['rank'],
      isFinished: json['isFinished'],
    );
  }
} 