import React from 'react';
import GameScreen from './components/GameScreen';
import { GameProvider } from './context/GameContext';
import './App.css';

function App() {
  return (
    <GameProvider>
      <div className="App">
        <GameScreen />
      </div>
    </GameProvider>
  );
}

export default App;