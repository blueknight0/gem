import React from 'react';
import './CSSCharacter.css';

// CSS로 그린 상세한 픽셀 아트 캐릭터
export default function CSSCharacter({ character, animated = false }) {
  const getCharacterClass = (bodyType) => {
    return `css-character css-character-${bodyType} ${animated ? 'animated' : ''}`;
  };

  return (
    <div className={getCharacterClass(character.bodyType)}>
      {/* 머리 */}
      <div className="char-head">
        <div className="hair"></div>
        <div className="face">
          <div className="eye left-eye"></div>
          <div className="eye right-eye"></div>
          <div className="mouth"></div>
        </div>
      </div>
      
      {/* 몸통 */}
      <div className="char-body">
        <div className="chest"></div>
        <div className="abs"></div>
      </div>
      
      {/* 팔 */}
      <div className="char-arms">
        <div className="arm left-arm">
          <div className="bicep"></div>
          <div className="forearm"></div>
        </div>
        <div className="arm right-arm">
          <div className="bicep"></div>
          <div className="forearm"></div>
        </div>
      </div>
      
      {/* 다리 */}
      <div className="char-legs">
        <div className="leg left-leg">
          <div className="thigh"></div>
          <div className="calf"></div>
        </div>
        <div className="leg right-leg">
          <div className="thigh"></div>
          <div className="calf"></div>
        </div>
      </div>
      
      {/* 레벨 표시 */}
      <div className="char-level">Lv.{character.level}</div>
      
      {/* 체형 표시 */}
      <div className="char-type">{character.bodyType.toUpperCase()}</div>
    </div>
  );
}