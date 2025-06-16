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
        setupRacers();
        setupScreen.classList.add('hidden');
        raceScreen.classList.remove('hidden');
    });

    // 경주마(참가자)들을 트랙에 배치 (이전과 동일)
    function setupRacers() {
        racetrack.innerHTML = '<div class="finish-line"></div>';
        const trackHeight = participants.length * 40 + 20;
        racetrack.style.height = `${trackHeight}px`;

        participants.forEach((name, index) => {
            const racer = document.createElement('div');
            racer.className = 'racer';
            racer.textContent = name;
            racer.style.top = `${index * 40 + 10}px`;
            racer.dataset.name = name;
            racetrack.appendChild(racer);
        });
    }

    // "경주 시작!" 버튼 클릭 이벤트 (결승선 통과 로직 수정)
    startButton.addEventListener('click', () => {
        startButton.disabled = true;
        winners = [];

        // getBoundingClientRect는 스크롤 위치에 따라 값이 변하므로, 시작 전에 고정된 값을 계산
        const racetrackRect = racetrack.getBoundingClientRect();
        const finishLineCoord = racetrackRect.right - 30; // 결승선 x좌표 (여유 공간 30px)

        raceInterval = setInterval(() => {
            const racers = document.querySelectorAll('.racer');

            racers.forEach(racer => {
                if (racer.dataset.finished) return;

                // getComputedStyle과 DOMMatrix를 사용하여 현재 transform 값을 정확히 읽어옴
                const currentTransform = new DOMMatrix(getComputedStyle(racer).transform).m41;
                const randomMove = Math.random() * 10;
                // 기존 transform 값에 새로운 이동거리를 더함
                const newTransform = currentTransform + randomMove;
                
                racer.style.transform = `translateX(${newTransform}px)`;

                // 결승선 통과 체크 로직 수정: 실제 렌더링된 박스의 오른쪽 끝 위치로 판단
                const racerRightEdge = racer.getBoundingClientRect().right;
                if (racerRightEdge >= finishLineCoord) {
                    racer.dataset.finished = 'true';
                    winners.push(racer.dataset.name);
                    
                    if (winners.length >= 3 || winners.length === participants.length) {
                        endRace(winners);
                    }
                }
            });
        }, 100);
    });

    // 경주 종료 및 시상대 표시 함수 (이전과 동일)
    function endRace(finalWinners) {
        clearInterval(raceInterval);
        
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

    // "다시하기" 버튼 클릭 이벤트 (이전과 동일)
    resetButton.addEventListener('click', () => {
        winnerAnnouncer.classList.add('hidden');
        raceScreen.classList.add('hidden');
        setupScreen.classList.remove('hidden');
        startButton.disabled = false;
    });
});
