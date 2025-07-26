import React from 'react';
import CharacterSprite from './CharacterSprite';
import './CharacterDisplay.css';

export default function CharacterDisplay({ character }) {
  const getBodyTypeEmoji = (bodyType) => {
    switch (bodyType) {
      case 'beginner': return '🙂';
      case 'intermediate': return '💪';
      case 'advanced': return '🏋️';
      case 'elite': return '🏆';
      default: return '🙂';
    }
  };

  return (
    <div className="character-display card">
      <h3>캐릭터</h3>
      
      <div className="character-container">
        <div className="character-artwork">
          <CharacterSprite character={character} size="large" animated={true} />
        </div>
        
        <div className="character-info">
          <div className="body-type">
            {getBodyTypeEmoji(character.bodyType)} {character.bodyType.toUpperCase()}
          </div>
          
          <div className="character-stats">
            <div className="stat-item">
              <span className="stat-label">EXP:</span>
              <span className="stat-value exp">{character.experience}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">💰</span>
              <span className="stat-value coins">{character.coins}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}