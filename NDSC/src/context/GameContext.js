import React, { createContext, useContext, useReducer, useEffect } from 'react';

const GameContext = createContext();

const initialState = {
  character: {
    level: 1,
    strength: 10,
    endurance: 10,
    agility: 10,
    bodyType: 'beginner', // beginner, intermediate, advanced, elite
    experience: 0,
    coins: 100
  },
  currentWOD: null,
  wodHistory: [],
  daysRemaining: 28, // 4주 = 28일
  gamePhase: 'training', // training, competition
  lastSaveTime: Date.now(),
  totalScore: 0
};

function gameReducer(state, action) {
  switch (action.type) {
    case 'COMPLETE_WOD':
      const expGain = action.payload.score * 10;
      const coinGain = Math.floor(action.payload.score / 10);
      
      // 능력치 증가 계산
      const strengthGain = action.payload.wodType === 'strength' ? 3 : 1;
      const enduranceGain = action.payload.wodType === 'cardio' ? 3 : 1;
      const agilityGain = action.payload.wodType === 'agility' ? 3 : 1;
      
      const newStrength = state.character.strength + strengthGain;
      const newEndurance = state.character.endurance + enduranceGain;
      const newAgility = state.character.agility + agilityGain;
      
      // 레벨업 체크
      const newExp = state.character.experience + expGain;
      const newLevel = Math.floor(newExp / 1000) + 1;
      
      // 체형 변화 체크 (새로운 능력치로 계산)
      const totalStats = newStrength + newEndurance + newAgility;
      let newBodyType = 'beginner';
      
      if (totalStats >= 200) newBodyType = 'elite';
      else if (totalStats >= 150) newBodyType = 'advanced';
      else if (totalStats >= 100) newBodyType = 'intermediate';
      else newBodyType = 'beginner';
      
      return {
        ...state,
        character: {
          ...state.character,
          level: newLevel,
          experience: newExp,
          coins: state.character.coins + coinGain,
          strength: newStrength,
          endurance: newEndurance,
          agility: newAgility,
          bodyType: newBodyType
        },
        wodHistory: [...state.wodHistory, {
          ...action.payload,
          timestamp: Date.now()
        }],
        totalScore: state.totalScore + action.payload.score,
        lastSaveTime: Date.now()
      };
    
    case 'ADVANCE_DAY':
      const newDaysRemaining = Math.max(0, state.daysRemaining - 1);
      return {
        ...state,
        daysRemaining: newDaysRemaining,
        gamePhase: newDaysRemaining <= 0 ? 'competition' : 'training',
        lastSaveTime: Date.now()
      };
    
    case 'SET_WOD':
      return {
        ...state,
        currentWOD: action.payload
      };
    
    case 'LOAD_GAME':
      return {
        ...state,
        ...action.payload
      };
    
    case 'RESET_GAME':
      return {
        ...initialState,
        lastSaveTime: Date.now()
      };
    
    default:
      return state;
  }
}

export function GameProvider({ children }) {
  const [state, dispatch] = useReducer(gameReducer, initialState);

  // 게임 저장 (localStorage 사용)
  useEffect(() => {
    const saveGame = () => {
      try {
        localStorage.setItem('crossfitGame', JSON.stringify(state));
      } catch (error) {
        console.error('게임 저장 실패:', error);
      }
    };
    
    saveGame();
  }, [state]);

  // 게임 로드
  useEffect(() => {
    const loadGame = () => {
      try {
        const savedGame = localStorage.getItem('crossfitGame');
        if (savedGame) {
          const gameData = JSON.parse(savedGame);
          dispatch({ type: 'LOAD_GAME', payload: gameData });
        }
      } catch (error) {
        console.error('게임 로드 실패:', error);
      }
    };
    
    loadGame();
  }, []);

  // 자동 진행 (방치형 요소) - 30초마다 하루 진행
  useEffect(() => {
    if (state.gamePhase === 'training' && state.daysRemaining > 0) {
      const autoProgress = setInterval(() => {
        dispatch({ type: 'ADVANCE_DAY' });
      }, 30000); // 30초마다 하루 진행

      return () => clearInterval(autoProgress);
    }
  }, [state.gamePhase, state.daysRemaining]);

  return (
    <GameContext.Provider value={{ state, dispatch }}>
      {children}
    </GameContext.Provider>
  );
}

export const useGame = () => {
  const context = useContext(GameContext);
  if (!context) {
    throw new Error('useGame은 GameProvider 내에서 사용해야 합니다');
  }
  return context;
};