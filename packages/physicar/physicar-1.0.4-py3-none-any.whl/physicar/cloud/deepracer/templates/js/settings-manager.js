/**
 * 설정 로드/저장 관리
 * - 페이지 로드 시 기존 설정 불러오기
 * - 사용자 입력 시 실시간 저장
 */

// 설정 저장 debounce 타이머
let saveTimers = {};

/**
 * debounce 저장 함수
 */
function debounceSave(key, saveFunc, delay = 500) {
  if (saveTimers[key]) {
    clearTimeout(saveTimers[key]);
  }
  saveTimers[key] = setTimeout(saveFunc, delay);
}

/**
 * 모든 설정 로드
 */
async function loadAllSettings() {
  try {
    const response = await fetch('/api/settings');
    if (!response.ok) {
      console.error('Failed to load settings:', response.status);
      return null;
    }
    return await response.json();
  } catch (error) {
    console.error('Error loading settings:', error);
    return null;
  }
}

/**
 * 시뮬레이션 설정 적용
 */
function applySimulationSettings(simSettings) {
  if (!simSettings) return;
  
  // 서브 시뮬레이션 수
  const subSimCountSelect = document.getElementById('sub-simulation-count-id');
  if (subSimCountSelect && simSettings.sub_simulation_count !== undefined) {
    // CPU가 줄어서 기존 값이 max를 초과하면 max로 설정
    const maxSubSim = simSettings.max_sub_simulation_count;
    const currentCount = Math.min(simSettings.sub_simulation_count, maxSubSim);
    subSimCountSelect.value = currentCount.toString();
    // 변경 이벤트 발생 (탭 표시/숨김 처리)
    subSimCountSelect.dispatchEvent(new Event('change'));
  }
  
  // 메인 시뮬레이션 설정
  if (simSettings.main) {
    applyMainSimulationSettings(simSettings.main);
  }
  
  // 서브 시뮬레이션 설정
  if (simSettings.sub_simulations) {
    simSettings.sub_simulations.forEach((subSim, index) => {
      applySubSimulationSettings(index, subSim);
    });
  }
  
  // Best Model Metric
  if (simSettings.best_model_metric) {
    const metricRadio = document.querySelector(`input[name="best_model_metric"][value="${simSettings.best_model_metric}"]`);
    if (metricRadio) {
      metricRadio.checked = true;
    }
  }
}

/**
 * 메인 시뮬레이션 설정 적용
 */
function applyMainSimulationSettings(mainSim) {
  // 트랙 (track-preview-box에 표시)
  if (mainSim.track_id) {
    const trackInput = document.querySelector(`input[name="form-imagecheck-radio"][value="${mainSim.track_id}"]`) ||
                       document.querySelector(`input[value="${mainSim.track_id}"]`);
    if (trackInput) {
      // 트랙 선택 클릭 시뮬레이션
      const label = trackInput.closest('label');
      if (label) {
        const img = label.querySelector('img');
        const trackName = trackInput.dataset.trackName || '';
        const trackWidth = trackInput.dataset.trackWidth || '-';
        const trackLength = trackInput.dataset.trackLength || '-';
        const trackDescription = trackInput.dataset.trackDescription || '';
        const trackDirection = trackInput.dataset.trackDirection || '';
        
        const trackPreviewElem = document.getElementById('track-preview-box');
        const trackDescElem = document.getElementById('track-description-box');
        
        if (trackPreviewElem && img) {
          trackPreviewElem.innerHTML = `
            <img src="${img.src}" alt="Track"
                 style="max-height:210px;width:100%;margin-bottom:8px;">
            <span class="text-muted small">${trackName}</span>`;
        }
        if (trackDescElem) {
          trackDescElem.innerHTML = `
            <h5 class="mb-3">${trackName}</h5>
            <div class="mb-2"><strong>Width:</strong> ${trackWidth}</div>
            <div class="mb-2"><strong>Length:</strong> ${trackLength}</div>
            <div class="mb-2"><strong>Direction:</strong> ${trackDirection.replace(/,/g, ', ')}</div>
            <div class="mt-3"><strong>Description:</strong><br><small class="text-muted">${trackDescription}</small></div>
          `;
        }
        if (window.tabStates && window.tabStates['tabs-main']) {
          window.tabStates['tabs-main'].trackId = mainSim.track_id;
          window.tabStates['tabs-main'].trackName = trackName;
        }
      }
    }
  }
  
  // Race Type (API: TIME_TRIAL/OBJECT_AVOIDANCE, HTML: TIME_TRIAL/OBJECT_AVOIDANCE)
  if (mainSim.race_type) {
    const raceTypeValue = mainSim.race_type.toUpperCase();
    const raceTypeRadio = document.querySelector(`input[name="race-type"][value="${raceTypeValue}"]`);
    if (raceTypeRadio) {
      raceTypeRadio.checked = true;
      raceTypeRadio.dispatchEvent(new Event('change'));
    }
  }
  
  // Direction (HTML: name="clock-direction")
  if (mainSim.direction) {
    const directionValue = mainSim.direction === 'counterclockwise' ? 'counterclockwise' : 'clockwise';
    const directionRadio = document.querySelector(`input[name="clock-direction"][value="${directionValue}"]`);
    if (directionRadio) {
      directionRadio.checked = true;
    }
  }
  
  // Alternate Direction
  const alternateCheckbox = document.getElementById('alternate-training-main');
  if (alternateCheckbox && mainSim.alternate_direction !== undefined) {
    alternateCheckbox.checked = mainSim.alternate_direction;
  }
  
  // Object Avoidance 설정
  if (mainSim.object_avoidance) {
    const oa = mainSim.object_avoidance;
    
    // Number of obstacles
    const numObstacles = document.getElementById('number-of-objects');
    if (numObstacles && oa.number_of_obstacles) {
      numObstacles.value = oa.number_of_obstacles.toString();
    }
    
    // Object Type - select 요소에 값 설정
    const objectType = document.querySelector('select[name="object-type"]');
    if (objectType && oa.object_type) {
      // 옵션이 존재하는지 확인 후 설정
      const optionExists = Array.from(objectType.options).some(opt => opt.value === oa.object_type);
      if (optionExists) {
        objectType.value = oa.object_type;
      } else {
        console.warn(`[applyMainSimulationSettings] object_type "${oa.object_type}" 옵션 없음`);
      }
    }
    
    // Randomize locations checkbox
    const objectPosition = document.getElementById('object-position');
    if (objectPosition && oa.randomize_locations !== undefined) {
      objectPosition.checked = oa.randomize_locations;
    }
    
    // object-location-wrapper 표시/숨김 (randomize 상태에 따라)
    const wrapper = document.getElementById('object-location-wrapper');
    if (wrapper) {
      if (oa.randomize_locations) {
        wrapper.classList.add('d-none');
      } else {
        wrapper.classList.remove('d-none');
        // object_positions UI 렌더링
        renderObjectPositions('object-location-wrapper-inside', oa.object_positions || [], oa.number_of_obstacles || 3);
      }
    }
  }
}

