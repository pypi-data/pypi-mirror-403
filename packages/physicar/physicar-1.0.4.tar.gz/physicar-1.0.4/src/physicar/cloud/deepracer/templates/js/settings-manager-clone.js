/**
 * Clone 모드 전용 설정 관리
 * - 기존 모델에서 설정 로드
 * - Clone API로 제출
 */

// Clone 모드 플래그
const isCloneMode = true;

/**
 * Clone용 설정 로드 (기존 모델에서)
 */
async function loadCloneSettings(modelName) {
  try {
    const response = await fetch(`/api/models/${encodeURIComponent(modelName)}/clone-config`);
    if (!response.ok) {
      console.error('Failed to load clone settings:', response.status);
      return null;
    }
    return await response.json();
  } catch (error) {
    console.error('Error loading clone settings:', error);
    return null;
  }
}

/**
 * 시뮬레이션 설정 적용
 */
function applySimulationSettings(simSettings, subSimCount) {
  if (!simSettings) return;
  
  // 서브 시뮬레이션 수 적용
  const subSimCountSelect = document.getElementById('sub-simulation-count-id');
  if (subSimCountSelect && subSimCount !== undefined) {
    subSimCountSelect.value = subSimCount.toString();
    subSimCountSelect.dispatchEvent(new Event('change'));
  }
  
  // 메인 시뮬레이션 설정
  applyMainSimulationSettings(simSettings);
}

/**
 * 메인 시뮬레이션 설정 적용
 */
