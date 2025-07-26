import React from 'react';

// SVG로 그린 캐릭터 컴포넌트
export default function SVGCharacter({ character, size = 120, animated = false }) {
  const getBodyColor = (bodyType) => {
    switch (bodyType) {
      case 'beginner': return '#95a5a6';
      case 'intermediate': return '#3498db';
      case 'advanced': return '#e67e22';
      case 'elite': return '#f1c40f';
      default: return '#95a5a6';
    }
  };

  const getMuscleSize = (bodyType) => {
    switch (bodyType) {
      case 'beginner': return 1;
      case 'intermediate': return 1.1;
      case 'advanced': return 1.2;
      case 'elite': return 1.3;
      default: return 1;
    }
  };

  const bodyColor = getBodyColor(character.bodyType);
  const muscleScale = getMuscleSize(character.bodyType);

  return (
    <div className={`svg-character ${animated ? 'animated' : ''}`}>
      <svg width={size} height={size * 1.2} viewBox="0 0 100 120">
        {/* 그림자 */}
        <ellipse cx="50" cy="115" rx="20" ry="3" fill="rgba(0,0,0,0.2)" />
        
        {/* 머리 */}
        <circle 
          cx="50" 
          cy="15" 
          r="12" 
          fill="#fdbcb4" 
          stroke="#d4a574" 
          strokeWidth="1"
        />
        
        {/* 얼굴 */}
        <circle cx="46" cy="12" r="1.5" fill="#333" /> {/* 왼쪽 눈 */}
        <circle cx="54" cy="12" r="1.5" fill="#333" /> {/* 오른쪽 눈 */}
        <path d="M 47 18 Q 50 20 53 18" stroke="#333" strokeWidth="1" fill="none" /> {/* 입 */}
        
        {/* 몸통 */}
        <rect 
          x={50 - (15 * muscleScale)} 
          y="30" 
          width={30 * muscleScale} 
          height={35 * muscleScale} 
          rx="5" 
          fill={bodyColor}
          stroke="#2c3e50" 
          strokeWidth="1"
        />
        
        {/* 왼쪽 팔 */}
        <rect 
          x={35 - (5 * muscleScale)} 
          y="35" 
          width={8 * muscleScale} 
          height={25 * muscleScale} 
          rx="4" 
          fill={bodyColor}
          stroke="#2c3e50" 
          strokeWidth="1"
        />
        
        {/* 오른쪽 팔 */}
        <rect 
          x={65 - (3 * muscleScale)} 
          y="35" 
          width={8 * muscleScale} 
          height={25 * muscleScale} 
          rx="4" 
          fill={bodyColor}
          stroke="#2c3e50" 
          strokeWidth="1"
        />
        
        {/* 왼쪽 다리 */}
        <rect 
          x="42" 
          y="70" 
          width="6" 
          height="35" 
          rx="3" 
          fill="#34495e"
          stroke="#2c3e50" 
          strokeWidth="1"
        />
        
        {/* 오른쪽 다리 */}
        <rect 
          x="52" 
          y="70" 
          width="6" 
          height="35" 
          rx="3" 
          fill="#34495e"
          stroke="#2c3e50" 
          strokeWidth="1"
        />
        
        {/* 엘리트 레벨 특수 효과 */}
        {character.bodyType === 'elite' && (
          <>
            <circle cx="50" cy="60" r="25" fill="none" stroke="#f1c40f" strokeWidth="2" opacity="0.3">
              <animate attributeName="r" values="25;30;25" dur="2s" repeatCount="indefinite" />
              <animate attributeName="opacity" values="0.3;0.1;0.3" dur="2s" repeatCount="indefinite" />
            </circle>
            <text x="50" y="110" textAnchor="middle" fill="#f1c40f" fontSize="8" fontWeight="bold">
              ⭐ ELITE ⭐
            </text>
          </>
        )}
        
        {/* 레벨 표시 */}
        <text x="50" y="5" textAnchor="middle" fill="#f1c40f" fontSize="10" fontWeight="bold">
          Lv.{character.level}
        </text>
      </svg>
    </div>
  );
}