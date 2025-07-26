import React, { useState } from 'react';
import { useGame } from '../context/GameContext';
import CharacterDisplay from './CharacterDisplay';
import WODSelector from './WODSelector';
import RhythmGame from './RhythmGame';
import StatsPanel from './StatsPanel';
import CompetitionScreen from './CompetitionScreen';
import './GameScreen.css';

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

  const handleResetGame = () => {
    if (window.confirm('게임을 초기화하시겠습니까? 모든 진행상황이 삭제됩니다.')) {
      dispatch({ type: 'RESET_GAME' });
    }
  };

  const renderMainView = () => (
    <div className="main-container fade-in">
      <header className="game-header">
        <h1 className="game-title">💪 나대신 크로스핏</h1>
        <div className="days-remaining">
          {state.gamePhase === 'training' 
            ? `🏆 대회까지 ${state.daysRemaining}일` 
            : '🎉 대회 진행중!'
          }
        </div>
      </header>
      
      <div className="game-content">
        <div className="left-panel">
          <CharacterDisplay character={state.character} />
          <StatsPanel character={state.character} />
        </div>
        
        <div className="right-panel">
          <div className="game-info card">
            <h3>게임 정보</h3>
            <p>총 점수: <span className="highlight">{state.totalScore}</span></p>
            <p>완료한 WOD: <span className="highlight">{state.wodHistory.length}</span></p>
            <p>현재 레벨: <span className="highlight">{state.character.level}</span></p>
            {state.gamePhase === 'training' && (
              <p className="auto-progress">
                ⏰ 자동 진행: 30초마다 하루씩
              </p>
            )}
          </div>
          
          {state.gamePhase === 'training' && (
            <button 
              className="btn btn-primary wod-button bounce"
              onClick={() => setCurrentView('wod')}
            >
              🏋️ 오늘의 WOD 선택
            </button>
          )}
          
          {state.gamePhase === 'competition' && (
            <button 
              className="btn btn-warning competition-button bounce"
              onClick={() => setCurrentView('competition')}
            >
              🏆 대회 참가하기
            </button>
          )}
          
          <button 
            className="btn btn-secondary reset-button"
            onClick={handleResetGame}
          >
            🔄 게임 초기화
          </button>
        </div>
      </div>
    </div>
  );

  return (
    <div className="game-screen">
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
      {currentView === 'competition' && (
        <CompetitionScreen 
          character={state.character}
          onBack={() => setCurrentView('main')}
        />
      )}
    </div>
  );
}