/**
 * 서브 시뮬레이션 설정 적용
 */
function applySubSimulationSettings(index, subSim) {
  const subKey = `sub${index + 1}`;
  
  // 트랙
  if (subSim.track_id) {
    const trackPreviewElem = document.getElementById(`track-preview-box-${subKey}`);
    const trackDescElem = document.getElementById(`track-description-box-${subKey}`);
    const trackInput = document.querySelector(`input[name="form-imagecheck-radio"][value="${subSim.track_id}"]`) ||
                       document.querySelector(`input[value="${subSim.track_id}"]`);
    if (trackPreviewElem && trackInput) {
      const label = trackInput.closest('label');
      if (label) {
        const img = label.querySelector('img');
        const trackName = trackInput.dataset.trackName || '';
        const trackWidth = trackInput.dataset.trackWidth || '-';
        const trackLength = trackInput.dataset.trackLength || '-';
        const trackDescription = trackInput.dataset.trackDescription || '';
        const trackDirection = trackInput.dataset.trackDirection || '';
        
        if (img) {
          trackPreviewElem.innerHTML = `
            <img src="${img.src}" alt="Track"
                 style="max-height:210px;width:100%;margin-bottom:8px;">
            <span class="text-muted small">${trackName}</span>`;
        }
        if (trackDescElem) {
          trackDescElem.innerHTML = `
            <h5 class="mb-3">${trackName}</h5>
            <div class="mb-2"><strong>Width:</strong> ${trackWidth}</div>
            <div class="mb-2"><strong>Length:</strong> ${trackLength}</div>
            <div class="mb-2"><strong>Direction:</strong> ${trackDirection.replace(/,/g, ', ')}</div>
            <div class="mt-3"><strong>Description:</strong><br><small class="text-muted">${trackDescription}</small></div>
          `;
        }
        if (window.tabStates && window.tabStates[`tabs-${subKey}`]) {
          window.tabStates[`tabs-${subKey}`].trackId = subSim.track_id;
          window.tabStates[`tabs-${subKey}`].trackName = trackName;
        }
      }
    }
  }
  
  // Race Type (API: TIME_TRIAL/OBJECT_AVOIDANCE, HTML: TIME_TRIAL/OBJECT_AVOIDANCE)
  if (subSim.race_type) {
    const raceTypeValue = subSim.race_type.toUpperCase();
    const raceTypeRadio = document.querySelector(`#tabs-${subKey} input[name="race-type-${subKey}"][value="${raceTypeValue}"]`);
    if (raceTypeRadio) {
      raceTypeRadio.checked = true;
      raceTypeRadio.dispatchEvent(new Event('change'));
    }
  }
  
  // Direction (HTML: name="clock-direction-sub1", etc.)
  if (subSim.direction) {
    const directionValue = subSim.direction === 'counterclockwise' ? 'counterclockwise' : 'clockwise';
    const directionRadio = document.querySelector(`#tabs-${subKey} input[name="clock-direction-${subKey}"][value="${directionValue}"]`);
    if (directionRadio) {
      directionRadio.checked = true;
    }
  }
  
  // Alternate Direction
  const alternateCheckbox = document.getElementById(`alternate-${subKey}`);
  if (alternateCheckbox && subSim.alternate_direction !== undefined) {
    alternateCheckbox.checked = subSim.alternate_direction;
  }
  
  // Object Avoidance 설정
  if (subSim.object_avoidance) {
    const oa = subSim.object_avoidance;
    
    // Number of obstacles
    const numObstacles = document.getElementById(`number-of-objects-${subKey}`);
    if (numObstacles && oa.number_of_obstacles) {
      numObstacles.value = oa.number_of_obstacles.toString();
    }
    
    // Object Type - select 요소에 값 설정
    const objectType = document.querySelector(`select[name="object-type-${subKey}"]`);
    if (objectType && oa.object_type) {
      // 옵션이 존재하는지 확인 후 설정
      const optionExists = Array.from(objectType.options).some(opt => opt.value === oa.object_type);
      if (optionExists) {
        objectType.value = oa.object_type;
      } else {
      }
    }
    
    // Randomize locations checkbox
    const objectPosition = document.getElementById(`object-position-${subKey}`);
    if (objectPosition && oa.randomize_locations !== undefined) {
      objectPosition.checked = oa.randomize_locations;
    }
    
    // object-location-wrapper 표시/숨김 (randomize 상태에 따라)
    const wrapper = document.getElementById(`object-location-wrapper-${subKey}`);
    if (wrapper) {
      if (oa.randomize_locations) {
        wrapper.classList.add('d-none');
      } else {
        wrapper.classList.remove('d-none');
        // object_positions UI 렌더링
        renderObjectPositions(`object-location-wrapper-inside-${subKey}`, oa.object_positions || [], oa.number_of_obstacles || 3, subKey);
      }
    }
  }
}

