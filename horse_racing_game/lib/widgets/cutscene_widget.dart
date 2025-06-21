import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/race_provider.dart';

class CutsceneWidget extends StatefulWidget {
  const CutsceneWidget({Key? key}) : super(key: key);

  @override
  _CutsceneWidgetState createState() => _CutsceneWidgetState();
}

class _CutsceneWidgetState extends State<CutsceneWidget> with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _animation;
  String? _currentImagePath;
  bool _isFromLeft = true;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: const Duration(milliseconds: 600),
      vsync: this,
    );

    _animation = CurvedAnimation(
      parent: _controller,
      curve: Curves.easeOutCubic,
    );
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    final raceProvider = Provider.of<RaceProvider>(context);
    
    // 이미지 경로가 변경되었을 때만 애니메이션 실행
    if (raceProvider.cutsceneImagePath != null && raceProvider.cutsceneImagePath != _currentImagePath) {
      setState(() {
        _currentImagePath = raceProvider.cutsceneImagePath;
        _isFromLeft = raceProvider.cutsceneFromLeft;
      });
      _controller.forward(from: 0.0);
    } else if (raceProvider.cutsceneImagePath == null && _currentImagePath != null) {
      // 컷씬이 사라져야 할 때 (상태가 null로 바뀔 때)
      setState(() {
        _currentImagePath = null;
      });
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (_currentImagePath == null) {
      return const SizedBox.shrink(); // 이미지가 없으면 아무것도 그리지 않음
    }

    final size = MediaQuery.of(context).size;
    final imageWidth = size.width * 0.2; // 화면 너비의 20% (기존 40%에서 1/2)
    final imageHeight = imageWidth * 1.2; // 이미지 높이

    return AnimatedBuilder(
      animation: _animation,
      builder: (context, child) {
        // 애니메이션 값(0.0 -> 1.0)에 따라 위치 계산
        final position = _animation.value;
        double left = _isFromLeft ? -imageWidth + (imageWidth * position) : size.width - (imageWidth * position);
        
        // 정점에 도달하면 잠시 멈췄다가 빠르게 사라지는 효과
        double opacity = 1.0;
        if (_controller.value > 0.5) {
           // 0.5 -> 1.0 동안 1.0 -> 0.0 으로 투명도 변경
          opacity = 1.0 - ((_controller.value - 0.5) * 2);
        }

        return Positioned(
          left: left,
          top: size.height * 0.2,
          child: Opacity(
            opacity: opacity < 0 ? 0 : opacity,
            child: Transform(
              transform: Matrix4.identity()
                ..setEntry(3, 2, 0.001) // 3D 효과를 위한 원근감
                ..rotateY(_isFromLeft ? 0.2 * (1 - position) : -0.2 * (1-position)), // 약간 회전
              alignment: _isFromLeft ? FractionalOffset.centerRight : FractionalOffset.centerLeft,
              child: Image.asset(
                _currentImagePath!,
                width: imageWidth,
                height: imageHeight,
                fit: BoxFit.contain,
              ),
            ),
          ),
        );
      },
    );
  }
} 