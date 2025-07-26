import React, { useState, useEffect, useRef, useCallback } from 'react';
import './RhythmGame.css';

export default function RhythmGame({ wod, onComplete, onBack }) {
  const [gameState, setGameState] = useState('ready'); // ready, playing, finished
  const [score, setScore] = useState(0);
  const [combo, setCombo] = useState(0);
  const [maxCombo, setMaxCombo] = useState(0);
  const [timeLeft, setTimeLeft] = useState(wod.duration);
  const [notes, setNotes] = useState([]);
  const [nextNoteId, setNextNoteId] = useState(0);
  const [missedNotes, setMissedNotes] = useState(0);
  
  const gameLoopRef = useRef();
  const noteSpawnRef = useRef();
  const gameAreaRef = useRef();
  
  // 노트 생성
  const createNote = useCallback(() => {
    if (!gameAreaRef.current || gameState !== 'playing') return;
    
    const gameArea = gameAreaRef.current.getBoundingClientRect();
    const newNote = {
      id: nextNoteId,
      x: Math.random() * (gameArea.width - 80) + 40,
      y: -50,
      speed: 3 + Math.random() * 2, // 속도 조정
      type: Math.random() > 0.7 ? 'special' : 'normal', // 특수 노트 확률 증가
      hit: false
    };
    
    setNotes(prev => [...prev, newNote]);
    setNextNoteId(prev => prev + 1);
  }, [nextNoteId, gameState]);

  // 게임 시작
  const startGame = () => {
    setGameState('playing');
    setScore(0);
    setCombo(0);
    setMaxCombo(0);
    setTimeLeft(wod.duration);
    setNotes([]);
    setMissedNotes(0);
    setNextNoteId(0);
    
    // 노트 생성 간격 (난이도에 따라 조절)
    const spawnInterval = wod.difficulty === 'elite' ? 800 : 
                         wod.difficulty === 'advanced' ? 1000 : 
                         wod.difficulty === 'intermediate' ? 1200 : 1500;
    
    noteSpawnRef.current = setInterval(createNote, spawnInterval);
    
    // 타이머 (1초마다)
    const timerRef = setInterval(() => {
      setTimeLeft(prev => {
        if (prev <= 1) {
          endGame();
          clearInterval(timerRef);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    
    // 게임 루프 (노트 이동용, 60fps)
    gameLoopRef.current = setInterval(() => {
      // 노트 이동 및 놓친 노트 처리
      setNotes(prev => {
        let missedCount = 0;
        const updatedNotes = prev.map(note => ({
          ...note,
          y: note.y + note.speed
        })).filter(note => {
          if (note.y > window.innerHeight + 50 && !note.hit) {
            missedCount++;
            setCombo(0); // 놓치면 콤보 리셋
            return false;
          }
          return note.y < window.innerHeight + 100;
        });
        
        if (missedCount > 0) {
          setMissedNotes(m => m + missedCount);
        }
        
        return updatedNotes;
      });
    }, 16); // 60fps
  };

  // 게임 종료
  const endGame = useCallback(() => {
    setGameState('finished');
    if (gameLoopRef.current) clearInterval(gameLoopRef.current);
    if (noteSpawnRef.current) clearInterval(noteSpawnRef.current);
  }, []);

  // 노트 터치
  const hitNote = (noteId, event) => {
    if (event) event.stopPropagation();
    
    setNotes(prev => {
      const targetNote = prev.find(note => note.id === noteId);
      if (!targetNote || targetNote.hit) return prev;
      
      // 점수 계산
      const basePoints = targetNote.type === 'special' ? 50 : 20;
      const comboBonus = Math.floor(combo * 0.5);
      const totalPoints = basePoints + comboBonus;
      
      setScore(prevScore => prevScore + totalPoints);
      setCombo(prevCombo => {
        const newCombo = prevCombo + 1;
        setMaxCombo(max => Math.max(max, newCombo));
        return newCombo;
      });
      
      // 노트 제거
      return prev.filter(note => note.id !== noteId);
    });
  };

  // 컴포넌트 정리
  useEffect(() => {
    return () => {
      clearInterval(gameLoopRef.current);
      clearInterval(noteSpawnRef.current);
    };
  }, []);

  // 키보드 이벤트 (스페이스바로 노트 치기)
  useEffect(() => {
    const handleKeyPress = (event) => {
      if (event.code === 'Space' && gameState === 'playing') {
        event.preventDefault();
        // 히트존에 있는 가장 가까운 노트 치기
        const hitZoneY = window.innerHeight - 180; // 히트존 위치
        const hitableNotes = notes
          .filter(note => !note.hit && Math.abs(note.y - hitZoneY) < 80)
          .sort((a, b) => Math.abs(a.y - hitZoneY) - Math.abs(b.y - hitZoneY));
        
        if (hitableNotes.length > 0) {
          hitNote(hitableNotes[0].id);
        } else {
          // 빗나감 - 콤보 리셋
          setCombo(0);
        }
      }
    };

    if (gameState === 'playing') {
      window.addEventListener('keydown', handleKeyPress);
      return () => window.removeEventListener('keydown', handleKeyPress);
    }
  }, [notes, gameState]);

  const getScoreGrade = (score) => {
    if (score >= 2000) return { grade: 'S', color: '#f1c40f' };
    if (score >= 1500) return { grade: 'A', color: '#e67e22' };
    if (score >= 1000) return { grade: 'B', color: '#3498db' };
    if (score >= 500) return { grade: 'C', color: '#2ecc71' };
    return { grade: 'D', color: '#95a5a6' };
  };

  const renderReadyScreen = () => (
    <div className="rhythm-screen ready-screen">
      <div className="ready-content fade-in">
        <h2 className="wod-title">{wod.name}</h2>
        <div className="wod-emoji">{wod.emoji}</div>
        <p className="wod-description">{wod.description}</p>
        <div className="game-instructions">
          <p>🎯 떨어지는 노트를 클릭하거나 스페이스바를 누르세요!</p>
          <p>⭐ 황금 노트는 더 많은 점수를 줍니다</p>
          <p>🔥 콤보를 유지해서 보너스 점수를 받으세요</p>
        </div>
        <button className="btn btn-primary start-button bounce" onClick={startGame}>
          🚀 운동 시작!
        </button>
      </div>
    </div>
  );

  const renderGameScreen = () => (
    <div className="rhythm-screen game-screen">
      <div className="game-header">
        <div className="game-stats">
          <div className="stat-item">
            <span className="stat-label">⏰</span>
            <span className="stat-value">{timeLeft}초</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">점수</span>
            <span className="stat-value">{score}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">콤보</span>
            <span className="stat-value combo">{combo}</span>
          </div>
        </div>
        <button className="btn btn-secondary pause-button" onClick={endGame}>
          ⏸️ 일시정지
        </button>
      </div>
      
      <div className="game-area" ref={gameAreaRef}>
        {notes.map(note => (
          <div
            key={note.id}
            className={`note ${note.type} ${note.hit ? 'hit' : ''}`}
            style={{
              left: `${note.x}px`,
              top: `${note.y}px`,
            }}
            onClick={(e) => hitNote(note.id, e)}
          >
            <div className="note-content">
              {note.type === 'special' ? '⭐' : '💪'}
            </div>
          </div>
        ))}
        
        <div className="hit-zone">
          <div className="hit-zone-line"></div>
          <span className="hit-zone-text">HIT ZONE</span>
        </div>
      </div>
    </div>
  );

  const renderFinishedScreen = () => {
    const grade = getScoreGrade(score);
    const totalNotes = combo + maxCombo + missedNotes;
    const hitNotes = totalNotes - missedNotes;
    const accuracy = totalNotes > 0 ? Math.round((hitNotes / totalNotes) * 100) : 100;
    
    return (
      <div className="rhythm-screen finished-screen">
        <div className="finished-content fade-in">
          <h2 className="finished-title">🎉 운동 완료!</h2>
          
          <div className="score-display">
            <div className="final-score" style={{ color: grade.color }}>
              {score}
            </div>
            <div className="score-grade" style={{ color: grade.color }}>
              등급: {grade.grade}
            </div>
          </div>
          
          <div className="game-results">
            <div className="result-item">
              <span className="result-label">최대 콤보:</span>
              <span className="result-value">{maxCombo}</span>
            </div>
            <div className="result-item">
              <span className="result-label">정확도:</span>
              <span className="result-value">{accuracy}%</span>
            </div>
            <div className="result-item">
              <span className="result-label">놓친 노트:</span>
              <span className="result-value">{missedNotes}</span>
            </div>
          </div>
          
          <div className="result-buttons">
            <button 
              className="btn btn-success complete-button" 
              onClick={() => onComplete(score)}
            >
              ✅ 완료
            </button>
            <button className="btn btn-warning retry-button" onClick={startGame}>
              🔄 다시하기
            </button>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="rhythm-game">
      <button className="btn btn-secondary back-button" onClick={onBack}>
        ← 뒤로가기
      </button>
      
      {gameState === 'ready' && renderReadyScreen()}
      {gameState === 'playing' && renderGameScreen()}
      {gameState === 'finished' && renderFinishedScreen()}
    </div>
  );
}