/**
 * 차량/액션 스페이스 설정 적용
 */
function applyVehiclesSettings(vehiclesSettings) {
  if (!vehiclesSettings) return;
  
  // Vehicle Type
  const layoutSelect = document.getElementById('vehicle-layout');
  if (layoutSelect && vehiclesSettings.vehicle_type) {
    layoutSelect.value = vehiclesSettings.vehicle_type;
    layoutSelect.dispatchEvent(new Event('change'));
  }
  
  // Lidar
  const lidarCheckbox = document.getElementById('lidar-checkbox');
  if (lidarCheckbox && vehiclesSettings.lidar !== undefined) {
    lidarCheckbox.checked = vehiclesSettings.lidar;
    lidarCheckbox.dispatchEvent(new Event('change'));
  }
  
  // Action Space
  if (vehiclesSettings.action_space && Array.isArray(vehiclesSettings.action_space)) {
    // vehicles.js의 actions 배열에 반영
    if (typeof window.setActions === 'function') {
      window.setActions(vehiclesSettings.action_space);
    } else {
      // vehicles.js 로드 후에 설정
      window.pendingActionSpace = vehiclesSettings.action_space;
    }
  }
  
  // Max Training Time
  const maxTrainingTime = document.getElementById('max_training_time');
  if (maxTrainingTime && vehiclesSettings.max_training_time) {
    maxTrainingTime.value = vehiclesSettings.max_training_time;
  }
}

/**
 * 하이퍼파라미터 설정 적용
 */
function applyHyperparametersSettings(hpSettings) {
  if (!hpSettings) return;
  
  // Batch Size
  const batchSize = document.getElementById('batchSize');
  if (batchSize && hpSettings.batch_size) {
    batchSize.value = hpSettings.batch_size.toString();
  }
  
  // Discount Factor
  const discountFactor = document.querySelector('input[name="discount_factor"]');
  if (discountFactor && hpSettings.discount_factor !== undefined) {
    discountFactor.value = hpSettings.discount_factor;
  }
  
  // Learning Rate
  const learningRate = document.querySelector('input[name="learning_rate"]');
  if (learningRate && hpSettings.learning_rate !== undefined) {
    learningRate.value = hpSettings.learning_rate;
  }
  
  // Entropy
  const entropy = document.querySelector('input[name="entropy"]');
  if (entropy && hpSettings.entropy !== undefined) {
    entropy.value = hpSettings.entropy;
  }
  
  // Loss Type
  if (hpSettings.loss_type) {
    const lossTypeRadio = document.querySelector(`input[name="loss_type"][value="${hpSettings.loss_type}"]`);
    if (lossTypeRadio) {
      lossTypeRadio.checked = true;
    }
  }
}

/**
 * 보상 함수 적용
 */
function applyRewardFunction(rewardCode) {
  if (!rewardCode) return;
  
  // CodeMirror 에디터에 설정
  if (window.editor) {
    window.editor.setValue(rewardCode);
  } else {
    // 에디터가 아직 로드되지 않은 경우 textarea에 직접 설정
    const editorTextarea = document.getElementById('editor');
    if (editorTextarea) {
      editorTextarea.value = rewardCode;
    }
    // 에디터 로드 후 설정을 위해 저장
    window.pendingRewardFunction = rewardCode;
  }
}

/**
 * 실시간 저장 이벤트 바인딩
 * NOTE: 실시간 저장 비활성화됨 - Create Model 버튼 클릭 시 collectFormData()로 일괄 수집
 *       UI 이벤트 핸들러는 유지하되 실제 API 호출은 비활성화
 */
