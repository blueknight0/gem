document.addEventListener('DOMContentLoaded', () => {
    // HTML 요소 가져오기
    const setupScreen = document.getElementById('setup-screen');
    const raceScreen = document.getElementById('race-screen');
    const participantsInput = document.getElementById('participants-input');
    const prepareButton = document.getElementById('prepare-button');
    const racetrack = document.getElementById('racetrack');
    const startButton = document.getElementById('start-button');
    const winnerAnnouncer = document.getElementById('winner-announcer');
    const resetButton = document.getElementById('reset-button'); // 'resetButton' 변수 선언
    const rankingList = document.getElementById('ranking-list');
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
    let winners = [];
    let raceInterval;
    let totalDistance = 2000; // 총 경주 거리 (미터)
    let pixelsPerMeter = 0; // 픽셀당 미터 (경주 시작 시 계산)
    
    // 부스터 효과 텍스트 배열
    const boostTexts = [
        "간닷!", "이럇!!", "영혼의질주!", "젖먹던힘까지!", "으랴랴랴랴",
        "불타올라!", "질풍같이!", "번개처럼!", "폭풍질주!", "최고속도!",
        "가즈아!", "돌진!", "전력질주!", "미친속도!", "초고속!"
    ];

    // "경주 준비" 버튼 클릭 이벤트 (이전과 동일)
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
    });

    // 경주마와 실시간 순위 창을 함께 설정 (이전과 동일)
    function setupRacersAndRanking() {
        racetrack.innerHTML = '<div class="finish-line"></div>';
        rankingList.innerHTML = '';
        const trackHeight = participants.length * 40 + 20;
        racetrack.style.height = `${trackHeight}px`;
        
        // 결승선 높이를 트랙 높이에 맞게 설정
        const finishLine = racetrack.querySelector('.finish-line');
        finishLine.style.height = `${trackHeight}px`;
        
        participants.forEach((name, index) => {
            const racer = document.createElement('div');
            racer.className = 'racer';
            racer.textContent = name;
            racer.style.top = `${index * 40 + 10}px`;
            racer.dataset.name = name;
            racetrack.appendChild(racer);
            const rankItem = document.createElement('li');
            rankItem.className = 'rank-item';
            rankItem.dataset.name = name;
            rankItem.style.top = `${index * 40}px`;
            rankItem.innerHTML = `<span class="rank-num">${index + 1}</span> ${name}`;
            if(index >= 5) rankItem.classList.add('rank-hidden');
            rankingList.appendChild(rankItem);
        });
    }

    // "경주 시작!" 버튼 클릭 이벤트 (이전과 동일)
    startButton.addEventListener('click', () => {
        startButton.disabled = true;
        winners = [];
        commentaryText.textContent = "출발! 2000m 대장정이 시작됩니다!";
        distanceRemaining.textContent = "남은 거리: 2000m";
        
        setTimeout(() => {
            const racetrackRect = racetrack.getBoundingClientRect();
            const finishLineCoord = racetrackRect.right - 30;
            const startLineCoord = racetrackRect.left + 150;
            const totalPixels = finishLineCoord - startLineCoord;
            pixelsPerMeter = totalPixels / totalDistance;
            
            raceInterval = setInterval(() => {
                updateRaceState(finishLineCoord);
            }, 400); // 100ms에서 400ms로 증가 (이동 주기 증가)
        }, 10);
    });
    
    // 부스터 오버레이 텍스트 생성 함수
    function createBoostOverlay(racer) {
        const overlay = document.createElement('div');
        overlay.className = 'boost-overlay';
        const randomText = boostTexts[Math.floor(Math.random() * boostTexts.length)];
        overlay.textContent = randomText;
        racer.appendChild(overlay);
        
        console.log(`부스터 발동! ${racer.dataset.name}: ${randomText}`); // 디버깅용 로그
        
        // 1초 후 오버레이 제거
        setTimeout(() => {
            if (overlay.parentNode) {
                overlay.parentNode.removeChild(overlay);
            }
        }, 1000);
    }

    // updateRaceState 함수 (이전과 동일)
    function updateRaceState(finishLineCoord) {
        const racers = Array.from(document.querySelectorAll('.racer'));
        racers.forEach(racer => {
            if (racer.dataset.finished) return;
            let move = Math.random() * 20; // 기본 이동 거리를 10에서 20으로 증가
            if (Math.random() < 0.02 && !racer.classList.contains('boost')) { // 부스트 확률을 테스트용으로 0.02로 증가
                racer.classList.add('boost');
                move *= 3; // 부스트 시 3배 속도
                createBoostOverlay(racer); // 부스터 오버레이 텍스트 생성
                setTimeout(() => racer.classList.remove('boost'), 1000);
            }
            const currentTransform = new DOMMatrix(getComputedStyle(racer).transform).m41;
            racer.style.transform = `translateX(${currentTransform + move}px)`;
        });

        racers.sort((a, b) => b.getBoundingClientRect().right - a.getBoundingClientRect().right);

        racers.forEach(racer => {
            racer.classList.remove('rank-1', 'rank-2', 'rank-3');
        });
        if (racers[0] && !racers[0].dataset.finished) racers[0].classList.add('rank-1');
        if (racers[1] && !racers[1].dataset.finished) racers[1].classList.add('rank-2');
        if (racers[2] && !racers[2].dataset.finished) racers[2].classList.add('rank-3');

        racers.forEach((racer, index) => {
            const rankItem = rankingList.querySelector(`li[data-name="${racer.dataset.name}"]`);
            if (rankItem) {
                rankItem.style.top = `${index * 40}px`;
                rankItem.innerHTML = `<span class="rank-num">${index + 1}</span> ${racer.dataset.name}`;
                if (index < 5) rankItem.classList.remove('rank-hidden');
                else rankItem.classList.add('rank-hidden');
            }
        });

        // 선두 주자의 남은 거리 계산 및 중계
        if (racers[0] && !racers[0].dataset.finished) {
            const leadRacer = racers[0];
            const currentTransform = new DOMMatrix(getComputedStyle(leadRacer).transform).m41;
            const distanceCovered = currentTransform / pixelsPerMeter;
            const remainingDistance = Math.max(0, totalDistance - distanceCovered);
            
            distanceRemaining.textContent = `남은 거리: ${Math.round(remainingDistance)}m`;
            
            // 거리별 중계 멘트
            updateCommentary(remainingDistance, leadRacer.dataset.name, racers);
        }

        racers.forEach(racer => {
            if (!racer.dataset.finished && racer.getBoundingClientRect().right >= finishLineCoord) {
                racer.dataset.finished = 'true';
                winners.push(racer.dataset.name);
                racer.classList.add(`finished-${winners.length}`);
                if (winners.length >= 3 || winners.length === participants.length) {
                    endRace(winners);
                }
            }
        });
    }
    
    // 거리별 중계 멘트 함수
    function updateCommentary(remainingDistance, leaderName, racers) {
        let commentary = "";
        
        if (remainingDistance > 1800) {
            commentary = "출발선을 통과했습니다! 모든 선수들이 힘차게 달리기 시작합니다!";
        } else if (remainingDistance > 1500 && remainingDistance <= 1800) {
            commentary = `초반 선두는 ${leaderName}! 아직 갈 길이 멉니다!`;
        } else if (remainingDistance > 1200 && remainingDistance <= 1500) {
            commentary = `500m 지점 통과! ${leaderName}이(가) 앞서나가고 있습니다!`;
        } else if (remainingDistance > 1000 && remainingDistance <= 1200) {
            commentary = `800m 지점! 이제 본격적인 레이스가 시작됩니다!`;
        } else if (remainingDistance > 800 && remainingDistance <= 1000) {
            commentary = `반환점 통과! ${leaderName}이(가) 여전히 선두를 유지하고 있습니다!`;
        } else if (remainingDistance > 600 && remainingDistance <= 800) {
            commentary = `1200m 지점! 후반부로 접어들었습니다! 순위 경쟁이 치열합니다!`;
        } else if (remainingDistance > 400 && remainingDistance <= 600) {
            commentary = `1400m 통과! 이제 600m 남았습니다! ${leaderName}이(가) 선두!`;
        } else if (remainingDistance > 200 && remainingDistance <= 400) {
            commentary = `직선 주로 진입! 마지막 스퍼트가 시작됩니다!`;
        } else if (remainingDistance > 100 && remainingDistance <= 200) {
            commentary = `200m 남았습니다! 숨막히는 접전입니다!`;
        } else if (remainingDistance > 50 && remainingDistance <= 100) {
            commentary = `마지막 100m! 누가 우승할까요?!`;
        } else if (remainingDistance <= 50) {
            commentary = `결승선이 눈앞입니다! 최후의 승부!`;
        }
        
        // 2위와의 격차가 작을 때 추가 멘트
        if (racers.length > 1 && racers[0] && racers[1]) {
            const gap = racers[0].getBoundingClientRect().right - racers[1].getBoundingClientRect().right;
            if (gap < 30 && remainingDistance < 1000) {
                commentary += ` ${racers[1].dataset.name}이(가) 맹추격 중입니다!`;
            }
        }
        
        commentaryText.textContent = commentary;
    }
    
    // endRace 함수 (이전과 동일)
    function endRace(finalWinners) {
        clearInterval(raceInterval);
        commentaryText.textContent = `경주 종료! ${finalWinners[0]}이(가) 우승했습니다! 🏆`;
        distanceRemaining.textContent = "경주 완료!";
        confetti({ particleCount: 150, spread: 90, origin: { y: 0.6 } });
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

    // --- 수정된 부분 ---
    // 함수의 이름을 'resetButton'에서 'resetGame'으로 변경
    function resetGame() {
        winnerAnnouncer.classList.add('hidden');
        raceScreen.style.display = 'none';
        startButton.classList.add('hidden');
        startButton.disabled = false;
        setupScreen.style.display = 'block';
        
        // 중계 전광판 초기화
        commentaryText.textContent = "경주 준비 중...";
        distanceRemaining.textContent = "남은 거리: 2000m";
        
        // 경주 관련 변수들 초기화
        winners = [];
        if (raceInterval) {
            clearInterval(raceInterval);
            raceInterval = null;
        }
    }
    // 'resetButton' 변수(버튼 요소)에 'resetGame' 함수를 클릭 이벤트로 연결
    resetButton.addEventListener('click', resetGame);
    // --- 여기까지 수정 ---
});
