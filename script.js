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

    let participants = [];
    let winners = [];
    let raceInterval;

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
        setTimeout(() => {
            const racetrackRect = racetrack.getBoundingClientRect();
            const finishLineCoord = racetrackRect.right - 30;
            raceInterval = setInterval(() => {
                updateRaceState(finishLineCoord);
            }, 100);
        }, 10);
    });
    
    // updateRaceState 함수 (이전과 동일)
    function updateRaceState(finishLineCoord) {
        const racers = Array.from(document.querySelectorAll('.racer'));
        racers.forEach(racer => {
            if (racer.dataset.finished) return;
            let move = Math.random() * 10;
            if (Math.random() < 0.005 && !racer.classList.contains('boost')) {
                racer.classList.add('boost');
                move *= 3;
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
    
    // endRace 함수 (이전과 동일)
    function endRace(finalWinners) {
        clearInterval(raceInterval);
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
    }
    // 'resetButton' 변수(버튼 요소)에 'resetGame' 함수를 클릭 이벤트로 연결
    resetButton.addEventListener('click', resetGame);
    // --- 여기까지 수정 ---
});