function bindSaveEvents() {
  // ============ 시뮬레이션 ============
  
  // 서브 시뮬레이션 수 변경 (실시간 저장 비활성화)
  const subSimCountSelect = document.getElementById('sub-simulation-count-id');
  if (subSimCountSelect) {
    subSimCountSelect.addEventListener('change', function() {
      // 실시간 저장 비활성화
      console.debug('[bindSaveEvents] sub-simulation-count 변경:', this.value);
      // fetch('/api/settings/simulation/count', {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify({ count: parseInt(this.value) })
      // });
    });
  }
  
  // 메인 시뮬레이션 설정 변경
  bindMainSimulationEvents();
  
  // 서브 시뮬레이션 설정 변경 (sub1 ~ sub6)
  bindSubSimulationEvents();
  
  // Best Model Metric
  document.querySelectorAll('input[name="best_model_metric"]').forEach(radio => {
    radio.addEventListener('change', function() {
      saveMainSimulation({ best_model_metric: this.value });
    });
  });
  
  // ============ 차량/액션 스페이스 ============
  
  // Vehicle Type
  const layoutSelect = document.getElementById('vehicle-layout');
  if (layoutSelect) {
    layoutSelect.addEventListener('change', function() {
      saveVehiclesSettings({ vehicle_type: this.value });
    });
  }
  
  // Lidar
  const lidarCheckbox = document.getElementById('lidar-checkbox');
  if (lidarCheckbox) {
    lidarCheckbox.addEventListener('change', function() {
      saveVehiclesSettings({ lidar: this.checked });
    });
  }
  
  // Max Training Time
  const maxTrainingTime = document.getElementById('max_training_time');
  if (maxTrainingTime) {
    maxTrainingTime.addEventListener('input', function() {
      debounceSave('max_training_time', () => {
        saveVehiclesSettings({ max_training_time: parseInt(this.value) || 60 });
      });
    });
  }
  
  // ============ 하이퍼파라미터 ============
  
  // Batch Size
  const batchSize = document.getElementById('batchSize');
  if (batchSize) {
    batchSize.addEventListener('change', function() {
      saveHyperparameters({ batch_size: parseInt(this.value) });
    });
  }
  
  // Discount Factor
  const discountFactor = document.querySelector('input[name="discount_factor"]');
  if (discountFactor) {
    discountFactor.addEventListener('input', function() {
      debounceSave('discount_factor', () => {
        saveHyperparameters({ discount_factor: parseFloat(this.value) });
      });
    });
  }
  
  // Learning Rate
  const learningRate = document.querySelector('input[name="learning_rate"]');
  if (learningRate) {
    learningRate.addEventListener('input', function() {
      debounceSave('learning_rate', () => {
        saveHyperparameters({ learning_rate: parseFloat(this.value) });
      });
    });
  }
  
  // Entropy
  const entropy = document.querySelector('input[name="entropy"]');
  if (entropy) {
    entropy.addEventListener('input', function() {
      debounceSave('entropy', () => {
        saveHyperparameters({ entropy: parseFloat(this.value) });
      });
    });
  }
  
  // Loss Type
  document.querySelectorAll('input[name="loss_type"]').forEach(radio => {
    radio.addEventListener('change', function() {
      saveHyperparameters({ loss_type: this.value });
    });
  });
  
  // ============ 보상 함수 ============
  // CodeMirror 에디터 변경 이벤트는 code-mirror.js에서 처리
}

/**
 * 메인 시뮬레이션 이벤트 바인딩
 */
function bindMainSimulationEvents() {
  // Race Type (값은 대문자로 변환해서 저장)
  document.querySelectorAll('input[name="race-type"]').forEach(radio => {
    radio.addEventListener('change', function() {
      saveMainSimulation({ race_type: this.value.toUpperCase() });
    });
  });
  
  // Direction (HTML: name="clock-direction")
  document.querySelectorAll('input[name="clock-direction"]').forEach(radio => {
    radio.addEventListener('change', function() {
      saveMainSimulation({ direction: this.value });
    });
  });
  
  // Alternate Direction
  const alternateMain = document.getElementById('alternate-training-main');
  if (alternateMain) {
    alternateMain.addEventListener('change', function() {
      saveMainSimulation({ alternate_direction: this.checked });
    });
  }
  
  // Object Avoidance
  const numObstacles = document.getElementById('number-of-objects');
  if (numObstacles) {
    numObstacles.addEventListener('change', function() {
      const numValue = parseInt(this.value);
      
      // randomize=False 상태면 UI를 먼저 업데이트하고 저장
      const objectPosition = document.getElementById('object-position');
      if (objectPosition && !objectPosition.checked) {
        // 클라이언트에서 바로 새 positions 생성하여 렌더링
        const newPositions = generateDefaultObjectPositions(numValue);
        renderObjectPositions('object-location-wrapper-inside', newPositions, numValue);
        
        // 서버에 저장 (서버에서도 동일한 positions 생성됨)
        saveMainSimulation({
          object_avoidance: { number_of_obstacles: numValue }
        });
      } else {
        saveMainSimulation({
          object_avoidance: { number_of_obstacles: numValue }
        });
      }
    });
  }
  
  const objectType = document.querySelector('select[name="object-type"]');
  if (objectType) {
    objectType.addEventListener('change', function() {
      saveMainSimulation({
        object_avoidance: { object_type: this.value }
      });
    });
  }
  
  const objectPosition = document.getElementById('object-position');
  if (objectPosition) {
    objectPosition.addEventListener('change', function() {
      const wrapper = document.getElementById('object-location-wrapper');
      
      if (wrapper) {
        if (this.checked) {
          wrapper.classList.add('d-none');
          saveMainSimulation({
            object_avoidance: { randomize_locations: true }
          });
        } else {
          wrapper.classList.remove('d-none');
          // 클라이언트에서 바로 기본 positions 생성하여 렌더링
          const numValue = parseInt(document.getElementById('number-of-objects')?.value || '3');
          const newPositions = generateDefaultObjectPositions(numValue);
          renderObjectPositions('object-location-wrapper-inside', newPositions, numValue);
          
          saveMainSimulation({
            object_avoidance: { randomize_locations: false }
          });
        }
      }
    });
  }
}

