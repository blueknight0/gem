import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Dimensions } from 'react-native';
import { useGame } from '../context/GameContext';
import CharacterDisplay from '../components/CharacterDisplay';
import WODSelector from '../components/WODSelector';
import RhythmGame from '../components/RhythmGame';
import StatsPanel from '../components/StatsPanel';

const { width, height } = Dimensions.get('window');

export default function GameScreen() {
  const { state, dispatch } = useGame();
  const [currentView, setCurrentView] = useState('main');
  const [selectedWOD, setSelectedWOD] = useState(null);

  const handleWODSelect = (wod) => {
    setSelectedWOD(wod);
    dispatch({ type: 'SET_WOD', payload: wod });
    setCurrentView('rhythm');
  };

  const handleWODComplete = (score) => {
    dispatch({ 
      type: 'COMPLETE_WOD', 
      payload: { 
        ...selectedWOD, 
        score,
        wodType: selectedWOD.type 
      } 
    });
    setCurrentView('main');
    setSelectedWOD(null);
  };

  const renderMainView = () => (
    <View style={styles.mainContainer}>
      <View style={styles.header}>
        <Text style={styles.title}>나대신 크로스핏</Text>
        <Text style={styles.daysRemaining}>
          {state.gamePhase === 'training' 
            ? `대회까지 ${state.daysRemaining}일` 
            : '대회 진행중!'
          }
        </Text>
      </View>
      
      <CharacterDisplay character={state.character} />
      
      <StatsPanel character={state.character} />
      
      {state.gamePhase === 'training' && (
        <TouchableOpacity 
          style={styles.wodButton}
          onPress={() => setCurrentView('wod')}
        >
          <Text style={styles.wodButtonText}>오늘의 WOD 선택</Text>
        </TouchableOpacity>
      )}
      
      {state.gamePhase === 'competition' && (
        <TouchableOpacity 
          style={styles.competitionButton}
          onPress={() => setCurrentView('competition')}
        >
          <Text style={styles.competitionButtonText}>대회 참가</Text>
        </TouchableOpacity>
      )}
    </View>
  );

  return (
    <View style={styles.container}>
      {currentView === 'main' && renderMainView()}
      {currentView === 'wod' && (
        <WODSelector 
          onSelect={handleWODSelect}
          onBack={() => setCurrentView('main')}
        />
      )}
      {currentView === 'rhythm' && selectedWOD && (
        <RhythmGame 
          wod={selectedWOD}
          onComplete={handleWODComplete}
          onBack={() => setCurrentView('main')}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#2c3e50',
  },
  mainContainer: {
    flex: 1,
    padding: 20,
    alignItems: 'center',
  },
  header: {
    alignItems: 'center',
    marginBottom: 20,
    marginTop: 40,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#ecf0f1',
    marginBottom: 10,
  },
  daysRemaining: {
    fontSize: 16,
    color: '#e74c3c',
    fontWeight: '600',
  },
  wodButton: {
    backgroundColor: '#e74c3c',
    paddingHorizontal: 30,
    paddingVertical: 15,
    borderRadius: 25,
    marginTop: 20,
  },
  wodButtonText: {
    color: 'white',
    fontSize: 18,
    fontWeight: 'bold',
  },
  competitionButton: {
    backgroundColor: '#f39c12',
    paddingHorizontal: 30,
    paddingVertical: 15,
    borderRadius: 25,
    marginTop: 20,
  },
  competitionButtonText: {
    color: 'white',
    fontSize: 18,
    fontWeight: 'bold',
  },
});