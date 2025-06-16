document.addEventListener('DOMContentLoaded', () => {
    // HTML 요소 가져오기 (이전과 동일 + 추가)
    const setupScreen = document.getElementById('setup-screen');
    const raceScreen = document.getElementById('race-screen');
    const liveRanking = document.getElementById('live-ranking');
    const rankingList = document.getElementById('ranking-list');
    const participantsInput = document.getElementById('participants-input');
    const prepareButton = document.getElementById('prepare-button');
    const racetrack = document.getElementById('racetrack');
    const startButton = document.getElementById('start-button');
    const winnerAnnouncer = document.getElementById('winner-announcer');
    const resetButton = document.getElementById('reset-button');
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

    let participants = [];
    let winners = [];
    let raceInterval;

    // "경주 준비" 버튼 클릭 이벤트
    prepareButton.addEventListener('click', () => {
        const names = participantsInput.value.split('\n').filter(name => name.trim() !== '');
        if (names.length < 1) {
            alert('최소 1명 이상의 참가자를 입력해주세요.');
            return;
        }
        participants = names;
        setupRacersAndRanking();
        setupScreen.classList.add('hidden');
        raceScreen.style.display = 'flex';
        liveRanking.classList.remove('hidden');
        startButton.classList.remove('hidden');
    });

    // 경주마와 실시간 순위 창을 함께 설정
    function setupRacersAndRanking() {
        racetrack.innerHTML = '<div class="finish-line"></div>';
        rankingList.innerHTML = '';
        const trackHeight = participants.length * 40 + 20;
        racetrack.style.height = `${trackHeight}px`;

        participants.forEach((name, index) => {
            // 경주마 생성
            const racer = document.createElement('div');
            racer.className = 'racer';
            racer.textContent = name;
            racer.style.top = `${index * 40 + 10}px`;
            racer.dataset.name = name;
            racetrack.appendChild(racer);

            // 실시간 순위 아이템 생성
            const rankItem = document.createElement('li');
            rankItem.className = 'rank-item';
            rankItem.dataset.name = name;
            rankItem.style.top = `${index * 40}px`;
            rankItem.innerHTML = `<span class="rank-num">${index + 1}</span> ${name}`;
            if(index >= 5) rankItem.classList.add('rank-hidden');
            rankingList.appendChild(rankItem);
        });
    }

    // "경주 시작!" 버튼 클릭 이벤트
    startButton.addEventListener('click', () => {
        startButton.disabled = true;
        winners = [];
        const racetrackRect = racetrack.getBoundingClientRect();
        const finishLineCoord = racetrackRect.right - 30;

        raceInterval = setInterval(() => {
            updateRaceState(finishLineCoord);
        }, 100);
    });

    // 레이스 상태를 업데이트하는 메인 함수
    function updateRaceState(finishLineCoord) {
        const racers = Array.from(document.querySelectorAll('.racer'));

        // 1. 말 이동 및 부스트 효과 적용
        racers.forEach(racer => {
            if (racer.dataset.finished) return;

            let move = Math.random() * 10;
            // 부스트 효과 적용
            if (Math.random() < 0.005 && !racer.classList.contains('boost')) {
                racer.classList.add('boost');
                move *= 3; // 부스트 시 더 많이 이동
                setTimeout(() => racer.classList.remove('boost'), 1000);
            }

            const currentTransform = new DOMMatrix(getComputedStyle(racer).transform).m41;
            racer.style.transform = `translateX(${currentTransform + move}px)`;
        });

        // 2. 실시간 순위 업데이트
        racers.sort((a, b) => b.getBoundingClientRect().right - a.getBoundingClientRect().right);

        racers.forEach((racer, index) => {
            const rankItem = rankingList.querySelector(`li[data-name="${racer.dataset.name}"]`);
            if (rankItem) {
                rankItem.style.top = `${index * 40}px`;
                rankItem.innerHTML = `<span class="rank-num">${index + 1}</span> ${racer.dataset.name}`;
                if (index < 5) rankItem.classList.remove('rank-hidden');
                else rankItem.classList.add('rank-hidden');
            }
        });

        // 3. 결승선 통과 체크 및 세리머니
        racers.forEach(racer => {
            if (!racer.dataset.finished && racer.getBoundingClientRect().right >= finishLineCoord) {
                racer.dataset.finished = 'true';
                winners.push(racer.dataset.name);
                racer.classList.add(`finished-${winners.length}`); // 등수별 세리머니 클래스 추가
                
                if (winners.length >= 3 || winners.length === participants.length) {
                    endRace(winners);
                }
            }
        });
    }
    
    // 경주 종료 및 시상대 표시 함수
    function endRace(finalWinners) {
        clearInterval(raceInterval);
        
        // 콘페티 효과!
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

    // "다시하기" 버튼 클릭 이벤트
    resetButton.addEventListener('click', () => {
        winnerAnnouncer.classList.add('hidden');
        raceScreen.style.display = 'none';
        liveRanking.classList.add('hidden');
        startButton.classList.add('hidden');
        startButton.disabled = false;
        setupScreen.classList.remove('hidden');
    });
});