/**
 * 서브 시뮬레이션 이벤트 바인딩 (sub1 ~ sub6)
 */
function bindSubSimulationEvents() {
  for (let i = 1; i <= 6; i++) {
    const subKey = `sub${i}`;
    const index = i - 1;  // API는 0-based index
    
    // Race Type
    document.querySelectorAll(`input[name="race-type-${subKey}"]`).forEach(radio => {
      radio.addEventListener('change', function() {
        const raceType = this.value.toUpperCase();
        saveSubSimulation(index, { race_type: raceType });
        
        // Object Avoidance로 변경 시 기본값 설정
        if (raceType === 'OBJECT_AVOIDANCE') {
          // Object Type 기본값 설정
          const objectType = document.querySelector(`select[name="object-type-${subKey}"]`);
          if (objectType && !objectType.value) {
            objectType.value = 'box_obstacle';
          }
          
          // Randomize Locations 상태 확인하여 Object Locations UI 렌더링
          const objectPositionCheckbox = document.getElementById(`object-position-${subKey}`);
          const wrapper = document.getElementById(`object-location-wrapper-${subKey}`);
          if (objectPositionCheckbox && wrapper && !objectPositionCheckbox.checked) {
            wrapper.classList.remove('d-none');
            const numValue = parseInt(document.getElementById(`number-of-objects-${subKey}`)?.value || '3');
            const newPositions = generateDefaultObjectPositions(numValue);
            renderObjectPositions(`object-location-wrapper-inside-${subKey}`, newPositions, numValue, subKey);
          }
        }
      });
    });
    
    // Direction
    document.querySelectorAll(`input[name="clock-direction-${subKey}"]`).forEach(radio => {
      radio.addEventListener('change', function() {
        saveSubSimulation(index, { direction: this.value });
      });
    });
    
    // Alternate Direction
    const alternateSub = document.getElementById(`alternate-${subKey}`);
    if (alternateSub) {
      alternateSub.addEventListener('change', ((idx) => function() {
        saveSubSimulation(idx, { alternate_direction: this.checked });
      })(index));
    }
    
    // Object Avoidance - Number of Objects
    const numObstaclesSub = document.getElementById(`number-of-objects-${subKey}`);
    if (numObstaclesSub) {
      numObstaclesSub.addEventListener('change', ((idx, sk) => function() {
        const numValue = parseInt(this.value);
        
        // randomize=False 상태면 UI를 먼저 업데이트하고 저장
        const objectPositionCheckbox = document.getElementById(`object-position-${sk}`);
        if (objectPositionCheckbox && !objectPositionCheckbox.checked) {
          const newPositions = generateDefaultObjectPositions(numValue);
          renderObjectPositions(`object-location-wrapper-inside-${sk}`, newPositions, numValue, sk);
        }
        
        saveSubSimulation(idx, {
          object_avoidance: { number_of_obstacles: numValue }
        });
      })(index, subKey));
    }
    
    // Object Avoidance - Object Type
    const objectTypeSub = document.querySelector(`select[name="object-type-${subKey}"]`);
    if (objectTypeSub) {
      objectTypeSub.addEventListener('change', ((idx) => function() {
        saveSubSimulation(idx, {
          object_avoidance: { object_type: this.value }
        });
      })(index));
    }
    
    // Object Avoidance - Randomize Locations
    const objectPositionSub = document.getElementById(`object-position-${subKey}`);
    if (objectPositionSub) {
      objectPositionSub.addEventListener('change', ((idx, sk) => function() {
        const wrapper = document.getElementById(`object-location-wrapper-${sk}`);
        
        if (wrapper) {
          if (this.checked) {
            wrapper.classList.add('d-none');
            saveSubSimulation(idx, {
              object_avoidance: { randomize_locations: true }
            });
          } else {
            wrapper.classList.remove('d-none');
            const numValue = parseInt(document.getElementById(`number-of-objects-${sk}`)?.value || '3');
            const newPositions = generateDefaultObjectPositions(numValue);
            renderObjectPositions(`object-location-wrapper-inside-${sk}`, newPositions, numValue, sk);
            
            saveSubSimulation(idx, {
              object_avoidance: { randomize_locations: false }
            });
          }
        }
      })(index, subKey));
    }
  }
}

/**
 * 메인 시뮬레이션 저장
 * NOTE: 실시간 저장 비활성화 - Create Model 버튼 클릭 시 일괄 저장
 */
function saveMainSimulation(data) {
  // 실시간 저장 비활성화 (collectFormData에서 일괄 수집)
  // fetch('/api/settings/simulation/main', {
  //   method: 'POST',
  //   headers: { 'Content-Type': 'application/json' },
  //   body: JSON.stringify(data)
  // });
  console.debug('[saveMainSimulation] 실시간 저장 비활성화됨:', data);
}

/**
 * 서브 시뮬레이션 저장
 * NOTE: 실시간 저장 비활성화 - Create Model 버튼 클릭 시 일괄 저장
 */
