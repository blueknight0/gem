import 'dart:async';
import 'dart:math';
import 'package:flutter/foundation.dart';
import '../models/participant.dart';

enum RaceState { setup, ready, racing, finished }

class RaceProvider with ChangeNotifier {
  // 게임 상태
  RaceState _raceState = RaceState.setup;
  String _tournamentName = "다그닥 다그닥 그랑프리";
  List<Participant> _participants = [];
  List<Participant> _winners = [];
  
  // 경주 설정
  final double _raceDistance = 500.0; // 픽셀 단위
  Timer? _raceTimer;
  Timer? _boostTimer;
  double _remainingDistance = 2000.0; // 미터 단위
  String _commentary = "경주 준비 중...";
  
  // 사운드 관련
  bool _isSoundEnabled = true;
  
  // Getters
  RaceState get raceState => _raceState;
  String get tournamentName => _tournamentName;
  List<Participant> get participants => _participants;
  List<Participant> get winners => _winners;
  double get raceDistance => _raceDistance;
  double get remainingDistance => _remainingDistance;
  String get commentary => _commentary;
  bool get isSoundEnabled => _isSoundEnabled;
  
  // 참가자 순위 정렬
  List<Participant> get sortedParticipants {
    final sorted = List<Participant>.from(_participants);
    sorted.sort((a, b) => b.position.compareTo(a.position));
    
    // 순위 업데이트
    for (int i = 0; i < sorted.length; i++) {
      sorted[i].rank = i + 1;
    }
    
    return sorted;
  }

  void setTournamentName(String name) {
    _tournamentName = name;
    notifyListeners();
  }

  void setParticipants(List<String> names) {
    _participants = names.map((name) => Participant(
      name: name,
      speed: 0.8 + Random().nextDouble() * 0.4, // 0.8 ~ 1.2 속도
    )).toList();
    notifyListeners();
  }

  void prepareRace() {
    if (_participants.isNotEmpty) {
      _raceState = RaceState.ready;
      _commentary = "경주 준비 완료! 시작 버튼을 눌러주세요.";
      // 참가자 위치 초기화
      for (var participant in _participants) {
        participant.position = 0.0;
        participant.isFinished = false;
        participant.rank = 0;
      }
      notifyListeners();
    }
  }

  void startRace() {
    if (_raceState == RaceState.ready) {
      _raceState = RaceState.racing;
      _commentary = "경주 시작! 🏁";
      _remainingDistance = 2000.0;
      
      // 경주 시뮬레이션 타이머 시작
      _raceTimer = Timer.periodic(const Duration(milliseconds: 50), (timer) {
        _updateRace();
      });

      // 랜덤 부스터 타이머
      _boostTimer = Timer.periodic(const Duration(milliseconds: 500), (timer) {
        _randomBoost();
      });
      
      notifyListeners();
    }
  }

  void _updateRace() {
    bool raceFinished = true;
    
    for (var participant in _participants) {
      if (!participant.isFinished) {
        // 랜덤한 속도 변화
        double speedVariation = 0.9 + Random().nextDouble() * 0.2; // 0.9 ~ 1.1
        participant.updatePosition(0.05 * speedVariation);
        
        // 결승선 도착 체크
        if (participant.position >= _raceDistance) {
          participant.position = _raceDistance;
          participant.isFinished = true;
          if (!_winners.contains(participant)) {
            _winners.add(participant);
          }
        } else {
          raceFinished = false;
        }
      }
    }

    // 남은 거리 계산 (선두 기준)
    double maxPosition = _participants.map((p) => p.position).reduce(max);
    _remainingDistance = 2000 - (maxPosition / _raceDistance * 2000);
    if (_remainingDistance < 0) _remainingDistance = 0;

    // 해설 업데이트
    _updateCommentary();

    if (raceFinished || _winners.length >= 3) {
      _finishRace();
    }
    
    notifyListeners();
  }

  void _randomBoost() {
    if (_participants.isNotEmpty && Random().nextDouble() < 0.3) {
      final randomParticipant = _participants[Random().nextInt(_participants.length)];
      if (!randomParticipant.isFinished && !randomParticipant.isBoosting) {
        randomParticipant.boost();
        
        // 1초 후 부스터 해제
        Timer(const Duration(seconds: 1), () {
          randomParticipant.resetBoost();
        });
      }
    }
  }

  void _updateCommentary() {
    final leader = sortedParticipants.first;
    final commentaries = [
      "${leader.name}이(가) 선두를 달리고 있습니다!",
      "치열한 접전이 벌어지고 있습니다!",
      "${leader.name}의 질주가 계속됩니다!",
      "누가 우승할까요?",
      "마지막 스퍼트입니다!"
    ];
    
    if (Random().nextDouble() < 0.1) { // 10% 확률로 해설 변경
      _commentary = commentaries[Random().nextInt(commentaries.length)];
    }
  }

  void _finishRace() {
    _raceState = RaceState.finished;
    _raceTimer?.cancel();
    _boostTimer?.cancel();
    
    if (_winners.isNotEmpty) {
      _commentary = "🏆 ${_winners.first.name}님이 우승하셨습니다!";
    }
    
    notifyListeners();
  }

  void resetRace() {
    _raceState = RaceState.setup;
    _participants.clear();
    _winners.clear();
    _commentary = "경주 준비 중...";
    _remainingDistance = 2000.0;
    _raceTimer?.cancel();
    _boostTimer?.cancel();
    notifyListeners();
  }

  void toggleSound() {
    _isSoundEnabled = !_isSoundEnabled;
    notifyListeners();
  }

  @override
  void dispose() {
    _raceTimer?.cancel();
    _boostTimer?.cancel();
    super.dispose();
  }
} 