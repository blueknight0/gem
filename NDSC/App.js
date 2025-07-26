import React, { useState, useEffect } from 'react';
import { View, StyleSheet } from 'react-native';
import GameScreen from './src/screens/GameScreen';
import { GameProvider } from './src/context/GameContext';

export default function App() {
  return (
    <GameProvider>
      <View style={styles.container}>
        <GameScreen />
      </View>
    </GameProvider>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#2c3e50',
  },
});