function saveSubSimulation(index, data) {
  // 실시간 저장 비활성화 (collectFormData에서 일괄 수집)
  // fetch(`/api/settings/simulation/sub/${index}`, {
  //   method: 'POST',
  //   headers: { 'Content-Type': 'application/json' },
  //   body: JSON.stringify(data)
  // });
  console.debug(`[saveSubSimulation] 실시간 저장 비활성화됨 (sub${index}):`, data);
}

/**
 * 차량/액션 스페이스 저장 (debounce 적용)
 * NOTE: 실시간 저장 비활성화 - Create Model 버튼 클릭 시 일괄 저장
 */
let vehiclesDebounceTimer = null;

function saveVehiclesSettings(data) {
  // 실시간 저장 비활성화 (collectFormData에서 일괄 수집)
  console.debug('[saveVehiclesSettings] 실시간 저장 비활성화됨:', data);
  // if (data.action_space) {
  //   if (vehiclesDebounceTimer) {
  //     clearTimeout(vehiclesDebounceTimer);
  //   }
  //   vehiclesDebounceTimer = setTimeout(() => {
  //     vehiclesDebounceTimer = null;
  //     fetch('/api/settings/vehicles', {
  //       method: 'POST',
  //       headers: { 'Content-Type': 'application/json' },
  //       body: JSON.stringify(data)
  //     });
  //   }, 300);
  // } else {
  //   fetch('/api/settings/vehicles', {
  //     method: 'POST',
  //     headers: { 'Content-Type': 'application/json' },
  //     body: JSON.stringify(data)
  //   });
  // }
}

/**
 * 하이퍼파라미터 저장
 * NOTE: 실시간 저장 비활성화 - Create Model 버튼 클릭 시 일괄 저장
 */
function saveHyperparameters(data) {
  // 실시간 저장 비활성화 (collectFormData에서 일괄 수집)
  console.debug('[saveHyperparameters] 실시간 저장 비활성화됨:', data);
  // fetch('/api/settings/hyperparameters', {
  //   method: 'POST',
  //   headers: { 'Content-Type': 'application/json' },
  //   body: JSON.stringify(data)
  // });
}

/**
 * 보상 함수 저장
 * NOTE: 실시간 저장 비활성화 - Create Model 버튼 클릭 시 일괄 저장
 */
function saveRewardFunction(code) {
  // 실시간 저장 비활성화 (collectFormData에서 일괄 수집)
  console.debug('[saveRewardFunction] 실시간 저장 비활성화됨');
  // debounceSave('reward_function', () => {
  //   fetch('/api/settings/reward-function', {
  //     method: 'POST',
  //     headers: { 'Content-Type': 'application/json' },
  //     body: JSON.stringify({ code })
  //   });
  // }, 1000);
}

/**
 * 기본 object_positions 생성 (서버와 동일한 로직)
 */
function generateDefaultObjectPositions(numObstacles) {
  if (numObstacles <= 0) return [];
  
  const positions = [];
  for (let i = 0; i < numObstacles; i++) {
    // 트랙을 균등하게 분할 (0~100 사이, 정수)
    const progress = Math.round((i + 1) * 100 / (numObstacles + 1));
    // inside/outside 번갈아 배치
    const lane = i % 2 === 0 ? 'inside' : 'outside';
    positions.push({ progress, lane });
  }
  
  return positions;
}

/**
 * 액션 스페이스 저장 (vehicles.js에서 호출)
 * 설정 로드 완료 전에는 저장하지 않음
 */
let settingsLoaded = false;

function saveActionSpace(actions) {
  if (!settingsLoaded) return;  // 설정 로드 전에는 저장하지 않음
  saveVehiclesSettings({ action_space: actions });
}

/**
 * 트랙 선택 저장 (메인)
 */
function saveMainTrack(trackId) {
  saveMainSimulation({ track_id: trackId });
}

/**
 * 트랙 선택 저장 (서브)
 */
function saveSubTrack(index, trackId) {
  saveSubSimulation(index, { track_id: trackId });
}

// 전역 함수로 노출
window.saveActionSpace = saveActionSpace;
window.saveRewardFunction = saveRewardFunction;
window.saveMainTrack = saveMainTrack;
window.saveSubTrack = saveSubTrack;
window.saveMainSimulation = saveMainSimulation;
window.saveSubSimulation = saveSubSimulation;

/**
 * Object Positions UI 렌더링
 */
