/**
 * Evaluation Page JavaScript
 * - Track selection modal handling
 * - Object avoidance settings (same as create/clone)
 * - Form submission with CPU check
 */

(function () {
  "use strict";

  const modelName = document.getElementById("model-name-id").value;

  // ========== TRACK SELECTION MODAL ==========
  const tracksData = {{ tracks_info | tojson }};

  function updateUI(trackId) {
    const trackInfo = tracksData[trackId];
    if (!trackInfo) return;

    // Update hidden input (inside preview box)
    const hiddenInput = document.querySelector('input[name="track-id"]');
    if (hiddenInput) hiddenInput.value = trackId;

    // Update preview box (keep hidden input, replace rest)
    const previewBox = document.getElementById("track-preview-box");
    const imgUrl = `/static/img/tracks_thumbnail/${trackInfo.thumbnail}`;
    
    // Keep the hidden input, update visual elements
    const existingHidden = previewBox.querySelector('input[name="track-id"]');
    previewBox.innerHTML = `
      <img src="${imgUrl}" alt="${trackInfo.track_name}">
      <span class="text-muted small mt-2">${trackInfo.track_name}</span>
    `;
    // Re-add hidden input at the beginning
    if (existingHidden) {
      existingHidden.value = trackId;
      previewBox.insertBefore(existingHidden, previewBox.firstChild);
    } else {
      const newHidden = document.createElement('input');
      newHidden.type = 'hidden';
      newHidden.name = 'track-id';
      newHidden.value = trackId;
      previewBox.insertBefore(newHidden, previewBox.firstChild);
    }

    // Update description box
    const descBox = document.getElementById("track-description-box");
    const dirs = trackInfo.track_direction ? trackInfo.track_direction.join(", ") : "";
    descBox.innerHTML = `
      <h5>${trackInfo.track_name}</h5>
      <p class="mb-1"><strong>Width:</strong> ${trackInfo.track_width}m</p>
      <p class="mb-1"><strong>Length:</strong> ${trackInfo.track_length}m</p>
      ${dirs ? `<p class="mb-1"><strong>Directions:</strong> ${dirs}</p>` : ""}
    `;

    // Update direction radios based on track support
    const directions = trackInfo.track_direction || [];
    document.querySelectorAll('input[name="clock-direction"]').forEach(radio => {
      const enabled = directions.includes(radio.value);
      radio.disabled = !enabled;
      radio.closest('label')?.classList.toggle('text-muted', !enabled);
      if (!enabled) radio.checked = false;
    });

    // Auto-select if single direction
    if (directions.length === 1) {
      const radio = document.querySelector(`input[name="clock-direction"][value="${directions[0]}"]`);
      if (radio) radio.checked = true;
    }
  }

  // Track selection handler - listen to radio change (same as create-model.js)
  document.querySelectorAll('input[name="form-imagecheck-radio"]').forEach(radio => {
    radio.addEventListener('change', (e) => {
      const trackId = e.target.value;
      updateUI(trackId);

      // Close modal
      document.querySelector('#modal-report .btn-close')?.click();
    });
  });

  // ========== RACE TYPE TOGGLE ==========
  const raceTypeRadios = document.querySelectorAll('input[name="race-type"]');
  const raceTypeWrapper = document.getElementById("race-type-wrapper");

  raceTypeRadios.forEach(radio => {
    radio.addEventListener("change", function () {
      if (this.value === "OBJECT_AVOIDANCE") {
        raceTypeWrapper.classList.remove("d-none");
      } else {
        raceTypeWrapper.classList.add("d-none");
      }
    });
  });

  // ========== OBJECT AVOIDANCE (same as create-model.js) ==========
  const numSelect = document.getElementById("number-of-objects");
  const typeSelect = document.getElementById("object-type");
  const posCheckbox = document.getElementById("object-position");
  const locationWrapper = document.getElementById("object-location-wrapper");

  // Render object locations based on count and randomize checkbox
  function renderObjectLocations() {
    if (!locationWrapper || !numSelect || !posCheckbox) return;

    const count = parseInt(numSelect.value, 10);
    const randomize = posCheckbox.checked;

    if (!randomize && count > 0) {
      // Fixed positions - show location wrapper
      locationWrapper.classList.remove("d-none");

      const innerContainer = document.getElementById("object-location-wrapper-inside");
      if (!innerContainer) return;
      innerContainer.innerHTML = "";

      for (let i = 0; i < count; i++) {
        const isOdd = (i + 1) % 2 === 1;
        const progressValue = ((100 / (count + 1)) * (i + 1)).toFixed(0);

        const block = document.createElement("div");
        block.className = "obstable-block mb-2 p-2 border rounded bg-light";
        block.innerHTML = `
          <div class="d-flex align-items-center gap-2">
            <span class="fw-bold" style="min-width:40px;">${i}</span>
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
                <input class="form-check-input" type="radio" name="lane-${i + 1}" value="inside" ${isOdd ? "checked" : ""}>
                <span class="form-check-label small">IN</span>
              </label>
              <label class="form-check form-check-inline mb-0">
                <input class="form-check-input" type="radio" name="lane-${i + 1}" value="outside" ${!isOdd ? "checked" : ""}>
                <span class="form-check-label small">OUT</span>
              </label>
            </div>
          </div>
        `;
        innerContainer.appendChild(block);
      }
    } else {
      // Random positions - hide location wrapper
      locationWrapper.classList.add("d-none");
    }
  }

  // Event listeners for Object Avoidance
  posCheckbox?.addEventListener("change", renderObjectLocations);
  numSelect?.addEventListener("change", renderObjectLocations);

  // Initial render
  renderObjectLocations();

  // ========== FORM SUBMISSION ==========
  const startBtn = document.getElementById("start-evaluation-btn");

  startBtn?.addEventListener("click", async function () {
    // Gather simulation config
    const trackIdInput = document.querySelector('input[name="track-id"]');
    const trackId = trackIdInput?.value;
    const directionRadio = document.querySelector('input[name="clock-direction"]:checked');
    const raceTypeRadio = document.querySelector('input[name="race-type"]:checked');

    // Validation
    if (!trackId) {
      Swal.fire("Error", "Please select a track.", "error");
      return;
    }
    if (!directionRadio) {
      Swal.fire("Error", "Please select a direction.", "error");
      return;
    }
    if (!raceTypeRadio) {
      Swal.fire("Error", "Please select a race type.", "error");
      return;
    }

    const direction = directionRadio.value;
    const raceType = raceTypeRadio.value;

    // Object avoidance config
    let objectAvoidance = null;
    if (raceType === "OBJECT_AVOIDANCE") {
      const randomize = posCheckbox.checked;
      const numObjects = parseInt(numSelect.value);
      const objectType = typeSelect.value;

      objectAvoidance = {
        number_of_objects: numObjects,
        object_type: objectType,
        randomize_locations: randomize,
        object_locations: null
      };

      // Fixed positions - collect progress/lane data (same as create-model.js)
      if (!randomize) {
        const locations = [];
        for (let i = 1; i <= numObjects; i++) {
          const progressInput = document.querySelector(`input[name="progress-${i}"]`);
          const laneRadio = document.querySelector(`input[name="lane-${i}"]:checked`);
          
          if (progressInput && laneRadio) {
            locations.push({
              progress: parseFloat(progressInput.value) || 0,
              lane: laneRadio.value  // "inside" or "outside" string
            });
          }
        }
        objectAvoidance.object_locations = locations.length > 0 ? locations : null;
      }
    }

    // Gather evaluation config
    const numberOfTrials = parseInt(document.getElementById("number-of-trials").value) || 5;
    const checkpoint = document.querySelector('input[name="checkpoint"]:checked').value;
    const offtrackPenalty = parseFloat(document.getElementById("offtrack-penalty").value) || 5;
    const collisionPenalty = parseFloat(document.getElementById("collision-penalty").value) || 5;

    // Validation
    if (numberOfTrials < 1 || numberOfTrials > 20) {
      Swal.fire("Error", "Number of trials must be between 1 and 20.", "error");
      return;
    }

    // Build request body - use track_direction instead of direction
    const requestBody = {
      model_name: modelName,
      simulation: {
        track_id: trackId,
        track_direction: direction,
        race_type: raceType,
        object_avoidance: objectAvoidance
      },
      evaluation: {
        number_of_trials: numberOfTrials,
        checkpoint: checkpoint,
        offtrack_penalty: offtrackPenalty,
        collision_penalty: collisionPenalty
      }
    };

    // Submit
    startBtn.disabled = true;
    startBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Starting...';

    try {
      const res = await fetch("/api/evaluation/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestBody)
      });

      const data = await res.json();

      if (res.ok && data.success) {
        Swal.fire({
          title: "Evaluation Started",
          text: data.message || "Evaluation has started successfully.",
          icon: "success",
          timer: 2000,
          showConfirmButton: false
        }).then(() => {
          if (data.redirect_url) {
            window.location.href = data.redirect_url;
          } else {
            window.location.href = `/pages/models/model?model_name=${modelName}#evaluation`;
          }
        });
      } else {
        // Handle 503 error (CPU resource)
        if (res.status === 503) {
          Swal.fire("CPU 자원 부족", data.detail || "CPU 자원이 부족합니다. 기존 작업을 종료하세요.", "error");
        } else {
          Swal.fire("Error", data.detail || data.error || "Failed to start evaluation.", "error");
        }
        startBtn.disabled = false;
        startBtn.innerHTML = '<i class="fas fa-play me-1"></i>Start Evaluation';
      }
    } catch (e) {
      console.error("Evaluation start failed:", e);
      Swal.fire("Error", "Network error. Please try again.", "error");
      startBtn.disabled = false;
      startBtn.innerHTML = '<i class="fas fa-play me-1"></i>Start Evaluation';
    }
  });

})();
