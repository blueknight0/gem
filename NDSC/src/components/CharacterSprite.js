import React from 'react';
import './CharacterSprite.css';

// 캐릭터 스프라이트 컴포넌트
export default function CharacterSprite({ character, size = 'normal', animated = false }) {
  const getCharacterImage = (bodyType) => {
    // 실제 이미지 파일 경로
    const imagePaths = {
      beginner: '/images/characters/beginner.png',
      intermediate: '/images/characters/intermediate.png',
      advanced: '/images/characters/advanced.png',
      elite: '/images/characters/elite.png'
    };
    
    return imagePaths[bodyType] || imagePaths.beginner;
  };

  const getSizeClass = (size) => {
    switch (size) {
      case 'small': return 'character-sprite-small';
      case 'large': return 'character-sprite-large';
      default: return 'character-sprite-normal';
    }
  };

  const handleImageError = (e) => {
    console.log(`이미지 로드 실패: ${e.target.src}`);
    e.target.style.display = 'none';
    e.target.nextSibling.style.display = 'block';
  };

  return (
    <div className={`character-sprite ${getSizeClass(size)} ${animated ? 'animated' : ''}`}>
      <img 
        src={getCharacterImage(character.bodyType)}
        alt={`${character.bodyType} character`}
        className="character-image"
        onError={handleImageError}
        onLoad={() => console.log(`이미지 로드 성공: ${getCharacterImage(character.bodyType)}`)}
      />
      
      {/* 폴백 픽셀 캐릭터 */}
      <div className="pixel-character-fallback" style={{ display: 'none' }}>
        <div className="pixel-head" style={{ backgroundColor: '#fdbcb4' }} />
        <div className="pixel-torso" style={{ backgroundColor: getBodyTypeColor(character.bodyType) }} />
        <div className="pixel-left-arm" style={{ backgroundColor: getBodyTypeColor(character.bodyType) }} />
        <div className="pixel-right-arm" style={{ backgroundColor: getBodyTypeColor(character.bodyType) }} />
        <div className="pixel-left-leg" style={{ backgroundColor: '#34495e' }} />
        <div className="pixel-right-leg" style={{ backgroundColor: '#34495e' }} />
      </div>
      
      <div className="character-level">Lv.{character.level}</div>
    </div>
  );
}

// 체형별 색상 (폴백용)
function getBodyTypeColor(bodyType) {
  switch (bodyType) {
    case 'beginner': return '#95a5a6';
    case 'intermediate': return '#3498db';
    case 'advanced': return '#e67e22';
    case 'elite': return '#f1c40f';
    default: return '#95a5a6';
  }
}