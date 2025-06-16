document.addEventListener('DOMContentLoaded', () => {
    // HTML 요소 가져오기
    const setupScreen = document.getElementById('setup-screen');
    const raceScreen = document.getElementById('race-screen');
    const participantsInput = document.getElementById('participants-input');
    const prepareButton = document.getElementById('prepare-button');
    const racetrack = document.getElementById('racetrack');
    const startButton = document.getElementById('start-button');
    const winnerAnnouncer = document.getElementById('winner-announcer');
    const resetButton = document.getElementById('reset-button');
    const rankingList = document.getElementById('ranking-list');
    const liveRanking = document.getElementById('live-ranking');
    const toggleRankingButton = document.getElementById('toggle-ranking');
    const podiumStands = {
        1: document.querySelector('.podium-stand.first'),
        2: document.querySelector('.podium-stand.second'),
        3: document.querySelector('.podium-stand.third')
    };
    const winnerNames = {
        1: document.getElementById('winner-1'),
        2: document.getElementById('winner-2'),
        3: document.getElementById('winner-3')
    };
    const commentaryText = document.getElementById('commentary-text');
    const distanceRemaining = document.getElementById('distance-remaining');

    let participants = [];
    let racersData = [];
    let winners = [];
    let raceInterval;
    let totalDistance = 2000;
    let pixelsPerMeter = 0;
    let racePixelDistance = 0;
    let raceFinished = false;
    let isRankingVisible = false;

    // 부스터 텍스트 배열
    const boostTexts = [
        "이랏!",
        "질주한다!",
        "나먼저 간다~!",
        "젖먹던힘까지!",
        "번개같이!",
        "바람처럼!",
        "화이팅!",
        "따라잡아라!",
        "전속력!",
        "돌진!",
        "스피드업!",
        "가속!"
    ];

    // 모바일 터치 이벤트 처리
    function addTouchSupport() {
        // 터치 이벤트를 클릭 이벤트로 변환
        document.addEventListener('touchstart', function(e) {
            // 기본 터치 동작 방지 (더블 탭 줌 등)
            if (e.target.tagName === 'BUTTON' || e.target.tagName === 'TEXTAREA') {
                e.preventDefault();
            }
        });
    }

    // 순위 토글 기능
    toggleRankingButton.addEventListener('click', () => {
        isRankingVisible = !isRankingVisible;
        if (isRankingVisible) {
            liveRanking.classList.remove('ranking-hidden');
            toggleRankingButton.textContent = '순위 숨기기';
        } else {
            liveRanking.classList.add('ranking-hidden');
            toggleRankingButton.textContent = '순위 보기';
        }
    });

    prepareButton.addEventListener('click', () => {
        const names = participantsInput.value.split('\n').filter(name => name.trim() !== '');
        if (names.length < 1) {
            alert('최소 1명 이상의 참가자를 입력해주세요.');
            return;
        }
        participants = names;
        setupRacersAndRanking();
        setupScreen.style.display = 'none';
        raceScreen.style.display = 'flex';
        startButton.classList.remove('hidden');
        
        // 모바일에서는 기본적으로 순위를 숨김
        liveRanking.classList.add('ranking-hidden');
        isRankingVisible = false;
        toggleRankingButton.textContent = '순위 보기';
    });

    function setupRacersAndRanking() {
        racetrack.innerHTML = '<div class="finish-line"></div>';
        rankingList.innerHTML = '';
        
        // 모바일에서는 고정 높이 사용
        const trackHeight = Math.max(300, Math.min(participants.length * 30 + 20, 400));
        racetrack.style.height = `${trackHeight}px`;

        const finishLine = racetrack.querySelector('.finish-line');
        finishLine.style.height = `${trackHeight}px`;

        racersData = [];
        participants.forEach((name, index) => {
            const racerElement = document.createElement('div');
            racerElement.className = 'racer';
            racerElement.textContent = name;
            racerElement.style.top = `${index * 30 + 10}px`;
            racetrack.appendChild(racerElement);

            racersData.push({
                name: name,
                element: racerElement,
                position: 0,
                finished: false
            });

            const rankItem = document.createElement('li');
            rankItem.className = 'rank-item';
            rankItem.dataset.name = name;
            rankItem.innerHTML = `<span class="rank-num">${index + 1}</span> ${name}`;
            rankingList.appendChild(rankItem);
        });
    }

    startButton.addEventListener('click', () => {
        startButton.disabled = true;
        winners = [];
        raceFinished = false;
        
        // 기존 부스터 텍스트들 모두 제거
        const existingBoostTexts = racetrack.querySelectorAll('.boost-text');
        existingBoostTexts.forEach(text => text.remove());
        
        racersData.forEach(racer => {
            racer.position = 0;
            racer.finished = false;
            racer.element.style.transform = `translateX(0px)`;
            racer.element.className = 'racer';
        });

        commentaryText.textContent = "출발! 2000m 대장정이 시작됩니다!";
        distanceRemaining.textContent = "남은 거리: 2000m";

        setTimeout(() => {
            const racetrackRect = racetrack.getBoundingClientRect();
            // 모바일에 맞게 조정된 거리 계산
            racePixelDistance = racetrackRect.width - 80 - 15; // 시작점 80px, 결승선 15px
            pixelsPerMeter = racePixelDistance / totalDistance;

            raceInterval = setInterval(updateRaceState, 100);
        }, 10);
    });

    function updateRaceState() {
        racersData.forEach(racer => {
            if (racer.finished) return;

            // 모바일에서는 약간 더 빠른 속도
            let move = Math.random() * 6;
            if (Math.random() < 0.015 && !racer.element.classList.contains('boost')) {
                racer.element.classList.add('boost');
                move *= 3;
                
                // 랜덤 부스터 텍스트 표시
                const randomText = boostTexts[Math.floor(Math.random() * boostTexts.length)];
                const boostTextElement = document.createElement('div');
                boostTextElement.className = 'boost-text';
                boostTextElement.textContent = randomText;
                
                // 말의 실제 위치 계산
                const racerRect = racer.element.getBoundingClientRect();
                const racetrackRect = racetrack.getBoundingClientRect();
                
                const racerCenterX = racerRect.left - racetrackRect.left + racerRect.width / 2;
                const racerTopY = racerRect.top - racetrackRect.top;
                
                // 모바일에서는 더 보수적으로 텍스트 위치 설정
                const racerIndex = racersData.findIndex(r => r.name === racer.name);
                const isTopRacer = racerIndex <= 1; // 상위 2명은 아래쪽에 표시
                
                boostTextElement.style.position = 'absolute';
                boostTextElement.style.left = `${racerCenterX}px`;
                boostTextElement.style.top = `${racerTopY + (isTopRacer ? 35 : -25)}px`;
                boostTextElement.style.transform = 'translateX(-50%)';
                boostTextElement.style.zIndex = '1000';
                
                racetrack.appendChild(boostTextElement);
                
                setTimeout(() => {
                    racer.element.classList.remove('boost');
                    if (boostTextElement && boostTextElement.parentNode) {
                        boostTextElement.parentNode.removeChild(boostTextElement);
                    }
                }, 1000);
            }
            racer.position += move;

            racer.element.style.transform = `translateX(${racer.position}px)`;

            if (racer.position >= racePixelDistance) {
                racer.finished = true;
                winners.push(racer.name);
                racer.element.classList.add(`finished-${winners.length}`);
                if (winners.length >= 3 || winners.length === participants.length) {
                    raceFinished = true;
                    endRace(winners);
                }
            }
        });

        racersData.sort((a, b) => b.position - a.position);

        // 순위 업데이트
        if (!raceFinished) {
            racersData.forEach((racer, index) => {
                const rankItem = rankingList.querySelector(`li[data-name="${racer.name}"]`);
                if (rankItem) {
                    rankItem.innerHTML = `<span class="rank-num">${index + 1}</span> ${racer.name}`;
                }

                racer.element.classList.remove('rank-1', 'rank-2', 'rank-3');
                if (!racer.finished) {
                    if (index === 0) racer.element.classList.add('rank-1');
                    else if (index === 1) racer.element.classList.add('rank-2');
                    else if (index === 2) racer.element.classList.add('rank-3');
                }
            });
        } else {
            // 경기 종료 후 최종 순위 표시
            const finalRanking = [];
            winners.forEach((name, index) => {
                const racer = racersData.find(r => r.name === name);
                if (racer) finalRanking.push({ ...racer, finalRank: index + 1 });
            });
            const unfinishedRacers = racersData.filter(r => !r.finished)
                .sort((a, b) => b.position - a.position);
            unfinishedRacers.forEach((racer, index) => {
                finalRanking.push({ ...racer, finalRank: winners.length + index + 1 });
            });
            
            finalRanking.forEach((racer) => {
                const rankItem = rankingList.querySelector(`li[data-name="${racer.name}"]`);
                if (rankItem) {
                    const rankText = racer.finished ? `${racer.finalRank}등 (완주)` : `${racer.finalRank}등`;
                    rankItem.innerHTML = `<span class="rank-num">${racer.finalRank}</span> ${racer.name}`;
                }
            });
        }

        const leadRacer = racersData[0];
        if (leadRacer && !leadRacer.finished) {
            const distanceCovered = leadRacer.position / pixelsPerMeter;
            const remainingDistance = Math.max(0, totalDistance - distanceCovered);
            distanceRemaining.textContent = `남은 거리: ${Math.round(remainingDistance)}m`;
            updateCommentary(remainingDistance, leadRacer.name);
        } else if (leadRacer && leadRacer.finished) {
            distanceRemaining.textContent = "경주 완료!";
        }
    }

    function updateCommentary(remainingDistance, leaderName) {
        let commentary = "";
        
        if (remainingDistance > 1800) commentary = "출발! 모든 선수들이 힘차게 달리기 시작합니다!";
        else if (remainingDistance > 1500) commentary = `초반 선두는 ${leaderName}! 아직 갈 길이 멉니다!`;
        else if (remainingDistance > 1200) commentary = `500m 지점! ${leaderName}이(가) 앞서나가고 있습니다!`;
        else if (remainingDistance > 1000) commentary = `800m 지점! 본격적인 레이스가 시작됩니다!`;
        else if (remainingDistance > 800) commentary = `반환점! ${leaderName}이(가) 선두를 유지합니다!`;
        else if (remainingDistance > 600) commentary = `1200m 지점! 순위 경쟁이 치열합니다!`;
        else if (remainingDistance > 400) commentary = `1400m 통과! ${leaderName}이(가) 선두!`;
        else if (remainingDistance > 200) commentary = `직선 주로! 마지막 스퍼트!`;
        else if (remainingDistance > 100) commentary = `200m 남았습니다! 숨막히는 접전!`;
        else if (remainingDistance > 50) commentary = `마지막 100m! 누가 우승할까요?!`;
        else commentary = `결승선이 눈앞! 최후의 승부!`;
        
        if (racersData.length > 1) {
            const leadPosition = racersData[0].position;
            const secondPosition = racersData[1].position;
            const gapPixels = leadPosition - secondPosition;
            if (gapPixels < 25 && remainingDistance < 1000) {
                commentary += ` ${racersData[1].name}이(가) 맹추격 중!`;
            }
        }
        
        commentaryText.textContent = commentary;
    }
    
    function endRace(finalWinners) {
        clearInterval(raceInterval);
        commentaryText.textContent = `경주 종료! ${finalWinners[0]}이(가) 우승했습니다! 🏆`;
        distanceRemaining.textContent = "경주 완료!";
        
        // 모바일에서는 confetti 효과를 약간 줄임
        confetti({ 
            particleCount: 100, 
            spread: 80, 
            origin: { y: 0.6 },
            colors: ['#ffd700', '#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#ffeaa7']
        });
        
        Object.values(podiumStands).forEach(stand => stand.classList.add('hidden'));
        if (finalWinners[0]) {
            winnerNames[1].textContent = finalWinners[0];
            podiumStands[1].classList.remove('hidden');
        }
        if (finalWinners[1]) {
            winnerNames[2].textContent = finalWinners[1];
            podiumStands[2].classList.remove('hidden');
        }
        if (finalWinners[2]) {
            winnerNames[3].textContent = finalWinners[2];
            podiumStands[3].classList.remove('hidden');
        }
        winnerAnnouncer.classList.remove('hidden');
    }

    function resetGame() {
        winnerAnnouncer.classList.add('hidden');
        raceScreen.style.display = 'none';
        startButton.classList.add('hidden');
        startButton.disabled = false;
        setupScreen.style.display = 'block';
        
        commentaryText.textContent = "경주 준비 중...";
        distanceRemaining.textContent = "남은 거리: 2000m";
        
        // 모든 부스터 텍스트 제거
        if (racetrack) {
            const allBoostTexts = racetrack.querySelectorAll('.boost-text');
            allBoostTexts.forEach(text => text.remove());
        }
        
        winners = [];
        raceFinished = false;
        if (raceInterval) {
            clearInterval(raceInterval);
            raceInterval = null;
        }
        
        // 순위 표시 초기화
        liveRanking.classList.add('ranking-hidden');
        isRankingVisible = false;
        toggleRankingButton.textContent = '순위 보기';
    }

    resetButton.addEventListener('click', resetGame);

    // 페이지 로드 시 터치 지원 초기화
    addTouchSupport();

    // 화면 크기 변경 시 대응
    window.addEventListener('resize', () => {
        if (raceInterval && racePixelDistance > 0) {
            // 화면 크기가 변경되면 거리 재계산
            setTimeout(() => {
                const racetrackRect = racetrack.getBoundingClientRect();
                racePixelDistance = racetrackRect.width - 80 - 15;
                pixelsPerMeter = racePixelDistance / totalDistance;
            }, 100);
        }
    });

    // 모바일 환경 감지 및 안내
    function isMobileDevice() {
        return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    }

    // 모바일 환경에서 추가 최적화
    if (isMobileDevice()) {
        // 모바일에서 더 큰 터치 영역 제공
        document.body.style.fontSize = '16px';
        
        // 스크롤 바운스 효과 방지
        document.body.style.overscrollBehavior = 'none';
        
        // 선택 방지
        document.body.style.userSelect = 'none';
        document.body.style.webkitUserSelect = 'none';
    }
}); 