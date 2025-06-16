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
        if (names.length < 1) { // 1명 이상이면 시작 가능하도록 변경
            alert('최소 1명 이상의 참가자를 입력해주세요.');
            return;
        }
        participants = names;
        setupRacers();
        setupScreen.classList.add('hidden');
        raceScreen.classList.remove('hidden');
    });

    // 경주마(참가자)들을 트랙에 배치
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

    // "경주 시작!" 버튼 클릭 이벤트
    startButton.addEventListener('click', () => {
        startButton.disabled = true;
        winners = []; // 우승자 배열 초기화

        raceInterval = setInterval(() => {
            const racers = document.querySelectorAll('.racer');
            const trackWidth = racetrack.clientWidth;
            const finishLine = trackWidth - 30; // 결승선 위치 (말 아이콘 너비 고려)

            racers.forEach(racer => {
                if (racer.dataset.finished) return; // 이미 들어온 말은 무시

                const currentTransform = new DOMMatrix(getComputedStyle(racer).transform).m41;
                const randomMove = Math.random() * 10;
                const newPosition = currentTransform + randomMove;
                
                racer.style.transform = `translateX(${newPosition}px)`;

                // 결승선 통과 체크 (오른쪽 끝 기준)
                if (newPosition + racer.clientWidth >= finishLine) {
                    racer.dataset.finished = 'true';
                    winners.push(racer.dataset.name);
                    
                    // 3등까지 들어오거나, 모든 참가자가 들어오면 경주 종료
                    if (winners.length >= 3 || winners.length === participants.length) {
                        endRace(winners);
                    }
                }
            });
        }, 100);
    });

    // 경주 종료 및 시상대 표시 함수
    function endRace(finalWinners) {
        clearInterval(raceInterval);
        
        // 시상대 초기화
        Object.values(podiumStands).forEach(stand => stand.classList.add('hidden'));

        // 1, 2, 3등 시상대 채우기
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
        raceScreen.classList.add('hidden');
        setupScreen.classList.remove('hidden');
        startButton.disabled = false;
        // 입력창을 비우지 않아 명단 수정 후 재시작 용이
        // participantsInput.value = ''; 
    });
});
