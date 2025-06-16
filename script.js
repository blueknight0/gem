document.addEventListener('DOMContentLoaded', () => {
    // HTML 요소 가져오기 (이전과 동일)
    const setupScreen = document.getElementById('setup-screen');
    const raceScreen = document.getElementById('race-screen');
    const participantsInput = document.getElementById('participants-input');
    const prepareButton = document.getElementById('prepare-button');
    const racetrack = document.getElementById('racetrack');
    const startButton = document.getElementById('start-button');
    const winnerAnnouncer = document.getElementById('winner-announcer');
    const resetButton = document.getElementById('reset-button');
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

    // "경주 준비" 버튼 클릭 이벤트
    prepareButton.addEventListener('click', () => {
        const names = participantsInput.value.split('\n').filter(name => name.trim() !== '');
        if (names.length < 1) {
            alert('최소 1명 이상의 참가자를 입력해주세요.');
            return;
        }
        participants = names;
        setupRacersAndRanking();

        // --- 수정된 부분 1 ---
        // CSS를 직접 제어하여 화면을 표시합니다.
        setupScreen.style.display = 'none';
        raceScreen.style.display = 'flex'; // flex로 설정하여 보이게 함
        startButton.classList.remove('hidden');
    });

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

    // "경주 시작!" 버튼 클릭 이벤트
    startButton.addEventListener('click', () => {
        startButton.disabled = true;
        winners = [];

        // --- 수정된 부분 2 ---
        // setTimeout으로 레이스 로직을 아주 잠깐 지연시켜 렌더링 문제를 해결합니다.
        setTimeout(() => {
            const racetrackRect = racetrack.getBoundingClientRect();
            const finishLineCoord = racetrackRect.right - 30;

            raceInterval = setInterval(() => {
                updateRaceState(finishLineCoord);
            }, 100);
        }, 10); // 0.01초의 찰나의 지연
    });
    
    // (이하 updateRaceState, endRace 함수는 이전과 동일)
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

    // 다시하기 버튼 로직 수정
    resetButton.addEventListener('click', () => {
        winnerAnnouncer.classList.add('hidden');
        raceScreen.style.display = 'none'; // flex 대신 none으로 설정하여 숨김
        startButton.classList.add('hidden');
        startButton.disabled = false;
        setupScreen.style.display = 'block'; // none 대신 block으로 설정하여 보이게 함
    });
});
