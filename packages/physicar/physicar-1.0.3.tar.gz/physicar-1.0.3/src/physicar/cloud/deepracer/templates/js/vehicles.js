    // 캔버스에 사용할 이미지 경로 설정 (actionSpaceImage는 HTML에서 전역 변수로 정의됨)

    // 캔버스 및 관련 DOM 요소 초기화 (DOMContentLoaded 내부로 이동)
    let canvas, ctx, modeSelect, actionList, addActionBtn, discInputs, contInputs, bg;
    let minSpeedInput, maxSpeedInput, minAngleInput, maxAngleInput; // Continuous 모드 입력 요소
    let isLoadingActions = false;  // 설정 로딩 중 플래그

    // 이미지 기준 비율 계산 (원본 734x363 기준)
    const origWidth = 734, origHeight = 363;
    const centerRatio = { x: 367.5 / origWidth, y: 301 / origHeight };
    const radiusRatio = 280 / origHeight;

    document.addEventListener('DOMContentLoaded', () => {
        // DOM 요소 초기화
        canvas = document.getElementById('canvas');
        if (canvas) { // canvas 요소가 있는지 확인 후 context 가져오기
            ctx = canvas.getContext('2d');
        }
        modeSelect = document.getElementById('mode');
        actionList = document.getElementById('actionList');
        addActionBtn = document.getElementById('addAction');
        discInputs = document.querySelectorAll('.discrete-only');
        contInputs = document.querySelectorAll('.continuous-only');

        // Continuous 모드 입력 요소
        minSpeedInput = document.getElementById('minSpeed');
        maxSpeedInput = document.getElementById('maxSpeed');
        minAngleInput = document.getElementById('minAngle');
        maxAngleInput = document.getElementById('maxAngle');

        // 배경 이미지 로드 후 캔버스 설정 및 초기 그리기
        bg = new Image();
        // bg.src = typeof actionSpaceImage !== 'undefined' ? actionSpaceImage : '/static/img/action_space.png'; // HTML에서 actionSpaceImage를 받도록 수정
        if (typeof actionSpaceImage !== 'undefined') {
            bg.src = actionSpaceImage;
        } else {
            console.error('actionSpaceImage is not defined. Please define it in the HTML before loading this script.');
            // 대체 이미지 또는 오류 처리
            bg.src = '/static/img/action_space.png';
        }
        bg.onload = () => {
            if (canvas && bg.naturalWidth > 0 && bg.naturalHeight > 0) {
                canvas.width = bg.naturalWidth;
                canvas.height = bg.naturalHeight;
                // modeSelect가 없어도 Discrete 모드로 초기화
                initDiscreteMode();
            } else if (canvas) {
                console.error("Background image could not be loaded or has zero dimensions, or canvas is not ready.");
                canvas.width = origWidth; 
                canvas.height = origHeight;
                if (modeSelect) toggleMode(); else redraw();
            }
        };
        bg.onerror = () => {
            console.error("Error loading background image:", bg.src);
            if (canvas) {
                canvas.width = origWidth;
                canvas.height = origHeight;
                if (modeSelect) toggleMode(); else redraw();
            }
        };

        // 이벤트 리스너 등록
        if (modeSelect) {
            modeSelect.addEventListener('change', toggleMode);
        }
        if (addActionBtn) {
            addActionBtn.addEventListener('click', () => addAction());
            // 초기 버튼 상태 설정
            updateAddActionButtonState();
        }

        // continuous 모드 입력창에 redraw 바인딩
        [minSpeedInput, maxSpeedInput, minAngleInput, maxAngleInput].forEach(inp => {
            if (inp) inp.addEventListener('input', redraw);
        });

        // 초기화 코드가 모두 로드된 후, Discrete 모드라면 기본 액션 추가
        // toggleMode() 함수 내부에서 이미 처리하고 있으므로, 여기서는 중복 호출을 피합니다.
        // 만약 toggleMode()가 초기에 호출되지 않는 경우를 대비한다면 아래와 같이 추가할 수 있습니다.
        /*
        if (modeSelect && modeSelect.value === 'discrete') {
            if (!actionList || actionList.querySelectorAll('.action-row').length === 0) {
                const predefinedActions = [
                    { angle: -30, speed: 0.5 },
                    { angle: -15, speed: 1.0 },
                    { angle: 0, speed: 1.5 },
                    { angle: 15, speed: 1.0 },
                    { angle: 30, speed: 0.5 },
                ];
                predefinedActions.forEach(action => {
                    addAction(action.speed, action.angle);
                });
            }
        }
        */
    });

    /**
    * Discrete 모드 초기화 (modeSelect가 없을 때도 동작)
    */
    function initDiscreteMode() {
        // Discrete 영역 표시
        discInputs.forEach(el => el.style.display = 'flex');
        // Continuous 영역 숨김
        contInputs.forEach(el => el.classList.remove('show'));
        
        // 초기 액션은 settings-manager.js에서 로드된 설정으로 추가됨
        // 여기서는 기본값을 추가하지 않음 (중복 저장 방지)
        redraw();
    }

    /**
    * 모드 변경 처리 (Discrete <-> Continuous)
    */
    function toggleMode() {
        const isDiscrete = modeSelect && modeSelect.value === 'discrete';

        // Toggle sections
        // discInputs.forEach(el => el.style.display = isDiscrete ? 'flex' : 'none');
        // contInputs.forEach(el => el.style.display = isDiscrete ? 'none' : 'flex');

        /* Discrete 영역은 이전처럼 flex 토글 */
        discInputs.forEach(el => el.style.display = isDiscrete ? 'flex' : 'none');

        /* Continuous 영역은 show 클래스로만 토글 */
        contInputs.forEach(el => el.classList.toggle('show', !isDiscrete));

        // Clear actions if switching to continuous
        if (!isDiscrete) {
            actionList.innerHTML = '';
        } else {
            // discrete로 왔을 때 액션이 없다면 초기값 5개 추가
            if (actionList.querySelectorAll('.action-row').length === 0) {
            const predefinedActions = [
                { angle: -25, speed: 0.8 },
                { angle: -12, speed: 1.0 },
                { angle: 0, speed: 1.5 },
                { angle: 12, speed: 1.0 },
                { angle: 25, speed: 0.8 },
            ];
            predefinedActions.forEach(action => {
                addAction(action.speed, action.angle);
            });
            }
        }
        redraw();
    }

    /**
    * 액션 하나 추가 (Discrete 모드)
    */


    function addAction(speed = 2.5, angle = 0) {

        const currentCount = document.querySelectorAll('.action-row').length;
        if (currentCount >= 30) {
            updateAddActionButtonState();
            return;
        }

        /* ── 첫 액션일 때만 헤더(라벨) 생성 ─────────────────────── */
        if (currentCount === 0) {
            const header = document.createElement('div');
            header.className = 'row gx-1 mb-1 fw-bold';
            header.innerHTML = `
            <!-- 인덱스와 동일한 폭 확보 : 0 두 개를 invisible 로 -->
            <div class="idx-col col-auto text-end pe-4 invisible">00</div>

            <div class="col-6 col-md-4 text-start">Speed (m/s)
            
                <div class="mt-1">
                    <p class="text-muted fs-6">${window.translations?.vehicles?.speed_message || ''}</p>
                </div>
            </div>
            <div class="col-6 col-md-4 text-start" style = "white-space: nowrap;">Steering &nbsp;Angle (°)
            
            <div class="mt-1">
                <p class="text-muted fs-6">${window.translations?.vehicles?.steering_angle_message || ''}</p>
            </div>
            
            </div>

            <!-- 삭제 버튼 자리도 인풋행과 동일하게 col-auto -->
            <div class="col-auto d-none d-md-block"></div>`;
            actionList.appendChild(header);
        }

        /* ── 액션 한 줄 ────────────────────────────────────────── */
        const row = document.createElement('div');
        row.className = 'row action-row gx-0 align-items-center';

        const idxCol = document.createElement('div');
        idxCol.className = 'idx-col col-auto text-end pe-4';  

        idxCol.textContent = currentCount

        /* speed number box */
        const speedCol = document.createElement('div');
        speedCol.className = 'col-6 col-md-4 px-0';
        const speedInp = document.createElement('input');
        speedInp.type = 'number';
        speedInp.min = '0.5';
        speedInp.max = '4';
        speedInp.step = '0.1';
        speedInp.value = speed;
        speedInp.className = 'speed form-control';
        speedInp.name = `action_${currentCount}_speed`;
        speedInp.setAttribute(
            'oninput',
            `this.value = Math.max(this.min, Math.min(this.max, this.value)); redraw();`
        );


        speedCol.appendChild(speedInp);

        /* angle number box */
        const angleCol = document.createElement('div');
        angleCol.className = 'col-6 col-md-4 px-0';
        const angleInp = document.createElement('input');
        angleInp.type = 'number';
        angleInp.min = '-25';
        angleInp.max = '25';
        angleInp.step = '1';
        angleInp.value = angle;
        angleInp.className = 'angle form-control';
        angleInp.name = `action_${currentCount}_steering`;
        angleInp.setAttribute(
            'oninput',
            `this.value = Math.max(this.min, Math.min(this.max, this.value)); redraw();`
        );

        angleCol.appendChild(angleInp);

        /* remove (✕) */
        const btnCol = document.createElement('div');
        btnCol.className = 'col-auto d-flex justify-content-center ps-0';
        const rmBtn = document.createElement('button');
        rmBtn.className = 'remove-btn btn btn-sm btn-outline-danger rounded-circle';
        rmBtn.innerHTML = '&times;';
        btnCol.appendChild(rmBtn);

        //append 
        row.append(idxCol, speedCol, angleCol, btnCol);
        actionList.appendChild(row);
        // ← ❷ 새 행 추가 후 번호 갱신
        updateRowIndices();                               

        /* 캔버스 갱신 및 저장 */
        [speedInp, angleInp].forEach(inp => inp.addEventListener('input', () => {
            redraw();
            saveCurrentActions();
        }));

        rmBtn.addEventListener('click', () => {
            row.remove();                                     // ← 행 제거
            updateRowIndices();                               // ← ❸ 남은 행 번호 다시 매김
            redraw();
            updateRemoveButtonStates();
            saveCurrentActions();
        });

        redraw();
        updateRemoveButtonStates();
        // 번호 인덱스 갱신
        updateRowIndices();
        // 새 액션 추가 시 저장
        saveCurrentActions();
    }

    /**
    * 현재 액션 스페이스를 수집하여 저장
    */
    function saveCurrentActions() {
        // 설정 로딩 중에는 저장하지 않음
        if (isLoadingActions) return;
        
        const actions = [];
        document.querySelectorAll('.action-row').forEach(row => {
            const speed = parseFloat(row.querySelector('.speed').value);
            const angle = parseFloat(row.querySelector('.angle').value);
            actions.push({ speed, steering_angle: angle });
        });
        if (window.saveActionSpace && actions.length > 0) {
            window.saveActionSpace(actions);
        }
    }

    /**
    * 각 속도/각도를 캔버스 좌표로 변환
    */
    function toPoint(angleDeg, speed, maxSpeed) {
        const cx = canvas.width * centerRatio.x;
        const cy = canvas.height * centerRatio.y;
        const maxR = Math.min(canvas.width, canvas.height) * radiusRatio;
        const r = (speed / maxSpeed) * maxR;
        const rad = (-angleDeg * 2 - 90) * Math.PI / 180;
        return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) };
    }

    /**
    * 전체 캔버스 다시 그리기
    */
    function redraw() {
        if (!bg.complete) return;
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.drawImage(bg, 0, 0, canvas.width, canvas.height);

        // modeSelect가 없으면 항상 discrete 모드
        const isDiscrete = !modeSelect || modeSelect.value === 'discrete';
        if (isDiscrete) drawDiscrete();
        else drawContinuous();
    }

    /**
    * Discrete 모드에서 벡터 그리기
    */
    function drawDiscrete() {
        const actions = [];
        document.querySelectorAll('.action-row').forEach(row => {
            const speedElem = row.querySelector('.speed');
            const angleElem = row.querySelector('.angle');
            const speed = parseFloat(speedElem.value);
            const angle = parseFloat(angleElem.value);
            const maxSpeed = parseFloat(speedElem.max);
            const end = toPoint(angle, speed, maxSpeed);
            const cx = canvas.width * centerRatio.x;
            const cy = canvas.height * centerRatio.y;

            // 액션 저장용 데이터 수집
            actions.push({ speed, steering_angle: angle });

            // 벡터 선
            ctx.strokeStyle = 'blue';
            ctx.lineWidth = 4;
            ctx.beginPath(); ctx.moveTo(cx, cy); ctx.lineTo(end.x, end.y); ctx.stroke();

            // 화살표 머리
            if (speed !== 0) {
            const headLen = 15 * (canvas.width / origWidth);
            const headAng = 30 * Math.PI / 180;
            const vx = cx - end.x, vy = cy - end.y;
            const base = Math.atan2(vy, vx);
            const x1 = end.x + headLen * Math.cos(base + headAng);
            const y1 = end.y + headLen * Math.sin(base + headAng);
            const x2 = end.x + headLen * Math.cos(base - headAng);
            const y2 = end.y + headLen * Math.sin(base - headAng);
            ctx.beginPath(); ctx.moveTo(end.x, end.y); ctx.lineTo(x1, y1);
            ctx.moveTo(end.x, end.y); ctx.lineTo(x2, y2); ctx.stroke();
            }
        });
        
        // 캔버스 그리기만 수행 (저장은 사용자 액션 시에만)
    }

    /**
    * Continuous 모드에서 곡선 그리기
    */
    function drawContinuous() {
        const minSpeedInput = document.getElementById('minSpeed');
        const maxSpeedInput = document.getElementById('maxSpeed');
        const minAngleInput = document.getElementById('minAngle');
        const maxAngleInput = document.getElementById('maxAngle');

        if (!minSpeedInput || !maxSpeedInput || !minAngleInput || !maxAngleInput) return;

        const lowSpeed = parseFloat(minSpeedInput.value);
        const highSpeed = parseFloat(maxSpeedInput.value);
        const ABS_MAX   = parseFloat(maxSpeedInput.getAttribute('max')) || 4;
        const maxSpeed = ABS_MAX; // 변경: highSpeed 대신 ABS_MAX 사용
        const lowAng = parseFloat(minAngleInput.value);
        const highAng = parseFloat(maxAngleInput.value);

        const pts = [];
        for (let a = lowAng; a <= highAng; a++) pts.push(toPoint(a, highSpeed, maxSpeed)); // 변경: toPoint의 세 번째 인자를 maxSpeed로 (ABS_MAX과 동일)
        for (let a = highAng; a >= lowAng; a--) pts.push(toPoint(a, lowSpeed, maxSpeed));  // 변경: toPoint의 세 번째 인자를 maxSpeed로 (ABS_MAX과 동일)

        ctx.fillStyle = 'rgba(0,0,255,0.3)';
        ctx.beginPath();
        pts.forEach((p, i) => i === 0 ? ctx.moveTo(p.x, p.y) : ctx.lineTo(p.x, p.y));
        ctx.closePath();
        ctx.fill();
    }

    /**
    * 삭제 버튼 활성/비활성 처리
    */
    function updateRemoveButtonStates() {
        const rows = document.querySelectorAll('.action-row');
        const onlyOne = rows.length <= 1;
        rows.forEach(row => {
            const btn = row.querySelector('.remove-btn');
            if (btn) {
            btn.disabled = onlyOne;
            btn.classList.toggle('disabled', onlyOne);
            }
        });
        
        // 액션 추가 버튼 상태도 함께 업데이트
        updateAddActionButtonState();
    }

    /**
    * 액션 추가 버튼 활성화/비활성화 처리
    */
    function updateAddActionButtonState() {
        if (addActionBtn) {
            const currentCount = document.querySelectorAll('.action-row').length;
            const isMaxReached = currentCount >= 30;
            addActionBtn.disabled = isMaxReached;
            addActionBtn.classList.toggle('disabled', isMaxReached);
            
            // 버튼의 배경색을 변경하여 시각적 피드백 제공
            if (isMaxReached) {
                addActionBtn.classList.remove('btn-primary');
                addActionBtn.classList.add('btn-secondary');
            } else {
                addActionBtn.classList.remove('btn-secondary');
                addActionBtn.classList.add('btn-primary');
            }
        }
    }

    //speed ,steering angle 앞 번호를 새로 매겨 주는 유틸 함수
    function updateRowIndices () {
        document
            .querySelectorAll('#actionList .action-row .idx-col')
            .forEach((cell, i) => cell.textContent = i);   // ← ❶ 인덱스 덮어쓰기
    }

    /**
    * 외부에서 액션 스페이스 설정 (설정 로드 시 사용)
    */
    window.setActions = function(actions) {
        if (!actionList || !Array.isArray(actions) || actions.length === 0) return;
        
        isLoadingActions = true;  // 로딩 중 플래그
        
        // 기존 액션 모두 제거
        actionList.innerHTML = '';
        
        // 새 액션 추가
        actions.forEach(action => {
            const speed = action.speed !== undefined ? action.speed : 1.5;
            const angle = action.steering_angle !== undefined ? action.steering_angle : 0;
            addAction(speed, angle);
        });
        
        isLoadingActions = false;  // 로딩 완료
    };

    // 설정 로드 시 pendingActionSpace가 있으면 적용
    if (window.pendingActionSpace) {
        setTimeout(() => {
            window.setActions(window.pendingActionSpace);
            delete window.pendingActionSpace;
        }, 100);
    }