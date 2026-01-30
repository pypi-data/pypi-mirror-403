  // main 탭(tabs-main)에서만 사용할 전역 변수들
  //model name input
  const modelNameInput = document.getElementById('model-name-id');

  // raceTypeRadio input - main 탭에서만 사용 (querySelectorAll로 NodeList 반환 - forEach 지원)
  const raceTypeRadioInput = document.querySelectorAll('input[name="race-type"]');
  // raceTypeRadio wrapper - main 탭에서만 사용
  const raceTypeWrapper = document.getElementById('race-type-wrapper');

  // object positon input - main 탭에서만 사용
  const objectPostionInput = document.getElementById('object-position');
  // number_of_objects 셀렉터 - main 탭에서만 사용
  const objectCountSelect = document.getElementById('number-of-objects');
  // object-location-wrapper - main 탭에서만 사용
  const objectLocationWrapper = document.getElementById('object-location-wrapper');
  // object-location-wrapper-inside - main 탭에서만 사용
  const objectLocationWrapperInside = document.getElementById('object-location-wrapper-inside');
  // object-type 셀렉터 - main 탭에서만 사용
  const objectTypeSelect = document.querySelector('#tabs-main select[name="object-type"]');

  // 이제 기본 트랙 이미지 선택은 `initSimulationPane` 함수에서 처리합니다.

  // race type 선택시 하단 보이고 안보이고 설정 (main 탭에서만 사용)
  raceTypeRadioInput.forEach((radio) => {
    radio.addEventListener('change', function () {
      const selectedValue = this.value;
      if (selectedValue === 'OBJECT_AVOIDANCE') {
        // OBJECT_AVOIDANCE 일때 하단 보여주기
        raceTypeWrapper.classList.remove("d-none");
      } else {
        // TIME_TRIAL 일때 하단 없애주기
        raceTypeWrapper.classList.add("d-none");
      }
    });
  });

  // 모델 이름 검증은 create.html의 모델 이름 중복 체크 스크립트에서 처리합니다.

  // 체크박스 & select 둘 다에 이벤트 연결
  objectPostionInput.addEventListener('change', renderObjectLocations);
  objectCountSelect.addEventListener('change', renderObjectLocations);

  // simulation count id
  const subSimulationCount = document.getElementById('sub-simulation-count-id');

  // 탭 sub items
  const subNavItems = document.querySelectorAll('.sub-nav-item');

  // Sub Simulation Count → Accordion 제어

  if (subSimulationCount) {
    subSimulationCount.addEventListener('change', function () {

      const subSimulCount = Number(this.value);

      if (subSimulCount => 0) {
        subNavItems.forEach((item, index) => {
          //console.log("index: " + index);
          if (index <= subSimulCount) {
            item.classList.remove('d-none'); // 보여주기
          } else {
            item.classList.add('d-none'); // 숨기기
          }
        });
      }
    })
  }


  // model close button 
  const modalCloseButton = document.getElementById('btn-track-modal');
  // 모달 선택하고 나오는 이미지랑 ID 보여줄 부분
  const trackPreviewBox = document.getElementById('track-preview-box');

  // 현재 활성화된 탭을 저장할 변수
  let currentActiveTabForTrack = 'tabs-main';

  // 모달이 열릴 때 현재 활성 탭 저장 및 트랙 라디오 기본 선택
  document.querySelectorAll('[data-bs-toggle="modal"][data-bs-target="#modal-report"]').forEach(btn => {
    btn.addEventListener('click', function () {
      // 이 버튼이 속한 탭 찾기
      const parentPane = this.closest('.simulation-pane');
      if (parentPane) {
        currentActiveTabForTrack = parentPane.id;
        console.log(`트랙 모달이 열림: ${currentActiveTabForTrack} 탭에서`);

        // 해당 탭의 마지막 선택값(없으면 기본값)으로 라디오 체크
        let checkedValue = null;
        let checkedTrackName = null;
        if (tabStates[currentActiveTabForTrack] && tabStates[currentActiveTabForTrack].trackId) {
          checkedValue = tabStates[currentActiveTabForTrack].trackId;
          checkedTrackName = tabStates[currentActiveTabForTrack].trackName;
        }
        // 라디오 목록
        const radios = document.querySelectorAll('input[name="form-imagecheck-radio"]');
        let found = false;
        radios.forEach(radio => {
          // 이전에 선택한 트랙이 있으면 그걸 체크
          if (checkedValue && radio.value === checkedValue && radio.dataset.trackName === checkedTrackName) {
            radio.checked = true;
            found = true;
          } else {
            radio.checked = false;
          }
        });
        // 이전 선택이 없으면 기본값 체크
        if (!found) {
          const defaultRadio = document.querySelector('input[name="form-imagecheck-radio"][value="reInvent2019_wide"][data-track-name="A to Z Speedway"]');
          if (defaultRadio) {
            defaultRadio.checked = true;
          }
        }
      }
    });
  });

  // 모달창 안에서 버튼 클릭 시 이미지 append 
  document.querySelectorAll('input[name="form-imagecheck-radio"]').forEach(radio => {
    radio.addEventListener('change', function () {
      const selectedInput = this;
      const selectedTrackId = this.value;
      const selectedTrackName = selectedInput.dataset.trackName;

      // console.log("트랙아이디" + selectedTrackId)
      // console.log("트랙네임" + selectedTrackName)
      console.log(`트랙 선택: ${selectedTrackName}(${selectedTrackId}), 대상 탭: ${currentActiveTabForTrack}`);

      // 1) 방향 문자열 꺼내기
      const dirStr = selectedInput.dataset.trackDirection;           // e.g. "clockwise,counterclockwise"
      // 2) 배열로 파싱
      const directions = dirStr.split(',').map(s => s.trim());       // ["clockwise", "counterclockwise"]


      // 현재 활성 탭 찾기
      const activePane = document.getElementById(currentActiveTabForTrack);
      if (!activePane) return;

      // 이 탭 내의 방향 라디오 버튼들 찾기
      // 탭ID에 맞는 name 속성 가져오기
      const tabSuffix = currentActiveTabForTrack.replace('tabs-', '');
      const clockDirName = tabSuffix === 'main' ? 'clock-direction' : `clock-direction-${tabSuffix}`;

      const directionRadios = activePane.querySelectorAll(`input[name="${clockDirName}"]`);

      // 방향 라디오 활성/비활성 처리
      directionRadios.forEach(r => {
        if (directions.includes(r.value)) {
          r.disabled = false;
          r.closest('label').classList.remove('text-muted');
        } else {
          r.disabled = true;
          r.checked = false;
          r.closest('label').classList.add('text-muted');
        }
      });

      // 방향이 하나만 있으면 자동으로 선택
      if (directions.length === 1) {
        const only = directions[0];
        const r = activePane.querySelector(`input[name="${clockDirName}"][value="${only}"]`);
        if (r) r.checked = true;
      }

      //console.log("방향: " + directions);

      if (!selectedInput) return;

      const imgElement = selectedInput.closest('label').querySelector('img');
      const imgSrc = imgElement ? imgElement.src : null;

      // 트랙 상세 정보 가져오기
      const trackWidth = selectedInput.dataset.trackWidth || '-';
      const trackLength = selectedInput.dataset.trackLength || '-';
      const trackDescription = selectedInput.dataset.trackDescription || '';
      const trackDirection = selectedInput.dataset.trackDirection || '';

      // 현재 탭의 트랙 프리뷰 박스 찾기
      const tabSuffixPreview = currentActiveTabForTrack.replace('tabs-', '');
      const trackPreviewId = tabSuffixPreview === 'main' ? 'track-preview-box' : `track-preview-box-${tabSuffixPreview}`;
      const trackDescId = tabSuffixPreview === 'main' ? 'track-description-box' : `track-description-box-${tabSuffixPreview}`;
      const previewElem = activePane.querySelector(`#${trackPreviewId}`);
      const descElem = activePane.querySelector(`#${trackDescId}`);

      if (!previewElem) return;

      // 이미지 + ID 렌더링
      previewElem.innerHTML = `
          <img src="${imgSrc}" alt="Selected Track" style="max-height: 210px; width:100%; margin-bottom: 8px;">
          <span class="text-muted small">${selectedTrackName}</span>
        `;

      // 트랙 상세 정보 렌더링
      if (descElem) {
        descElem.innerHTML = `
          <h5 class="mb-3">${selectedTrackName}</h5>
          <div class="mb-2"><strong>Width:</strong> ${trackWidth}</div>
          <div class="mb-2"><strong>Length:</strong> ${trackLength}</div>
          <div class="mb-2"><strong>Direction:</strong> ${trackDirection.replace(/,/g, ', ')}</div>
          <div class="mt-3"><strong>Description:</strong><br><small class="text-muted">${trackDescription}</small></div>
        `;
      }

      // 현재 탭의 상태에 트랙 정보 저장
      if (tabStates[currentActiveTabForTrack]) {
        tabStates[currentActiveTabForTrack].trackId = selectedTrackId;
        tabStates[currentActiveTabForTrack].trackName = selectedTrackName;
        tabStates[currentActiveTabForTrack].trackImage = imgSrc;
        tabStates[currentActiveTabForTrack].trackWidth = trackWidth;
        tabStates[currentActiveTabForTrack].trackLength = trackLength;
        tabStates[currentActiveTabForTrack].trackDescription = trackDescription;
        tabStates[currentActiveTabForTrack].trackDirection = trackDirection;
      }

      // 모달 닫기 버튼을 강제로 클릭하여 완전한 닫힘 유도 (스크롤 등 포함)
      document.querySelector('#modal-report .btn-close').click();

      // 트랙 선택 후 해당 탭의 상태를 명시적으로 저장
      if (currentActiveTabForTrack) {
        const targetPane = document.getElementById(currentActiveTabForTrack);
        if (targetPane) {
          saveTabState(targetPane);
          console.log(`${currentActiveTabForTrack} 탭의 상태가 저장됨:`, tabStates[currentActiveTabForTrack]);
        }
        
        // 트랙 선택을 서버에 저장
        if (currentActiveTabForTrack === 'tabs-main') {
          if (window.saveMainTrack) {
            window.saveMainTrack(selectedTrackId);
          }
        } else {
          // tabs-sub1 -> index 0, tabs-sub2 -> index 1, ...
          const subIndex = parseInt(currentActiveTabForTrack.replace('tabs-sub', '')) - 1;
          if (!isNaN(subIndex) && window.saveSubTrack) {
            window.saveSubTrack(subIndex, selectedTrackId);
          }
        }
      }
    });
  });

  // 모달 닫힐 때 이벤트
  document.querySelector('#modal-report').addEventListener('hidden.bs.modal', function () {
    console.log('트랙 선택 모달이 닫힘');
  });


  // 공통 렌더링 함수 (randomize object , number of object 관련이벤트)
  function renderObjectLocations() {
    const count = parseInt(objectCountSelect.value, 10);

    if (!objectPostionInput.checked && count > 0) {
      objectLocationWrapper.classList.remove('d-none');

      // 대상 card-body 내부를 비우고 다시 채움
      const innerContainer = objectLocationWrapper.querySelector('.card-body');
      innerContainer.innerHTML = '';

      for (let i = 0; i < count; i++) {
        //홀수 짝수 판단
        const isOdd = (i + 1) % 2 === 1;

        // 총 Object 수에 따라 0부터 100 사이의 값을 균등 간격으로 분배하여 Progress 값 설정
        const progressValue = ((100 / (count + 1)) * (i + 1)).toFixed(0);

        const block = document.createElement('div');
        block.className = 'obstable-block mb-2 p-2 border rounded bg-light';

        block.innerHTML = `
          <div class="d-flex align-items-center gap-2">
            <span class="fw-bold" style="min-width:60px;">Obj ${i + 1}</span>
            <div class="d-flex align-items-center gap-1">
              <label class="form-label mb-0 small">Progress:</label>
              <input type="number" step="any" class="form-control form-control-sm progress-valid"
                     name="progress-${i + 1}" max="100" style="width:70px;"
                     oninput="this.value = Math.min(100, Math.max(0, this.value))"
                     value="${progressValue}">
              <span class="small">%</span>
            </div>
            <div class="d-flex align-items-center gap-1 ms-2">
              <label class="form-label mb-0 small">Lane:</label>
              <label class="form-check form-check-inline mb-0">
                <input class="form-check-input" type="radio" name="lane-${i + 1}" value="inside" ${isOdd ? 'checked' : ''}>
                <span class="form-check-label small">IN</span>
              </label>
              <label class="form-check form-check-inline mb-0">
                <input class="form-check-input" type="radio" name="lane-${i + 1}" value="outside" ${!isOdd ? 'checked' : ''}>
                <span class="form-check-label small">OUT</span>
              </label>
            </div>
          </div>
        `;
        innerContainer.appendChild(block);
      }
    } else {
      objectLocationWrapper.classList.add('d-none');
      const innerContainer = objectLocationWrapper.querySelector('.card-body');
      if (innerContainer) innerContainer.innerHTML = '';
    }
  }


  // 각 탭의 상태를 저장할 객체
  const tabStates = {
    // 초기 상태값으로 기본값 설정 - null은 DOM에서 읽도록
    'tabs-main': {
      clockDirection: null,
      raceType: null, // DOM에서 읽도록 null
      alternateTrain: null,
      objectPosition: null, // DOM에서 읽도록 null
      objectCount: null,
      trackId: null,
      trackName: null,
      trackImage: null
    }
  };

  // 현재 화면에 노출된 탭을 기억
  let activePane = document.querySelector('.tab-pane.active.show');

  // 탭 전환 시 activePane 갱신 및 상태 저장/복원 (Bootstrap 5)
  document.querySelectorAll('[data-bs-toggle="tab"]').forEach(tab => {
    tab.addEventListener('shown.bs.tab', e => {
      // 이전 탭의 상태 저장
      if (activePane) {
        saveTabState(activePane);
        // console.log(`${activePane.id} 상태 저장:`, tabStates[activePane.id]);
      }

      // 새 탭 참조 갱신
      activePane = document.querySelector(e.target.getAttribute('href'));

      // 새 탭 상태 복원
      restoreTabState(activePane);
      //console.log(`${activePane.id} 상태 복원:`, tabStates[activePane.id]);
    });
  });

  // 탭의 상태를 저장하는 함수
  function saveTabState(pane) {
    if (!pane) return;

    const tabId = pane.id;

    // 기존 상태가 없으면 새로운 객체 생성, 있으면 기존 상태 복사
    // DOM에서 실제 값을 읽으므로 기본값은 null로 설정
    const state = tabStates[tabId] || {
      clockDirection: null,
      raceType: null,
      alternateTrain: null,
      objectPosition: null,
      objectCount: null,
      trackId: null,
      trackName: null,
      trackImage: null,
      objectType: null,
      objectLocations: []
    };

    // Direction 라디오 버튼 상태 저장
    const tabSuffix = pane.id.replace('tabs-', '');
    const clockDirName = tabSuffix === 'main' ? 'clock-direction' : `clock-direction-${tabSuffix}`;
    const clockDirection = pane.querySelector(`input[name="${clockDirName}"]:checked`);
    if (clockDirection) {
      state.clockDirection = clockDirection.value;
    }

    // Race Type 라디오 버튼 상태 저장
    const raceTypeName = tabSuffix === 'main' ? 'race-type' : `race-type-${tabSuffix}`;
    const raceType = pane.querySelector(`input[name="${raceTypeName}"]:checked`);
    if (raceType) {
      state.raceType = raceType.value;
    }

    // Alternate Training 체크박스 상태 저장
    // 탭이 main인 경우 'alternate-training-main' ID 사용, 그렇지 않으면 'alternate-sub숫자' ID 사용
    const alternateTrainId = tabSuffix === 'main' ? 'alternate-training-main' : `alternate-${tabSuffix}`;
    const alternateTrain = document.getElementById(alternateTrainId);
    if (alternateTrain) {
      state.alternateTrain = alternateTrain.checked;
    }

    // Object Position 체크박스 상태 저장
    const objectPosition = pane.querySelector('input[id^="object-position"]');
    if (objectPosition) {
      state.objectPosition = objectPosition.checked;
    }

    // Number of Objects 셀렉트 상태 저장
    const objectCount = pane.querySelector('select[id^="number-of-objects"]');
    if (objectCount) {
      state.objectCount = objectCount.value;
    }

    // Object Type 셀렉트 상태 저장
    const objectType = pane.querySelector('select[name^="object-type"]');
    if (objectType) {
      state.objectType = objectType.value;
    }

    // 트랙 정보는 이미 트랙을 선택할 때 저장되므로, 여기서는 트랙 프리뷰 정보만 가져옴
    const tabSuffixPreview = pane.id.replace('tabs-', '');
    const trackPreviewId = tabSuffixPreview === 'main' ? 'track-preview-box' : `track-preview-box-${tabSuffixPreview}`;
    const trackPreview = pane.querySelector(`#${trackPreviewId}`);

    if (trackPreview && trackPreview.innerHTML && !state.trackImage) {
      const imgElement = trackPreview.querySelector('img');
      const nameSpan = trackPreview.querySelector('span.text-muted');

      if (imgElement) {
        state.trackImage = imgElement.src;
      }

      if (nameSpan) {
        state.trackName = nameSpan.textContent.trim();
      }
    }

    // 오브젝트 위치 정보 저장 (Randomize가 체크되지 않았을 때)
    if (state.raceType === 'OBJECT_AVOIDANCE' && !state.objectPosition) {
      state.objectLocations = [];
      const objectBlocks = pane.querySelectorAll('.obstable-block');

      objectBlocks.forEach((block, index) => {
        const progress = block.querySelector(`input[name^="progress-"]`);
        const lane = block.querySelector(`input[name^="lane-"]:checked`);

        if (progress && lane) {
          state.objectLocations.push({
            index: index,
            progress: progress.value,
            lane: lane.value
          });
        }
      });
    }

    // 상태 객체에 저장
    tabStates[tabId] = state;
  }

  // 탭의 상태를 복원하는 함수
  function restoreTabState(pane) {
    if (!pane) return;

    const tabId = pane.id;
    const state = tabStates[tabId];

    if (!state) return;

    // Direction 라디오 버튼 상태 복원
    if (state.clockDirection) {
      const tabSuffix = pane.id.replace('tabs-', '');
      const clockDirName = tabSuffix === 'main' ? 'clock-direction' : `clock-direction-${tabSuffix}`;
      const clockDirection = pane.querySelector(`input[name="${clockDirName}"][value="${state.clockDirection}"]`);
      if (clockDirection) {
        clockDirection.checked = true;
      }
    }

    // Race Type 라디오 버튼 상태 복원
    if (state.raceType) {
      const tabSuffixRace = pane.id.replace('tabs-', '');
      const raceTypeName = tabSuffixRace === 'main' ? 'race-type' : `race-type-${tabSuffixRace}`;
      const raceType = pane.querySelector(`input[name="${raceTypeName}"][value="${state.raceType}"]`);
      if (raceType) {
        raceType.checked = true;
        // Object Avoidance 관련 UI 표시 여부 설정
        const raceTypeWrapperId = tabSuffixRace === 'main' ? 'race-type-wrapper' : `race-type-wrapper-${tabSuffixRace}`;
        const raceTypeWrapper = pane.querySelector(`#${raceTypeWrapperId}`);
        if (raceTypeWrapper) {
          raceTypeWrapper.classList.toggle('d-none', state.raceType !== 'OBJECT_AVOIDANCE');
        }
      }
    }

    // Alternate Training 체크박스 상태 복원
    const tabSuffixAlt = pane.id.replace('tabs-', '');
    const alternateTrainId = tabSuffixAlt === 'main' ? 'alternate-training-main' : `alternate-${tabSuffixAlt}`;
    const alternateTrain = document.getElementById(alternateTrainId);
    if (alternateTrain && state.alternateTrain !== undefined) {
      alternateTrain.checked = state.alternateTrain;
    }

    // Object Position 체크박스 상태 복원 (null이 아닌 경우만)
    const objectPosition = pane.querySelector('input[id^="object-position"]');
    if (objectPosition && state.objectPosition !== null && state.objectPosition !== undefined) {
      objectPosition.checked = state.objectPosition;
    }

    // Number of Objects 셀렉트 상태 복원 (null이 아닌 경우만)
    const objectCount = pane.querySelector('select[id^="number-of-objects"]');
    if (objectCount && state.objectCount !== null && state.objectCount !== undefined) {
      objectCount.value = state.objectCount;
    }

    // Object Type 셀렉트 상태 복원 (null이 아닌 경우만)
    const objectType = pane.querySelector('select[name^="object-type"]');
    if (objectType && state.objectType !== null && state.objectType !== undefined) {
      objectType.value = state.objectType;
    }

    // 트랙 프리뷰 복원
    const tabSuffixPreview = tabId.replace('tabs-', '');
    const trackPreviewId = tabSuffixPreview === 'main' ? 'track-preview-box' : `track-preview-box-${tabSuffixPreview}`;
    const trackPreview = pane.querySelector(`#${trackPreviewId}`);

    if (trackPreview) {
      if (state.trackImage) {
        trackPreview.innerHTML = `
          <img src="${state.trackImage}" alt="Selected Track" 
              style="max-height: 210px; width:100%; margin-bottom: 8px;">
          <span class="text-muted small">${state.trackName || ''}</span>
        `;
      }
    }

    // 오브젝트 위치 정보 복원 (Randomize 체크박스 상태에 따라)
    const objectLocationWrap = pane.querySelector('#object-location-wrapper');
    if (objectLocationWrap && state.raceType === 'OBJECT_AVOIDANCE') {
      // Randomize Object Locations 체크박스 상태에 맞게 표시/숨김 처리
      objectLocationWrap.classList.toggle('d-none', state.objectPosition || !state.objectCount);

      // Randomize가 체크되지 않았고 object count가 있을 때만 오브젝트 위치 렌더링
      if (!state.objectPosition && state.objectCount > 0 && state.objectLocations?.length > 0) {
        const inner = objectLocationWrap.querySelector('.card-body');
        if (inner) {
          inner.innerHTML = ''; // 기존 내용 삭제

          // 저장된 오브젝트 위치 정보 복원
          state.objectLocations.forEach((obj, i) => {
            const isOdd = (i + 1) % 2 === 1;

            inner.insertAdjacentHTML('beforeend', `
              <div class="row mb-4 obstable-block">
                <div class="col-12 mb-3">
                  <div class="border rounded p-3 shadow-sm bg-white">
                    <div class="row">
                      <div class="col-md-2 d-flex align-items-center justify-content-center">
                        <h3>Object ${i + 1}</h3>
                      </div>
                      <div class="col-md-5">
                        <label class="form-label">Progress</label>
                        <input type="number" step="any" class="form-control mb-2 progress-valid"
                              name="progress-${pane.id}-${i + 1}" max="100"
                              style="width:50%;" value="${obj.progress}"
                              oninput="this.value=Math.min(100,Math.max(0,this.value))">
                      </div>
                      <div class="col-md-5">
                        <label class="form-label">Lane</label>
                        <div class="mt-1">
                          <label class="form-check form-check-inline">
                            <input class="form-check-input" type="radio"
                                  name="lane-${pane.id}-${i + 1}" value="inside"
                                  ${obj.lane === 'inside' ? 'checked' : ''}>
                            <span class="form-check-label">INSIDE</span>
                          </label>
                          <label class="form-check form-check-inline">
                            <input class="form-check-input" type="radio"
                                  name="lane-${pane.id}-${i + 1}" value="outside"
                                  ${obj.lane === 'outside' ? 'checked' : ''}>
                            <span class="form-check-label">OUTSIDE</span>
                          </label>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            `);
          });
        }
      } else if (!state.objectPosition && state.objectCount > 0) {
        // 상태는 있지만 위치 정보가 없는 경우 기본 위치 렌더링 호출
        const renderLocFunc = window[`renderObjectLocations_${pane.id}`];
        if (typeof renderLocFunc === 'function') {
          renderLocFunc();
        } else {
          // 기본 렌더링 함수로 대체
          renderObjectLocations();
        }
      }
    }
  }


  /* ------------------------------------------------------------------ */
  /*  탭 하나를 초기화하는 헬퍼                                           */
  /* ------------------------------------------------------------------ */
  function initSimulationPane(pane) {
    // pane.querySelector 단축용 헬퍼
    const $ = sel => pane.querySelector(sel);
    const $$ = sel => pane.querySelectorAll(sel);

    /* --------- 요소 캐시 --------- */
    const tabId = pane.id;
    const modelNameInput = $('#model-name-id');

    // 탭 suffix 생성
    const tabSuffix = tabId.replace('tabs-', '');
    const raceTypeName = tabSuffix === 'main' ? 'race-type' : `race-type-${tabSuffix}`;
    const raceTypeWrapperId = tabSuffix === 'main' ? 'race-type-wrapper' : `race-type-wrapper-${tabSuffix}`;

    const raceTypeRadios = $$(`[name="${raceTypeName}"]`);
    const raceTypeWrapper = $(`#${raceTypeWrapperId}`);
    const objectPositionInput = $(`#object-position${tabSuffix !== 'main' ? `-${tabSuffix}` : ''}`);
    const objectCountSelect = $(`#number-of-objects${tabSuffix !== 'main' ? `-${tabSuffix}` : ''}`);
    const objectTypeSelect = $(`select[name^="object-type${tabSuffix !== 'main' ? `-${tabSuffix}` : ''}"]`);
    const objectLocationWrap = $(`#object-location-wrapper${tabSuffix !== 'main' ? `-${tabSuffix}` : ''}`);
    const trackPreviewId = tabSuffix === 'main' ? 'track-preview-box' : `track-preview-box-${tabSuffix}`;
    const trackPreviewElem = $(`#${trackPreviewId}`);
    const subSimulationCount = $('#sub-simulation-count-id');
    const subNavItems = $$('.sub-nav-item');

    // 탭 초기 상태 설정 - settings-manager.js가 API에서 로드 후 설정하므로 기본값은 null
    // 탭 전환 시 saveTabState에서 DOM 현재값을 저장함
    if (!tabStates[tabId]) {
      tabStates[tabId] = {
        clockDirection: null,
        raceType: null,  // API에서 로드
        alternateTrain: null,
        objectPosition: null,  // API에서 로드
        objectCount: null,  // API에서 로드
        objectType: null,  // API에서 로드
        trackId: null,
        trackName: null,
        trackImage: null,
        objectLocations: []
      };
    }

    /* ------------------ 공용 유틸 ------------------ */
    const renderObjectLocations = () => {
      // 이 함수는 각 탭마다 독립적으로 동작
      if (!objectPositionInput || !objectCountSelect || !objectLocationWrap) return;

      const count = parseInt(objectCountSelect.value, 10);
      const inner = objectLocationWrap.querySelector('.card-body');

      if (!inner) return;

      if (!objectPositionInput.checked && count > 0) {
        objectLocationWrap.classList.remove('d-none');
        inner.innerHTML = '';    // 기존 내용 삭제

        for (let i = 0; i < count; i++) {
          const isOdd = (i + 1) % 2 === 1;
          const prog = ((100 / (count + 1)) * (i + 1)).toFixed(0);

          inner.insertAdjacentHTML('beforeend', `
            <div class="row mb-4 obstable-block">
              <div class="col-12 mb-3">
                <div class="border rounded p-3 shadow-sm bg-white">
                  <div class="row">
                    <div class="col-md-2 d-flex align-items-center justify-content-center">
                      <h3>Object ${i + 1}</h3>
                    </div>
                    <div class="col-md-5">
                      <label class="form-label">Progress</label>
                      <input type="number" step="any" class="form-control mb-2 progress-valid"
                            name="progress-${tabId}-${i + 1}" max="100"
                            style="width:50%;" value="${prog}"
                            oninput="this.value=Math.min(100,Math.max(0,this.value))">
                    </div>
                    <div class="col-md-5">
                      <label class="form-label">Lane</label>
                      <div class="mt-1">
                        <label class="form-check form-check-inline">
                          <input class="form-check-input" type="radio"
                                name="lane-${tabId}-${i + 1}" value="inside"
                                ${isOdd ? 'checked' : ''}>
                          <span class="form-check-label">INSIDE</span>
                        </label>
                        <label class="form-check form-check-inline">
                          <input class="form-check-input" type="radio"
                                name="lane-${tabId}-${i + 1}" value="outside"
                                ${!isOdd ? 'checked' : ''}>
                          <span class="form-check-label">OUTSIDE</span>
                        </label>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>`);
        }

        // 상태에 위치 정보 저장
        saveObjectLocations();
      } else {
        objectLocationWrap.classList.add('d-none');
        inner.innerHTML = '';

        // 위치 정보 초기화
        if (tabStates[tabId]) {
          tabStates[tabId].objectLocations = [];
        }
      }
    };

    // 전역 공간에 등록 (다른 코드에서 호출할 수 있도록)
    window[`renderObjectLocations_${tabId}`] = renderObjectLocations;

    // 객체 위치 정보를 저장하는 헬퍼 함수
    function saveObjectLocations() {
      if (!tabStates[tabId] || !objectLocationWrap) return;

      const objectBlocks = objectLocationWrap.querySelectorAll('.obstable-block');
      tabStates[tabId].objectLocations = [];

      objectBlocks.forEach((block, index) => {
        const progress = block.querySelector(`input[name^="progress-"]`);
        const lane = block.querySelector(`input[name^="lane-"]:checked`);

        if (progress && lane) {
          tabStates[tabId].objectLocations.push({
            index: index,
            progress: progress.value,
            lane: lane.value
          });
        }
      });

    }

    /* ------------------ 이벤트 연결 ------------------ */

    // 트랙 선택 버튼 이벤트 등록
    const chooseTrackBtn = $('a[data-bs-toggle="modal"][data-bs-target="#modal-report"]');
    if (chooseTrackBtn) {
      chooseTrackBtn.addEventListener('click', function () {
        currentActiveTabForTrack = tabId;
        // syncTrackModal 함수가 window 객체에 있는지 확인 후 호출
        if (typeof window.syncTrackModal === 'function') {
          window.syncTrackModal(tabId);
        }
      });
    }
    // 트랙 라디오 change 이벤트 등록 (중복 제거)
    $$('input[name="form-imagecheck-radio"]').forEach(radio =>
      radio.addEventListener('change', function () {
        handleTrackRadioChange(tabId, this);
      })
    );

    // 레이스 타입: object_avoidance 선택 시 세부 영역 토글
    if (raceTypeRadios && raceTypeRadios.length > 0 && raceTypeWrapper) {
      raceTypeRadios.forEach(radio => {
        radio.addEventListener('change', function () {
          // 선택한 값이 object_avoidance인 경우 표시, 아니면 숨김
          const isObjectAvoidance = this.value === 'OBJECT_AVOIDANCE';
          // 탭 별 race-type-wrapper 사용
          if (raceTypeWrapper) {
            raceTypeWrapper.classList.toggle('d-none', !isObjectAvoidance);
          }

          // 상태 갱신
          if (tabStates[tabId]) {
            tabStates[tabId].raceType = this.value;
          }

        });

        // 저장된 상태에 따라 초기 상태 설정
        if (tabStates[tabId] && tabStates[tabId].raceType) {
          if (radio.value === tabStates[tabId].raceType) {
            radio.checked = true;
            if (raceTypeWrapper) {
              raceTypeWrapper.classList.toggle('d-none', radio.value !== 'OBJECT_AVOIDANCE');
            }
          }
        }
      });
    }

    // 모델명 유효성
    if (modelNameInput) {
      modelNameInput.addEventListener('change', function () {
        const ok = /^[a-zA-Z0-9_.-]+$/.test(this.value.trim());
        this.classList.toggle('is-valid', ok);
        this.classList.toggle('is-invalid', !ok);
        if (!ok) this.focus();
      });
    }

    // Object Type - 이벤트 리스너만 등록 (초기값 설정은 settings-manager.js가 담당)
    if (objectTypeSelect) {
      objectTypeSelect.addEventListener('change', function () {
        if (tabStates[tabId]) {
          tabStates[tabId].objectType = this.value;
        }
      });
      // 초기 상태 설정 제거 - settings-manager.js가 API에서 로드한 값 적용
    }

    // 오브젝트 배치 - 이벤트 리스너만 등록 (초기값 설정은 settings-manager.js가 담당)
    if (objectPositionInput && objectCountSelect) {
      objectPositionInput.addEventListener('change', function () {
        // 상태 갱신
        if (tabStates[tabId]) {
          tabStates[tabId].objectPosition = this.checked;
        }
        renderObjectLocations();
      });

      objectCountSelect.addEventListener('change', function () {
        // 상태 갱신
        if (tabStates[tabId]) {
          tabStates[tabId].objectCount = this.value;
        }
        renderObjectLocations();
      });

      // 초기 상태 설정 제거 - settings-manager.js가 API에서 로드한 값 적용
      // renderObjectLocations 호출도 제거 - settings-manager.js가 담당
    }

    // 서브 시뮬레이션 카운트 → 아코디언/탭 활성
    // 메인 탭에서만 등록
    if (tabId === 'tabs-main' && subSimulationCount) {
      subSimulationCount.addEventListener('change', function () {
        const n = Number(this.value);
        subNavItems.forEach((item, idx) =>
          item.classList.toggle('d-none', idx > n));
      });
    }

    /* ---------- 트랙 프리뷰(모달 선택) ---------- */
    // 모든 탭에서 공통으로 트랙 선택 모달 이벤트 등록
    $$('input[name="form-imagecheck-radio"]').forEach(radio =>
      radio.addEventListener('change', function () {
        const imgSrc = this.closest('label')?.querySelector('img')?.src || '';
        const nameStr = this.dataset.trackName || '';
        const trackId = this.value;
        const dirStr = (this.dataset.trackDirection || '').split(',').map(s => s.trim());

        // 방향 라디오 활성/비활성
        const tabSuffixInner = tabId.replace('tabs-', '');
        const clockDirName = tabSuffixInner === 'main' ? 'clock-direction' : `clock-direction-${tabSuffixInner}`;
        const clockDirectionRadios = $$(`input[name="${clockDirName}"]`);

        clockDirectionRadios.forEach(r => {
          const ok = dirStr.includes(r.value);
          r.disabled = !ok;
          if (!ok) r.checked = false;
          r.closest('label').classList.toggle('text-muted', !ok);
        });

        if (dirStr.length === 1) {
          const only = $(`input[name="${clockDirName}"][value="${dirStr[0]}"]`);
          if (only) {
            only.checked = true;
            // 상태 갱신
            if (tabStates[tabId]) {
              tabStates[tabId].clockDirection = dirStr[0];
            }
          }
        }

        // 프리뷰 렌더
        if (trackPreviewElem) {
          trackPreviewElem.innerHTML = `
            <img src="${imgSrc}" alt="Selected Track"
                style="max-height:210px;width:100%;margin-bottom:8px;">
            <span class="text-muted small">${nameStr}</span>`;
        }

        // 상태에 트랙 정보 저장
        if (tabStates[tabId]) {
          tabStates[tabId].trackId = trackId;
          tabStates[tabId].trackName = nameStr;
          tabStates[tabId].trackImage = imgSrc;
        }

        // 모달 닫기
        document.querySelector('#modal-report .btn-close')?.click();
      })
    );

    // 기본 트랙 이미지 설정 (처음 로드 시)
    // create_model.html에서 직접 처리하도록 코드 이동됨
  }

  /* ------------------------------------------------------------------ */
  /*  페이지 진입 시 각 탭을 초기화                                       */
  /* ------------------------------------------------------------------ */
  document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.simulation-pane').forEach(initSimulationPane);

    // 메인 탭 상태 복원은 제거 - settings-manager.js가 API에서 로드한 설정을 적용하므로
    // restoreTabState가 덮어쓰면 안됨
    // const mainTab = document.getElementById('tabs-main');
    // if (mainTab) {
    //   restoreTabState(mainTab);
    // }

    // 데이터 제출 버튼 이벤트 리스너 (제출 버튼이 있는 경우)
    const submitButton = document.getElementById('submit-model-btn');

    // 초기 상태에서 버튼 활성화 (disabled 속성 제거 및 disabled 클래스 제거)
    submitButton.disabled = false;
    submitButton.classList.remove('disabled');

    submitButton.addEventListener("click", function () {

      // 모델명 유효성 검사
      const modelName = modelNameInput.value.trim();
      const pattern = /^[a-zA-Z0-9_.-]+$/;

      if (!modelName || !pattern.test(modelName)) {
        // 모델명이 비어있거나 패턴에 맞지 않으면 오류 표시
        modelNameInput.classList.remove('is-valid');
        modelNameInput.classList.add('is-invalid');
        modelNameInput.focus();
        return; // 클릭 이벤트 처리 중단
      }

      // 로딩 스피너 표시
      const loadingSpinner = document.getElementById('createModelSpinner');
      if (loadingSpinner) loadingSpinner.classList.remove('d-none');
      this.disabled = true;
      this.classList.add('disabled'); // disabled 클래스 추가

      // 검증이 안 된 경우 먼저 검증
      if (!submitCodeBtnClicked) {
        submitCodeBtn.click();
        setTimeout(() => {
          if (!checkForErrors()) {
            // 에러가 없으면 제출 진행
            submitModelData();
          } else {
            // 에러가 있으면 버튼 상태 복원
            if (loadingSpinner) loadingSpinner.classList.add('d-none');
            this.disabled = false;
            this.classList.remove('disabled'); // disabled 클래스 제거
          }
        }, 1000);
        return;
      }

      // 이미 검증이 완료된 경우, 에러 확인 후 제출
      if (!checkForErrors()) {
        submitModelData();
      } else {
        // 에러가 있으면 버튼 상태 복원
        if (loadingSpinner) loadingSpinner.classList.add('d-none');
        this.disabled = false;
        this.classList.remove('disabled'); // disabled 클래스 제거
      }
    });
  });

  /* ------------------------------------------------------------------ */
  /*  모든 탭의 데이터 수집 및 서버로 전송                                */
  /* ------------------------------------------------------------------ */
  // 에러가 있는지 확인하는 함수
  function checkForErrors() {
    const responseOutput = document.getElementById('responseOutput');
    if (!responseOutput.classList.contains("d-none")) {
      responseOutput.scrollIntoView({ behavior: 'smooth', block: 'center' });
      return true; // 에러 있음
    }
    return false; // 에러 없음
  }

  function submitModelData() {
    // 모델 이름 유효성 체크
    const modelName = modelNameInput.value.trim();
    const pattern = /^[a-zA-Z0-9_.-]+$/;

    // 모델명 검증 실패 시 처리
    if (!pattern.test(modelName)) {
      // 오류 표시
      modelNameInput.classList.remove('is-valid');
      modelNameInput.classList.add('is-invalid');
      modelNameInput.focus();
      return; // 함수 실행 중단
    }

    // collectFormData()를 사용하여 CreateModelRequest 스키마에 맞는 데이터 수집
    const apiData = window.collectFormData();
    
    // Clone 모드 여부 확인
    const isCloneMode = window.isCloneMode || document.getElementById('is-clone-mode')?.value === 'true';
    const apiEndpoint = isCloneMode ? '/api/training/clone' : '/api/training/start';
    
    console.log(`API 전송 데이터 (${isCloneMode ? 'CloneModelRequest' : 'CreateModelRequest'}):`, apiData);

    // 로딩 표시 시작
    const submitButton = document.getElementById('submit-model-btn');
    const loadingSpinner = document.getElementById('createModelSpinner');

    if (submitButton) {
      submitButton.disabled = true;
      submitButton.classList.add('disabled');
    }
    if (loadingSpinner) loadingSpinner.classList.remove('d-none');

    // 서버로 데이터 전송
    fetch(apiEndpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(apiData)
    })
      .then(async response => {
        const submitBtn = document.getElementById('submit-model-btn');
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.classList.remove('disabled');
        }
        if (loadingSpinner) loadingSpinner.classList.add('d-none');

        const ctype = response.headers.get('content-type') || '';

        // HTML(리다이렉트 페이지)인 경우 → 그냥 이동
        if (!ctype.includes('application/json')) {
          window.location.href = response.url;
          return;
        }

        // JSON인 경우 → 파싱 후 처리
        const data = await response.json();

        if (data.success) {
          console.log('훈련 시작 성공:', data);
          // 성공 시 모델 상세 페이지로 이동
          window.location.href = `/pages/models/model?model_name=${data.model_name}`;
        } else if (data.detail) {
          // FastAPI HTTPException 에러
          Swal.fire({
            title: 'Error',
            text: data.detail,
            icon: 'error',
            confirmButtonText: 'OK'
          });
        } else {
          // 기타 에러
          Swal.fire({
            title: 'Error',
            text: data.message || '알 수 없는 오류가 발생했습니다.',
            icon: 'error',
            confirmButtonText: 'OK'
          });
        }
      })
      .catch(error => {
        const submitBtn = document.getElementById('submit-model-btn');
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.classList.remove('disabled');
        }
        if (loadingSpinner) loadingSpinner.classList.add('d-none');
        console.error('네트워크 오류:', error);
        
        Swal.fire({
          title: 'Error',
          text: '서버 연결 오류가 발생했습니다.',
          icon: 'error',
          confirmButtonText: 'OK'
        });
      });
  }

  function stopAllJobs() {
    // 모든 작업 중지 요청
    console.log("모든 작업 중지 요청");

    fetch('/api/jobs/stop-all', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({})
    })
      .then(res => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then(data => {
        if (data.status === 'success') {
          console.log('모든 작업이 성공적으로 중지되었습니다.');
        } else {
          console.error('중지 중 오류 발생:', data.error);
        }
      })
      .catch(err => {
        console.error('네트워크 오류 또는 서버 에러:', err);
      });
  }

