document.addEventListener('DOMContentLoaded', () => {
    // HTML 요소 가져오기
    const setupScreen = document.getElementById('setup-screen');
    const raceScreen = document.getElementById('race-screen');
    const participantsInput = document.getElementById('participants-input');
    const prepareButton = document.getElementById('prepare-button');
    const tournamentNameInput = document.getElementById('tournament-name');
    const racetrack = document.getElementById('racetrack');
    const startButton = document.getElementById('start-button');
    const backToSetupButton = document.getElementById('back-to-setup-button');
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

    let allParticipants = [];
    let currentRoundParticipants = [];
    let racersData = [];
    let winners = [];
    let raceInterval;
    let totalDistance = 2000;
    let pixelsPerMeter = 0;
    let racePixelDistance = 0;
    let raceFinished = false;
    let isRankingVisible = false;
    
    // 토너먼트 시스템 관련 변수
    let tournamentMode = false;
    let currentRound = 1;
    let totalRounds = 1;
    let roundResults = [];
    let advancedParticipants = [];
    
    // 라운드 정보 표시 요소 추가
    let roundInfoElement;

    // 🎵 사운드 시스템 추가
    let audioContext;
    let raceBackgroundSound;
    let isAudioEnabled = false;

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

    // 🎵 사운드 초기화
    function initAudio() {
        try {
            audioContext = new (window.AudioContext || window.webkitAudioContext)();
            isAudioEnabled = true;
            console.log('오디오 시스템 초기화 완료');
        } catch (error) {
            console.warn('오디오 지원하지 않음:', error);
            isAudioEnabled = false;
        }
    }

    // 🎵 말발굽 소리 생성 (반복적인 클립클롭 소리)
    function createHorseGallopSound() {
        if (!isAudioEnabled || !audioContext) return null;

        const gainNode = audioContext.createGain();
        gainNode.gain.value = 0.3;
        
        let isRunning = true; // 소리가 계속 재생되어야 하는지 확인
        let intervalId; // setInterval ID 저장
        
        function playClop() {
            if (!isRunning) return; // 경주가 끝나면 중지
            
            const currentTime = audioContext.currentTime;
            
            // 높은 톤 (앞발)
            const osc1 = audioContext.createOscillator();
            const gain1 = audioContext.createGain();
            osc1.frequency.setValueAtTime(800, currentTime);
            osc1.frequency.exponentialRampToValueAtTime(200, currentTime + 0.1);
            gain1.gain.setValueAtTime(0, currentTime);
            gain1.gain.linearRampToValueAtTime(0.15, currentTime + 0.01);
            gain1.gain.exponentialRampToValueAtTime(0.001, currentTime + 0.1);
            
            osc1.connect(gain1);
            gain1.connect(gainNode);
            osc1.start(currentTime);
            osc1.stop(currentTime + 0.1);
            
            // 낮은 톤 (뒷발) - 약간 지연
            setTimeout(() => {
                if (!isRunning) return;
                const currentTime2 = audioContext.currentTime;
                const osc2 = audioContext.createOscillator();
                const gain2 = audioContext.createGain();
                osc2.frequency.setValueAtTime(600, currentTime2);
                osc2.frequency.exponentialRampToValueAtTime(150, currentTime2 + 0.1);
                gain2.gain.setValueAtTime(0, currentTime2);
                gain2.gain.linearRampToValueAtTime(0.15, currentTime2 + 0.01);
                gain2.gain.exponentialRampToValueAtTime(0.001, currentTime2 + 0.1);
                
                osc2.connect(gain2);
                gain2.connect(gainNode);
                osc2.start(currentTime2);
                osc2.stop(currentTime2 + 0.1);
            }, 100);
        }
        
        // 0.25초마다 말발굽 소리 재생
        intervalId = setInterval(playClop, 250);
        
        // 소리 중지 함수를 gainNode에 추가
        gainNode.stopGallop = function() {
            isRunning = false;
            if (intervalId) {
                clearInterval(intervalId);
                intervalId = null;
            }
        };
        
        gainNode.connect(audioContext.destination);
        return gainNode;
    }

    // 🎵 부스터 효과음
    function playBoostSound() {
        if (!isAudioEnabled || !audioContext) return;

        const osc = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        
        osc.frequency.setValueAtTime(220, audioContext.currentTime);
        osc.frequency.exponentialRampToValueAtTime(880, audioContext.currentTime + 0.2);
        osc.frequency.exponentialRampToValueAtTime(440, audioContext.currentTime + 0.5);
        
        gainNode.gain.setValueAtTime(0, audioContext.currentTime);
        gainNode.gain.linearRampToValueAtTime(0.1, audioContext.currentTime + 0.1);
        gainNode.gain.exponentialRampToValueAtTime(0.001, audioContext.currentTime + 0.5);
        
        osc.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        osc.start(audioContext.currentTime);
        osc.stop(audioContext.currentTime + 0.5);
    }

    // 🎵 우승 팡파레
    function playVictoryFanfare() {
        if (!isAudioEnabled || !audioContext) return;

        const notes = [523.25, 659.25, 783.99, 1046.50]; // C5, E5, G5, C6
        let delay = 0;
        
        notes.forEach((freq, i) => {
            setTimeout(() => {
                const osc = audioContext.createOscillator();
                const gainNode = audioContext.createGain();
                
                osc.frequency.setValueAtTime(freq, audioContext.currentTime);
                gainNode.gain.setValueAtTime(0, audioContext.currentTime);
                gainNode.gain.linearRampToValueAtTime(0.2, audioContext.currentTime + 0.1);
                gainNode.gain.exponentialRampToValueAtTime(0.001, audioContext.currentTime + 0.8);
                
                osc.connect(gainNode);
                gainNode.connect(audioContext.destination);
                
                osc.start(audioContext.currentTime);
                osc.stop(audioContext.currentTime + 0.8);
            }, delay);
            delay += 200;
        });
    }

    // 🎵 카운트다운 효과음
    function playCountdownBeep(isStart = false) {
        if (!isAudioEnabled || !audioContext) return;

        const osc = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        
        osc.frequency.setValueAtTime(isStart ? 880 : 440, audioContext.currentTime);
        gainNode.gain.setValueAtTime(0, audioContext.currentTime);
        gainNode.gain.linearRampToValueAtTime(0.15, audioContext.currentTime + 0.1);
        gainNode.gain.exponentialRampToValueAtTime(0.001, audioContext.currentTime + 0.3);
        
        osc.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        osc.start(audioContext.currentTime);
        osc.stop(audioContext.currentTime + 0.3);
    }

    // 모바일 터치 이벤트 처리
    function addTouchSupport() {
        document.addEventListener('touchstart', function(e) {
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
        if (names.length > 30) {
            alert('참가자는 최대 30명까지 가능합니다.');
            return;
        }
        
        allParticipants = names;
        
        // 대회 이름 업데이트
        const tournamentName = tournamentNameInput.value.trim() || '다그닥 다그닥 그랑프리';
        document.querySelector('h1').innerHTML = `달려라 달려!<br>${tournamentName} 🐎`;
        
        // 🎵 오디오 초기화 (사용자 상호작용 후)
        if (!isAudioEnabled) {
            initAudio();
        }
        
        setupTournament();
        setupScreen.style.display = 'none';
        raceScreen.style.display = 'flex';
        startButton.classList.remove('hidden');
        backToSetupButton.classList.remove('hidden');
        
        // 모바일에서는 기본적으로 순위를 숨김
        liveRanking.classList.add('ranking-hidden');
        isRankingVisible = false;
        toggleRankingButton.textContent = '순위 보기';
    });

    function setupTournament() {
        // 초기화
        currentRound = 1;
        roundResults = [];
        advancedParticipants = [];
        
        // 토너먼트 모드 설정
        if (allParticipants.length <= 10) {
            tournamentMode = false;
            totalRounds = 1;
            currentRoundParticipants = [...allParticipants];
        } else {
            tournamentMode = true;
            // 라운드 수 계산
            if (allParticipants.length <= 20) {
                totalRounds = 3; // 예선 2라운드 + 결승
            } else {
                totalRounds = 4; // 예선 3라운드 + 결승
            }
            setupRounds();
        }
        
        // 라운드 정보 표시 요소 생성
        createRoundInfoDisplay();
        updateRoundInfo();
        setupCurrentRound();
    }

    function createRoundInfoDisplay() {
        // 기존 라운드 정보 제거
        const existingRoundInfo = document.getElementById('round-info');
        if (existingRoundInfo) {
            existingRoundInfo.remove();
        }
        
        // 새 라운드 정보 요소 생성
        roundInfoElement = document.createElement('div');
        roundInfoElement.id = 'round-info';
        roundInfoElement.style.cssText = `
            background: linear-gradient(135deg, #28a745, #20c997);
            color: white;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 10px;
            text-align: center;
            font-weight: bold;
            font-size: 0.9em;
            line-height: 1.3;
        `;
        
        // 해설 박스 다음에 삽입
        const commentaryBox = document.getElementById('race-commentary');
        commentaryBox.parentNode.insertBefore(roundInfoElement, commentaryBox.nextSibling);
    }

    function updateRoundInfo() {
        if (!roundInfoElement) return;
        
        if (!tournamentMode) {
            roundInfoElement.textContent = `전체 ${allParticipants.length}명 단일 경주`;
        } else {
            if (currentRound < totalRounds) {
                roundInfoElement.textContent = `예선 ${currentRound}라운드 (${currentRoundParticipants.length}명)\n상위 3명 결승 진출`;
            } else {
                roundInfoElement.textContent = `🏆 결승전 (${currentRoundParticipants.length}명)\n최종 순위 결정`;
            }
        }
    }

    function setupRounds() {
        // 참가자를 라운드별로 분배
        const shuffled = [...allParticipants].sort(() => Math.random() - 0.5);
        
        if (allParticipants.length <= 20) {
            // 2개 예선으로 분배
            const mid = Math.ceil(shuffled.length / 2);
            roundResults.push({ participants: shuffled.slice(0, mid), winners: [] });
            roundResults.push({ participants: shuffled.slice(mid), winners: [] });
        } else {
            // 3개 예선으로 분배
            const third = Math.ceil(shuffled.length / 3);
            roundResults.push({ participants: shuffled.slice(0, third), winners: [] });
            roundResults.push({ participants: shuffled.slice(third, third * 2), winners: [] });
            roundResults.push({ participants: shuffled.slice(third * 2), winners: [] });
        }
        
        // 결승전 슬롯 추가
        roundResults.push({ participants: [], winners: [] });
    }

    function setupCurrentRound() {
        if (!tournamentMode) {
            // 단일 경주
            currentRoundParticipants = [...allParticipants];
        } else if (currentRound < totalRounds && roundResults.length > 0) {
            // 예선 라운드 - roundResults 배열이 존재하는지 확인
            if (roundResults[currentRound - 1] && roundResults[currentRound - 1].participants) {
                currentRoundParticipants = roundResults[currentRound - 1].participants;
            } else {
                console.error('라운드 데이터가 없습니다:', currentRound, roundResults);
                currentRoundParticipants = [...allParticipants];
            }
        } else {
            // 결승전
            currentRoundParticipants = [...advancedParticipants];
        }
        
        setupRacersAndRanking();
        updateRoundInfo();
    }

    function setupRacersAndRanking() {
        racetrack.innerHTML = '<div class="finish-line"></div>';
        rankingList.innerHTML = '';
        
        // 모바일에서는 고정 높이 사용 - 최대 10명까지만 표시 가능하도록 제한
        const trackHeight = Math.max(300, Math.min(currentRoundParticipants.length * 30 + 20, 350));
        racetrack.style.height = `${trackHeight}px`;

        const finishLine = racetrack.querySelector('.finish-line');
        finishLine.style.height = `${trackHeight}px`;

        racersData = [];
        currentRoundParticipants.forEach((name, index) => {
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

        const roundText = tournamentMode ? 
            (currentRound < totalRounds ? `예선 ${currentRound}라운드` : '결승전') : '경주';
        
        // 🎵 카운트다운 효과음과 함께 시작
        commentaryText.textContent = "3...";
        playCountdownBeep();
        
        setTimeout(() => {
            commentaryText.textContent = "2...";
            playCountdownBeep();
        }, 1000);
        
        setTimeout(() => {
            commentaryText.textContent = "1...";
            playCountdownBeep();
        }, 2000);
        
        setTimeout(() => {
            commentaryText.textContent = `${roundText} 출발! 2000m 대장정이 시작됩니다!`;
            playCountdownBeep(true); // 시작 신호
            
            // 🎵 말발굽 소리 시작
            if (isAudioEnabled && audioContext) {
                raceBackgroundSound = createHorseGallopSound();
            }
            
            distanceRemaining.textContent = "남은 거리: 2000m";

            const racetrackRect = racetrack.getBoundingClientRect();
            // 모바일에 맞게 조정된 거리 계산
            racePixelDistance = racetrackRect.width - 80 - 15; // 시작점 80px, 결승선 15px
            pixelsPerMeter = racePixelDistance / totalDistance;

            raceInterval = setInterval(updateRaceState, 100);
        }, 3000);
    });

    function updateRaceState() {
        racersData.forEach(racer => {
            if (racer.finished) return;

            // 모바일에서는 약간 더 빠른 속도
            let move = Math.random() * 6;
            if (Math.random() < 0.015 && !racer.element.classList.contains('boost')) {
                racer.element.classList.add('boost');
                move *= 3;
                
                // 🎵 부스터 효과음 재생
                playBoostSound();
                
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
                if (winners.length >= 3 || winners.length === currentRoundParticipants.length) {
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
        
        // 🎵 말발굽 소리 중지
        if (raceBackgroundSound) {
            if (raceBackgroundSound.stopGallop) {
                raceBackgroundSound.stopGallop();
            }
            raceBackgroundSound.disconnect();
            raceBackgroundSound = null;
        }
        
        // 라운드 결과 저장
        if (tournamentMode && currentRound < totalRounds) {
            // 예선 라운드 완료
            roundResults[currentRound - 1].winners = finalWinners.slice(0, 3); // 상위 3명만
            advancedParticipants.push(...finalWinners.slice(0, 3));
            
            commentaryText.textContent = `예선 ${currentRound}라운드 종료! ${finalWinners.slice(0, 3).join(', ')}이(가) 결승 진출!`;
            
            // 다음 라운드 버튼 표시
            showNextRoundButton();
        } else {
            // 최종 결승 또는 단일 경주 완료
            const winnerText = tournamentMode ? '최종 우승' : '우승';
            commentaryText.textContent = `경주 종료! ${finalWinners[0]}이(가) ${winnerText}했습니다! 🏆`;
            
            // 🎵 우승 팡파레 재생
            playVictoryFanfare();
            
            // 모바일에서는 confetti 효과를 약간 줄임
            confetti({ 
                particleCount: 100, 
                spread: 80, 
                origin: { y: 0.6 },
                colors: ['#ffd700', '#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#ffeaa7']
            });
            
            showFinalResults(finalWinners);
        }
        
        distanceRemaining.textContent = "경주 완료!";
    }

    function showNextRoundButton() {
        // 기존 다음 라운드 버튼 제거
        const existingNextButton = document.getElementById('next-round-button');
        if (existingNextButton) {
            existingNextButton.remove();
        }
        
        const nextButton = document.createElement('button');
        nextButton.id = 'next-round-button';
        nextButton.textContent = currentRound < totalRounds - 1 ? 
            `예선 ${currentRound + 1}라운드 시작` : '결승전 시작';
        nextButton.style.cssText = `
            background-color: #fd7e14;
            color: white;
            border: none;
            padding: 12px 20px;
            font-size: 14px;
            font-weight: bold;
            border-radius: 8px;
            cursor: pointer;
            margin-top: 10px;
            width: 100%;
            max-width: 300px;
        `;
        
        nextButton.addEventListener('click', () => {
            currentRound++;
            setupCurrentRound();
            startButton.disabled = false;
            startButton.classList.remove('hidden');
            nextButton.remove();
        });
        
        const buttonContainer = startButton.parentNode;
        buttonContainer.insertBefore(nextButton, startButton.nextSibling);
    }

    function showFinalResults(finalWinners) {
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
        backToSetupButton.classList.add('hidden');
        startButton.disabled = false;
        setupScreen.style.display = 'block';
        
        // 대회 이름 초기화
        document.querySelector('h1').innerHTML = '달려라 달려!<br>다그닥 다그닥 그랑프리 🐎';
        
        // 다음 라운드 버튼 제거
        const nextButton = document.getElementById('next-round-button');
        if (nextButton) {
            nextButton.remove();
        }
        
        // 라운드 정보 제거
        if (roundInfoElement) {
            roundInfoElement.remove();
            roundInfoElement = null;
        }
        
        commentaryText.textContent = "경주 준비 중...";
        distanceRemaining.textContent = "남은 거리: 2000m";
        
        // 🎵 사운드 정리
        if (raceBackgroundSound) {
            if (raceBackgroundSound.stopGallop) {
                raceBackgroundSound.stopGallop();
            }
            raceBackgroundSound.disconnect();
            raceBackgroundSound = null;
        }
        
        // 모든 부스터 텍스트 제거
        if (racetrack) {
            const allBoostTexts = racetrack.querySelectorAll('.boost-text');
            allBoostTexts.forEach(text => text.remove());
        }
        
        // 토너먼트 상태 초기화
        tournamentMode = false;
        currentRound = 1;
        totalRounds = 1;
        roundResults = [];
        advancedParticipants = [];
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

    // 설정으로 돌아가기 버튼 이벤트
    backToSetupButton.addEventListener('click', () => {
        // 경주가 진행 중이면 중지
        if (raceInterval) {
            clearInterval(raceInterval);
            raceInterval = null;
        }
        
        // 🎵 사운드 정리
        if (raceBackgroundSound) {
            if (raceBackgroundSound.stopGallop) {
                raceBackgroundSound.stopGallop();
            }
            raceBackgroundSound.disconnect();
            raceBackgroundSound = null;
        }
        
        // 기존 부스터 텍스트들 모두 제거
        if (racetrack) {
            const allBoostTexts = racetrack.querySelectorAll('.boost-text');
            allBoostTexts.forEach(text => text.remove());
        }
        
        // 다음 라운드 버튼 제거
        const nextButton = document.getElementById('next-round-button');
        if (nextButton) {
            nextButton.remove();
        }
        
        raceScreen.style.display = 'none';
        startButton.classList.add('hidden');
        backToSetupButton.classList.add('hidden');
        startButton.disabled = false;
        setupScreen.style.display = 'block';
        
        // 대회 이름 초기화
        document.querySelector('h1').innerHTML = '달려라 달려!<br>다그닥 다그닥 그랑프리 🐎';
        
        // 순위 표시 초기화
        liveRanking.classList.add('ranking-hidden');
        isRankingVisible = false;
        toggleRankingButton.textContent = '순위 보기';
    });

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