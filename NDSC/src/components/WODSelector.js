import React from 'react';
import './WODSelector.css';

const WODS = [
  {
    id: 1,
    name: 'Fran',
    type: 'strength',
    description: '21-15-9 스쿼트 + 푸시업',
    difficulty: 'intermediate',
    duration: 60,
    emoji: '💪'
  },
  {
    id: 2,
    name: 'Cindy',
    type: 'cardio',
    description: '5분간 버피 + 점프',
    difficulty: 'beginner',
    duration: 45,
    emoji: '🏃'
  },
  {
    id: 3,
    name: 'Grace',
    type: 'agility',
    description: '30회 클린 앤 저크',
    difficulty: 'advanced',
    duration: 90,
    emoji: '⚡'
  },
  {
    id: 4,
    name: 'Helen',
    type: 'cardio',
    description: '3라운드 런 + 케틀벨',
    difficulty: 'intermediate',
    duration: 75,
    emoji: '🔥'
  },
  {
    id: 5,
    name: 'Murph',
    type: 'strength',
    description: '1마일 런 + 체조',
    difficulty: 'elite',
    duration: 120,
    emoji: '🏆'
  },
  {
    id: 6,
    name: 'Annie',
    type: 'agility',
    description: '50-40-30-20-10 더블언더',
    difficulty: 'advanced',
    duration: 80,
    emoji: '🤸'
  }
];

export default function WODSelector({ onSelect, onBack }) {
  const getDifficultyColor = (difficulty) => {
    switch (difficulty) {
      case 'beginner': return '#2ecc71';
      case 'intermediate': return '#f39c12';
      case 'advanced': return '#e74c3c';
      case 'elite': return '#9b59b6';
      default: return '#95a5a6';
    }
  };

  const getTypeColor = (type) => {
    switch (type) {
      case 'strength': return '#e74c3c';
      case 'cardio': return '#2ecc71';
      case 'agility': return '#f39c12';
      default: return '#3498db';
    }
  };

  return (
    <div className="wod-selector fade-in">
      <div className="wod-header">
        <button className="btn btn-secondary back-button" onClick={onBack}>
          ← 뒤로가기
        </button>
        <h2 className="wod-title">🏋️ 오늘의 WOD 선택</h2>
      </div>

      <div className="wod-grid">
        {WODS.map((wod, index) => (
          <div
            key={wod.id}
            className="wod-card slide-in"
            style={{ animationDelay: `${index * 0.1}s` }}
            onClick={() => onSelect(wod)}
          >
            <div className="wod-card-header">
              <div className="wod-emoji">{wod.emoji}</div>
              <div className="wod-info">
                <h3 className="wod-name">{wod.name}</h3>
                <p className="wod-description">{wod.description}</p>
              </div>
              <div className="wod-duration">{wod.duration}초</div>
            </div>
            
            <div className="wod-card-footer">
              <span 
                className="difficulty-badge" 
                style={{ backgroundColor: getDifficultyColor(wod.difficulty) }}
              >
                {wod.difficulty.toUpperCase()}
              </span>
              <span 
                className="type-badge" 
                style={{ backgroundColor: getTypeColor(wod.type) }}
              >
                {wod.type.toUpperCase()}
              </span>
            </div>
            
            <div className="wod-hover-effect">
              <span>클릭하여 시작!</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}