document.addEventListener('DOMContentLoaded', () => {
    // HTML 요소 가져오기
    const setupScreen = document.getElementById('setup-screen');
    const raceScreen = document.getElementById('race-screen');
    const participantsInput = document.getElementById('participants-input');
    const prepareButton = document.getElementById('prepare-button');
    const racetrack = document.getElementById('racetrack');
    const startButton = document.getElementById('start-button');
    const winnerAnnouncer = document.getElementById('winner-announcer');
    const winnerName = document.getElementById('winner-name');
    const resetButton = document.getElementById('reset-button');

    let participants = [];
    let raceInterval;

    // "경주 준비" 버튼 클릭 이벤트
    prepareButton.addEventListener('click', () => {
        // 입력된 텍스트를 줄바꿈 기준으로 나누어 배열로 만듦
        const names = participantsInput.value.split('\n').filter(name => name.trim() !== '');
        
        if (names.length < 2) {
            alert('최소 2명 이상의 참가자를 입력해주세요.');
            return;
        }

        participants = names;
        setupRacers();

        // 화면 전환
        setupScreen.classList.add('hidden');
        raceScreen.classList.remove('hidden');
    });

    // 경주마(참가자)들을 트랙에 배치하는 함수
    function setupRacers() {
        racetrack.innerHTML = '<div class="finish-line"></div>'; // 기존 경주마 초기화 및 결승선 다시 그리기
        
        // 트랙 높이 조절
        const trackHeight = participants.length * 40 + 20; // 참가자 수에 따라 높이 조절
        racetrack.style.height = `${trackHeight}px`;

        participants.forEach((name, index) => {
            const racer = document.createElement('div');
            racer.className = 'racer';
            racer.textContent = name;
            racer.style.top = `${index * 40 + 10}px`; // 경주마들의 세로 위치 지정
            racer.dataset.name = name; // 데이터 속성에 이름 저장
            racetrack.appendChild(racer);
        });
    }

    // "경주 시작!" 버튼 클릭 이벤트
    startButton.addEventListener('click', () => {
        startButton.disabled = true; // 버튼 비활성화
        let winner = null;

        raceInterval = setInterval(() => {
            const racers = document.querySelectorAll('.racer');
            const trackWidth = racetrack.clientWidth;
            const finishLine = trackWidth - 80; // 결승선 위치 (너비, 패딩 등 고려)

            racers.forEach(racer => {
                // 현재 이동 거리를 가져와서 랜덤 값을 더함
                const currentTransform = new DOMMatrix(getComputedStyle(racer).transform).m41;
                const randomMove = Math.random() * 10; // 한번에 이동하는 거리 (조절 가능)
                const newPosition = currentTransform + randomMove;
                
                racer.style.transform = `translateX(${newPosition}px)`;

                // 결승선 통과 체크
                if (!winner && newPosition >= finishLine) {
                    winner = racer.dataset.name;
                    endRace(winner);
                }
            });
        }, 100); // 0.1초마다 경주마 이동
    });

    // 경주 종료 및 우승자 발표 함수
    function endRace(winner) {
        clearInterval(raceInterval); // 경주 중단
        winnerName.textContent = `${winner} 님`;
        winnerAnnouncer.classList.remove('hidden');
    }

    // "다시하기" 버튼 클릭 이벤트
    resetButton.addEventListener('click', () => {
        // 모든 상태 초기화 및 설정 화면으로 전환
        winnerAnnouncer.classList.add('hidden');
        raceScreen.classList.add('hidden');
        setupScreen.classList.remove('hidden');
        startButton.disabled = false;
        participantsInput.value = ''; // 입력창 초기화
    });
});