function renderObjectPositions(containerId, positions, numObstacles, simKey = 'main') {
  const container = document.getElementById(containerId);
  if (!container) return;
  
  // 기존 내용 제거
  container.innerHTML = '';
  
  // positions 배열이 numObstacles보다 작으면 기본값으로 채움
  const displayPositions = [];
  for (let i = 0; i < numObstacles; i++) {
    if (positions[i]) {
      displayPositions.push({
        progress: Math.round(positions[i].progress),
        lane: positions[i].lane
      });
    } else {
      // 기본값 생성 (정수)
      const progress = Math.round((i + 1) * 100 / (numObstacles + 1));
      const lane = i % 2 === 0 ? 'inside' : 'outside';
      displayPositions.push({ progress, lane });
    }
  }
  
  // 테이블 생성
  const table = document.createElement('table');
  table.className = 'table table-sm table-bordered';
  table.innerHTML = `
    <thead>
      <tr>
        <th style="width:60px">Idx</th>
        <th>Progress (%)</th>
        <th>Lane</th>
      </tr>
    </thead>
    <tbody id="object-positions-tbody-${simKey}">
    </tbody>
  `;
  container.appendChild(table);
  
  const tbody = table.querySelector('tbody');
  displayPositions.forEach((pos, idx) => {
    const row = document.createElement('tr');
    row.innerHTML = `
      <td>${idx}</td>
      <td>
        <input type="number" class="form-control form-control-sm object-progress" 
               data-index="${idx}" data-sim="${simKey}"
               min="0" max="100" step="1" value="${pos.progress}">
      </td>
      <td>
        <select class="form-select form-select-sm object-lane" data-index="${idx}" data-sim="${simKey}">
          <option value="inside" ${pos.lane === 'inside' ? 'selected' : ''}>Inside</option>
          <option value="outside" ${pos.lane === 'outside' ? 'selected' : ''}>Outside</option>
        </select>
      </td>
    `;
    tbody.appendChild(row);
  });
  
  // 이벤트 바인딩
  bindObjectPositionEvents(simKey);
}

/**
 * Object Position 변경 이벤트 바인딩
 */
function bindObjectPositionEvents(simKey) {
  const progressInputs = document.querySelectorAll(`.object-progress[data-sim="${simKey}"]`);
  const laneSelects = document.querySelectorAll(`.object-lane[data-sim="${simKey}"]`);
  
  const savePositions = () => {
    const positions = [];
    progressInputs.forEach((input, idx) => {
      const progress = Math.round(parseFloat(input.value)) || 0;
      const lane = laneSelects[idx]?.value || 'inside';
      positions.push({ progress, lane });
    });
    
    if (simKey === 'main') {
      saveMainSimulation({ object_avoidance: { object_positions: positions } });
    } else {
      const index = parseInt(simKey.replace('sub', '')) - 1;
      saveSubSimulation(index, { object_avoidance: { object_positions: positions } });
    }
  };
  
  progressInputs.forEach(input => {
    input.addEventListener('change', savePositions);
  });
  
  laneSelects.forEach(select => {
    select.addEventListener('change', savePositions);
  });
}

/**
 * 폼 데이터 수집 (CreateModelRequest 스키마에 맞춤)
 * @returns {Object} CreateModelRequest 형태의 데이터
 */
function collectFormData() {
  // 모델 이름
  const modelName = document.getElementById('model-name-id')?.value || '';
  
  // ============ 메인 시뮬레이션 ============
  const mainTrackId = window.tabStates?.['tabs-main']?.trackId || 'reInvent2019_wide';
  const mainDirection = document.querySelector('input[name="clock-direction"]:checked')?.value || 'counterclockwise';
  const mainAlternate = document.getElementById('alternate-training-main')?.checked || false;
  const mainRaceType = (document.querySelector('input[name="race-type"]:checked')?.value || 'time_trial').toUpperCase();
  
  const mainSimulation = {
    track_id: mainTrackId,
    track_direction: mainDirection,
    alternate_direction: mainAlternate,
    race_type: mainRaceType,
  };
  
  // Object Avoidance 설정 (main)
  if (mainRaceType === 'OBJECT_AVOIDANCE') {
    const numObstacles = parseInt(document.getElementById('number-of-objects')?.value || '3');
    const objectType = document.querySelector('select[name="object-type"]')?.value || 'box_obstacle';
    const randomizeLocations = document.getElementById('object-position')?.checked ?? true;
    
    mainSimulation.object_avoidance = {
      object_type: objectType,
      number_of_objects: numObstacles,
      randomize_locations: randomizeLocations,
    };
    
    // 위치가 수동 설정된 경우
    if (!randomizeLocations) {
      const locations = collectObjectLocations('main');
      if (locations.length > 0) {
        mainSimulation.object_avoidance.object_locations = locations;
      }
    }
  }
  
  // ============ 서브 시뮬레이션 ============
  const subSimCount = parseInt(document.getElementById('sub-simulation-count-id')?.value || '0');
  const subSimulations = [];
  
  for (let i = 1; i <= subSimCount; i++) {
    const subKey = `sub${i}`;
    const subTrackId = window.tabStates?.[`tabs-${subKey}`]?.trackId || 'reInvent2019_wide';
    const subDirection = document.querySelector(`input[name="clock-direction-${subKey}"]:checked`)?.value || 'counterclockwise';
    const subAlternate = document.getElementById(`alternate-${subKey}`)?.checked || false;
    const subRaceType = (document.querySelector(`input[name="race-type-${subKey}"]:checked`)?.value || 'time_trial').toUpperCase();
    
    const subSim = {
      track_id: subTrackId,
      track_direction: subDirection,
      alternate_direction: subAlternate,
      race_type: subRaceType,
    };
    
    // Object Avoidance 설정 (sub)
    if (subRaceType === 'OBJECT_AVOIDANCE') {
      const numObstacles = parseInt(document.getElementById(`number-of-objects-${subKey}`)?.value || '3');
      const objectType = document.querySelector(`select[name="object-type-${subKey}"]`)?.value || 'box_obstacle';
      const randomizeLocations = document.getElementById(`object-position-${subKey}`)?.checked ?? true;
      
      subSim.object_avoidance = {
        object_type: objectType,
        number_of_objects: numObstacles,
        randomize_locations: randomizeLocations,
      };
      
      if (!randomizeLocations) {
        const locations = collectObjectLocations(subKey);
        if (locations.length > 0) {
          subSim.object_avoidance.object_locations = locations;
        }
      }
    }
    
    subSimulations.push(subSim);
  }
  
  // ============ 차량 설정 ============
  const vehicleType = document.getElementById('vehicle-layout')?.value || 'deepracer';
  const lidar = document.getElementById('lidar-checkbox')?.checked || false;
  
  // 액션 스페이스 수집
  const actionSpace = [];
  document.querySelectorAll('#actionList .action-row').forEach(row => {
    const steeringInput = row.querySelector('input[name$="_steering"]');
    const speedInput = row.querySelector('input[name$="_speed"]');
    if (steeringInput && speedInput) {
      actionSpace.push({
        steering_angle: parseInt(steeringInput.value) || 0,
        speed: parseFloat(speedInput.value) || 1.0,
      });
    }
  });
  
  const vehicle = {
    vehicle_type: vehicleType,
    lidar: lidar,
    action_space: actionSpace.length > 0 ? actionSpace : undefined,
  };
  
  // ============ 훈련 설정 ============
  const trainingTimeMinutes = parseInt(document.getElementById('max_training_time')?.value || '60');
  const bestModelMetric = document.querySelector('input[name="best_model_metric"]:checked')?.value || 'progress';
  
  // 하이퍼파라미터
  const batchSize = parseInt(document.querySelector('select[name="batch_size"]')?.value || '64');
  const discountFactor = parseFloat(document.querySelector('input[name="discount_factor"]')?.value || '0.999');
  const learningRate = parseFloat(document.querySelector('input[name="learning_rate"]')?.value || '0.0003');
  const lossType = document.querySelector('input[name="loss_type"]:checked')?.value || 'huber';
  const entropy = parseFloat(document.querySelector('input[name="entropy"]')?.value || '0.01');
  
  const training = {
    training_time_minutes: trainingTimeMinutes,
    best_model_metric: bestModelMetric,
    hyperparameters: {
      batch_size: batchSize,
      discount_factor: discountFactor,
      learning_rate: learningRate,
      loss_type: lossType,
      entropy: entropy,
    },
  };
  
  // ============ 보상 함수 ============
  const rewardFunction = window.editor?.getValue() || '';
  
  // ============ 최종 요청 객체 ============
  return {
    model_name: modelName,
    simulation: mainSimulation,
    sub_simulations: subSimulations,
    vehicle: vehicle,
    training: training,
    reward_function: rewardFunction,
  };
}

