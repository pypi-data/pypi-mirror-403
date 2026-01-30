/**
 * Create Model Page - 통합 모듈
 * 
 * 책임:
 * 1. FormState: 폼 상태 관리 (단일 진실의 원천)
 * 2. UI: DOM 업데이트
 * 3. API: 서버 통신
 * 4. Validation: 입력 검증
 * 5. ActionSpace: 캔버스 그리기
 * 6. SimulationTabs: 탭 관리
 */

(function() {
  'use strict';

  // ============================================================
  // 1. 상태 관리 (FormState)
  // ============================================================
  const FormState = {
    // 모델 이름
    modelName: '',
    
    // 메인 시뮬레이션
    simulation: {
      track_id: 'reInvent2019_wide',
      track_direction: 'counterclockwise',
      alternate_direction: false,
      race_type: 'TIME_TRIAL',
      object_avoidance: null
    },
    
    // 서브 시뮬레이션 (최대 6개)
    subSimulations: [],
    subSimulationCount: 0,
    
    // 차량 설정
    vehicle: {
      vehicle_type: 'deepracer',
      lidar: false,
      action_space: [
        { steering_angle: -25, speed: 0.5 },
        { steering_angle: -15, speed: 1.0 },
        { steering_angle: 0, speed: 1.5 },
        { steering_angle: 15, speed: 1.0 },
        { steering_angle: 25, speed: 0.5 }
      ]
    },
    
    // 훈련 설정
    training: {
      training_time_minutes: 60,
      best_model_metric: 'progress',
      hyperparameters: {
        batch_size: 32,
        discount_factor: 0.99,
        learning_rate: 0.0003,
        loss_type: 'huber',
        entropy: 0.01
      }
    },
    
    // 보상 함수
    rewardFunction: '',
    
    // 제출 상태
    isSubmitting: false,
    isRewardValidated: false,
    
    // 상태 업데이트 메서드
    update(path, value) {
      const keys = path.split('.');
      let obj = this;
      for (let i = 0; i < keys.length - 1; i++) {
        obj = obj[keys[i]];
      }
      obj[keys[keys.length - 1]] = value;
    },
    
    // 전체 폼 데이터 수집 (API 요청용)
    collectFormData() {
      return {
        model_name: this.modelName,
        simulation: { ...this.simulation },
        sub_simulations: this.subSimulations.slice(0, this.subSimulationCount),
        vehicle: { ...this.vehicle },
        training: { ...this.training },
        reward_function: this.rewardFunction
      };
    }
  };

  // ============================================================
  // 2. DOM 요소 캐시
  // ============================================================
  const DOM = {
    // 초기화 시 채워짐
    modelNameInput: null,
    submitBtn: null,
    submitSpinner: null,
    subSimCountSelect: null,
    subNavItems: null,
    actionList: null,
    addActionBtn: null,
    canvas: null,
    ctx: null,
    editor: null, // CodeMirror
    
    init() {
      this.modelNameInput = document.getElementById('model-name-id');
      this.submitBtn = document.getElementById('submit-model-btn');
      this.submitSpinner = document.getElementById('createModelSpinner');
      this.subSimCountSelect = document.getElementById('sub-simulation-count-id');
      this.subNavItems = document.querySelectorAll('.sub-nav-item');
      this.actionList = document.getElementById('actionList');
      this.addActionBtn = document.getElementById('addAction');
      this.canvas = document.getElementById('canvas');
      if (this.canvas) {
        this.ctx = this.canvas.getContext('2d');
      }
      // CodeMirror는 나중에 초기화됨
    }
  };

  // ============================================================
  // 3. API 클라이언트
  // ============================================================
  const API = {
    async checkModelName(name) {
      try {
        const res = await fetch(`/api/models/${encodeURIComponent(name)}/check`);
        return await res.json();
      } catch (e) {
        console.error('Model name check error:', e);
        return { available: true }; // 오류 시 일단 통과
      }
    },
    
    async validateRewardFunction(code) {
      try {
        const res = await fetch('/api/reward-function/validate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ reward_function: code })
        });
        return await res.json();
      } catch (e) {
        console.error('Reward validation error:', e);
        return { status: 'error', error: e.message };
      }
    },
    
    async startTraining(data) {
      const res = await fetch('/api/training/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      const json = await res.json();
      return { ok: res.ok, status: res.status, data: json };
    },
    
    async loadSettings() {
      try {
        const res = await fetch('/api/settings');
        if (!res.ok) return null;
        return await res.json();
      } catch (e) {
        console.error('Load settings error:', e);
        return null;
      }
    }
  };

  // ============================================================
  // 4. 검증 모듈
  // ============================================================
  const Validation = {
    modelNamePattern: /^[a-zA-Z0-9_.-]+$/,
    
    validateModelName(name) {
      if (!name || name.trim() === '') {
        return { valid: false, error: '모델 이름을 입력해주세요.' };
      }
      if (!this.modelNamePattern.test(name)) {
        return { valid: false, error: '모델 이름은 영문, 숫자, _, -, . 만 사용할 수 있습니다.' };
      }
      return { valid: true };
    },
    
    async validateModelNameAsync(name) {
      const syncResult = this.validateModelName(name);
      if (!syncResult.valid) return syncResult;
      
      const serverResult = await API.checkModelName(name);
      if (!serverResult.available) {
        return { valid: false, error: '이미 존재하는 모델 이름입니다.' };
      }
      return { valid: true };
    },
    
    validateRewardFunction(code) {
      if (!code || code.trim().length < 10) {
        return { valid: false, error: '보상 함수를 입력해주세요.' };
      }
      if (!code.includes('def reward_function')) {
        return { valid: false, error: '보상 함수에 "def reward_function"이 포함되어야 합니다.' };
      }
      return { valid: true };
    }
  };

  // ============================================================
  // 5. UI 관리
  // ============================================================
  const UI = {
    // 모델 이름 상태 표시
    showModelNameStatus(status, message) {
      const feedbackDiv = document.getElementById('model-name-feedback');
      const input = DOM.modelNameInput;
      
      input.classList.remove('is-valid', 'is-invalid');
      
      if (status === 'valid') {
        input.classList.add('is-valid');
        feedbackDiv.innerHTML = `<span class="text-success">${message}</span>`;
      } else if (status === 'invalid') {
        input.classList.add('is-invalid');
        feedbackDiv.innerHTML = `<span class="text-danger">${message}</span>`;
      } else {
        feedbackDiv.innerHTML = '';
      }
    },
    
    // 로딩 스피너 표시
    showModelNameSpinner(show) {
      const spinner = document.getElementById('model-name-spinner');
      spinner.classList.toggle('d-none', !show);
    },
    
    // 서브 시뮬레이션 탭 표시/숨김
    updateSubSimTabs(count) {
      DOM.subNavItems.forEach((item, index) => {
        // index 0은 main, 1~6은 sub1~sub6
        if (index === 0) return; // main은 항상 표시
        item.classList.toggle('d-none', index > count);
      });
    },
    
    // 트랙 프리뷰 업데이트
    updateTrackPreview(tabId, trackData) {
      const suffix = tabId.replace('tabs-', '');
      const previewId = suffix === 'main' ? 'track-preview-box' : `track-preview-box-${suffix}`;
      const descId = suffix === 'main' ? 'track-description-box' : `track-description-box-${suffix}`;
      
      const previewElem = document.getElementById(previewId);
      const descElem = document.getElementById(descId);
      
      if (previewElem && trackData.image) {
        previewElem.innerHTML = `
          <img src="${trackData.image}" alt="Track" style="max-height:210px;width:100%;margin-bottom:8px;">
          <span class="text-muted small">${trackData.name || ''}</span>
        `;
      }
      
      if (descElem && trackData.name) {
        descElem.innerHTML = `
          <h5 class="mb-3">${trackData.name}</h5>
          <div class="mb-2"><strong>Width:</strong> ${trackData.width || '-'}</div>
          <div class="mb-2"><strong>Length:</strong> ${trackData.length || '-'}</div>
          <div class="mb-2"><strong>Direction:</strong> ${(trackData.direction || '').replace(/,/g, ', ')}</div>
          <div class="mt-3"><strong>Description:</strong><br><small class="text-muted">${trackData.description || ''}</small></div>
        `;
      }
    },
    
    // Object Avoidance 섹션 표시/숨김
    showObjectAvoidance(tabId, show) {
      const suffix = tabId.replace('tabs-', '');
      const wrapperId = suffix === 'main' ? 'race-type-wrapper' : `race-type-wrapper-${suffix}`;
      const wrapper = document.getElementById(wrapperId);
      if (wrapper) {
        wrapper.classList.toggle('d-none', !show);
      }
    },
    
    // 제출 버튼 상태
    setSubmitButtonState(loading) {
      DOM.submitBtn.disabled = loading;
      DOM.submitBtn.classList.toggle('disabled', loading);
      DOM.submitSpinner.classList.toggle('d-none', !loading);
    },
    
    // SweetAlert2 팝업
    async showError(title, text) {
      await Swal.fire({ icon: 'error', title, text });
    },
    
    async showSuccess(title, text, timer = 2000) {
      await Swal.fire({ icon: 'success', title, text, timer, showConfirmButton: false });
    },
    
    showLoading(title) {
      Swal.fire({
        title,
        allowOutsideClick: false,
        allowEscapeKey: false,
        didOpen: () => Swal.showLoading()
      });
    }
  };

  // ============================================================
  // 6. 액션 스페이스 모듈
  // ============================================================
  const ActionSpace = {
    bg: null,
    origWidth: 734,
    origHeight: 363,
    centerRatio: { x: 367.5 / 734, y: 301 / 363 },
    radiusRatio: 280 / 363,
    
    init() {
      this.bg = new Image();
      this.bg.src = typeof actionSpaceImage !== 'undefined' 
        ? actionSpaceImage 
        : '/static/img/action_space.png';
      
      this.bg.onload = () => {
        if (DOM.canvas) {
          DOM.canvas.width = this.bg.naturalWidth || this.origWidth;
          DOM.canvas.height = this.bg.naturalHeight || this.origHeight;
          this.render();
        }
      };
      
      // 이벤트 바인딩
      if (DOM.addActionBtn) {
        DOM.addActionBtn.addEventListener('click', () => this.addAction());
      }
      
      // 초기 액션 렌더링
      this.renderActions(FormState.vehicle.action_space);
    },
    
    // 액션 목록 렌더링
    renderActions(actions) {
      if (!DOM.actionList) return;
      DOM.actionList.innerHTML = '';
      
      if (actions.length === 0) return;
      
      // 헤더
      const header = document.createElement('div');
      header.className = 'row gx-1 mb-1 fw-bold';
      header.innerHTML = `
        <div class="idx-col col-auto text-end pe-4 invisible">00</div>
        <div class="col-6 col-md-4 text-start">Speed (m/s)</div>
        <div class="col-6 col-md-4 text-start">Steering Angle (°)</div>
        <div class="col-auto d-none d-md-block"></div>
      `;
      DOM.actionList.appendChild(header);
      
      // 각 액션 행
      actions.forEach((action, index) => {
        this.createActionRow(index, action.speed, action.steering_angle);
      });
      
      this.updateButtonStates();
      this.render();
    },
    
    // 액션 행 생성
    createActionRow(index, speed, angle) {
      const row = document.createElement('div');
      row.className = 'row action-row gx-0 align-items-center';
      row.dataset.index = index;
      
      row.innerHTML = `
        <div class="idx-col col-auto text-end pe-4">${index}</div>
        <div class="col-6 col-md-4 px-0">
          <input type="number" class="speed form-control" min="0.5" max="4" step="0.1" value="${speed}">
        </div>
        <div class="col-6 col-md-4 px-0">
          <input type="number" class="angle form-control" min="-25" max="25" step="1" value="${angle}">
        </div>
        <div class="col-auto d-flex justify-content-center ps-0">
          <button class="remove-btn btn btn-sm btn-outline-danger rounded-circle">&times;</button>
        </div>
      `;
      
      // 이벤트 바인딩
      const speedInput = row.querySelector('.speed');
      const angleInput = row.querySelector('.angle');
      const removeBtn = row.querySelector('.remove-btn');
      
      // 클램핑 후 DOM 업데이트 함수
      const clampSpeed = () => {
        let val = parseFloat(speedInput.value);
        if (!isNaN(val) && (val < 0.5 || val > 4)) {
          speedInput.value = this.clamp(val, 0.5, 4);
        }
      };
      const clampAngle = () => {
        let val = parseFloat(angleInput.value);
        if (!isNaN(val) && (val < -25 || val > 25)) {
          angleInput.value = this.clamp(val, -25, 25);
        }
      };
      
      speedInput.addEventListener('input', () => {
        clampSpeed();
        this.syncToState();
        this.render();
      });
      
      angleInput.addEventListener('input', () => {
        clampAngle();
        this.syncToState();
        this.render();
      });
      
      removeBtn.addEventListener('click', () => {
        row.remove();
        this.reindex();
        this.syncToState();
        this.updateButtonStates();
        this.render();
      });
      
      DOM.actionList.appendChild(row);
    },
    
    // 액션 추가
    addAction(speed = 1.5, angle = 0) {
      const currentCount = DOM.actionList.querySelectorAll('.action-row').length;
      if (currentCount >= 30) return;
      
      // 헤더가 없으면 추가
      if (currentCount === 0) {
        this.renderActions([{ speed, steering_angle: angle }]);
        return;
      }
      
      this.createActionRow(currentCount, speed, angle);
      this.syncToState();
      this.updateButtonStates();
      this.render();
    },
    
    // 인덱스 재정렬
    reindex() {
      DOM.actionList.querySelectorAll('.action-row').forEach((row, i) => {
        row.dataset.index = i;
        row.querySelector('.idx-col').textContent = i;
      });
    },
    
    // 값 클램핑
    clamp(val, min, max) {
      return Math.max(min, Math.min(max, val));
    },
    
    // 상태 동기화 (DOM → FormState)
    syncToState() {
      const actions = [];
      DOM.actionList.querySelectorAll('.action-row').forEach(row => {
        let speed = parseFloat(row.querySelector('.speed').value) || 1.0;
        let angle = parseFloat(row.querySelector('.angle').value) || 0;
        // 클램핑: speed 0.5~4, angle -25~25
        speed = this.clamp(speed, 0.5, 4);
        angle = this.clamp(angle, -25, 25);
        actions.push({ steering_angle: angle, speed });
      });
      FormState.vehicle.action_space = actions;
    },
    
    // 버튼 상태 업데이트
    updateButtonStates() {
      const rows = DOM.actionList.querySelectorAll('.action-row');
      const count = rows.length;
      
      // 삭제 버튼 (1개 이하면 비활성화)
      rows.forEach(row => {
        const btn = row.querySelector('.remove-btn');
        btn.disabled = count <= 1;
        btn.classList.toggle('disabled', count <= 1);
      });
      
      // 추가 버튼 (30개 이상이면 비활성화)
      if (DOM.addActionBtn) {
        DOM.addActionBtn.disabled = count >= 30;
        DOM.addActionBtn.classList.toggle('disabled', count >= 30);
      }
    },
    
    // 캔버스 좌표 변환
    toPoint(angleDeg, speed, maxSpeed) {
      const cx = DOM.canvas.width * this.centerRatio.x;
      const cy = DOM.canvas.height * this.centerRatio.y;
      const maxR = Math.min(DOM.canvas.width, DOM.canvas.height) * this.radiusRatio;
      const r = (speed / maxSpeed) * maxR;
      const rad = (-angleDeg * 2 - 90) * Math.PI / 180;
      return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) };
    },
    
    // 캔버스 렌더링
    render() {
      if (!DOM.canvas || !DOM.ctx || !this.bg.complete) return;
      
      const ctx = DOM.ctx;
      ctx.clearRect(0, 0, DOM.canvas.width, DOM.canvas.height);
      ctx.drawImage(this.bg, 0, 0, DOM.canvas.width, DOM.canvas.height);
      
      const cx = DOM.canvas.width * this.centerRatio.x;
      const cy = DOM.canvas.height * this.centerRatio.y;
      const maxSpeed = 4;
      
      FormState.vehicle.action_space.forEach(action => {
        const end = this.toPoint(action.steering_angle, action.speed, maxSpeed);
        
        // 벡터 선
        ctx.strokeStyle = 'blue';
        ctx.lineWidth = 4;
        ctx.beginPath();
        ctx.moveTo(cx, cy);
        ctx.lineTo(end.x, end.y);
        ctx.stroke();
        
        // 화살표
        if (action.speed !== 0) {
          const headLen = 15 * (DOM.canvas.width / this.origWidth);
          const headAng = 30 * Math.PI / 180;
          const vx = cx - end.x, vy = cy - end.y;
          const base = Math.atan2(vy, vx);
          
          ctx.beginPath();
          ctx.moveTo(end.x, end.y);
          ctx.lineTo(end.x + headLen * Math.cos(base + headAng), end.y + headLen * Math.sin(base + headAng));
          ctx.moveTo(end.x, end.y);
          ctx.lineTo(end.x + headLen * Math.cos(base - headAng), end.y + headLen * Math.sin(base - headAng));
          ctx.stroke();
        }
      });
    }
  };

  // ============================================================
  // 7. 시뮬레이션 탭 모듈
  // ============================================================
  const SimulationTabs = {
    currentTab: 'tabs-main',
    
    init() {
      // 서브 시뮬레이션 카운트 변경
      if (DOM.subSimCountSelect) {
        DOM.subSimCountSelect.addEventListener('change', (e) => {
          const count = parseInt(e.target.value) || 0;
          FormState.subSimulationCount = count;
          UI.updateSubSimTabs(count);
          this.ensureSubSimulations(count);
          
          // 새로 보이는 탭에 기본 트랙 설정
          for (let i = 1; i <= count; i++) {
            this.setDefaultTrack(`tabs-sub${i}`);
          }
        });
      }
      
      // 탭 전환 이벤트
      document.querySelectorAll('[data-bs-toggle="tab"]').forEach(tab => {
        tab.addEventListener('shown.bs.tab', (e) => {
          this.currentTab = e.target.getAttribute('href').replace('#', '');
        });
      });
      
      // 각 탭 초기화
      this.initTab('tabs-main');
      for (let i = 1; i <= 6; i++) {
        this.initTab(`tabs-sub${i}`);
        // 서브 시뮬레이션 기본 설정 생성
        FormState.subSimulations[i - 1] = this.createDefaultSimulation();
      }
      
      // 트랙 모달 이벤트
      this.initTrackModal();
      
      // 메인 탭 기본 트랙 설정
      this.setDefaultTrack('tabs-main');
    },
    
    createDefaultSimulation() {
      return {
        track_id: 'reInvent2019_wide',
        track_direction: 'counterclockwise',
        alternate_direction: false,
        race_type: 'TIME_TRIAL',
        object_avoidance: null
      };
    },
    
    ensureSubSimulations(count) {
      while (FormState.subSimulations.length < count) {
        FormState.subSimulations.push(this.createDefaultSimulation());
      }
    },
    
    initTab(tabId) {
      const pane = document.getElementById(tabId);
      if (!pane) return;
      
      const suffix = tabId.replace('tabs-', '');
      const isMain = suffix === 'main';
      
      // Race Type 라디오
      const raceTypeName = isMain ? 'race-type' : `race-type-${suffix}`;
      pane.querySelectorAll(`input[name="${raceTypeName}"]`).forEach(radio => {
        radio.addEventListener('change', (e) => {
          const value = e.target.value.toUpperCase();
          this.updateSimulation(tabId, { race_type: value });
          UI.showObjectAvoidance(tabId, value === 'OBJECT_AVOIDANCE');
        });
      });
      
      // Direction 라디오
      const dirName = isMain ? 'clock-direction' : `clock-direction-${suffix}`;
      pane.querySelectorAll(`input[name="${dirName}"]`).forEach(radio => {
        radio.addEventListener('change', (e) => {
          this.updateSimulation(tabId, { track_direction: e.target.value });
        });
      });
      
      // Alternate Direction 체크박스
      const altId = isMain ? 'alternate-training-main' : `alternate-${suffix}`;
      const altCheckbox = document.getElementById(altId);
      if (altCheckbox) {
        altCheckbox.addEventListener('change', (e) => {
          this.updateSimulation(tabId, { alternate_direction: e.target.checked });
        });
      }
      
      // Object Avoidance 설정
      this.initObjectAvoidance(tabId);
    },
    
    initObjectAvoidance(tabId) {
      const suffix = tabId.replace('tabs-', '');
      const isMain = suffix === 'main';
      
      const numSelect = document.getElementById(isMain ? 'number-of-objects' : `number-of-objects-${suffix}`);
      const typeSelect = document.querySelector(isMain ? 'select[name="object-type"]' : `select[name="object-type-${suffix}"]`);
      const posCheckbox = document.getElementById(isMain ? 'object-position' : `object-position-${suffix}`);
      const locationWrapper = document.getElementById(isMain ? 'object-location-wrapper' : `object-location-wrapper-${suffix}`);
      
      // Object Locations 렌더링 함수
      const renderObjectLocations = () => {
        if (!locationWrapper || !numSelect || !posCheckbox) return;
        
        const count = parseInt(numSelect.value, 10);
        const randomize = posCheckbox.checked;
        
        if (!randomize && count > 0) {
          locationWrapper.classList.remove('d-none');
          
          const innerContainer = locationWrapper.querySelector('.card-body');
          if (!innerContainer) return;
          innerContainer.innerHTML = '';
          
          for (let i = 0; i < count; i++) {
            const isOdd = (i + 1) % 2 === 1;
            const progressValue = ((100 / (count + 1)) * (i + 1)).toFixed(0);
            
            const block = document.createElement('div');
            block.className = 'obstable-block mb-2 p-2 border rounded bg-light';
            
            // suffix를 이름에 포함하여 각 탭별로 구분
            const nameSuffix = isMain ? '' : `-${suffix}`;
            block.innerHTML = `
              <div class="d-flex align-items-center gap-2">
                <span class="fw-bold" style="min-width:40px;">${i}</span>
                <div class="d-flex align-items-center gap-1">
                  <label class="form-label mb-0 small">Progress:</label>
                  <input type="number" step="any" class="form-control form-control-sm progress-valid"
                         name="progress-${i + 1}${nameSuffix}" max="100" style="width:70px;"
                         oninput="this.value = Math.min(100, Math.max(0, this.value))"
                         value="${progressValue}">
                  <span class="small">%</span>
                </div>
                <div class="d-flex align-items-center gap-1 ms-2">
                  <label class="form-label mb-0 small">Lane:</label>
                  <label class="form-check form-check-inline mb-0">
                    <input class="form-check-input" type="radio" name="lane-${i + 1}${nameSuffix}" value="inside" ${isOdd ? 'checked' : ''}>
                    <span class="form-check-label small">IN</span>
                  </label>
                  <label class="form-check form-check-inline mb-0">
                    <input class="form-check-input" type="radio" name="lane-${i + 1}${nameSuffix}" value="outside" ${!isOdd ? 'checked' : ''}>
                    <span class="form-check-label small">OUT</span>
                  </label>
                </div>
              </div>
            `;
            innerContainer.appendChild(block);
          }
        } else {
          locationWrapper.classList.add('d-none');
          const innerContainer = locationWrapper.querySelector('.card-body');
          if (innerContainer) innerContainer.innerHTML = '';
        }
      };
      
      if (numSelect) {
        numSelect.addEventListener('change', (e) => {
          const num = parseInt(e.target.value);
          this.updateObjectAvoidance(tabId, { number_of_objects: num });
          renderObjectLocations();
        });
      }
      
      if (typeSelect) {
        typeSelect.addEventListener('change', (e) => {
          this.updateObjectAvoidance(tabId, { object_type: e.target.value });
        });
      }
      
      if (posCheckbox) {
        posCheckbox.addEventListener('change', (e) => {
          this.updateObjectAvoidance(tabId, { randomize_locations: e.target.checked });
          renderObjectLocations();
        });
      }
      
      // 초기 렌더링은 SettingsLoader.load()에서 처리 (API 값 적용 후)
      // 이벤트 핸들러만 등록하고, 초기 렌더링은 생략
    },
    
    updateSimulation(tabId, data) {
      if (tabId === 'tabs-main') {
        Object.assign(FormState.simulation, data);
      } else {
        const index = parseInt(tabId.replace('tabs-sub', '')) - 1;
        if (FormState.subSimulations[index]) {
          Object.assign(FormState.subSimulations[index], data);
        }
      }
    },
    
    updateObjectAvoidance(tabId, data) {
      const sim = tabId === 'tabs-main' 
        ? FormState.simulation 
        : FormState.subSimulations[parseInt(tabId.replace('tabs-sub', '')) - 1];
      
      if (!sim) return;
      
      if (!sim.object_avoidance) {
        sim.object_avoidance = {
          object_type: 'box_obstacle',
          number_of_objects: 3,
          randomize_locations: true,
          object_locations: null
        };
      }
      Object.assign(sim.object_avoidance, data);
    },
    
    initTrackModal() {
      // 모달 열기 버튼들
      document.querySelectorAll('[data-bs-toggle="modal"][data-bs-target="#modal-report"]').forEach(btn => {
        btn.addEventListener('click', () => {
          const pane = btn.closest('.simulation-pane');
          if (pane) {
            this.currentTab = pane.id;
          }
        });
      });
      
      // 트랙 선택
      document.querySelectorAll('input[name="form-imagecheck-radio"]').forEach(radio => {
        radio.addEventListener('change', (e) => {
          const input = e.target;
          const trackId = input.value;
          const trackName = input.dataset.trackName || '';
          const label = input.closest('label');
          const img = label?.querySelector('img');
          
          const trackData = {
            id: trackId,
            name: trackName,
            image: img?.src || '',
            width: input.dataset.trackWidth || '-',
            length: input.dataset.trackLength || '-',
            direction: input.dataset.trackDirection || '',
            description: input.dataset.trackDescription || ''
          };
          
          // 상태 업데이트
          this.updateSimulation(this.currentTab, { track_id: trackId });
          
          // UI 업데이트
          UI.updateTrackPreview(this.currentTab, trackData);
          
          // 방향 라디오 업데이트
          this.updateDirectionRadios(this.currentTab, trackData.direction);
          
          // 모달 닫기
          document.querySelector('#modal-report .btn-close')?.click();
        });
      });
    },
    
    updateDirectionRadios(tabId, dirStr) {
      const suffix = tabId.replace('tabs-', '');
      const dirName = suffix === 'main' ? 'clock-direction' : `clock-direction-${suffix}`;
      const pane = document.getElementById(tabId);
      if (!pane) return;
      
      const directions = (dirStr || '').split(',').map(s => s.trim()).filter(Boolean);
      
      pane.querySelectorAll(`input[name="${dirName}"]`).forEach(radio => {
        const enabled = directions.includes(radio.value);
        radio.disabled = !enabled;
        radio.closest('label')?.classList.toggle('text-muted', !enabled);
        if (!enabled) radio.checked = false;
      });
      
      // 단방향 트랙이면 자동 선택
      if (directions.length === 1) {
        const radio = pane.querySelector(`input[name="${dirName}"][value="${directions[0]}"]`);
        if (radio) {
          radio.checked = true;
          this.updateSimulation(tabId, { track_direction: directions[0] });
        }
      }
    },
    
    // 기본 트랙 설정 (A to Z Speedway)
    setDefaultTrack(tabId) {
      const suffix = tabId.replace('tabs-', '');
      const previewId = suffix === 'main' ? 'track-preview-box' : `track-preview-box-${suffix}`;
      const previewElem = document.getElementById(previewId);
      
      // 이미 트랙이 설정되어 있으면 스킵
      if (previewElem && previewElem.innerHTML.trim() && previewElem.querySelector('img')) {
        return;
      }
      
      // 기본 트랙 찾기
      const defaultInput = Array.from(document.querySelectorAll('input[value="reInvent2019_wide"]'))
        .find(input => input.dataset.trackName === 'A to Z Speedway');
      
      if (defaultInput) {
        const label = defaultInput.closest('label');
        const img = label?.querySelector('img');
        const trackData = {
          id: 'reInvent2019_wide',
          name: defaultInput.dataset.trackName || 'A to Z Speedway',
          image: img?.src || '',
          width: defaultInput.dataset.trackWidth || '-',
          length: defaultInput.dataset.trackLength || '-',
          direction: defaultInput.dataset.trackDirection || 'clockwise,counterclockwise',
          description: defaultInput.dataset.trackDescription || ''
        };
        
        UI.updateTrackPreview(tabId, trackData);
        this.updateSimulation(tabId, { track_id: trackData.id });
        this.updateDirectionRadios(tabId, trackData.direction);
      }
    },
    
    // Object Locations 데이터 수집
    collectObjectLocations(tabId) {
      const suffix = tabId.replace('tabs-', '');
      const isMain = suffix === 'main';
      const wrapperId = isMain ? 'object-location-wrapper' : `object-location-wrapper-${suffix}`;
      const wrapper = document.getElementById(wrapperId);
      
      if (!wrapper || wrapper.classList.contains('d-none')) {
        return null;
      }
      
      const locations = [];
      const blocks = wrapper.querySelectorAll('.obstable-block');
      const nameSuffix = isMain ? '' : `-${suffix}`;
      
      blocks.forEach((block, idx) => {
        const progressInput = block.querySelector(`input[name="progress-${idx + 1}${nameSuffix}"]`);
        const laneInput = block.querySelector(`input[name="lane-${idx + 1}${nameSuffix}"]:checked`);
        
        if (progressInput && laneInput) {
          locations.push({
            progress: parseFloat(progressInput.value) || 0,
            lane: laneInput.value
          });
        }
      });
      
      return locations.length > 0 ? locations : null;
    }
  };

  // ============================================================
  // 8. 훈련 설정 모듈
  // ============================================================
  const TrainingSettings = {
    init() {
      // Batch Size
      const batchSize = document.getElementById('batchSize');
      if (batchSize) {
        batchSize.addEventListener('change', (e) => {
          FormState.training.hyperparameters.batch_size = parseInt(e.target.value);
        });
      }
      
      // Discount Factor
      const discount = document.querySelector('input[name="discount_factor"]');
      if (discount) {
        discount.addEventListener('input', (e) => {
          FormState.training.hyperparameters.discount_factor = parseFloat(e.target.value);
        });
      }
      
      // Learning Rate
      const lr = document.querySelector('input[name="learning_rate"]');
      if (lr) {
        lr.addEventListener('input', (e) => {
          FormState.training.hyperparameters.learning_rate = parseFloat(e.target.value);
        });
      }
      
      // Entropy
      const entropy = document.querySelector('input[name="entropy"]');
      if (entropy) {
        entropy.addEventListener('input', (e) => {
          FormState.training.hyperparameters.entropy = parseFloat(e.target.value);
        });
      }
      
      // Loss Type
      document.querySelectorAll('input[name="loss_type"]').forEach(radio => {
        radio.addEventListener('change', (e) => {
          FormState.training.hyperparameters.loss_type = e.target.value;
        });
      });
      
      // Best Model Metric
      document.querySelectorAll('input[name="best_model_metric"]').forEach(radio => {
        radio.addEventListener('change', (e) => {
          FormState.training.best_model_metric = e.target.value;
        });
      });
      
      // Max Training Time
      const maxTime = document.getElementById('max_training_time');
      if (maxTime) {
        maxTime.addEventListener('input', (e) => {
          FormState.training.training_time_minutes = parseInt(e.target.value) || 60;
        });
      }
    }
  };

  // ============================================================
  // 9. 차량 설정 모듈
  // ============================================================
  const VehicleSettings = {
    init() {
      // Vehicle Type
      const layoutSelect = document.getElementById('vehicle-layout');
      if (layoutSelect) {
        layoutSelect.addEventListener('change', (e) => {
          FormState.vehicle.vehicle_type = e.target.value;
          this.updateLidarState(e.target.value);
          this.updateVehicleImage();
        });
        
        // 초기 상태 설정
        this.updateLidarState(layoutSelect.value);
      }
      
      // Lidar
      const lidarCheckbox = document.getElementById('lidar-checkbox');
      if (lidarCheckbox) {
        lidarCheckbox.addEventListener('change', (e) => {
          FormState.vehicle.lidar = e.target.checked;
          this.updateVehicleImage();
        });
      }
      
      // 초기 차량 이미지 설정
      this.updateVehicleImage();
    },
    
    updateLidarState(vehicleType) {
      const lidarCheckbox = document.getElementById('lidar-checkbox');
      if (!lidarCheckbox) return;
      
      if (vehicleType === 'physicar') {
        lidarCheckbox.checked = true;
        lidarCheckbox.disabled = true;
        FormState.vehicle.lidar = true;
      } else {
        lidarCheckbox.disabled = false;
      }
    },
    
    updateVehicleImage() {
      const img = document.getElementById('vehicleImg');
      if (!img) return;
      
      const layout = FormState.vehicle.vehicle_type;
      const lidar = FormState.vehicle.lidar ? 'true' : 'false';
      img.src = `/static/img/sensor_modification/${layout}/camera_1-lidar_${lidar}.png`;
    }
  };

  // ============================================================
  // 10. 폼 제출 핸들러
  // ============================================================
  const FormHandler = {
    init() {
      if (!DOM.submitBtn) return;
      
      // 기존 이벤트 제거 (중복 방지)
      DOM.submitBtn.replaceWith(DOM.submitBtn.cloneNode(true));
      DOM.submitBtn = document.getElementById('submit-model-btn');
      
      // 단일 이벤트 리스너 등록
      DOM.submitBtn.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        this.handleSubmit();
      });
      
      // 버튼 활성화
      DOM.submitBtn.disabled = false;
      DOM.submitBtn.classList.remove('disabled');
    },
    
    async handleSubmit() {
      // 중복 제출 방지
      if (FormState.isSubmitting) {
        console.warn('[FormHandler] 이미 제출 중');
        return;
      }
      
      FormState.isSubmitting = true;
      UI.setSubmitButtonState(true);
      
      try {
        // 1. 상태에서 최신 값 동기화
        this.syncFromDOM();
        
        // 2. 모델 이름 검증
        const modelNameResult = await Validation.validateModelNameAsync(FormState.modelName);
        if (!modelNameResult.valid) {
          UI.showModelNameStatus('invalid', modelNameResult.error);
          await UI.showError('오류', modelNameResult.error);
          DOM.modelNameInput.focus();
          return;
        }
        
        // 3. 보상 함수 검증
        const rewardCode = window.editor?.getValue() || '';
        FormState.rewardFunction = rewardCode;
        
        const rewardSyncResult = Validation.validateRewardFunction(rewardCode);
        if (!rewardSyncResult.valid) {
          await UI.showError('오류', rewardSyncResult.error);
          return;
        }
        
        // 4. 서버 보상 함수 검증
        UI.showLoading('보상 함수를 검증하고 있습니다...');
        const rewardApiResult = await API.validateRewardFunction(rewardCode);
        
        if (rewardApiResult.status === 'error') {
          Swal.close();
          const errorMsg = rewardApiResult.error?.error_message || rewardApiResult.error || '보상 함수 검증 실패';
          await UI.showError('보상 함수 오류', errorMsg);
          return;
        }
        
        // 5. 훈련 시작
        UI.showLoading('훈련을 시작하고 있습니다...');
        
        const formData = FormState.collectFormData();
        console.log('[FormHandler] 전송 데이터:', formData);
        
        const result = await API.startTraining(formData);
        Swal.close();
        
        if (!result.ok) {
          if (result.status === 503) {
            await UI.showError('CPU 자원 부족', 'CPU 자원이 부족합니다. 기존 작업을 종료하세요.');
          } else {
            await UI.showError('오류', result.data?.detail || '훈련 시작에 실패했습니다.');
          }
          return;
        }
        
        // 6. 성공
        await UI.showSuccess('훈련이 시작되었습니다!', `Run ID: ${result.data.run_id}`);
        
        // 7. 리다이렉트
        const redirectUrl = result.data.redirect_url || `/pages/models/${encodeURIComponent(result.data.model_name || FormState.modelName)}`;
        window.location.href = redirectUrl;
        
      } catch (error) {
        console.error('[FormHandler] 에러:', error);
        Swal.close();
        await UI.showError('오류', error.message || '예상치 못한 오류가 발생했습니다.');
      } finally {
        FormState.isSubmitting = false;
        UI.setSubmitButtonState(false);
      }
    },
    
    // DOM에서 최신 값 동기화
    syncFromDOM() {
      // 모델 이름
      FormState.modelName = DOM.modelNameInput?.value?.trim() || '';
      
      // 액션 스페이스
      ActionSpace.syncToState();
      
      // 보상 함수
      FormState.rewardFunction = window.editor?.getValue() || '';
      
      // 하이퍼파라미터 (DOM에서 직접 읽기)
      const batchSize = document.getElementById('batchSize');
      if (batchSize) FormState.training.hyperparameters.batch_size = parseInt(batchSize.value);
      
      const discount = document.querySelector('input[name="discount_factor"]');
      if (discount) FormState.training.hyperparameters.discount_factor = parseFloat(discount.value);
      
      const lr = document.querySelector('input[name="learning_rate"]');
      if (lr) FormState.training.hyperparameters.learning_rate = parseFloat(lr.value);
      
      const entropy = document.querySelector('input[name="entropy"]');
      if (entropy) FormState.training.hyperparameters.entropy = parseFloat(entropy.value);
      
      const lossType = document.querySelector('input[name="loss_type"]:checked');
      if (lossType) FormState.training.hyperparameters.loss_type = lossType.value;
      
      const bestMetric = document.querySelector('input[name="best_model_metric"]:checked');
      if (bestMetric) FormState.training.best_model_metric = bestMetric.value;
      
      const maxTime = document.getElementById('max_training_time');
      if (maxTime) FormState.training.training_time_minutes = parseInt(maxTime.value) || 60;
      
      // 시뮬레이션 설정 동기화
      this.syncSimulationFromDOM();
    },
    
    // 시뮬레이션 DOM에서 동기화
    syncSimulationFromDOM() {
      // 메인 시뮬레이션
      this.syncTabFromDOM('tabs-main', FormState.simulation);
      
      // 서브 시뮬레이션
      for (let i = 0; i < FormState.subSimulationCount; i++) {
        if (!FormState.subSimulations[i]) {
          FormState.subSimulations[i] = SimulationTabs.createDefaultSimulation();
        }
        this.syncTabFromDOM(`tabs-sub${i + 1}`, FormState.subSimulations[i]);
      }
    },
    
    // 개별 탭 동기화
    syncTabFromDOM(tabId, simObj) {
      const suffix = tabId.replace('tabs-', '');
      const isMain = suffix === 'main';
      const pane = document.getElementById(tabId);
      if (!pane) return;
      
      // Direction
      const dirName = isMain ? 'clock-direction' : `clock-direction-${suffix}`;
      const dirRadio = pane.querySelector(`input[name="${dirName}"]:checked`);
      if (dirRadio) simObj.track_direction = dirRadio.value;
      
      // Race Type
      const raceTypeName = isMain ? 'race-type' : `race-type-${suffix}`;
      const raceTypeRadio = pane.querySelector(`input[name="${raceTypeName}"]:checked`);
      if (raceTypeRadio) simObj.race_type = raceTypeRadio.value.toUpperCase();
      
      // Alternate Direction
      const altId = isMain ? 'alternate-training-main' : `alternate-${suffix}`;
      const altCheckbox = document.getElementById(altId);
      if (altCheckbox) simObj.alternate_direction = altCheckbox.checked;
      
      // Object Avoidance 설정
      if (simObj.race_type === 'OBJECT_AVOIDANCE') {
        const numSelect = document.getElementById(isMain ? 'number-of-objects' : `number-of-objects-${suffix}`);
        const typeSelect = pane.querySelector(isMain ? 'select[name="object-type"]' : `select[name="object-type-${suffix}"]`);
        const posCheckbox = document.getElementById(isMain ? 'object-position' : `object-position-${suffix}`);
        
        simObj.object_avoidance = {
          object_type: typeSelect?.value || 'box_obstacle',
          number_of_objects: parseInt(numSelect?.value) || 3,
          randomize_locations: posCheckbox?.checked ?? true,
          object_locations: SimulationTabs.collectObjectLocations(tabId)
        };
      } else {
        simObj.object_avoidance = null;
      }
    }
  };

  // ============================================================
  // 11. 모델 이름 검증 모듈
  // ============================================================
  const ModelNameValidator = {
    checkTimeout: null,
    
    init() {
      if (!DOM.modelNameInput) return;
      
      DOM.modelNameInput.addEventListener('input', (e) => {
        this.handleInput(e.target.value);
      });
      
      DOM.modelNameInput.addEventListener('blur', (e) => {
        this.handleBlur(e.target.value);
      });
    },
    
    handleInput(value) {
      // 이전 타이머 취소
      if (this.checkTimeout) {
        clearTimeout(this.checkTimeout);
      }
      
      // 상태 초기화
      UI.showModelNameStatus('', '');
      UI.showModelNameSpinner(false);
      
      if (!value) return;
      
      // 정규식 검증
      const syncResult = Validation.validateModelName(value);
      if (!syncResult.valid) {
        UI.showModelNameStatus('invalid', syncResult.error);
        return;
      }
      
      // 서버 검증 (debounce)
      UI.showModelNameSpinner(true);
      
      this.checkTimeout = setTimeout(async () => {
        const serverResult = await API.checkModelName(value);
        UI.showModelNameSpinner(false);
        
        if (serverResult.available) {
          UI.showModelNameStatus('valid', '사용 가능한 이름입니다.');
          FormState.modelName = value;
        } else {
          UI.showModelNameStatus('invalid', '이미 존재하는 모델 이름입니다.');
        }
      }, 300);
    },
    
    handleBlur(value) {
      if (!value) {
        UI.showModelNameStatus('invalid', '모델 이름을 입력해주세요.');
      }
    }
  };

  // ============================================================
  // 12. 설정 로더 (기존 설정 불러오기)
  // ============================================================
  const SettingsLoader = {
    async load() {
      const settings = await API.loadSettings();
      if (!settings) return;
      
      // 시뮬레이션 설정
      if (settings.simulation) {
        this.applySimulation(settings.simulation);
      }
      
      // 차량 설정
      if (settings.vehicles) {
        this.applyVehicles(settings.vehicles);
      }
      
      // 하이퍼파라미터
      if (settings.hyperparameters) {
        this.applyHyperparameters(settings.hyperparameters);
      }
      
      // 보상 함수
      if (settings.reward_function) {
        this.applyRewardFunction(settings.reward_function);
      }
    },
    
    applySimulation(sim) {
      // 서브 시뮬레이션 수
      if (sim.sub_simulation_count !== undefined) {
        const count = Math.min(sim.sub_simulation_count, sim.max_sub_simulation_count || 6);
        FormState.subSimulationCount = count;
        
        const select = DOM.subSimCountSelect;
        if (select) {
          select.value = count.toString();
          select.dispatchEvent(new Event('change'));
        }
      }
      
      // 메인 시뮬레이션
      if (sim.main) {
        this.applyMainSimulation(sim.main);
      }
      
      // 서브 시뮬레이션
      if (sim.sub_simulations) {
        sim.sub_simulations.forEach((subSim, index) => {
          this.applySubSimulation(index, subSim);
        });
      }
      
      // Best Model Metric
      if (sim.best_model_metric) {
        FormState.training.best_model_metric = sim.best_model_metric;
        const radio = document.querySelector(`input[name="best_model_metric"][value="${sim.best_model_metric}"]`);
        if (radio) radio.checked = true;
      }
    },
    
    applyMainSimulation(main) {
      Object.assign(FormState.simulation, main);
      
      // 트랙
      if (main.track_id) {
        const trackInput = document.querySelector(`input[value="${main.track_id}"]`);
        if (trackInput) {
          const label = trackInput.closest('label');
          const img = label?.querySelector('img');
          UI.updateTrackPreview('tabs-main', {
            id: main.track_id,
            name: trackInput.dataset.trackName,
            image: img?.src,
            width: trackInput.dataset.trackWidth,
            length: trackInput.dataset.trackLength,
            direction: trackInput.dataset.trackDirection,
            description: trackInput.dataset.trackDescription
          });
        }
      }
      
      // Direction
      if (main.direction) {
        const radio = document.querySelector(`input[name="clock-direction"][value="${main.direction}"]`);
        if (radio) radio.checked = true;
      }
      
      // Race Type
      if (main.race_type) {
        const radio = document.querySelector(`input[name="race-type"][value="${main.race_type.toUpperCase()}"]`);
        if (radio) {
          radio.checked = true;
          UI.showObjectAvoidance('tabs-main', main.race_type.toUpperCase() === 'OBJECT_AVOIDANCE');
        }
      }
      
      // Alternate Direction
      const altCheckbox = document.getElementById('alternate-training-main');
      if (altCheckbox && main.alternate_direction !== undefined) {
        altCheckbox.checked = main.alternate_direction;
      }
      
      // Object Avoidance 설정 적용
      this.applyObjectAvoidance('tabs-main', main.object_avoidance);
    },
    
    applySubSimulation(index, subSim) {
      if (index >= FormState.subSimulations.length) return;
      Object.assign(FormState.subSimulations[index], subSim);
      
      const subKey = `sub${index + 1}`;
      
      // 트랙
      if (subSim.track_id) {
        const trackInput = document.querySelector(`input[value="${subSim.track_id}"]`);
        if (trackInput) {
          const label = trackInput.closest('label');
          const img = label?.querySelector('img');
          UI.updateTrackPreview(`tabs-${subKey}`, {
            id: subSim.track_id,
            name: trackInput.dataset.trackName,
            image: img?.src,
            width: trackInput.dataset.trackWidth,
            length: trackInput.dataset.trackLength,
            direction: trackInput.dataset.trackDirection,
            description: trackInput.dataset.trackDescription
          });
        }
      }
      
      // Direction
      if (subSim.direction) {
        const radio = document.querySelector(`input[name="clock-direction-${subKey}"][value="${subSim.direction}"]`);
        if (radio) radio.checked = true;
      }
      
      // Race Type
      if (subSim.race_type) {
        const radio = document.querySelector(`input[name="race-type-${subKey}"][value="${subSim.race_type.toUpperCase()}"]`);
        if (radio) {
          radio.checked = true;
          UI.showObjectAvoidance(`tabs-${subKey}`, subSim.race_type.toUpperCase() === 'OBJECT_AVOIDANCE');
        }
      }
      
      // Alternate Direction
      const altCheckbox = document.getElementById(`alternate-${subKey}`);
      if (altCheckbox && subSim.alternate_direction !== undefined) {
        altCheckbox.checked = subSim.alternate_direction;
      }
      
      // Object Avoidance 설정 적용
      this.applyObjectAvoidance(`tabs-${subKey}`, subSim.object_avoidance);
    },
    
    // Object Avoidance 설정을 DOM에 적용
    applyObjectAvoidance(tabId, oa) {
      if (!oa) return;
      
      const suffix = tabId.replace('tabs-', '');
      const isMain = suffix === 'main';
      
      // Number of Objects
      const numSelect = document.getElementById(isMain ? 'number-of-objects' : `number-of-objects-${suffix}`);
      if (numSelect && oa.number_of_obstacles !== undefined) {
        numSelect.value = oa.number_of_obstacles.toString();
      }
      
      // Object Type
      const typeSelect = document.querySelector(isMain ? 'select[name="object-type"]' : `select[name="object-type-${suffix}"]`);
      if (typeSelect && oa.object_type) {
        typeSelect.value = oa.object_type;
      }
      
      // Randomize Locations checkbox
      const posCheckbox = document.getElementById(isMain ? 'object-position' : `object-position-${suffix}`);
      if (posCheckbox && oa.randomize_locations !== undefined) {
        posCheckbox.checked = oa.randomize_locations;
      }
      
      // Object Locations wrapper 표시/숨김
      const locationWrapper = document.getElementById(isMain ? 'object-location-wrapper' : `object-location-wrapper-${suffix}`);
      if (locationWrapper) {
        if (oa.randomize_locations) {
          locationWrapper.classList.add('d-none');
        } else {
          locationWrapper.classList.remove('d-none');
          // Object Positions UI 렌더링
          this.renderObjectPositions(tabId, oa.object_positions || [], oa.number_of_obstacles || 3);
        }
      }
    },
    
    // Object Positions를 DOM에 렌더링
    renderObjectPositions(tabId, positions, count) {
      const suffix = tabId.replace('tabs-', '');
      const isMain = suffix === 'main';
      const wrapperId = isMain ? 'object-location-wrapper' : `object-location-wrapper-${suffix}`;
      const wrapper = document.getElementById(wrapperId);
      
      if (!wrapper) return;
      
      const innerContainer = wrapper.querySelector('.card-body');
      if (!innerContainer) return;
      
      innerContainer.innerHTML = '';
      
      const nameSuffix = isMain ? '' : `-${suffix}`;
      
      for (let i = 0; i < count; i++) {
        // positions 배열에서 값 가져오기 (없으면 기본값)
        const pos = positions[i] || {};
        const progressValue = pos.progress !== undefined ? pos.progress : ((100 / (count + 1)) * (i + 1)).toFixed(0);
        const laneValue = pos.lane || ((i + 1) % 2 === 1 ? 'inside' : 'outside');
        
        const block = document.createElement('div');
        block.className = 'obstable-block mb-2 p-2 border rounded bg-light';
        
        block.innerHTML = `
          <div class="d-flex align-items-center gap-2">
            <span class="fw-bold" style="min-width:40px;">${i}</span>
            <div class="d-flex align-items-center gap-1">
              <label class="form-label mb-0 small">Progress:</label>
              <input type="number" step="any" class="form-control form-control-sm progress-valid"
                     name="progress-${i + 1}${nameSuffix}" max="100" style="width:70px;"
                     oninput="this.value = Math.min(100, Math.max(0, this.value))"
                     value="${progressValue}">
              <span class="small">%</span>
            </div>
            <div class="d-flex align-items-center gap-1 ms-2">
              <label class="form-label mb-0 small">Lane:</label>
              <label class="form-check form-check-inline mb-0">
                <input class="form-check-input" type="radio" name="lane-${i + 1}${nameSuffix}" value="inside" ${laneValue === 'inside' ? 'checked' : ''}>
                <span class="form-check-label small">IN</span>
              </label>
              <label class="form-check form-check-inline mb-0">
                <input class="form-check-input" type="radio" name="lane-${i + 1}${nameSuffix}" value="outside" ${laneValue === 'outside' ? 'checked' : ''}>
                <span class="form-check-label small">OUT</span>
              </label>
            </div>
          </div>
        `;
        innerContainer.appendChild(block);
      }
    },
    
    applyVehicles(vehicles) {
      // Vehicle Type
      if (vehicles.vehicle_type) {
        FormState.vehicle.vehicle_type = vehicles.vehicle_type;
        const select = document.getElementById('vehicle-layout');
        if (select) {
          select.value = vehicles.vehicle_type;
          VehicleSettings.updateLidarState(vehicles.vehicle_type);
        }
      }
      
      // Lidar
      if (vehicles.lidar !== undefined) {
        FormState.vehicle.lidar = vehicles.lidar;
        const checkbox = document.getElementById('lidar-checkbox');
        if (checkbox) checkbox.checked = vehicles.lidar;
      }
      
      VehicleSettings.updateVehicleImage();
      
      // Action Space
      if (vehicles.action_space && Array.isArray(vehicles.action_space)) {
        FormState.vehicle.action_space = vehicles.action_space;
        ActionSpace.renderActions(vehicles.action_space);
      }
      
      // Max Training Time
      if (vehicles.max_training_time) {
        FormState.training.training_time_minutes = vehicles.max_training_time;
        const input = document.getElementById('max_training_time');
        if (input) input.value = vehicles.max_training_time;
      }
    },
    
    applyHyperparameters(hp) {
      Object.assign(FormState.training.hyperparameters, hp);
      
      // Batch Size
      if (hp.batch_size) {
        const select = document.getElementById('batchSize');
        if (select) select.value = hp.batch_size.toString();
      }
      
      // Discount Factor
      if (hp.discount_factor !== undefined) {
        const input = document.querySelector('input[name="discount_factor"]');
        if (input) input.value = hp.discount_factor;
      }
      
      // Learning Rate
      if (hp.learning_rate !== undefined) {
        const input = document.querySelector('input[name="learning_rate"]');
        if (input) input.value = hp.learning_rate;
      }
      
      // Entropy
      if (hp.entropy !== undefined) {
        const input = document.querySelector('input[name="entropy"]');
        if (input) input.value = hp.entropy;
      }
      
      // Loss Type
      if (hp.loss_type) {
        const radio = document.querySelector(`input[name="loss_type"][value="${hp.loss_type}"]`);
        if (radio) radio.checked = true;
      }
    },
    
    applyRewardFunction(code) {
      FormState.rewardFunction = code;
      
      if (window.editor) {
        window.editor.setValue(code);
      } else {
        // CodeMirror가 아직 로드되지 않은 경우
        const textarea = document.getElementById('editor');
        if (textarea) textarea.value = code;
        window.pendingRewardFunction = code;
      }
    }
  };

  // ============================================================
  // 13. Validate 버튼 모듈 (보상함수 검증)
  // ============================================================
  const RewardValidator = {
    validated: false,
    
    init() {
      const submitCodeBtn = document.getElementById('submitCodeBtn');
      const loadingSpinner = document.getElementById('loadingSpinner');
      const successIcon = document.getElementById('successIcon');
      const responseOutput = document.getElementById('responseOutput');
      
      if (!submitCodeBtn) return;
      
      submitCodeBtn.addEventListener('click', async () => {
        const code = window.editor?.getValue() || '';
        
        // 빈 코드 체크
        if (!code.trim()) {
          responseOutput.textContent = '보상 함수를 입력해주세요.';
          responseOutput.classList.remove('d-none');
          successIcon.classList.add('d-none');
          return;
        }
        
        // 로딩 상태
        loadingSpinner.classList.remove('d-none');
        submitCodeBtn.disabled = true;
        successIcon.classList.add('d-none');
        responseOutput.classList.add('d-none');
        
        try {
          const result = await API.validateRewardFunction(code);
          
          if (result.status === 'success') {
            // 성공
            this.validated = true;
            FormState.isRewardValidated = true;
            successIcon.classList.remove('d-none');
            responseOutput.classList.add('d-none');
          } else {
            // 실패
            this.validated = false;
            FormState.isRewardValidated = false;
            successIcon.classList.add('d-none');
            
            const errorMsg = result.error?.error_message || result.error || '보상 함수 검증에 실패했습니다.';
            responseOutput.textContent = errorMsg;
            responseOutput.classList.remove('d-none');
          }
        } catch (e) {
          this.validated = false;
          FormState.isRewardValidated = false;
          responseOutput.textContent = '오류: ' + e.message;
          responseOutput.classList.remove('d-none');
        } finally {
          loadingSpinner.classList.add('d-none');
          submitCodeBtn.disabled = false;
        }
      });
      
      // 에디터 변경 시 검증 상태 리셋
      if (window.editor) {
        window.editor.on('change', () => {
          this.validated = false;
          FormState.isRewardValidated = false;
          successIcon?.classList.add('d-none');
        });
      }
    }
  };

  // ============================================================
  // 14. 초기화
  // ============================================================
  async function init() {
    // DOM 요소 캐시
    DOM.init();
    
    // 모듈 초기화
    ModelNameValidator.init();
    SimulationTabs.init();
    VehicleSettings.init();
    TrainingSettings.init();
    ActionSpace.init();
    FormHandler.init();
    RewardValidator.init();
    
    // 설정 로드 (비동기)
    await SettingsLoader.load();
    
    console.log('[CreateModel] 초기화 완료');
  }
  
  // DOMContentLoaded 이벤트
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
  
  // 전역 노출 (디버깅용 + 호환성)
  window.CreateModel = {
    FormState,
    ActionSpace,
    SimulationTabs,
    FormHandler,
    RewardValidator
  };
  
  // 기존 코드 호환성 (window.collectFormData)
  window.collectFormData = () => {
    FormHandler.syncFromDOM();
    return FormState.collectFormData();
  };
  
})();
