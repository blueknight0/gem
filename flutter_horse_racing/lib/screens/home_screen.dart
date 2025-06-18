import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/race_provider.dart';
import '../widgets/setup_widget.dart';
import '../widgets/race_widget.dart';
import '../widgets/result_widget.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF8F9FA),
      appBar: AppBar(
        title: const Text(
          '다그닥 다그닥 그랑프리 🐎',
          style: TextStyle(
            fontWeight: FontWeight.bold,
            fontSize: 20,
          ),
        ),
        backgroundColor: const Color(0xFF005A9C),
        foregroundColor: Colors.white,
        centerTitle: true,
        elevation: 0,
        actions: [
          Consumer<RaceProvider>(
            builder: (context, raceProvider, child) {
              return IconButton(
                icon: Icon(
                  raceProvider.isSoundEnabled 
                    ? Icons.volume_up 
                    : Icons.volume_off,
                ),
                onPressed: raceProvider.toggleSound,
              );
            },
          ),
        ],
      ),
      body: Consumer<RaceProvider>(
        builder: (context, raceProvider, child) {
          switch (raceProvider.raceState) {
            case RaceState.setup:
              return const SetupWidget();
            case RaceState.ready:
            case RaceState.racing:
              return const RaceWidget();
            case RaceState.finished:
              return const ResultWidget();
            default:
              return const SetupWidget();
          }
        },
      ),
    );
  }
} 