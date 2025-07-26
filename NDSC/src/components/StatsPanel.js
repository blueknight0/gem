import React from 'react';
import './StatsPanel.css';

export default function StatsPanel({ character }) {
  const renderStatBar = (label, value, maxValue = 100, color = '#3498db', icon = '') => {
    const percentage = Math.min((value / maxValue) * 100, 100);
    
    return (
      <div className="stat-row">
        <div className="stat-label">
          {icon} {label}
        </div>
        <div className="stat-bar-container">
          <div 
            className="stat-bar" 
            style={{ 
              width: `${percentage}%`,
              backgroundColor: color 
            }}
          />
          <div className="stat-value">{value}</div>
        </div>
      </div>
    );
  };

  const totalStats = character.strength + character.endurance + character.agility;

  return (
    <div className="stats-panel card">
      <h3>능력치</h3>
      
      <div className="stats-container">
        {renderStatBar('근력', character.strength, 100, '#e74c3c', '💪')}
        {renderStatBar('지구력', character.endurance, 100, '#2ecc71', '🏃')}
        {renderStatBar('민첩성', character.agility, 100, '#f39c12', '⚡')}
        
        <div className="total-stats">
          <div className="total-label">총합</div>
          <div className="total-value">{totalStats}</div>
        </div>
        
        <div className="progress-info">
          <div className="progress-item">
            <span>다음 체형까지:</span>
            <span className="progress-value">
              {character.bodyType === 'elite' ? 'MAX' : 
               character.bodyType === 'advanced' ? `${200 - totalStats}` :
               character.bodyType === 'intermediate' ? `${150 - totalStats}` :
               `${100 - totalStats}`}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}