function applyMainSimulationSettings(mainSim) {
  if (!mainSim) return;
  
  // 트랙 (track-preview-box에 표시)
  if (mainSim.track_id) {
    const trackInput = document.querySelector(`input[name="form-imagecheck-radio"][value="${mainSim.track_id}"]`) ||
                       document.querySelector(`input[value="${mainSim.track_id}"]`);
    if (trackInput) {
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
  
  // Race Type
  if (mainSim.race_type) {
    const raceTypeValue = mainSim.race_type.toUpperCase();
    const raceTypeRadio = document.querySelector(`input[name="race-type"][value="${raceTypeValue}"]`);
    if (raceTypeRadio) {
      raceTypeRadio.checked = true;
      raceTypeRadio.dispatchEvent(new Event('change'));
    }
  }
  
  // Direction
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
    
    const numObstacles = document.getElementById('number-of-objects');
    if (numObstacles && oa.number_of_obstacles) {
      numObstacles.value = oa.number_of_obstacles.toString();
    }
    
    const objectType = document.querySelector('select[name="object-type"]');
    if (objectType && oa.object_type) {
      const optionExists = Array.from(objectType.options).some(opt => opt.value === oa.object_type);
      if (optionExists) {
        objectType.value = oa.object_type;
      }
    }
    
    const objectPosition = document.getElementById('object-position');
    if (objectPosition && oa.randomize_locations !== undefined) {
      objectPosition.checked = oa.randomize_locations;
    }
    
    const wrapper = document.getElementById('object-location-wrapper');
    if (wrapper) {
      if (oa.randomize_locations) {
        wrapper.classList.add('d-none');
      } else {
        wrapper.classList.remove('d-none');
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
  
  // Race Type
  if (subSim.race_type) {
    const raceTypeValue = subSim.race_type.toUpperCase();
    const raceTypeRadio = document.querySelector(`#tabs-${subKey} input[name="race-type-${subKey}"][value="${raceTypeValue}"]`);
    if (raceTypeRadio) {
      raceTypeRadio.checked = true;
      raceTypeRadio.dispatchEvent(new Event('change'));
    }
  }
  
  // Direction
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
    
    const numObstacles = document.getElementById(`number-of-objects-${subKey}`);
    if (numObstacles && oa.number_of_obstacles) {
      numObstacles.value = oa.number_of_obstacles.toString();
    }
    
    const objectType = document.querySelector(`select[name="object-type-${subKey}"]`);
    if (objectType && oa.object_type) {
      const optionExists = Array.from(objectType.options).some(opt => opt.value === oa.object_type);
      if (optionExists) {
        objectType.value = oa.object_type;
      }
    }
    
    const objectPosition = document.getElementById(`object-position-${subKey}`);
    if (objectPosition && oa.randomize_locations !== undefined) {
      objectPosition.checked = oa.randomize_locations;
    }
    
    const wrapper = document.getElementById(`object-location-wrapper-${subKey}`);
    if (wrapper) {
      if (oa.randomize_locations) {
        wrapper.classList.add('d-none');
      } else {
        wrapper.classList.remove('d-none');
        renderObjectPositions(`object-location-wrapper-inside-${subKey}`, oa.object_positions || [], oa.number_of_obstacles || 3, subKey);
      }
    }
  }
}

/**
 * 차량 설정 적용
 */
function applyVehiclesSettings(vehiclesSettings) {
  if (!vehiclesSettings) return;
  
  // Lidar (disabled이지만 값은 설정)
  const lidarCheckbox = document.getElementById('lidar-checkbox');
  if (lidarCheckbox && vehiclesSettings.lidar !== undefined) {
    lidarCheckbox.checked = vehiclesSettings.lidar;
    // 이미지 업데이트
    updateVehicleImage(vehiclesSettings.lidar);
  }
  
  // Action Space (개수는 고정, 값은 수정 가능)
  if (vehiclesSettings.action_space && Array.isArray(vehiclesSettings.action_space)) {
    if (typeof window.setActions === 'function') {
      window.setActions(vehiclesSettings.action_space);
      // Clone 모드에서 remove 버튼만 숨김 (값은 수정 가능)
      setTimeout(() => {
        document.querySelectorAll('#actionList .remove-btn').forEach(btn => {
          btn.style.display = 'none';
        });
      }, 100);
    } else {
      window.pendingActionSpace = vehiclesSettings.action_space;
    }
  }
}

/**
 * 차량 이미지 업데이트
 */
function updateVehicleImage(hasLidar) {
  const vehicleImg = document.getElementById('vehicleImg');
  if (vehicleImg) {
    const lidarSuffix = hasLidar ? 'true' : 'false';
    vehicleImg.src = `/static/img/sensor_modification/deepracer/camera_1-lidar_${lidarSuffix}.png`;
  }
}

/**
 * 하이퍼파라미터 설정 적용
 */
function applyHyperparametersSettings(hpSettings) {
  if (!hpSettings) return;
  
  const batchSize = document.getElementById('batchSize');
  if (batchSize && hpSettings.batch_size) {
    batchSize.value = hpSettings.batch_size.toString();
  }
  
  const discountFactor = document.querySelector('input[name="discount_factor"]');
  if (discountFactor && hpSettings.discount_factor !== undefined) {
    discountFactor.value = hpSettings.discount_factor;
  }
  
  const learningRate = document.querySelector('input[name="learning_rate"]');
  if (learningRate && hpSettings.learning_rate !== undefined) {
    learningRate.value = hpSettings.learning_rate;
  }
  
  const entropy = document.querySelector('input[name="entropy"]');
  if (entropy && hpSettings.entropy !== undefined) {
    entropy.value = hpSettings.entropy;
  }
  
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
  
  if (window.editor) {
    window.editor.setValue(rewardCode);
  } else {
    const editorTextarea = document.getElementById('editor');
    if (editorTextarea) {
      editorTextarea.value = rewardCode;
    }
    window.pendingRewardFunction = rewardCode;
  }
}

/**
 * 훈련 설정 적용
 */
function applyTrainingSettings(training) {
  if (!training) return;
  
  // Best Model Metric
  if (training.best_model_metric) {
    const metricRadio = document.querySelector(`input[name="best_model_metric"][value="${training.best_model_metric}"]`);
    if (metricRadio) {
      metricRadio.checked = true;
    }
  }
  
  // Hyperparameters
  if (training.hyperparameters) {
    applyHyperparametersSettings(training.hyperparameters);
  }
}

/**
 * Object Positions UI 렌더링
 */
function renderObjectPositions(containerId, positions, count, subKey = null) {
  const container = document.getElementById(containerId);
  if (!container) return;
  
  container.innerHTML = '';
  
  for (let i = 0; i < count; i++) {
    const pos = positions[i] || { progress: (i + 1) * (100 / (count + 1)), lane: 'inside' };
    const simKey = subKey || 'main';
    
    const block = document.createElement('div');
    block.className = 'obstable-block mb-3 p-3 border rounded';
    block.innerHTML = `
      <div class="row align-items-center">
        <div class="col-md-6">
          <label class="form-label">Object ${i + 1} Progress (%)</label>
          <input type="number" class="form-control object-progress" data-sim="${simKey}"
                 name="progress-${simKey}-${i}" value="${pos.progress}" min="0" max="100" step="0.1">
        </div>
        <div class="col-md-6">
          <label class="form-label">Lane</label>
          <div>
            <div class="form-check form-check-inline">
              <input class="form-check-input object-lane" type="radio" data-sim="${simKey}"
                     name="lane-${simKey}-${i}" value="inside" ${pos.lane === 'inside' ? 'checked' : ''}>
              <label class="form-check-label">Inside</label>
            </div>
            <div class="form-check form-check-inline">
              <input class="form-check-input object-lane" type="radio" data-sim="${simKey}"
                     name="lane-${simKey}-${i}" value="outside" ${pos.lane === 'outside' ? 'checked' : ''}>
              <label class="form-check-label">Outside</label>
            </div>
          </div>
        </div>
      </div>
    `;
    container.appendChild(block);
  }
}

/**
 * Clone용 폼 데이터 수집
 */
function collectCloneFormData() {
  const pretrainedModelName = document.getElementById('pretrained-model-name')?.value || '';
  const pretrainedCheckpoint = document.querySelector('input[name="pretrained_checkpoint"]:checked')?.value || 'last';
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
  
  // ============ 차량 설정 (Clone 시 기존 값 유지) ============
  const lidar = document.getElementById('lidar-checkbox')?.checked || false;
  
  // 액션 스페이스 수집 (개수는 고정, 값은 사용자가 수정한 값 전송)
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
    vehicle_type: 'deepracer',
    lidar: lidar,
    action_space: actionSpace.length > 0 ? actionSpace : undefined,
  };
  
  // ============ 훈련 설정 ============
  const trainingTimeMinutes = parseInt(document.getElementById('max_training_time')?.value || '60');
  const bestModelMetric = document.querySelector('input[name="best_model_metric"]:checked')?.value || 'progress';
  
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
  
  // ============ Clone 전용 필드 포함 ============
  return {
    model_name: modelName,
    pretrained_model_name: pretrainedModelName,
    pretrained_checkpoint: pretrainedCheckpoint,
    simulation: mainSimulation,
    sub_simulations: subSimulations,
    vehicle: vehicle,
    training: training,
    reward_function: rewardFunction,
  };
}

/**
 * Object Locations 수집
 */
function collectObjectLocations(simKey) {
  const locations = [];
  
  const progressInputs = document.querySelectorAll(`.object-progress[data-sim="${simKey}"]`);
  const laneSelects = document.querySelectorAll(`.object-lane[data-sim="${simKey}"]:checked`);
  
  progressInputs.forEach((input, idx) => {
    const progress = parseFloat(input.value) || 0;
    const lane = laneSelects[idx]?.value || 'inside';
    locations.push({ progress, lane });
  });
  
  return locations;
}

// 전역으로 노출
window.collectFormData = collectCloneFormData;
window.isCloneMode = true;

/**
 * 초기화
 */
document.addEventListener('DOMContentLoaded', async function() {
  // Clone 모드: 기존 모델에서 설정 로드
  const pretrainedModelName = document.getElementById('pretrained-model-name')?.value;
  
  if (!pretrainedModelName) {
    console.error('Pretrained model name not found');
    alert('Error: pretrained model name not specified. Redirecting to models list.');
    window.location.href = '/pages/models';
    return;
  }
  
  console.log('[Clone Mode] Loading settings from:', pretrainedModelName);
  
  const settings = await loadCloneSettings(pretrainedModelName);
  
  if (!settings) {
    console.error('Failed to load clone settings for:', pretrainedModelName);
    alert(`Error: Failed to load settings for model "${pretrainedModelName}". The model may not exist.`);
    window.location.href = '/pages/models';
    return;
  }
  
  console.log('[Clone Mode] Settings loaded:', settings);
  
  // 시뮬레이션 설정 적용
  applySimulationSettings(settings.simulation, settings.sub_simulation_count);
  
  // 서브 시뮬레이션 설정 적용
  if (settings.sub_simulations) {
    settings.sub_simulations.forEach((subSim, index) => {
      applySubSimulationSettings(index, subSim);
    });
  }
  
  // 차량/액션 스페이스 설정 적용
  applyVehiclesSettings(settings.vehicle);
  
  // 훈련 설정 적용
  applyTrainingSettings(settings.training);
  
  // 보상 함수 적용
  applyRewardFunction(settings.reward_function);
});
