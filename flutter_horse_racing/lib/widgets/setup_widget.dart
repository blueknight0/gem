import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/race_provider.dart';

class SetupWidget extends StatefulWidget {
  const SetupWidget({Key? key}) : super(key: key);

  @override
  State<SetupWidget> createState() => _SetupWidgetState();
}

class _SetupWidgetState extends State<SetupWidget> {
  final TextEditingController _tournamentController = TextEditingController();
  final TextEditingController _participantsController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _tournamentController.text = "다그닥 다그닥 그랑프리";
    _participantsController.text = "김민준\n이서연\n박도윤\n최지우\n정하은\n이준호";
  }

  @override
  void dispose() {
    _tournamentController.dispose();
    _participantsController.dispose();
    super.dispose();
  }

  void _prepareRace() {
    final raceProvider = Provider.of<RaceProvider>(context, listen: false);
    
    // 대회 이름 설정
    raceProvider.setTournamentName(_tournamentController.text.trim());
    
    // 참가자 목록 설정
    final participantNames = _participantsController.text
        .split('\n')
        .map((name) => name.trim())
        .where((name) => name.isNotEmpty)
        .toList();
    
    if (participantNames.length < 2) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('최소 2명 이상의 참가자가 필요합니다.'),
          backgroundColor: Colors.red,
        ),
      );
      return;
    }
    
    if (participantNames.length > 8) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('최대 8명까지 참가할 수 있습니다.'),
          backgroundColor: Colors.orange,
        ),
      );
      return;
    }
    
    raceProvider.setParticipants(participantNames);
    raceProvider.prepareRace();
  }

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // 제목
          const Text(
            '달려라 달려!\n다그닥 다그닥 그랑프리 🐎',
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.bold,
              color: Color(0xFF005A9C),
              height: 1.3,
            ),
          ),
          const SizedBox(height: 30),
          
          // 경주 설정 카드
          Card(
            elevation: 4,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12),
            ),
            child: Padding(
              padding: const EdgeInsets.all(20.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    '경주 설정',
                    style: TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                      color: Color(0xFF005A9C),
                    ),
                  ),
                  const SizedBox(height: 20),
                  
                  // 대회 이름 입력
                  const Text(
                    '대회 이름',
                    style: TextStyle(
                      fontWeight: FontWeight.bold,
                      color: Color(0xFF005A9C),
                    ),
                  ),
                  const SizedBox(height: 8),
                  TextField(
                    controller: _tournamentController,
                    decoration: InputDecoration(
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(8),
                      ),
                      focusedBorder: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(8),
                        borderSide: const BorderSide(
                          color: Color(0xFF005A9C),
                          width: 2,
                        ),
                      ),
                      contentPadding: const EdgeInsets.symmetric(
                        horizontal: 12,
                        vertical: 12,
                      ),
                    ),
                  ),
                  const SizedBox(height: 20),
                  
                  // 참가자 입력
                  const Text(
                    '참가자 명단',
                    style: TextStyle(
                      fontWeight: FontWeight.bold,
                      color: Color(0xFF005A9C),
                    ),
                  ),
                  const SizedBox(height: 4),
                  const Text(
                    '참가자 이름을 한 줄에 한 명씩 입력해주세요. (최소 2명, 최대 8명)',
                    style: TextStyle(
                      fontSize: 12,
                      color: Colors.grey,
                    ),
                  ),
                  const SizedBox(height: 8),
                  TextField(
                    controller: _participantsController,
                    maxLines: 8,
                    decoration: InputDecoration(
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(8),
                      ),
                      focusedBorder: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(8),
                        borderSide: const BorderSide(
                          color: Color(0xFF005A9C),
                          width: 2,
                        ),
                      ),
                      contentPadding: const EdgeInsets.all(12),
                      hintText: '김민준\n이서연\n박도윤\n최지우\n...',
                    ),
                  ),
                  const SizedBox(height: 20),
                  
                  // 경주 준비 버튼
                  SizedBox(
                    width: double.infinity,
                    height: 50,
                    child: ElevatedButton(
                      onPressed: _prepareRace,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFF007BFF),
                        foregroundColor: Colors.white,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(8),
                        ),
                        elevation: 2,
                      ),
                      child: const Text(
                        '경주 준비',
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
          
          const SizedBox(height: 20),
          
          // 게임 설명
          Card(
            elevation: 2,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12),
            ),
            child: const Padding(
              padding: EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    '🎮 게임 방법',
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                      color: Color(0xFF005A9C),
                    ),
                  ),
                  SizedBox(height: 8),
                  Text(
                    '• 참가자들이 경주를 벌입니다\n'
                    '• 랜덤한 속도로 말들이 달립니다\n'
                    '• 때때로 부스터 효과가 발동됩니다\n'
                    '• 가장 먼저 결승선에 도착하는 사람이 승리!',
                    style: TextStyle(
                      fontSize: 14,
                      color: Colors.grey,
                      height: 1.5,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
} 