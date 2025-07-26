import React, { useState, useEffect } from 'react';
import './CompetitionScreen.css';

export default function CompetitionScreen({ character, onBack }) {
  const [competitionState, setCompetitionState] = useState('intro'); // intro, competing, results
  const [competitors, setCompetitors] = useState([]);
  const [playerRank, setPlayerRank] = useState(0);
  const [prize, setPrize] = useState('');

  useEffect(() => {
    // AI 경쟁자들 생성
    const generateCompetitors = () => {
      const names = ['김철수', '이영희', '박민수', '최지은', '정태호', '한소영', '윤대성', '임수진'];
      const totalStats = character.strength + character.endurance + character.agility;
      
      const aiCompetitors = names.map((name, index) => ({
        id: index + 1,
        name,
        totalStats: Math.max(50, totalStats + (Math.random() - 0.5) * 40),
        bodyType: totalStats >= 180 ? 'elite' : 
                 totalStats >= 140 ? 'advanced' : 
                 totalStats >= 100 ? 'intermediate' : 'beginner'
      }));

      // 플레이어 추가
      const allCompetitors = [
        ...aiCompetitors,
        {
          id: 0,
          name: '나',
          totalStats,
          bodyType: character.bodyType,
          isPlayer: true
        }
      ];

      // 총 능력치로 정렬
      const sortedCompetitors = allCompetitors.sort((a, b) => b.totalStats - a.totalStats);
      
      setCompetitors(sortedCompetitors);
      
      // 플레이어 순위 찾기
      const playerIndex = sortedCompetitors.findIndex(comp => comp.isPlayer);
      setPlayerRank(playerIndex + 1);
      
      // 상금/상품 결정
      if (playerIndex === 0) setPrize('🥇 금메달 + 1000코인');
      else if (playerIndex === 1) setPrize('🥈 은메달 + 500코인');
      else if (playerIndex === 2) setPrize('🥉 동메달 + 300코인');
      else if (playerIndex <= 5) setPrize('🏅 입상 + 100코인');
      else setPrize('🎖️ 참가상 + 50코인');
    };

    generateCompetitors();
  }, [character]);

  const startCompetition = () => {
    setCompetitionState('competing');
    
    // 3초 후 결과 표시
    setTimeout(() => {
      setCompetitionState('results');
    }, 3000);
  };

  const renderIntroScreen = () => (
    <div className="competition-intro fade-in">
      <h2 className="competition-title">🏆 크로스핏 대회</h2>
      <div className="competition-description">
        <p>4주간의 훈련이 끝났습니다!</p>
        <p>이제 다른 선수들과 경쟁할 시간입니다.</p>
        <p>당신의 총 능력치: <span className="highlight">{character.strength + character.endurance + character.agility}</span></p>
      </div>
      
      <div className="player-preview">
        <h3>참가자 정보</h3>
        <div className="player-card">
          <div className="player-name">나 (Lv.{character.level})</div>
          <div className="player-stats">
            <span>💪 {character.strength}</span>
            <span>🏃 {character.endurance}</span>
            <span>⚡ {character.agility}</span>
          </div>
          <div className="player-body-type">{character.bodyType.toUpperCase()}</div>
        </div>
      </div>
      
      <button className="btn btn-primary start-competition-button bounce" onClick={startCompetition}>
        🚀 대회 시작!
      </button>
    </div>
  );

  const renderCompetingScreen = () => (
    <div className="competition-competing fade-in">
      <h2 className="competing-title">🏃‍♂️ 경기 진행중...</h2>
      <div className="competing-animation">
        <div className="runner runner-1">🏃‍♂️</div>
        <div className="runner runner-2">🏃‍♀️</div>
        <div className="runner runner-3">🏃‍♂️</div>
      </div>
      <p className="competing-text">선수들이 최선을 다하고 있습니다!</p>
    </div>
  );

  const renderResultsScreen = () => (
    <div className="competition-results fade-in">
      <h2 className="results-title">🎉 대회 결과</h2>
      
      <div className="final-ranking">
        <h3>최종 순위</h3>
        <div className="ranking-list">
          {competitors.slice(0, 8).map((competitor, index) => (
            <div 
              key={competitor.id} 
              className={`ranking-item ${competitor.isPlayer ? 'player-rank' : ''}`}
            >
              <div className="rank-number">
                {index + 1}
                {index === 0 && '🥇'}
                {index === 1 && '🥈'}
                {index === 2 && '🥉'}
              </div>
              <div className="competitor-info">
                <div className="competitor-name">{competitor.name}</div>
                <div className="competitor-stats">총합: {Math.round(competitor.totalStats)}</div>
              </div>
              <div className="competitor-type">{competitor.bodyType}</div>
            </div>
          ))}
        </div>
      </div>
      
      <div className="player-result">
        <h3>당신의 결과</h3>
        <div className="result-card">
          <div className="result-rank">
            {playerRank}위 / {competitors.length}명
          </div>
          <div className="result-prize">{prize}</div>
        </div>
      </div>
      
      <div className="result-buttons">
        <button className="btn btn-success" onClick={onBack}>
          🏠 메인으로
        </button>
        <button className="btn btn-warning" onClick={() => setCompetitionState('intro')}>
          🔄 다시 도전
        </button>
      </div>
    </div>
  );

  return (
    <div className="competition-screen">
      <button className="btn btn-secondary back-button" onClick={onBack}>
        ← 뒤로가기
      </button>
      
      {competitionState === 'intro' && renderIntroScreen()}
      {competitionState === 'competing' && renderCompetingScreen()}
      {competitionState === 'results' && renderResultsScreen()}
    </div>
  );
}