/**
 * Object Locations 수집 (특정 시뮬레이션용)
 */
function collectObjectLocations(simKey) {
  const suffix = simKey === 'main' ? '' : `-${simKey}`;
  const locations = [];
  
  const progressInputs = document.querySelectorAll(`.object-progress[data-sim="${simKey}"]`);
  const laneSelects = document.querySelectorAll(`.object-lane[data-sim="${simKey}"]`);
  
  progressInputs.forEach((input, idx) => {
    const progress = parseFloat(input.value) || 0;
    const lane = laneSelects[idx]?.value || 'inside';
    locations.push({ progress, lane });
  });
  
  return locations;
}

// 전역으로 노출 (Create Model 버튼에서 사용)
// NOTE: create.html에 별도 collectFormData가 있으므로 전역 노출하지 않음
// window.collectFormData = collectFormData;

/**
 * 초기화
 */
document.addEventListener('DOMContentLoaded', async function() {
  // 설정 로드
  const settings = await loadAllSettings();
  
  if (settings) {
    // 모델명은 로드하지 않음 (사용자가 직접 입력해야 함)
    // applyModelName(settings.model_name);
    
    // 시뮬레이션 설정 적용
    applySimulationSettings(settings.simulation);
    
    // 차량/액션 스페이스 설정 적용
    applyVehiclesSettings(settings.vehicles);
    
    // 하이퍼파라미터 설정 적용
    applyHyperparametersSettings(settings.hyperparameters);
    
    // 보상 함수 적용
    applyRewardFunction(settings.reward_function);
  }
  
  // 설정 로드 완료 - 이제부터 저장 허용
  settingsLoaded = true;
  
  // 실시간 저장 이벤트 바인딩
  bindSaveEvents();
});


/**
 * 모델명 적용
 */
function applyModelName(modelName) {
  if (!modelName) return;
  
  const modelNameInput = document.getElementById('model-name-id');
  if (modelNameInput) {
    modelNameInput.value = modelName;
    // 입력 이벤트 트리거 (유효성 검사 실행)
    modelNameInput.dispatchEvent(new Event('input'));
  }
}


/**
 * 모델명 저장
 * NOTE: 실시간 저장 비활성화 - Create Model 버튼 클릭 시 일괄 저장
 */
function saveModelName(modelName) {
  // 실시간 저장 비활성화 (collectFormData에서 일괄 수집)
  console.debug('[saveModelName] 실시간 저장 비활성화됨:', modelName);
  // if (!settingsLoaded) return;
  // debounceSave('model_name', () => {
  //   fetch('/api/settings/model-name', {
  //     method: 'POST',
  //     headers: { 'Content-Type': 'application/json' },
  //     body: JSON.stringify({ model_name: modelName })
  //   });
  // }, 500);
}

// 전역으로 노출
window.saveModelName = saveModelName;
