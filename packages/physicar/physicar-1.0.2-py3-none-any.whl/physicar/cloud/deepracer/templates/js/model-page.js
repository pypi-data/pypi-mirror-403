/**
 * Model Page - 모델 상세/모니터링 페이지 JavaScript
 * 
 * 구조:
 * 1. State - 전역 상태 관리
 * 2. API - 서버 통신
 * 3. UI - DOM 조작
 * 4. Charts - Chart.js 래퍼
 * 5. Stream - 실시간 스트림 관리
 * 6. Training - 훈련 탭 로직
 * 7. Evaluation - 평가 탭 로직
 * 8. Init - 초기화
 */
(function() {
  'use strict';
  
  // ============================================================
  // 1. 전역 상태
  // ============================================================
  const State = {
    modelName: '',
    
    // 상태: ready, training, evaluating, failed
    status: 'unknown',
    isTraining: false,
    isEvaluating: false,
    
    // 훈련 시간
    trainingStartTime: null,
    trainingElapsedSeconds: 0,
    maxTrainingMinutes: null,
    
    // 폴링
    pollingInterval: null,
    pollingRate: 5000,
    
    // 훈련 타이머
    trainingTimerId: null,
    
    // 현재 활성 탭
    activePageTab: 'training',  // training | evaluation
    activeSimTab: 'main',       // main | sub1 | sub2 | ...
    
    // 스트림 URL 캐시
    streamUrls: null,
    
    // 차트 인스턴스
    charts: {
      main: { reward: null, progress: null },
      sub1: { reward: null, progress: null },
      sub2: { reward: null, progress: null },
      sub3: { reward: null, progress: null },
      sub4: { reward: null, progress: null },
      sub5: { reward: null, progress: null },
      sub6: { reward: null, progress: null }
    },
    
    // 차트 설정
    numEpisodesBetweenTraining: 10,
    bestCheckpointIteration: null,
    bestModelMetric: 'progress',
    
    // 서브 시뮬레이션 수
    subSimulationCount: 0,
    
    // 모델 정보 로드 완료 여부
    infoLoaded: false,
    
    // 평가용
    evalTracksLoaded: false,
    evalPollingId: null,
    evalStartedAt: null,
    evalElapsedTimerId: null,
    modelTrackId: null,
  };
  
  // ============================================================
  // 2. API 모듈
  // ============================================================
  const API = {
    timeout: 10000,
    
    async fetch(url, options = {}) {
      const controller = new AbortController();
      const id = setTimeout(() => controller.abort(), this.timeout);
      try {
        const res = await fetch(url, { ...options, signal: controller.signal });
        clearTimeout(id);
        return res;
      } catch (e) {
        clearTimeout(id);
        throw e;
      }
    },
    
    async getStatus() {
      try {
        const res = await this.fetch(`/api/models/${State.modelName}/status`);
        if (!res.ok) return null;
        return await res.json();
      } catch (e) {
        console.error('[API] getStatus error:', e);
        return null;
      }
    },
    
    async getInfo() {
      try {
        const res = await this.fetch(`/api/models/${State.modelName}/info`);
        if (!res.ok) return null;
        return await res.json();
      } catch (e) {
        console.error('[API] getInfo error:', e);
        return null;
      }
    },
    
    async getMetrics(worker = 0) {
      try {
        const res = await this.fetch(`/api/models/${State.modelName}/training/metrics?worker=${worker}`);
        if (!res.ok) return null;
        return await res.json();
      } catch (e) {
        console.error('[API] getMetrics error:', e);
        return null;
      }
    },
    
    async getTrainingView() {
      try {
        const res = await this.fetch(`/api/models/${State.modelName}/training/view`, {
          cache: 'no-store',
          headers: { 'Cache-Control': 'no-cache', 'Pragma': 'no-cache' }
        });
        if (!res.ok) return null;
        return await res.json();
      } catch (e) {
        console.error('[API] getTrainingView error:', e);
        return null;
      }
    },
    
    async getRewardFunction() {
      try {
        const res = await this.fetch(`/api/models/${State.modelName}/reward_function`);
        if (!res.ok) return null;
        return await res.json();
      } catch (e) {
        console.error('[API] getRewardFunction error:', e);
        return null;
      }
    },
    
    async getPhysicalCarStatus() {
      try {
        const res = await this.fetch(`/api/models/${State.modelName}/physical-car-model/status`);
        if (!res.ok) return null;
        return await res.json();
      } catch (e) {
        console.error('[API] getPhysicalCarStatus error:', e);
        return null;
      }
    },
    
    async stopTraining() {
      try {
        // stop은 시간이 오래 걸릴 수 있으므로 타임아웃 없이 직접 fetch
        const res = await fetch(`/api/models/${State.modelName}/stop`, { method: 'POST' });
        return res.ok;
      } catch (e) {
        console.error('[API] stopTraining error:', e);
        return false;
      }
    },
    
    async getTracks() {
      try {
        const res = await this.fetch('/api/tracks');
        if (!res.ok) return null;
        return await res.json();
      } catch (e) {
        console.error('[API] getTracks error:', e);
        return null;
      }
    },
    
    async getEvaluationStatus() {
      try {
        const res = await this.fetch(`/api/models/${State.modelName}/evaluation/status`);
        if (!res.ok) return null;
        return await res.json();
      } catch (e) {
        console.error('[API] getEvaluationStatus error:', e);
        return null;
      }
    },
    
    async getEvaluationHistory() {
      try {
        const res = await this.fetch(`/api/models/${State.modelName}/evaluations`);
        if (!res.ok) return null;
        return await res.json();
      } catch (e) {
        console.error('[API] getEvaluationHistory error:', e);
        return null;
      }
    },
    
    async getEvaluationDetail(evalId) {
      try {
        const res = await this.fetch(`/api/models/${State.modelName}/evaluation/${evalId}`);
        if (!res.ok) return null;
        return await res.json();
      } catch (e) {
        console.error('[API] getEvaluationDetail error:', e);
        return null;
      }
    },
    
    async stopEvaluation(runId) {
      try {
        const res = await this.fetch(`/api/evaluation/${runId}/stop`, { method: 'POST' });
        return res.ok;
      } catch (e) {
        console.error('[API] stopEvaluation error:', e);
        return false;
      }
    }
  };
  
  // ============================================================
  // 3. UI 모듈
  // ============================================================
  const UI = {
    // DOM 캐시
    elements: {},
    
    init() {
      this.elements = {
        statusBadge: document.getElementById('training-status-badge'),
        trainingTime: document.getElementById('training-time-value'),
        maxTrainingTime: document.getElementById('max-training-time-display'),
        stopBtn: document.getElementById('stop-training-btn'),
        trainingWrapper: document.getElementById('training-wrapper'),
        evaluationWrapper: document.getElementById('evaluation-wrapper'),
        trainingTimeRow: document.getElementById('training-time'),
        trainingTab: document.getElementById('training-tab'),
        evaluationTab: document.getElementById('evaluation-tab'),
        simulationTabs: document.getElementById('simulation-tabs'),
        rewardFunctionCode: document.getElementById('reward-function-content'),
      };
    },
    
    updateStatusBadge(status) {
      const badge = this.elements.statusBadge;
      if (!badge) return;
      
      badge.className = '';
      badge.textContent = status || 'unknown';
      badge.classList.add(status || 'unknown');
      badge.style.display = 'inline-block';
      
      // Stop 버튼 표시
      const stopBtn = this.elements.stopBtn;
      if (stopBtn) {
        stopBtn.style.display = (status === 'training' || status === 'evaluating') ? 'inline-block' : 'none';
      }
      
      // Actions 메뉴 활성화/비활성화
      const startEvalMenu = document.getElementById('start-eval-menu');
      const cloneModelMenu = document.getElementById('clone-model-menu');
      
      // Start Evaluation: ready 상태일 때만 활성화
      if (startEvalMenu) {
        if (status === 'ready') {
          startEvalMenu.classList.remove('disabled');
          startEvalMenu.style.pointerEvents = '';
          startEvalMenu.style.opacity = '';
        } else {
          startEvalMenu.classList.add('disabled');
          startEvalMenu.style.pointerEvents = 'none';
          startEvalMenu.style.opacity = '0.5';
        }
      }
      
      // Clone Model: ready 또는 evaluating 상태일 때만 활성화
      if (cloneModelMenu) {
        if (status === 'ready' || status === 'evaluating') {
          cloneModelMenu.classList.remove('disabled');
          cloneModelMenu.style.pointerEvents = '';
          cloneModelMenu.style.opacity = '';
        } else {
          cloneModelMenu.classList.add('disabled');
          cloneModelMenu.style.pointerEvents = 'none';
          cloneModelMenu.style.opacity = '0.5';
        }
      }
    },
    
    updateTrainingTime(seconds) {
      const el = this.elements.trainingTime;
      if (!el) return;
      el.textContent = this.formatDuration(seconds);
    },
    
    updateMaxTrainingTime(minutes) {
      const el = this.elements.maxTrainingTime;
      if (!el) return;
      if (minutes == null) {
        el.textContent = '';
        return;
      }
      const h = Math.floor(minutes / 60);
      const m = minutes % 60;
      el.textContent = `/ ${h}:${String(m).padStart(2, '0')}:00`;
    },
    
    formatDuration(seconds) {
      if (isNaN(seconds) || seconds < 0) return '--:--:--';
      const h = Math.floor(seconds / 3600);
      const m = Math.floor((seconds % 3600) / 60);
      const s = Math.floor(seconds % 60);
      return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
    },
    
    showPageTab(tab, updateHash = true) {
      const { trainingWrapper, evaluationWrapper, trainingTimeRow, trainingTab, evaluationTab } = this.elements;
      
      if (tab === 'training') {
        trainingWrapper.style.display = 'block';
        evaluationWrapper.style.display = 'none';
        trainingTimeRow.style.display = 'block';
        trainingTab.classList.add('active');
        evaluationTab.classList.remove('active');
      } else {
        trainingWrapper.style.display = 'none';
        evaluationWrapper.style.display = 'block';
        trainingTimeRow.style.display = 'none';
        trainingTab.classList.remove('active');
        evaluationTab.classList.add('active');
      }
      State.activePageTab = tab;
      
      // URL 해시 업데이트 (뒤로가기/앞으로가기 지원)
      if (updateHash && window.location.hash !== `#${tab}`) {
        history.pushState(null, '', `#${tab}`);
      }
    },
    
    getTabFromHash() {
      const hash = window.location.hash.toLowerCase();
      if (hash === '#evaluation') return 'evaluation';
      return 'training';  // 기본값 또는 #training
    },
    
    updateSubSimTabs(count) {
      State.subSimulationCount = count;
      for (let i = 1; i <= 6; i++) {
        const tabItem = document.getElementById(`tab-item-sub${i}`);
        if (tabItem) {
          tabItem.classList.toggle('d-none', i > count);
        }
      }
    },
    
    updateSimulationInfo(simKey, data) {
      if (!data) return;
      
      const setText = (id, value) => {
        const el = document.getElementById(id);
        if (el) el.textContent = value || '-';
      };
      
      const setDisplay = (id, show) => {
        const el = document.getElementById(id);
        if (el) el.style.display = show ? 'block' : 'none';
      };
      
      setText(`sim-${simKey}-track-name`, data.track_name || data.track_id);
      setText(`sim-${simKey}-direction`, data.direction);
      setText(`sim-${simKey}-alternate`, data.alternate_direction ? 'Enabled' : 'Disabled');
      setText(`sim-${simKey}-race-type`, data.race_type);
      
      // 트랙 썸네일
      const thumbnail = document.getElementById(`sim-${simKey}-thumbnail`);
      if (thumbnail && data.thumbnail) {
        thumbnail.src = `/static/tracks/thumbnail/${data.thumbnail}`;
        thumbnail.style.display = 'block';
      }
      
      // Object Avoidance 설정
      if (data.race_type === 'OBJECT_AVOIDANCE') {
        setDisplay(`sim-${simKey}-oa-card`, true);
        setText(`sim-${simKey}-object-type`, data.obstacle_type);
        setText(`sim-${simKey}-num-objects`, data.number_of_obstacles);
        setText(`sim-${simKey}-randomize`, data.randomize_obstacles ? 'Enabled' : 'Disabled');
        
        // Object Positions
        const posCard = document.getElementById(`sim-${simKey}-positions-card`);
        const posTable = document.getElementById(`sim-${simKey}-positions`);
        if (!data.randomize_obstacles && data.object_positions?.length > 0) {
          if (posCard) posCard.style.display = 'block';
          if (posTable) {
            posTable.innerHTML = data.object_positions.map((p, i) =>
              `<tr><td>${i}</td><td>${Math.round(p.progress * 100)}</td><td>${p.lane === 1 ? 'Inside' : 'Outside'}</td></tr>`
            ).join('');
          }
        } else if (posCard) {
          posCard.style.display = 'none';
        }
      } else {
        setDisplay(`sim-${simKey}-oa-card`, false);
      }
    },
    
    updateVehicleInfo(data) {
      if (!data) return;
      
      document.getElementById('vehicle-type').textContent = data.vehicle_type || 'deepracer';
      
      const sensors = data.sensor || [];
      let sensorText = sensors.includes('FRONT_FACING_CAMERA') ? 'Camera' : '';
      if (sensors.includes('SECTOR_LIDAR')) {
        sensorText += sensorText ? ' + LIDAR' : 'LIDAR';
      }
      document.getElementById('vehicle-sensor').textContent = sensorText || '-';
      document.getElementById('vehicle-action-space-type').textContent = data.action_space_type || 'discrete';
      
      const actionSpace = data.action_space || [];
      const tbody = document.getElementById('action-space-table');
      if (tbody && actionSpace.length > 0) {
        tbody.innerHTML = actionSpace.map((a, i) =>
          `<tr><td>${i}</td><td>${a.steering_angle}°</td><td>${a.speed}</td></tr>`
        ).join('');
      }
    },
    
    updateHyperparameters(data) {
      if (!data) return;
      document.getElementById('batch-size').textContent = data.batch_size || '-';
      document.getElementById('discount-factor').textContent = data.discount_factor || '-';
      document.getElementById('learning-rate').textContent = data.lr || '-';
      document.getElementById('loss-type').textContent = data.loss_type || '-';
      document.getElementById('entropy').textContent = data.beta_entropy || '-';
    },
    
    updateTrainingSettings(bestMetric, maxTime) {
      document.getElementById('best-model-metric').textContent = bestMetric || '-';
      document.getElementById('max-training-time').textContent = maxTime ? `${maxTime} min` : '-';
    },
    
    updateRewardFunction(code) {
      const el = this.elements.rewardFunctionCode;
      if (!el || !code) return;
      el.textContent = code;
      if (window.hljs) {
        window.hljs.highlightElement(el);
      }
    },
    
    updatePhysicalCarMenu(bestExists, lastExists) {
      const submenu = document.getElementById('physical-car-submenu');
      if (!submenu) return;
      
      // 각 아이템 활성화/비활성화 업데이트
      submenu.querySelectorAll('.physical-car-item').forEach(item => {
        const type = item.getAttribute('data-type');
        const exists = type === 'best' ? bestExists : lastExists;
        if (exists) {
          item.classList.remove('disabled', 'text-muted');
          item.style.pointerEvents = '';
        } else {
          item.classList.add('disabled', 'text-muted');
          item.style.pointerEvents = 'none';
        }
      });
      
      // 메인 메뉴 활성화/비활성화
      const menu = document.getElementById('download-physical-car-menu');
      if (menu) {
        if (bestExists || lastExists) {
          menu.classList.remove('disabled', 'text-muted');
          menu.style.pointerEvents = '';
        } else {
          menu.classList.add('disabled', 'text-muted');
          menu.style.pointerEvents = 'none';
        }
      }
    }
  };
  
  // ============================================================
  // 4. Charts 모듈
  // ============================================================
  const Charts = {
    getOptions(yLabel, isProgress) {
      return {
        responsive: true,
        maintainAspectRatio: false,
        animation: false,
        interaction: { mode: 'nearest', intersect: false },
        layout: { padding: { top: 5, right: 10, bottom: 0, left: 0 } },
        scales: {
          x: {
            type: 'linear',
            title: { display: true, text: 'Iteration', font: { size: 11 } },
            ticks: { font: { size: 10 } }
          },
          y: {
            title: { display: true, text: yLabel, font: { size: 11, weight: 'bold' } },
            min: 0,
            max: isProgress ? 100 : undefined,
            ticks: { font: { size: 10 } }
          }
        },
        plugins: {
          legend: {
            display: true,
            position: 'top',
            align: 'start',
            labels: { usePointStyle: true, boxWidth: 6, boxHeight: 6, padding: 8, font: { size: 9 } }
          }
        }
      };
    },
    
    getBestCheckpointPlugin() {
      return {
        id: 'bestCheckpointLine',
        afterDraw: (chart) => {
          if (State.bestCheckpointIteration === null) return;
          
          const ctx = chart.ctx;
          const xScale = chart.scales.x;
          const yScale = chart.scales.y;
          const x = xScale.getPixelForValue(State.bestCheckpointIteration);
          
          ctx.save();
          ctx.strokeStyle = 'red';
          ctx.lineWidth = 1;
          ctx.setLineDash([5, 5]);
          ctx.beginPath();
          ctx.moveTo(x, yScale.top);
          ctx.lineTo(x, yScale.bottom);
          ctx.stroke();
          ctx.setLineDash([]);
          ctx.fillStyle = 'red';
          ctx.font = '10px sans-serif';
          ctx.textAlign = 'left';
          ctx.fillText('Best Checkpoint', x + 3, yScale.top + 12);
          ctx.restore();
        }
      };
    },
    
    initMain() {
      const rewardCtx = document.getElementById('reward-chart-main');
      const progressCtx = document.getElementById('progress-chart-main');
      if (!rewardCtx || !progressCtx) return;
      
      const plugin = this.getBestCheckpointPlugin();
      
      State.charts.main.reward = new Chart(rewardCtx, {
        type: 'scatter',
        data: {
          datasets: [
            { label: 'reward (training)', data: [], backgroundColor: 'rgba(31,119,180,0.3)', borderColor: 'transparent', pointRadius: 3, order: 2 },
            { label: 'reward (training) avg', data: [], type: 'line', borderColor: '#1f77b4', backgroundColor: 'transparent', borderWidth: 2, pointRadius: 0, tension: 0.1, order: 1, showLine: true },
            { label: 'reward (evaluation)', data: [], backgroundColor: 'rgba(214,39,40,0.3)', borderColor: 'transparent', pointRadius: 3, order: 2 },
            { label: 'reward (evaluation) avg', data: [], type: 'line', borderColor: '#d62728', backgroundColor: 'transparent', borderWidth: 2, pointRadius: 0, tension: 0.1, order: 1, showLine: true }
          ]
        },
        options: this.getOptions('Reward', false),
        plugins: [plugin]
      });
      
      State.charts.main.progress = new Chart(progressCtx, {
        type: 'scatter',
        data: {
          datasets: [
            { label: 'progress (training)', data: [], backgroundColor: 'rgba(31,119,180,0.3)', borderColor: 'transparent', pointRadius: 3, order: 2 },
            { label: 'progress (training) avg', data: [], type: 'line', borderColor: '#1f77b4', backgroundColor: 'transparent', borderWidth: 2, pointRadius: 0, tension: 0.1, order: 1, showLine: true },
            { label: 'progress (evaluation)', data: [], backgroundColor: 'rgba(214,39,40,0.3)', borderColor: 'transparent', pointRadius: 3, order: 2 },
            { label: 'progress (evaluation) avg', data: [], type: 'line', borderColor: '#d62728', backgroundColor: 'transparent', borderWidth: 2, pointRadius: 0, tension: 0.1, order: 1, showLine: true }
          ]
        },
        options: this.getOptions('Progress (completion) %', true),
        plugins: [plugin]
      });
    },
    
    initSub(simKey) {
      if (State.charts[simKey]?.reward) return;
      
      const rewardCtx = document.getElementById(`reward-chart-${simKey}`);
      const progressCtx = document.getElementById(`progress-chart-${simKey}`);
      if (!rewardCtx || !progressCtx) return;
      
      const plugin = this.getBestCheckpointPlugin();
      
      State.charts[simKey] = {
        reward: new Chart(rewardCtx, {
          type: 'scatter',
          data: {
            datasets: [
              { label: 'reward (training)', data: [], backgroundColor: 'rgba(31,119,180,0.3)', borderColor: 'transparent', pointRadius: 3, order: 2 },
              { label: 'reward (training) avg', data: [], type: 'line', borderColor: '#1f77b4', backgroundColor: 'transparent', borderWidth: 2, pointRadius: 0, tension: 0.1, order: 1, showLine: true }
            ]
          },
          options: this.getOptions('Reward', false),
          plugins: [plugin]
        }),
        progress: new Chart(progressCtx, {
          type: 'scatter',
          data: {
            datasets: [
              { label: 'progress (training)', data: [], backgroundColor: 'rgba(31,119,180,0.3)', borderColor: 'transparent', pointRadius: 3, order: 2 },
              { label: 'progress (training) avg', data: [], type: 'line', borderColor: '#1f77b4', backgroundColor: 'transparent', borderWidth: 2, pointRadius: 0, tension: 0.1, order: 1, showLine: true }
            ]
          },
          options: this.getOptions('Progress (completion) %', true),
          plugins: [plugin]
        })
      };
    },
    
    movingAverage(data, window) {
      const result = [];
      for (let i = 0; i < data.length; i++) {
        const start = Math.max(0, i - window + 1);
        const slice = data.slice(start, i + 1);
        result.push(slice.reduce((a, b) => a + b, 0) / slice.length);
      }
      return result;
    },
    
    updateMain(metrics, bestModelMetric) {
      const { reward, progress } = State.charts.main;
      if (!reward || !progress || !metrics?.length) return;
      
      const n = State.numEpisodesBetweenTraining;
      
      const training = metrics.filter(m => m.phase === 'training');
      const evaluation = metrics.filter(m => m.phase === 'evaluation');
      
      // Scatter 데이터
      const trainRewardScatter = training.map(m => ({ x: m.episode / n, y: m.reward_score }));
      const trainProgressScatter = training.map(m => ({ x: m.episode / n, y: m.completion_percentage }));
      const evalRewardScatter = evaluation.map(m => ({ x: m.episode / n, y: m.reward_score }));
      const evalProgressScatter = evaluation.map(m => ({ x: m.episode / n, y: m.completion_percentage }));
      
      // Training 이동평균
      const sortedTrain = [...training].sort((a, b) => a.episode - b.episode);
      const trainRewardMA = this.movingAverage(sortedTrain.map(m => m.reward_score), 10);
      const trainProgressMA = this.movingAverage(sortedTrain.map(m => m.completion_percentage), 10);
      const trainRewardLine = sortedTrain.map((m, i) => ({ x: m.episode / n, y: trainRewardMA[i] }));
      const trainProgressLine = sortedTrain.map((m, i) => ({ x: m.episode / n, y: trainProgressMA[i] }));
      
      // Evaluation 평균 (iteration별)
      const evalByIter = {};
      evaluation.forEach(m => {
        const iter = Math.floor(m.episode / n);
        if (!evalByIter[iter]) evalByIter[iter] = { rewards: [], progress: [] };
        evalByIter[iter].rewards.push(m.reward_score);
        evalByIter[iter].progress.push(m.completion_percentage);
      });
      const evalIters = Object.keys(evalByIter).map(Number).sort((a, b) => a - b);
      const evalRewardLine = evalIters.map(iter => ({
        x: iter,
        y: evalByIter[iter].rewards.reduce((a, b) => a + b, 0) / evalByIter[iter].rewards.length
      }));
      const evalProgressLine = evalIters.map(iter => ({
        x: iter,
        y: evalByIter[iter].progress.reduce((a, b) => a + b, 0) / evalByIter[iter].progress.length
      }));
      
      // Best checkpoint 계산
      if (evalIters.length > 0) {
        if (bestModelMetric === 'reward') {
          let max = -Infinity, bestIter = null;
          evalRewardLine.forEach(p => { if (p.y > max) { max = p.y; bestIter = p.x; } });
          State.bestCheckpointIteration = bestIter;
        } else {
          let max = -Infinity, bestIter = null;
          evalProgressLine.forEach(p => { if (p.y > max) { max = p.y; bestIter = p.x; } });
          State.bestCheckpointIteration = bestIter;
        }
        State.bestModelMetric = bestModelMetric;
      }
      
      // Reward 차트 업데이트
      reward.data.datasets[0].data = trainRewardScatter;
      reward.data.datasets[1].data = trainRewardLine;
      reward.data.datasets[2].data = evalRewardScatter;
      reward.data.datasets[3].data = evalRewardLine;
      reward.update('none');
      
      // Progress 차트 업데이트
      progress.data.datasets[0].data = trainProgressScatter;
      progress.data.datasets[1].data = trainProgressLine;
      progress.data.datasets[2].data = evalProgressScatter;
      progress.data.datasets[3].data = evalProgressLine;
      progress.update('none');
    },
    
    updateSub(simKey, metrics) {
      const charts = State.charts[simKey];
      if (!charts?.reward || !metrics?.length) return;
      
      const n = State.numEpisodesBetweenTraining;
      const training = metrics.filter(m => m.phase === 'training');
      
      const sorted = [...training].sort((a, b) => a.episode - b.episode);
      const rewardScatter = sorted.map(m => ({ x: m.episode / n, y: m.reward_score }));
      const progressScatter = sorted.map(m => ({ x: m.episode / n, y: m.completion_percentage }));
      const rewardMA = this.movingAverage(sorted.map(m => m.reward_score), 10);
      const progressMA = this.movingAverage(sorted.map(m => m.completion_percentage), 10);
      const rewardLine = sorted.map((m, i) => ({ x: m.episode / n, y: rewardMA[i] }));
      const progressLine = sorted.map((m, i) => ({ x: m.episode / n, y: progressMA[i] }));
      
      charts.reward.data.datasets[0].data = rewardScatter;
      charts.reward.data.datasets[1].data = rewardLine;
      charts.reward.update('none');
      
      charts.progress.data.datasets[0].data = progressScatter;
      charts.progress.data.datasets[1].data = progressLine;
      charts.progress.update('none');
    }
  };
  
  // ============================================================
  // 5. Stream 모듈
  // ============================================================
  const Stream = {
    getLoadingHtml(message = 'Please wait...') {
      return `
        <div>
          <div class="loading-spinner">
            <svg viewBox="25 25 50 50"><circle cx="50" cy="50" r="20"></circle></svg>
          </div>
          <div>${message}</div>
        </div>
      `;
    },
    
    getNotTrainingHtml() {
      return `
        <div class="training-complete" style="height:200px;">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#6c7a91" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:40px;height:40px;">
            <rect x="2" y="2" width="20" height="20" rx="2.18" ry="2.18"></rect>
            <line x1="7" y1="2" x2="7" y2="22"></line>
            <line x1="17" y1="2" x2="17" y2="22"></line>
            <line x1="2" y1="12" x2="22" y2="12"></line>
            <line x1="2" y1="7" x2="7" y2="7"></line>
            <line x1="2" y1="17" x2="7" y2="17"></line>
            <line x1="17" y1="17" x2="22" y2="17"></line>
            <line x1="17" y1="7" x2="22" y2="7"></line>
          </svg>
          <div class="training-complete-text" style="color:#6c7a91; margin-top:12px;">스트림은 훈련 중에만 볼 수 있습니다</div>
        </div>
      `;
    },
    
    showLoading(simKey, message) {
      const html = this.getLoadingHtml(message);
      this._updateElements(simKey, { loading: html, hideImg: true });
    },
    
    showNotTraining(simKey) {
      const html = this.getNotTrainingHtml();
      this._updateElements(simKey, { loading: html, hideImg: true });
    },
    
    showStream(simKey, urls) {
      const ts = Date.now();
      const addTs = (url) => url + (url.includes('?') ? '&' : '?') + '_t=' + ts;
      
      if (simKey === 'main') {
        this._setupImage('training-image-1', 'training-image-1-loading', urls.chase_overlay, addTs);
        this._setupImage('training-image-2', 'training-image-2-loading', urls.front, addTs);
      } else {
        this._setupImage(`training-image-${simKey}-chase`, `training-image-${simKey}-chase-loading`, urls.chase_overlay, addTs);
        this._setupImage(`training-image-${simKey}-front`, `training-image-${simKey}-front-loading`, urls.front, addTs);
      }
    },
    
    stopStream(simKey) {
      if (simKey === 'main') {
        this._clearImage('training-image-1');
        this._clearImage('training-image-2');
      } else {
        this._clearImage(`training-image-${simKey}-chase`);
        this._clearImage(`training-image-${simKey}-front`);
      }
    },
    
    _setupImage(imgId, loadingId, url, addTs) {
      const img = document.getElementById(imgId);
      const loading = document.getElementById(loadingId);
      if (!img || !url) return;
      
      img.onerror = () => {
        img.src = '';
        img.style.display = 'none';
        if (loading) loading.style.display = 'flex';
      };
      img.onload = () => {
        img.style.display = 'block';
        if (loading) loading.style.display = 'none';
      };
      
      const isVisible = img.style.display === 'block' && img.src;
      if (!isVisible) {
        img.src = addTs(url);
      }
    },
    
    _clearImage(imgId) {
      const img = document.getElementById(imgId);
      if (img) img.src = '';
    },
    
    _updateElements(simKey, { loading, hideImg }) {
      if (simKey === 'main') {
        const img1 = document.getElementById('training-image-1');
        const img2 = document.getElementById('training-image-2');
        const load1 = document.getElementById('training-image-1-loading');
        const load2 = document.getElementById('training-image-2-loading');
        if (hideImg) {
          if (img1) { img1.style.display = 'none'; img1.src = ''; }
          if (img2) { img2.style.display = 'none'; img2.src = ''; }
        }
        if (loading) {
          if (load1) { load1.style.display = 'flex'; load1.innerHTML = loading; }
          if (load2) { load2.style.display = 'flex'; load2.innerHTML = loading; }
        }
      } else {
        const chase = document.getElementById(`training-image-${simKey}-chase`);
        const front = document.getElementById(`training-image-${simKey}-front`);
        const chaseLoad = document.getElementById(`training-image-${simKey}-chase-loading`);
        const frontLoad = document.getElementById(`training-image-${simKey}-front-loading`);
        if (hideImg) {
          if (chase) { chase.style.display = 'none'; chase.src = ''; }
          if (front) { front.style.display = 'none'; front.src = ''; }
        }
        if (loading) {
          if (chaseLoad) { chaseLoad.style.display = 'flex'; chaseLoad.innerHTML = loading; }
          if (frontLoad) { frontLoad.style.display = 'flex'; frontLoad.innerHTML = loading; }
        }
      }
    }
  };
  
  // ============================================================
  // 6. Training 모듈
  // ============================================================
  const Training = {
    autoStopTriggered: false,
    
    async loadStatus() {
      const data = await API.getStatus();
      if (!data) return null;
      
      State.status = data.status;
      State.isTraining = data.is_training;
      State.isEvaluating = data.is_evaluating;
      if (data.max_training_time_minutes != null) {
        State.maxTrainingMinutes = data.max_training_time_minutes;
      }
      
      UI.updateStatusBadge(data.status);
      UI.updateMaxTrainingTime(State.maxTrainingMinutes);
      
      // 훈련 시간
      if (data.is_training && data.elapsed_seconds != null) {
        this.startTrainingTimer(data.elapsed_seconds);
      } else if (data.training_time_seconds != null) {
        this.stopTrainingTimer();
        UI.updateTrainingTime(data.training_time_seconds);
      }
      
      // 자동 정지
      if (data.should_stop && !this.autoStopTriggered && data.is_training) {
        this.autoStopTriggered = true;
        console.log('[Training] Max time exceeded, auto-stopping...');
        await API.stopTraining();
      }
      
      return data;
    },
    
    async loadMetrics() {
      const data = await API.getMetrics(0);
      if (!data?.metrics?.length) return null;
      
      if (data.num_episodes_between_training) {
        State.numEpisodesBetweenTraining = data.num_episodes_between_training;
      }
      
      Charts.updateMain(data.metrics, data.best_model_metric);
      return data;
    },
    
    async loadSubMetrics(workerNum) {
      const data = await API.getMetrics(workerNum);
      if (!data?.metrics?.length) return null;
      
      Charts.updateSub(`sub${workerNum}`, data.metrics);
      return data;
    },
    
    async loadView() {
      // 훈련 중이 아니면 API 호출 안함
      if (State.status !== 'training' && State.status !== 'unknown') {
        Stream.showNotTraining('main');
        for (let i = 1; i <= 6; i++) Stream.showNotTraining(`sub${i}`);
        return null;
      }
      
      const data = await API.getTrainingView();
      if (!data) {
        if (State.status === 'training') {
          Stream.showLoading('main', 'Waiting...');
        } else {
          Stream.showNotTraining('main');
        }
        return null;
      }
      
      State.streamUrls = data.view_urls;
      
      if (data.is_training && data.view_urls) {
        const activeUrls = data.view_urls[State.activeSimTab];
        if (activeUrls) {
          Stream.showStream(State.activeSimTab, activeUrls);
        } else {
          Stream.showLoading(State.activeSimTab, 'Starting simulation...');
        }
      } else if (data.is_training) {
        Stream.showLoading('main', 'Starting simulation...');
      } else {
        Stream.showNotTraining('main');
        for (let i = 1; i <= 6; i++) Stream.showNotTraining(`sub${i}`);
      }
      
      return data;
    },
    
    startTrainingTimer(baseSeconds) {
      this.stopTrainingTimer();
      
      const startTick = Date.now();
      const tick = () => {
        const clientElapsed = (Date.now() - startTick) / 1000;
        UI.updateTrainingTime(baseSeconds + clientElapsed);
      };
      tick();
      State.trainingTimerId = setInterval(tick, 1000);
    },
    
    stopTrainingTimer() {
      if (State.trainingTimerId) {
        clearInterval(State.trainingTimerId);
        State.trainingTimerId = null;
      }
    },
    
    startPolling() {
      if (State.pollingInterval) return;
      
      State.pollingInterval = setInterval(async () => {
        const status = await this.loadStatus();
        await this.loadMetrics();
        
        // info가 아직 로드되지 않았으면 재시도
        if (!State.infoLoaded) {
          await this.reloadInfo();
        }
        
        // 서브 탭이면 해당 메트릭도 업데이트
        if (State.activeSimTab !== 'main') {
          const workerNum = parseInt(State.activeSimTab.replace('sub', ''));
          await this.loadSubMetrics(workerNum);
        }
        
        await this.loadView();
        
        // 훈련 완료 시 폴링 중지
        if (status && status.status !== 'training' && status.status !== 'evaluating') {
          this.stopPolling();
        }
      }, State.pollingRate);
    },
    
    stopPolling() {
      if (State.pollingInterval) {
        clearInterval(State.pollingInterval);
        State.pollingInterval = null;
      }
    },
    
    async reloadInfo() {
      const infoData = await API.getInfo();
      if (!infoData) return;
      
      State.infoLoaded = true;
      
      // Simulations
      if (infoData.simulations) {
        Object.entries(infoData.simulations).forEach(([key, sim]) => {
          UI.updateSimulationInfo(key, sim);
          if (key === 'main' && sim.track_id) {
            State.modelTrackId = sim.track_id;
          }
        });
        UI.updateSubSimTabs(Object.keys(infoData.simulations).length - 1);
      }
      
      // Vehicle
      if (infoData.vehicle) {
        UI.updateVehicleInfo(infoData.vehicle);
      }
      
      // Hyperparameters
      if (infoData.hyperparameters) {
        UI.updateHyperparameters(infoData.hyperparameters);
      }
      
      // Training settings
      UI.updateTrainingSettings(infoData.best_model_metric, infoData.max_training_time);
    }
  };
  
  // ============================================================
  // 7. Evaluation 모듈
  // ============================================================
  const Evaluation = {
    // 로드된 평가 ID 추적 (lazy loading용)
    loadedEvalIds: new Set(),
    
    // 현재 진행중인 평가 ID
    currentEvalId: null,
    currentRunId: null,
    
    /**
     * 시간 포맷팅 (mm:ss.ms)
     */
    formatTime(seconds) {
      if (!seconds && seconds !== 0) return '-';
      const mins = Math.floor(seconds / 60);
      const secs = seconds % 60;
      return `${mins}:${secs.toFixed(2).padStart(5, '0')}`;
    },
    
    /**
     * timestamp를 사용자 타임존에 맞게 포맷팅
     * eval_id: "20260125071646" -> "2026-01-25 16:16:46" (Asia/Seoul 기준)
     */
    formatTimestamp(evalId) {
      // evalId: YYYYMMDDHHmmss (UTC)
      const year = evalId.slice(0, 4);
      const month = evalId.slice(4, 6);
      const day = evalId.slice(6, 8);
      const hour = evalId.slice(8, 10);
      const minute = evalId.slice(10, 12);
      const second = evalId.slice(12, 14);
      
      // UTC Date 생성
      const utcDate = new Date(Date.UTC(
        parseInt(year), parseInt(month) - 1, parseInt(day),
        parseInt(hour), parseInt(minute), parseInt(second)
      ));
      
      // 사용자 타임존으로 포맷팅 (브라우저 로캘 사용)
      return utcDate.toLocaleString('sv-SE', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
      }).replace('T', ' ');
    },
    
    /**
     * 평가 상태 확인 및 UI 업데이트
     */
    async checkStatus() {
      const data = await API.getEvaluationStatus();
      if (!data) return;
      
      if (data.running) {
        this.currentEvalId = data.eval_id;
        this.currentRunId = data.run_id;
        this.showRunningUI(data);
        this.startPolling();
      } else {
        this.currentEvalId = null;
        this.currentRunId = null;
        this.showReadyUI();
      }
    },
    
    showReadyUI() {
      // 스트림 중단을 위해 currentEvalId 초기화
      this.currentEvalId = null;
      this.currentRunId = null;
    },
    
    showRunningUI(data) {
      // 현재 평가 정보 저장
      this.currentEvalId = data.eval_id;
      this.currentRunId = data.run_id;
    },
    
    /**
     * 평가 히스토리 로드 (아코디언 UI)
     */
    async loadHistory() {
      const container = document.getElementById('eval-accordion-container');
      const loading = document.getElementById('eval-loading');
      const empty = document.getElementById('eval-empty');
      
      // 기존 평가 항목 제거 (로딩/빈화면 제외)
      container.querySelectorAll('.eval-accordion-item').forEach(el => el.remove());
      
      loading.style.display = 'block';
      empty.style.display = 'none';
      this.loadedEvalIds.clear();
      
      // 현재 진행중인 평가 상태 확인
      const statusData = await API.getEvaluationStatus();
      const isRunning = statusData?.running;
      const runningEvalId = statusData?.eval_id;
      
      // 평가 히스토리 로드
      const historyData = await API.getEvaluationHistory();
      loading.style.display = 'none';
      
      // 진행중인 평가가 있으면 목록 맨 앞에 추가
      let evaluations = historyData?.evaluations || [];
      if (isRunning && runningEvalId) {
        // 이미 목록에 없으면 추가
        if (!evaluations.find(ev => ev.eval_id === runningEvalId)) {
          evaluations.unshift({
            eval_id: runningEvalId,
            timestamp: this.formatTimestamp(runningEvalId),
            is_running: true,
            stream_url: statusData.stream_url,
          });
        } else {
          // 이미 있으면 running 플래그만 추가
          const ev = evaluations.find(ev => ev.eval_id === runningEvalId);
          ev.is_running = true;
          ev.stream_url = statusData.stream_url;
        }
      }
      
      if (!evaluations.length) {
        empty.style.display = 'block';
        return;
      }
      
      // 아코디언 항목 생성
      evaluations.forEach((ev, index) => {
        const item = this.createAccordionItem(ev, index === 0);
        container.appendChild(item);
      });
      
      // 첫 번째 항목 자동 펼치기 및 데이터 로드
      if (evaluations.length > 0) {
        const firstEv = evaluations[0];
        this.loadEvalContent(firstEv.eval_id, firstEv);
      }
    },
    
    /**
     * 아코디언 항목 생성
     */
    createAccordionItem(ev, isFirst) {
      const item = document.createElement('div');
      item.className = 'eval-accordion-item accordion-item';
      item.dataset.evalId = ev.eval_id;
      
      const headerId = `eval-header-${ev.eval_id}`;
      const collapseId = `eval-collapse-${ev.eval_id}`;
      
      // 상태 뱃지 (평가중인 것만 표시)
      let statusBadge = '';
      if (ev.is_running) {
        statusBadge = '<span class="badge bg-primary ms-2"><i class="fas fa-spinner fa-spin me-1"></i>Evaluating</span>';
      }
      
      // 타임스탬프를 사용자 타임존으로 변환
      const displayTime = this.formatTimestamp(ev.eval_id);
      
      item.innerHTML = `
        <h2 class="accordion-header" id="${headerId}">
          <button class="accordion-button ${isFirst ? '' : 'collapsed'}" type="button" 
                  data-bs-toggle="collapse" data-bs-target="#${collapseId}"
                  aria-expanded="${isFirst}" aria-controls="${collapseId}">
            <strong>${displayTime}</strong>
            ${statusBadge}
          </button>
        </h2>
        <div id="${collapseId}" class="accordion-collapse collapse ${isFirst ? 'show' : ''}"
             aria-labelledby="${headerId}">
          <div class="accordion-body" id="eval-body-${ev.eval_id}">
            <div class="text-center py-3">
              <div class="spinner-border spinner-border-sm text-primary"></div>
              <span class="ms-2">Loading...</span>
            </div>
          </div>
        </div>
      `;
      
      // 펼침 이벤트: lazy loading
      const collapseEl = item.querySelector('.accordion-collapse');
      collapseEl.addEventListener('show.bs.collapse', () => {
        if (!this.loadedEvalIds.has(ev.eval_id)) {
          this.loadEvalContent(ev.eval_id, ev);
        }
      });
      
      return item;
    },
    
    /**
     * 평가 콘텐츠 로드 (metrics table + video/stream)
     */
    async loadEvalContent(evalId, evData) {
      const body = document.getElementById(`eval-body-${evalId}`);
      if (!body) return;
      
      this.loadedEvalIds.add(evalId);
      
      // 진행중인 평가인 경우
      if (evData.is_running) {
        body.innerHTML = this.renderRunningContent(evalId, evData);
        // 스트림 URL이 있으면 바로 연결, 없으면 폴링으로 가져오기
        this.setupStream(evalId, evData.stream_url);
        return;
      }
      
      // 완료된 평가: metrics table + video
      body.innerHTML = this.renderCompletedContent(evalId, evData);
      
      // 비디오 lazy loading (펼쳐질 때만 로드)
      if (evData.has_video) {
        this.setupVideo(evalId);
      }
    },
    
    /**
     * 진행중인 평가 콘텐츠 렌더링
     */
    renderRunningContent(evalId, evData) {
      return `
        <div class="row">
          <div class="col-md-7">
            <div class="card bg-light">
              <div class="card-body">
                <div class="d-flex justify-content-between align-items-start">
                  <div>
                    <h5 class="card-title mb-3"><i class="fas fa-info-circle me-2"></i>Evaluation in Progress</h5>
                    <p class="mb-2">
                      <small class="text-muted">Eval ID:</small> <code>${evalId}</code>
                    </p>
                    <p class="mb-0">
                      <small class="text-muted">Started:</small> 
                      <span id="eval-started-${evalId}">${this.formatTimestamp(evalId)}</span>
                    </p>
                  </div>
                  <button class="btn btn-danger btn-sm" onclick="Evaluation.stop()">
                    <i class="fas fa-stop me-1"></i>Stop
                  </button>
                </div>
                <div class="mt-3">
                  <div class="alert alert-info mb-0">
                    <i class="fas fa-spinner fa-spin me-2"></i>
                    Metrics will be available after evaluation completes.
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div class="col-md-5">
            <div class="position-relative" style="aspect-ratio: 4/3; background: #1e293b; border-radius: 8px; overflow: hidden;">
              <div id="eval-stream-loading-${evalId}" class="position-absolute top-50 start-50 translate-middle text-center text-white">
                <div class="spinner-border text-primary mb-2"></div>
                <div>Connecting to stream...</div>
              </div>
              <img id="eval-stream-img-${evalId}" src="" alt="Evaluation Stream" 
                   style="width: 100%; height: 100%; object-fit: contain; display: none;">
            </div>
          </div>
        </div>
      `;
    },
    
    /**
     * 완료된 평가 콘텐츠 렌더링
     */
    renderCompletedContent(evalId, evData) {
      // Metrics 테이블
      let metricsHtml = '';
      if (evData.metrics) {
        const metrics = evData.metrics;
        const numRows = Object.keys(metrics.trial || {}).length;
        
        let rowsHtml = '';
        for (let i = 0; i < numRows; i++) {
          const trial = metrics.trial?.[String(i)] || (i + 1);
          const totalLapTime = metrics.total_lap_time?.[String(i)];
          const lapTime = metrics.lap_time?.[String(i)];
          const offTrack = metrics.off_track_count?.[String(i)] ?? '-';
          const crash = metrics.crash_count?.[String(i)] ?? '-';
          const status = metrics.trial_status?.[String(i)] || 'Unknown';
          
          // 상태에 따른 행 스타일
          let rowClass = '';
          let badgeClass = 'secondary';
          if (status === 'Complete') {
            rowClass = 'table-success';
            badgeClass = 'success';
          } else if (status === 'In progress') {
            rowClass = '';  // 진행중 - 기본 스타일
            badgeClass = 'info';
          } else if (status === 'Off_track') {
            rowClass = 'table-warning';
            badgeClass = 'warning';
          } else if (status === 'Crashed') {
            rowClass = 'table-danger';
            badgeClass = 'danger';
          }
          
          rowsHtml += `
            <tr class="${rowClass}">
              <td>${trial}</td>
              <td>${this.formatTime(totalLapTime)}</td>
              <td>${this.formatTime(lapTime)}</td>
              <td>${offTrack}</td>
              <td>${crash}</td>
            </tr>
          `;
        }
        
        if (!rowsHtml) {
          rowsHtml = '<tr><td colspan="5" class="text-center text-muted">No metrics data</td></tr>';
        }
        
        metricsHtml = `
          <div class="table-responsive">
            <table class="table table-sm table-bordered table-hover mb-0">
              <thead class="table-light">
                <tr>
                  <th style="width:60px;">Trial</th>
                  <th>Total Time</th>
                  <th>Lap Time</th>
                  <th style="width:80px;">Off-track</th>
                  <th style="width:60px;">Crash</th>
                </tr>
              </thead>
              <tbody>${rowsHtml}</tbody>
            </table>
          </div>
        `;
      } else {
        metricsHtml = `
          <div class="alert alert-secondary mb-0">
            <i class="fas fa-info-circle me-2"></i>No metrics data available.
          </div>
        `;
      }
      
      // 비디오 영역
      let videoHtml = '';
      if (evData.has_video) {
        const videoUrl = `/proxy/9000/bucket/models/${State.modelName}/evaluation/${evalId}/video.mp4`;
        videoHtml = `
          <div class="position-relative" style="aspect-ratio: 4/3; background: #1e293b; border-radius: 8px; overflow: hidden;">
            <video id="eval-video-${evalId}" controls style="width: 100%; height: 100%; object-fit: contain;"
                   preload="metadata">
              <source src="${videoUrl}" type="video/mp4">
              Your browser does not support the video tag.
            </video>
          </div>
        `;
      } else {
        videoHtml = `
          <div class="d-flex justify-content-center align-items-center h-100 border rounded p-3" 
               style="aspect-ratio: 4/3; background: #f8f9fa;">
            <div class="text-center text-muted">
              <i class="fas fa-video-slash fa-3x mb-2"></i>
              <div>No video available</div>
            </div>
          </div>
        `;
      }
      
      return `
        <div class="row">
          <div class="col-md-7">
            ${metricsHtml}
          </div>
          <div class="col-md-5">
            ${videoHtml}
          </div>
        </div>
      `;
    },
    
    /**
     * 스트림 설정 (진행중인 평가)
     */
    setupStream(evalId, streamUrl) {
      const img = document.getElementById(`eval-stream-img-${evalId}`);
      const loading = document.getElementById(`eval-stream-loading-${evalId}`);
      
      if (!img || !loading) return;
      
      // 스트림 URL이 없으면 API 폴링으로 가져오기
      if (!streamUrl) {
        const pollForStream = async () => {
          if (this.currentEvalId !== evalId) return; // 다른 평가로 전환됨
          
          try {
            const statusData = await API.getEvaluationStatus();
            if (statusData?.stream_url) {
              this.setupStream(evalId, statusData.stream_url);
              return;
            }
          } catch (e) {
            console.log('[Evaluation] Stream URL not ready, retrying...');
          }
          
          // 2초 후 재시도
          setTimeout(pollForStream, 2000);
        };
        
        pollForStream();
        return;
      }
      
      img.onerror = () => {
        img.style.display = 'none';
        loading.style.display = 'block';
        // 재시도
        setTimeout(() => {
          if (this.currentEvalId === evalId) {
            img.src = streamUrl + '&t=' + Date.now();
          }
        }, 2000);
      };
      
      img.onload = () => {
        img.style.display = 'block';
        loading.style.display = 'none';
      };
      
      img.src = streamUrl;
    },
    
    /**
     * 비디오 설정 (완료된 평가)
     */
    setupVideo(evalId) {
      const video = document.getElementById(`eval-video-${evalId}`);
      if (!video) return;
      
      // preload="none"이므로 사용자가 재생 버튼 클릭 시 로드됨
      video.addEventListener('error', (e) => {
        console.error(`Video load error for ${evalId}:`, e);
      });
    },
    
    /**
     * 경과 시간 타이머
     */
    startElapsedTimer(evalId) {
      const el = document.getElementById(`eval-elapsed-${evalId}`);
      if (!el) return;
      
      // evalId에서 시작 시간 파싱
      const year = parseInt(evalId.slice(0, 4));
      const month = parseInt(evalId.slice(4, 6)) - 1;
      const day = parseInt(evalId.slice(6, 8));
      const hour = parseInt(evalId.slice(8, 10));
      const minute = parseInt(evalId.slice(10, 12));
      const second = parseInt(evalId.slice(12, 14));
      const startTime = new Date(Date.UTC(year, month, day, hour, minute, second));
      
      const tick = () => {
        const elapsed = Math.floor((Date.now() - startTime.getTime()) / 1000);
        const m = Math.floor(elapsed / 60);
        const s = elapsed % 60;
        el.textContent = `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
      };
      
      tick();
      State.evalElapsedTimerId = setInterval(tick, 1000);
    },
    
    stopElapsedTimer() {
      if (State.evalElapsedTimerId) {
        clearInterval(State.evalElapsedTimerId);
        State.evalElapsedTimerId = null;
      }
    },
    
    /**
     * 폴링 시작 (진행중인 평가 상태 체크)
     */
    startPolling() {
      this.stopPolling();
      
      State.evalPollingId = setInterval(async () => {
        const data = await API.getEvaluationStatus();
        if (!data) return;
        
        if (data.running) {
          this.showRunningUI(data);
        } else {
          this.showReadyUI();
          this.stopPolling();
          this.stopElapsedTimer();
          // 완료된 평가 다시 로드
          await this.loadHistory();
        }
      }, 3000);
    },
    
    stopPolling() {
      if (State.evalPollingId) {
        clearInterval(State.evalPollingId);
        State.evalPollingId = null;
      }
    },
    
    /**
     * 평가 중지
     */
    async stop() {
      const result = await Swal.fire({
        title: 'Stop Evaluation?',
        text: 'Are you sure you want to stop the evaluation?',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#cd201f',
        confirmButtonText: 'Stop'
      });
      
      if (!result.isConfirmed) return;
      
      Swal.fire({
        title: 'Stopping...',
        allowOutsideClick: false,
        allowEscapeKey: false,
        showConfirmButton: false,
        didOpen: () => Swal.showLoading()
      });
      
      try {
        const status = await API.getEvaluationStatus();
        if (status?.running && status.run_id) {
          await API.stopEvaluation(status.run_id);
        }
        Swal.close();
        this.showReadyUI();
        this.stopPolling();
        this.stopElapsedTimer();
        await this.loadHistory();
      } catch (e) {
        Swal.fire('Error', 'Failed to stop evaluation: ' + e.message, 'error');
      }
    },
    
    // 구버전 호환용 메서드 (제거 예정)
    async loadTracks() {
      // 더 이상 사용하지 않음
    }
  };
  
  // ============================================================
  // 8. 초기화
  // ============================================================
  async function init() {
    // 모델 이름 가져오기
    State.modelName = window.MODEL_NAME || '';
    if (!State.modelName) {
      console.error('[ModelPage] MODEL_NAME not defined');
      return;
    }
    
    // DOM 초기화
    UI.init();
    
    // URL 해시에 따른 초기 탭 설정
    const initialTab = UI.getTabFromHash();
    UI.showPageTab(initialTab, false);  // 해시는 이미 URL에 있으므로 업데이트 안 함
    
    // 초기 로딩 상태 표시
    Stream.showLoading('main', 'Loading...');
    for (let i = 1; i <= 6; i++) Stream.showLoading(`sub${i}`, 'Loading...');
    
    // 차트 초기화
    Charts.initMain();
    
    // 데이터 로드
    const [statusData, infoData, metricsData, rewardData, physicalData] = await Promise.all([
      Training.loadStatus(),
      API.getInfo(),
      Training.loadMetrics(),
      API.getRewardFunction(),
      API.getPhysicalCarStatus()
    ]);
    
    // 모델 정보 업데이트
    if (infoData) {
      State.infoLoaded = true;
      
      // Simulations
      if (infoData.simulations) {
        Object.entries(infoData.simulations).forEach(([key, sim]) => {
          UI.updateSimulationInfo(key, sim);
          if (key === 'main' && sim.track_id) {
            State.modelTrackId = sim.track_id;
          }
        });
        UI.updateSubSimTabs(Object.keys(infoData.simulations).length - 1);
      }
      
      // Vehicle
      if (infoData.vehicle) {
        UI.updateVehicleInfo(infoData.vehicle);
      }
      
      // Hyperparameters
      if (infoData.hyperparameters) {
        UI.updateHyperparameters(infoData.hyperparameters);
      }
      
      // Training settings
      UI.updateTrainingSettings(infoData.best_model_metric, infoData.max_training_time);
    }
    
    // 보상 함수
    if (rewardData?.content) {
      UI.updateRewardFunction(rewardData.content);
    }
    
    // Physical car model 상태
    if (physicalData) {
      UI.updatePhysicalCarMenu(physicalData.best_exists, physicalData.last_exists);
    }
    
    // 훈련 뷰 로드
    await Training.loadView();
    
    // 훈련 중이면 폴링 시작
    if (statusData?.is_training || statusData?.is_evaluating) {
      Training.startPolling();
    }
    
    // Evaluation 탭으로 시작하는 경우 추가 로드
    if (initialTab === 'evaluation') {
      await Evaluation.loadTracks();
      await Evaluation.checkStatus();
      await Evaluation.loadHistory();
    }
    
    // 이벤트 바인딩
    bindEvents();
  }
  
  function bindEvents() {
    // 페이지 탭 전환
    UI.elements.trainingTab?.addEventListener('click', () => {
      UI.showPageTab('training');
      Evaluation.stopPolling();
    });
    
    UI.elements.evaluationTab?.addEventListener('click', async () => {
      UI.showPageTab('evaluation');
      await Evaluation.loadTracks();
      await Evaluation.checkStatus();
      await Evaluation.loadHistory();
    });
    
    // URL 해시 변경 감지 (뒤로가기/앞으로가기)
    window.addEventListener('hashchange', async () => {
      const tab = UI.getTabFromHash();
      if (tab !== State.activePageTab) {
        UI.showPageTab(tab, false);  // 해시 업데이트 안 함 (이미 변경됨)
        if (tab === 'evaluation') {
          await Evaluation.loadTracks();
          await Evaluation.checkStatus();
          await Evaluation.loadHistory();
        } else {
          Evaluation.stopPolling();
        }
      }
    });
    
    // 시뮬레이션 탭 전환
    document.querySelectorAll('#simulation-tabs .nav-link').forEach(tab => {
      tab.addEventListener('shown.bs.tab', async (e) => {
        const prevTab = State.activeSimTab;
        const targetId = e.target.getAttribute('href');
        
        // 이전 탭 스트림 중지
        Stream.stopStream(prevTab);
        
        if (targetId === '#tabs-main') {
          State.activeSimTab = 'main';
          if (State.streamUrls?.main) {
            Stream.showStream('main', State.streamUrls.main);
          }
        } else {
          const match = targetId.match(/#tabs-sub(\d+)/);
          if (match) {
            const num = parseInt(match[1]);
            const simKey = `sub${num}`;
            State.activeSimTab = simKey;
            
            Charts.initSub(simKey);
            await Training.loadSubMetrics(num);
            
            if (State.streamUrls?.[simKey]) {
              Stream.showStream(simKey, State.streamUrls[simKey]);
            }
          }
        }
      });
    });
    
    // Stop Training 버튼
    document.getElementById('stop-training-btn')?.addEventListener('click', async () => {
      const result = await Swal.fire({
        title: 'Stop Training?',
        text: 'Are you sure you want to stop training?',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#cd201f',
        confirmButtonText: 'Stop'
      });
      
      if (result.isConfirmed) {
        // 로딩 UI 표시
        Swal.fire({
          title: 'Stopping...',
          html: 'Saving logs and cleaning up containers...',
          allowOutsideClick: false,
          allowEscapeKey: false,
          showConfirmButton: false,
          didOpen: () => Swal.showLoading()
        });
        
        const success = await API.stopTraining();
        Swal.close();
        
        if (success) {
          Swal.fire('Stopped!', 'Training has been stopped.', 'success');
          await Training.loadStatus();
        } else {
          Swal.fire('Error', 'Failed to stop training.', 'error');
        }
      }
    });
    
    // 페이지 떠날 때
    window.addEventListener('beforeunload', () => {
      Training.stopPolling();
      Training.stopTrainingTimer();
      Evaluation.stopPolling();
      Evaluation.stopElapsedTimer();
    });
  }
  
  // 전역 함수 노출
  window.cloneModel = (name) => {
    window.location.href = `/pages/models/clone?model_name=${name}`;
  };
  
  window.downloadPhysicalCarModel = (name, type) => {
    const a = document.createElement('a');
    a.href = `/api/models/${encodeURIComponent(name)}/download/physical-car-model/${type}`;
    a.download = `${name}-${type}.tar.gz`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };
  
  window.downloadLogs = async (name) => {
    const btn = document.getElementById('download-logs-btn');
    const originalText = btn?.textContent;
    if (btn) {
      btn.textContent = 'Preparing...';
      btn.classList.add('disabled');
    }
    
    try {
      const res = await fetch(`/api/models/${encodeURIComponent(name)}/download/logs`);
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || 'Download failed');
      }
      
      const blob = await res.blob();
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = `${name}-logs.tar.gz`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(a.href);
    } catch (e) {
      console.error('Download logs error:', e);
      Swal.fire('Error', e.message || 'Failed to download logs', 'error');
    } finally {
      if (btn) {
        btn.textContent = originalText;
        btn.classList.remove('disabled');
      }
    }
  };
  
  window.deleteModel = async (name) => {
    // 훈련/평가 중인지 체크
    if (State.isTraining || State.isEvaluating) {
      Swal.fire('Cannot Delete', 'Stop training/evaluation before deleting the model.', 'warning');
      return;
    }
    
    const result = await Swal.fire({
      title: 'Delete Model?',
      html: `Are you sure you want to delete <strong>${name}</strong>?<br><br>This action cannot be undone.`,
      icon: 'warning',
      showCancelButton: true,
      confirmButtonColor: '#d33',
      confirmButtonText: 'Delete',
      cancelButtonText: 'Cancel'
    });
    
    if (!result.isConfirmed) return;
    
    try {
      const res = await fetch(`/api/models/${encodeURIComponent(name)}`, {
        method: 'DELETE'
      });
      
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || 'Delete failed');
      }
      
      await Swal.fire({
        title: 'Deleted!',
        text: `Model "${name}" has been deleted.`,
        icon: 'success',
        timer: 2000,
        showConfirmButton: false
      });
      
      // 모델 목록 페이지로 이동
      window.location.href = '/pages/models';
    } catch (e) {
      console.error('Delete model error:', e);
      Swal.fire('Error', e.message || 'Failed to delete model', 'error');
    }
  };
  
  // Delete 버튼 이벤트 바인딩
  document.getElementById('delete-model-btn')?.addEventListener('click', (e) => {
    e.preventDefault();
    const modelName = e.target.getAttribute('data-model-name');
    if (modelName) window.deleteModel(modelName);
  });
  
  // DOM Ready
  document.addEventListener('DOMContentLoaded', init);
})();
