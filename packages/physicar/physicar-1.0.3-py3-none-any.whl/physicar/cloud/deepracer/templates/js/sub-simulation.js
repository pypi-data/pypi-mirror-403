/* --------------------------------------------------
    서브 시뮬레이션 탭 활성화
  -------------------------------------------------- */
  function updateSubSimulationTabs(numberOfSubSimulations) {
    const subNavItems = document.querySelectorAll('.sub-nav-item');

    // 모든 서브 탭 숨김
    for (let i = 1; i < subNavItems.length; i++) {
      subNavItems[i].classList.add('d-none');
    }

    // 필요한 개수만 표시
    for (let i = 1; i <= numberOfSubSimulations; i++) {
      if (i < subNavItems.length) {
        subNavItems[i].classList.remove('d-none');
      }
    }
  }

  /* --------------------------------------------------
    방향 라디오 버튼 설정
  -------------------------------------------------- */
  function setDirectionRadio(prefix, direction) {
    if (!direction) return;

    const cw  = document.querySelector(`input[name="clock-direction${prefix}"][value="clockwise"]`);
    const ccw = document.querySelector(`input[name="clock-direction${prefix}"][value="counterclockwise"]`);

    if (cw && ccw) {
      if (direction === 'clockwise') {
        cw.checked = true;  ccw.checked = false;
      } else {
        cw.checked = false; ccw.checked = true;
      }
    }
  }

  /* --------------------------------------------------
    Alternate-training 체크박스 설정
  -------------------------------------------------- */
  function setAlternateTrainingDirection(prefix, val) {
    if (val === undefined || val === null) return;

    const id  = prefix ? `alternate${prefix}` : 'alternate-training-main';
    const chk = document.getElementById(id);

    if (chk) {
      chk.checked = Boolean(val);
      return;
    }

    /* 백업 — 라벨 직접 탐색 */
    const tabId  = prefix ? `tabs${prefix}` : 'tabs-main';
    const tabEl  = document.getElementById(tabId);
    if (!tabEl) return;

    const labels = tabEl.querySelectorAll('label.dropdown-item');
    for (const lbl of labels) {
      if (lbl.textContent.trim().includes('Alternate Training Direction')) {
        const backup = lbl.querySelector('input[type="checkbox"]');
        if (backup) backup.checked = Boolean(val);
        break;
      }
    }
  }

  /* --------------------------------------------------
    레이스 타입 라디오 설정
  -------------------------------------------------- */
  function setRaceTypeRadio(prefix, raceType) {
    if (!raceType) return;
    
    // 대문자로 통일
    const raceTypeUpper = raceType.toUpperCase();

    const subKey   = prefix ? prefix.replace('-', '') : '';
    const name     = prefix ? `race-type-${subKey}`   : 'race-type';
    const ttRadio  = document.querySelector(`input[name="${name}"][value="TIME_TRIAL"]`);
    const oaRadio  = document.querySelector(`input[name="${name}"][value="OBJECT_AVOIDANCE"]`);
    const wrapId   = prefix ? `race-type-wrapper-${subKey}` : 'race-type-wrapper';
    const wrapper  = document.getElementById(wrapId);

    if (!(ttRadio && oaRadio)) {
      if (raceTypeUpper === 'OBJECT_AVOIDANCE' && wrapper) wrapper.classList.remove('d-none');
      return;
    }

    if (raceTypeUpper === 'TIME_TRIAL') {
      oaRadio.checked = false;
      ttRadio.checked = true;
      if (wrapper) wrapper.classList.add('d-none');
    } else {
      ttRadio.checked = false;
      oaRadio.checked = true;
      if (wrapper) wrapper.classList.remove('d-none');
    }

    /* change 이벤트 한 번 트리거 */
    try {
      oaRadio.dispatchEvent(new Event('change'));
    } catch { /* noop */ }
  }

  /* --------------------------------------------------
    현재 활성 탭 ID
  -------------------------------------------------- */
  function getActiveTabId() {
    const panel = document.querySelector('.tab-pane.active');
    const id    = panel ? panel.id : 'tabs-main';
    console.log('활성화된 탭 ID:', id);
    return id;
  }

  /* --------------------------------------------------
    Object-location UI (공통)
  -------------------------------------------------- */
  function setupObjectLocationListeners() {
    setupObjectLocationUI('');
    for (let i = 1; i <= 6; i++) setupObjectLocationUI(`-sub${i}`);
  }

  function setupObjectLocationUI(prefix) {
    const subKey      = prefix ? prefix.replace('-', '') : '';
    const randId      = subKey ? `object-position-${subKey}`            : 'object-position';
    const wrapId      = subKey ? `object-location-wrapper-${subKey}`    : 'object-location-wrapper';
    const addBtnId    = subKey ? `add-object-btn-${subKey}`             : 'add-object-btn';
    const insideId    = subKey ? `object-location-wrapper-inside-${subKey}` : 'object-location-wrapper-inside';

    const randChk     = document.getElementById(randId);
    const wrapper     = document.getElementById(wrapId);
    const addBtn      = document.getElementById(addBtnId);
    const insideWrap  = document.getElementById(insideId);

    if (randChk && wrapper) {
      randChk.addEventListener('change', () => {
        if (randChk.checked) {
          wrapper.classList.add('d-none');
        } else {
          wrapper.classList.remove('d-none');
        }
      });

      // 초기 상태 적용 - checkbox 상태에 따라 wrapper 표시/숨김
      // NOTE: settings-manager.js에서 이미 처리하므로 여기선 이벤트만 등록
      // 초기 렌더 코드 제거 - settings-manager.js에서 처리
    }

    if (addBtn && insideWrap) {
      // 더미 데이터 생성 코드 주석 처리
      /*
      addBtn.addEventListener('click', () => addObjectLocation(prefix));
      insideWrap.querySelectorAll('.remove-object-btn').forEach(btn =>
        btn.addEventListener('click', () => btn.closest('.object-location-row').remove())
      );
      */
    }
  }

  // addObjectLocation 함수 주석 처리 - 불필요한 더미 데이터 생성 함수
  /*
  function addObjectLocation(prefix, location = {}) {
    const subKey       = prefix ? prefix.replace('-', '') : '';
    const insideId     = subKey ? `object-location-wrapper-inside-${subKey}` : 'object-location-wrapper-inside';
    const insideWrap   = document.getElementById(insideId);
    if (!insideWrap) return;

    const lane         = location.lane     ?? 'inside';
    const progress     = location.progress ?? 5;
    const laneName     = subKey ? `object-lane-${subKey}`    : 'object-lane';
    const progressName = subKey ? `object-progress-${subKey}`: 'object-progress';

    const row = document.createElement('div');
    row.className = 'object-location-row d-flex align-items-center mb-2';
    row.innerHTML = `
      <div class="me-3">
        <select class="form-select" name="${laneName}">
          <option value="inside"  ${lane === 'inside'  ? 'selected' : ''}>Inside</option>
          <option value="center"  ${lane === 'center'  ? 'selected' : ''}>Center</option>
          <option value="outside" ${lane === 'outside' ? 'selected' : ''}>Outside</option>
        </select>
      </div>
      <div class="me-3">
        <input type="number" class="form-control" name="${progressName}"
              min="1" max="100" value="${progress}">
      </div>
      <button type="button" class="btn btn-danger btn-sm remove-object-btn">Remove</button>
    `; // ← 닫는 백틱 반드시 필요
    insideWrap.appendChild(row);

    row.querySelector('.remove-object-btn')
      .addEventListener('click', () => row.remove());
  }
  */

  /* ==================================================
    DOMContentLoaded 진입
  ================================================== */
  document.addEventListener('DOMContentLoaded', () => {

    /* ---------------- 레이스 타입 리스너 ---------------- */
    function setupRaceTypeListeners() {
      /* 메인 */
      document.querySelectorAll('input[name="race-type"]').forEach(r =>
        r.addEventListener('change', () => {
          document.getElementById('race-type-wrapper')
                  .classList.toggle('d-none', r.value !== 'OBJECT_AVOIDANCE');
        })
      );

      const mainRand = document.getElementById('object-position');
      if (mainRand) {
        mainRand.addEventListener('change', () => {
          document.getElementById('object-location-wrapper')
                  ?.classList.toggle('d-none', mainRand.checked);
        });
      }

      /* 서브 */
      for (let i = 1; i <= 6; i++) {
        const subKey   = `sub${i}`;
        const name     = `race-type-${subKey}`;
        const wrapper  = document.getElementById(`race-type-wrapper-${subKey}`);

        document.querySelectorAll(`input[name="${name}"]`).forEach(radio => {
          radio.addEventListener('change', () => {
            if (wrapper) wrapper.classList.toggle('d-none', radio.value !== 'OBJECT_AVOIDANCE');
          });
        });

        const randChk = document.getElementById(`object-position-${subKey}`);
        if (randChk) {
          randChk.addEventListener('change', () => {
            document.getElementById(`object-location-wrapper-${subKey}`)
                    ?.classList.toggle('d-none', randChk.checked);
          });
        }
      }
    }

    /* ---------------- Sub-simulation count ---------------- */
    const subCntSel = document.getElementById('sub-simulation-count-id');
    if (subCntSel) {
      subCntSel.addEventListener('change', () =>
        updateSubSimulationTabs(parseInt(subCntSel.value, 10))
      );
    }

    /* ---------------- 트랙 선택 모달 처리 ---------------- */
    const trackRadios = document.querySelectorAll('input[name="form-imagecheck-radio"]');
    trackRadios.forEach(radio => {
      radio.addEventListener('change', function () {
        if (!this.checked) return;

        const trackId = this.value;
        let prefix    = '';
        const active  = getActiveTabId();
        if (active !== 'tabs-main') prefix = `-${active.replace('tabs-', '')}`;
        setTrackImage(prefix, trackId);

        /* 상태 저장 */
        const imgSrc = this.closest('label')?.querySelector('img')?.src || '';
        const name   = this.dataset.trackName || '';
        window.tabStates ??= {};
        window.tabStates[active] ??= {};
        Object.assign(window.tabStates[active], {
          trackId,
          trackName: name,
          trackImage: imgSrc
        });
      });
    });

    /* ---------------- 초기 util 호출 ---------------- */
    setupObjectLocationListeners();
    setupRaceTypeListeners();

    /* ---------------- 모델 설정 로딩 ---------------- */
    setTimeout(() => {
      setupSimulationSettings();

      /* 여러 번 보정 */
      setTimeout(() => {
        reapplyRaceTypeSettings();
        setTimeout(reapplyRaceTypeSettings, 2000);
      }, 2000);
    }, 1000);

    /* ------------ 내부 함수 (async) ------------ */
    async function setupSimulationSettings() {
      try {
        let modelName = '';
        const parts   = window.location.pathname.split('/');

        for (let i = 0; i < parts.length; i++) {
          if (parts[i] === 'clone_model' && i + 1 < parts.length) {
            modelName = parts[i + 1];
            break;
          }
        }
        if (!modelName) {
          const inp = document.getElementById('model-name-id');
          if (inp && inp.value) modelName = inp.value.replace('-clone', '');
        }
        if (!modelName) return;

        if (window.tracksInfo) globalTracksInfo = window.tracksInfo;

        const res = await fetch(`/api/models/${modelName}/info`);
        if (!res.ok) {
          console.error('모델 정보 가져오기 실패:', res.statusText);
          return;
        }
        const data       = await res.json();
        const simulation = data?.config_training?.simulation;
        if (!simulation) return;

        /* 부분 생략 – 기존 로직 그대로 (direction/raceType 세팅 등) */
        /* ... (길어서 생략) */
      } catch (e) {
        console.error('모델 정보 가져오기 오류:', e);
      }
    }

    /* 다시 적용 */
    async function reapplyRaceTypeSettings() {
      try {
        let modelName = '';
        const parts   = window.location.pathname.split('/');
        for (let i = 0; i < parts.length; i++) {
          if (parts[i] === 'clone_model' && i + 1 < parts.length) {
            modelName = parts[i + 1];
            break;
          }
        }
        if (!modelName) {
          const inp = document.getElementById('model-name-id');
          if (inp && inp.value) modelName = inp.value.replace('-clone', '');
        }
        if (!modelName) return;

        const res = await fetch(`/api/models/${modelName}/info`);
        if (!res.ok) return;

        const data       = await res.json();
        const simulation = data?.config_training?.simulation;
        if (!simulation) return;

        /* 부분 생략 – 기존 로직 그대로 (raceType/randChk 재적용) */
        /* ... */
      } catch (e) {
        console.error('재적용 오류:', e);
      }
    }
  });

  /* ==================================================
    전역 util
  ================================================== */
  let globalTracksInfo = {};

  function setTrackImage(prefix, trackId) {
    if (!trackId) return;

    window.tabStates ??= {};
    const tabId = prefix ? `tabs-${prefix.replace('-', '')}` : 'tabs-main';
    window.tabStates[tabId] ??= {};
    window.tabStates[tabId].trackId = trackId;

    const selector = prefix ? `input[name="track-id${prefix}"]`
                            : 'input[name="track-id"]';
    const hidden   = document.querySelector(selector);
    if (hidden) hidden.value = trackId;
  }

  /* --------------------------------------------------
    Sub-simulation count select 초기화
  -------------------------------------------------- */

