document.addEventListener('DOMContentLoaded', () => {
    // HTML 요소 가져오기 (이전과 동일)
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

        // --- 수정된 부분 1 ---
        // 화면 표시 방식을 classList.remove로 변경하여 !important 문제를 해결합니다.
        setupScreen.classList.add('hidden');
        raceScreen.classList.remove('hidden'); // raceScreen.style.display = 'flex' 대신 사용
        // liveRanking과 startButton을 제어하는 코드는 raceScreen 내부에 있으므로 이제 불필요
        // liveRanking.classList.remove('hidden'); -> 삭제
        startButton.classList.remove('hidden');
    });

    // 경주마와 실시간 순위 창을 함께 설정
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
        // getBoundingClientRect()를 setInterval 바깥으로 이동하여
        // 레이스가 시작된 후, 화면이 보이는 상태에서 단 한 번만 계산합니다.
        const racetrackRect = racetrack.getBoundingClientRect();
        const finishLineCoord = racetrackRect.right - 30;

        raceInterval = setInterval(() => {
            updateRaceState(finishLineCoord);
        }, 100);
    });
    
    // (이하 updateRaceState, endRace, resetButton 함수는 이전과 동일)
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
                rankItem.style.top = `${
