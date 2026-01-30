"""
설정 파일 관리 모듈
- ~/deepracer-for-cloud/*.env 파일들
- bucket/custom_files/*.json, *.py 파일들 (MinIO API 사용)
"""
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from io import BytesIO
import re
import threading
import yaml


# ============ MinIO 설정 및 헬퍼 함수 ============
MINIO_ENDPOINT = "localhost:9000"
MINIO_ACCESS_KEY = "physicar"
MINIO_SECRET_KEY = "physicar"
MINIO_BUCKET = "bucket"

# MinIO 키 (bucket 내 경로)
CUSTOM_FILES_PREFIX = "custom_files"
MODEL_METADATA_KEY = f"{CUSTOM_FILES_PREFIX}/model_metadata.json"
HYPERPARAMETERS_KEY = f"{CUSTOM_FILES_PREFIX}/hyperparameters.json"
REWARD_FUNCTION_KEY = f"{CUSTOM_FILES_PREFIX}/reward_function.py"


def _get_minio_client():
    """MinIO 클라이언트 생성"""
    from minio import Minio
    return Minio(MINIO_ENDPOINT, access_key=MINIO_ACCESS_KEY, secret_key=MINIO_SECRET_KEY, secure=False)


def minio_read_json(key: str) -> Optional[dict]:
    """MinIO에서 JSON 파일 읽기"""
    try:
        client = _get_minio_client()
        response = client.get_object(MINIO_BUCKET, key)
        content = response.read().decode('utf-8')
        response.close()
        response.release_conn()
        return json.loads(content)
    except Exception:
        return None


def minio_write_json(key: str, data: dict, indent: int = 4):
    """MinIO에 JSON 파일 쓰기"""
    client = _get_minio_client()
    content = json.dumps(data, indent=indent).encode('utf-8')
    client.put_object(MINIO_BUCKET, key, BytesIO(content), len(content), content_type='application/json')


def minio_read_text(key: str) -> Optional[str]:
    """MinIO에서 텍스트 파일 읽기"""
    try:
        client = _get_minio_client()
        response = client.get_object(MINIO_BUCKET, key)
        content = response.read().decode('utf-8')
        response.close()
        response.release_conn()
        return content
    except Exception:
        return None


def minio_read_yaml(key: str) -> Optional[dict]:
    """MinIO에서 YAML 파일 읽기"""
    try:
        import yaml
        client = _get_minio_client()
        response = client.get_object(MINIO_BUCKET, key)
        content = response.read().decode('utf-8')
        response.close()
        response.release_conn()
        return yaml.safe_load(content)
    except Exception:
        return None


def minio_prefix_exists(prefix: str) -> bool:
    """MinIO에서 prefix로 시작하는 객체가 있는지 확인"""
    try:
        client = _get_minio_client()
        for _ in client.list_objects(MINIO_BUCKET, prefix=prefix, recursive=False):
            return True
        return False
    except Exception:
        return False


def minio_write_text(key: str, content: str):
    """MinIO에 텍스트 파일 쓰기"""
    client = _get_minio_client()
    data = content.encode('utf-8')
    client.put_object(MINIO_BUCKET, key, BytesIO(data), len(data), content_type='text/plain')


def atomic_write_json(path: Path, data: Any, indent: int = 4):
    """
    JSON 파일을 atomic하게 저장 (임시 파일 → rename)
    동시 쓰기로 인한 파일 손상 방지
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # 같은 디렉토리에 임시 파일 생성 (rename이 atomic하려면 같은 파일시스템이어야 함)
    fd, tmp_path = tempfile.mkstemp(suffix='.tmp', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as f:
            json.dump(data, f, indent=indent)
        # atomic rename
        os.replace(tmp_path, path)
    except:
        # 실패 시 임시 파일 정리
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


# 파일별 락 - 동시 수정 방지
_locks = {
    "simulation": threading.Lock(),      # run.env, system.env, worker-*.env
    "vehicles": threading.Lock(),         # model_metadata.json
    "hyperparameters": threading.Lock(),  # hyperparameters.json
    "reward_function": threading.Lock(),  # reward_function.py
}


# 경로 설정 (로컬 env 파일 접근용 - MinIO가 아닌 실제 파일시스템)
HOME_DIR = Path.home()
DRFC_DIR = HOME_DIR / "deepracer-for-cloud"

# config.py에서 TRACKS_INFO_PATH import
from physicar.cloud.deepracer.config import TRACKS_INFO_PATH

# DRFC env 파일 경로 (로컬 파일시스템 - MinIO 아님)
RUN_ENV_PATH = DRFC_DIR / "run.env"
SYSTEM_ENV_PATH = DRFC_DIR / "system.env"

# 트랙 정보 캐시
_tracks_info_cache = None


def get_tracks_info() -> Dict[str, Any]:
    """트랙 정보 로드 (캐시)"""
    global _tracks_info_cache
    if _tracks_info_cache is not None:
        return _tracks_info_cache
    
    if not TRACKS_INFO_PATH.exists():
        return {}
    
    with open(TRACKS_INFO_PATH, 'r') as f:
        _tracks_info_cache = yaml.safe_load(f) or {}
    return _tracks_info_cache


def decode_world_name(world_name: str) -> Tuple[str, str]:
    """
    DR_WORLD_NAME에서 track_id와 direction 추출
    예: "2024_reinvent_champ_ccw" -> ("2024_reinvent_champ", "counterclockwise")
    """
    tracks_info = get_tracks_info()
    
    # 모든 트랙의 npy 파일명과 비교
    for track_id, track_info in tracks_info.items():
        npy_info = track_info.get("npy", {})
        for direction, npy_file in npy_info.items():
            if npy_file:
                # npy 파일명에서 .npy 제거
                npy_name = npy_file.replace(".npy", "")
                if world_name == npy_name:
                    return track_id, direction
    
    # 매칭 실패 시 world_name 그대로 반환, direction은 clockwise
    return world_name, "clockwise"


def encode_world_name(track_id: str, direction: str) -> str:
    """
    track_id와 direction으로 DR_WORLD_NAME 생성
    예: ("2024_reinvent_champ", "counterclockwise") -> "2024_reinvent_champ_ccw"
    """
    tracks_info = get_tracks_info()
    
    if track_id in tracks_info:
        npy_info = tracks_info[track_id].get("npy", {})
        npy_file = npy_info.get(direction, "")
        if npy_file:
            return npy_file.replace(".npy", "")
    
    # 매칭 실패 시 track_id 그대로 반환
    return track_id


def get_worker_env_paths() -> list[Path]:
    """worker-*.env 파일 경로 목록 반환"""
    paths = []
    for i in range(2, 8):  # worker-2.env ~ worker-7.env
        path = DRFC_DIR / f"worker-{i}.env"
        if path.exists():
            paths.append(path)
    return paths


def parse_env_file(path: Path) -> Dict[str, str]:
    """env 파일 파싱"""
    env = {}
    if not path.exists():
        return env
    
    with open(path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, _, value = line.partition('=')
                # 따옴표 제거
                value = value.strip().strip('"').strip("'")
                env[key.strip()] = value
    return env


def _quote_env_value(value: str) -> str:
    """env 값에 특수문자가 있으면 따옴표로 감싸기"""
    # 세미콜론, 공백, 특수문자가 있으면 따옴표 필요
    if ';' in value or ' ' in value or '&' in value or '|' in value:
        # 이미 따옴표가 있으면 그대로
        if (value.startswith('"') and value.endswith('"')) or \
           (value.startswith("'") and value.endswith("'")):
            return value
        return f'"{value}"'
    return value


def write_env_file(path: Path, env: Dict[str, str]):
    """env 파일 쓰기 (기존 주석/순서 유지하면서 값만 업데이트)"""
    if not path.exists():
        # 새 파일 생성
        with open(path, 'w') as f:
            for key, value in env.items():
                f.write(f"{key}={_quote_env_value(value)}\n")
        return
    
    # 기존 파일 읽기
    with open(path, 'r') as f:
        lines = f.readlines()
    
    # 업데이트할 키 추적
    updated_keys = set()
    new_lines = []
    
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            new_lines.append(line)
            continue
        
        if '=' in stripped:
            key, _, _ = stripped.partition('=')
            key = key.strip()
            if key in env:
                new_lines.append(f"{key}={_quote_env_value(env[key])}\n")
                updated_keys.add(key)
            else:
                # 변경 대상이 아닌 키는 원래 라인 그대로 유지
                new_lines.append(line)
        else:
            new_lines.append(line)
    
    # 새 키 추가
    for key, value in env.items():
        if key not in updated_keys:
            new_lines.append(f"{key}={_quote_env_value(value)}\n")
    
    with open(path, 'w') as f:
        f.writelines(new_lines)


def update_env_values(path: Path, updates: Dict[str, str]):
    """env 파일의 특정 값들만 업데이트 (다른 값들은 원본 유지)"""
    if not path.exists():
        # 새 파일 생성
        with open(path, 'w') as f:
            for key, value in updates.items():
                f.write(f"{key}={_quote_env_value(value)}\n")
        return
    
    # 기존 파일 읽기
    with open(path, 'r') as f:
        lines = f.readlines()
    
    # 업데이트할 키 추적
    updated_keys = set()
    new_lines = []
    
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            new_lines.append(line)
            continue
        
        if '=' in stripped:
            key, _, _ = stripped.partition('=')
            key = key.strip()
            if key in updates:
                # 업데이트 대상인 키만 새 값으로 교체
                new_lines.append(f"{key}={_quote_env_value(updates[key])}\n")
                updated_keys.add(key)
            else:
                # 업데이트 대상이 아닌 키는 원래 라인 그대로 유지
                new_lines.append(line)
        else:
            new_lines.append(line)
    
    # 새 키 추가
    for key, value in updates.items():
        if key not in updated_keys:
            new_lines.append(f"{key}={_quote_env_value(value)}\n")
    
    with open(path, 'w') as f:
        f.writelines(new_lines)


def update_env_value(path: Path, key: str, value: str):
    """env 파일의 특정 값만 업데이트"""
    env = parse_env_file(path)
    env[key] = value
    write_env_file(path, env)


def get_cpu_count() -> int:
    """현재 CPU 수"""
    return os.cpu_count() or 4


def get_max_sub_simulation_count(cpu_count: int = None) -> int:
    """CPU 수에 따른 최대 서브 시뮬레이션 수"""
    cpu_count = cpu_count or get_cpu_count()
    # 훈련 시 CPU 사용: 1 (sagemaker) + (1 + sub_count) * 2 (robomaker)
    # 역산: sub_count = (cpu - 4) / 2
    if cpu_count <= 4:
        return 0
    elif cpu_count <= 6:
        return 1
    elif cpu_count <= 8:
        return 2
    elif cpu_count <= 10:
        return 3
    elif cpu_count <= 12:
        return 4
    elif cpu_count <= 14:
        return 5
    else:
        return 6


def get_num_episodes_between_training(sub_sim_count: int) -> int:
    """
    서브 시뮬레이션 수에 따른 num_episodes_between_training
    - sub 0: 10
    - sub 1: 20
    - sub 2: 30
    - sub 3: 40
    - sub 4: 50
    - sub 5: 60
    - sub 6: 70
    """
    return (sub_sim_count + 1) * 10


def get_num_epochs(sub_sim_count: int) -> int:
    """
    서브 시뮬레이션 수에 따른 num_epochs (PPO 기준)
    - sub 0: 6
    - sub 1: 5
    - sub 2: 4
    - sub 3: 3
    - sub 4: 3
    - sub 5: 2
    - sub 6: 2
    """
    epochs_map = {0: 6, 1: 5, 2: 4, 3: 3, 4: 3, 5: 2, 6: 2}
    return epochs_map.get(sub_sim_count, 2)


def decode_object_positions(encoded: str) -> List[Dict[str, Any]]:
    """
    ENV 형식을 리스트로 디코딩
    "0.33,1;0.67,-1" -> [{"progress": 33, "lane": "inside"}, {"progress": 67, "lane": "outside"}]
    """
    if not encoded:
        return []
    
    # 따옴표 제거
    encoded = encoded.strip('"\'')
    if not encoded:
        return []
    
    result = []
    for item in encoded.split(";"):
        if "," in item:
            parts = item.split(",")
            if len(parts) == 2:
                try:
                    progress = int(round(float(parts[0]) * 100))  # 0.33 -> 33, 정수로
                    lane_val = int(parts[1])
                    lane = "inside" if lane_val == 1 else "outside"
                    result.append({"progress": progress, "lane": lane})
                except (ValueError, IndexError):
                    continue
    return result


def encode_object_positions(positions: List[Dict[str, Any]]) -> str:
    """
    리스트를 ENV 형식으로 인코딩
    [{"progress": 33, "lane": "inside"}, {"progress": 67, "lane": "outside"}] -> "0.33,1;0.67,-1"
    """
    if not positions or not isinstance(positions, list):
        return ""
    
    items = []
    for pos in positions:
        if isinstance(pos, dict) and "progress" in pos and "lane" in pos:
            progress = round(pos["progress"] / 100, 4)  # 33 -> 0.33, 소수점 4자리로 반올림
            lane_val = 1 if pos["lane"] == "inside" else -1
            items.append(f"{progress},{lane_val}")
    
    if not items:
        return ""
    
    return f'"{";".join(items)}"'


def generate_default_object_positions(num_obstacles: int) -> List[Dict[str, Any]]:
    """
    장애물 수에 맞게 기본 object_positions 생성
    트랙을 균등하게 나누어 inside/outside를 번갈아 배치
    """
    if num_obstacles <= 0:
        return []
    
    positions = []
    for i in range(num_obstacles):
        # 트랙을 균등하게 분할 (0~100 사이, 정수)
        progress = int(round((i + 1) * 100 / (num_obstacles + 1)))
        # inside/outside 번갈아 배치
        lane = "inside" if i % 2 == 0 else "outside"
        positions.append({"progress": progress, "lane": lane})
    
    return positions


def load_settings() -> Dict[str, Any]:
    """모든 설정 로드"""
    settings = {
        "model_name": load_model_name(),
        "simulation": load_simulation_settings(),
        "vehicles": load_vehicles_settings(),
        "hyperparameters": load_hyperparameters(),
        "reward_function": load_reward_function(),
    }
    return settings


def load_simulation_settings() -> Dict[str, Any]:
    """시뮬레이션 설정 로드 (run.env, worker-*.env)"""
    run_env = parse_env_file(RUN_ENV_PATH)
    system_env = parse_env_file(SYSTEM_ENV_PATH)
    
    # 현재 CPU 수와 최대 서브 시뮬레이션 수
    cpu_count = get_cpu_count()
    max_sub_sim = get_max_sub_simulation_count(cpu_count)
    
    # DR_WORKERS 값으로 서브 시뮬레이션 수 파악 (DR_WORKERS = main + sub)
    dr_workers = int(system_env.get("DR_WORKERS", "1"))
    saved_sub_sim = max(0, dr_workers - 1)
    
    # min(저장된 값, CPU 기반 최댓값)으로 자동 조정
    current_sub_sim = min(saved_sub_sim, max_sub_sim)
    
    # 조정이 필요하면 저장
    if current_sub_sim != saved_sub_sim:
        system_env["DR_WORKERS"] = str(current_sub_sim + 1)
        write_env_file(SYSTEM_ENV_PATH, system_env)
    
    # worker-*.env 파일 경로
    worker_paths = get_worker_env_paths()
    
    # 메인 시뮬레이션 설정
    # DR_WORLD_NAME에서 track_id와 direction 추출
    main_world_name = run_env.get("DR_WORLD_NAME", "reInvent2019_wide")
    main_track_id, main_direction = decode_world_name(main_world_name)
    
    main_sim = {
        "track_id": main_track_id,
        "race_type": run_env.get("DR_RACE_TYPE", "TIME_TRIAL"),
        "direction": main_direction,
        "alternate_direction": run_env.get("DR_TRAIN_ALTERNATE_DRIVING_DIRECTION", "False") == "True",
        "object_avoidance": {
            "number_of_obstacles": int(run_env.get("DR_OA_NUMBER_OF_OBSTACLES", "3")),
            "object_type": run_env.get("DR_OA_OBSTACLE_TYPE", "box_obstacle"),
            "randomize_locations": run_env.get("DR_OA_RANDOMIZE_OBSTACLE_LOCATIONS", "True") == "True",
            "object_positions": decode_object_positions(run_env.get("DR_OA_OBJECT_POSITIONS", "")),
        }
    }
    
    # 서브 시뮬레이션 설정 (항상 모든 worker-*.env 로드 - UI에서는 sub_simulation_count로 탭 표시/숨김만 처리)
    sub_simulations = []
    for i, path in enumerate(worker_paths):  # 모든 worker 파일 로드
        worker_env = parse_env_file(path)
        # DR_WORLD_NAME에서 track_id와 direction 추출
        sub_world_name = worker_env.get("DR_WORLD_NAME", main_world_name)
        sub_track_id, sub_direction = decode_world_name(sub_world_name)
        
        sub_sim = {
            "track_id": sub_track_id,
            "race_type": worker_env.get("DR_RACE_TYPE", "TIME_TRIAL"),
            "direction": sub_direction,
            "alternate_direction": worker_env.get("DR_TRAIN_ALTERNATE_DRIVING_DIRECTION", "False") == "True",
            "object_avoidance": {
                "number_of_obstacles": int(worker_env.get("DR_OA_NUMBER_OF_OBSTACLES", "3")),
                "object_type": worker_env.get("DR_OA_OBSTACLE_TYPE", "box_obstacle"),
                "randomize_locations": worker_env.get("DR_OA_RANDOMIZE_OBSTACLE_LOCATIONS", "True") == "True",
                "object_positions": decode_object_positions(worker_env.get("DR_OA_OBJECT_POSITIONS", "")),
            }
        }
        sub_simulations.append(sub_sim)
    
    return {
        "cpu_count": cpu_count,
        "max_sub_simulation_count": max_sub_sim,
        "sub_simulation_count": current_sub_sim,
        "main": main_sim,
        "sub_simulations": sub_simulations,
        "best_model_metric": run_env.get("DR_TRAIN_BEST_MODEL_METRIC", "progress"),
    }


def load_vehicles_settings() -> Dict[str, Any]:
    """차량 및 액션 스페이스 설정 로드 (MinIO API 사용)"""
    metadata = minio_read_json(MODEL_METADATA_KEY)
    if not metadata:
        return get_default_vehicles_settings()
    
    # 센서 정보
    sensors = metadata.get("sensor", ["FRONT_FACING_CAMERA"])
    has_lidar = "LIDAR" in sensors
    
    # vehicle_type은 run.env의 DR_CAR_BODY_SHELL_TYPE에서 읽음 (근본)
    run_env = parse_env_file(RUN_ENV_PATH)
    vehicle_type = run_env.get("DR_CAR_BODY_SHELL_TYPE", "deepracer")
    
    # 액션 스페이스
    action_space = metadata.get("action_space", [])
    
    # max_training_time (커스텀 추가)
    max_training_time = metadata.get("max_training_time", 60)
    
    return {
        "vehicle_type": vehicle_type,
        "lidar": has_lidar,
        "action_space": action_space,
        "action_space_type": metadata.get("action_space_type", "discrete"),
        "neural_network": metadata.get("neural_network", "DEEP_CONVOLUTIONAL_NETWORK_SHALLOW"),
        "training_algorithm": metadata.get("training_algorithm", "clipped_ppo"),
        "max_training_time": max_training_time,
    }


def get_default_vehicles_settings() -> Dict[str, Any]:
    """기본 차량 설정"""
    return {
        "vehicle_type": "deepracer",
        "lidar": False,
        "action_space": [
            {"steering_angle": -25, "speed": 0.5},
            {"steering_angle": -15, "speed": 1.0},
            {"steering_angle": 0, "speed": 1.5},
            {"steering_angle": 15, "speed": 1.0},
            {"steering_angle": 25, "speed": 0.5},
        ],
        "action_space_type": "discrete",
        "neural_network": "DEEP_CONVOLUTIONAL_NETWORK_SHALLOW",
        "training_algorithm": "clipped_ppo",
        "max_training_time": 60,
    }


def load_hyperparameters() -> Dict[str, Any]:
    """하이퍼파라미터 로드 (MinIO API 사용)"""
    hp = minio_read_json(HYPERPARAMETERS_KEY)
    if not hp:
        return get_default_hyperparameters()
    
    return {
        "batch_size": hp.get("batch_size", 64),
        "discount_factor": hp.get("discount_factor", 0.99),
        "learning_rate": hp.get("lr", 0.0003),
        "entropy": hp.get("beta_entropy", 0.01),
        "loss_type": hp.get("loss_type", "huber"),
        # 동적 계산 필드 (참고용)
        "num_episodes_between_training": hp.get("num_episodes_between_training", 20),
        "num_epochs": hp.get("num_epochs", 5),
    }


def get_default_hyperparameters() -> Dict[str, Any]:
    """기본 하이퍼파라미터"""
    return {
        "batch_size": 64,
        "discount_factor": 0.99,
        "learning_rate": 0.0003,
        "entropy": 0.01,
        "loss_type": "huber",
        "num_episodes_between_training": 20,
        "num_epochs": 5,
    }


def load_reward_function() -> str:
    """보상 함수 코드 로드 (MinIO API 사용)"""
    content = minio_read_text(REWARD_FUNCTION_KEY)
    if content:
        return content
    return get_default_reward_function()


def get_default_reward_function() -> str:
    """기본 보상 함수"""
    return '''def reward_function(params):
    # Read input parameters
    distance_from_center = params['distance_from_center']
    track_width = params['track_width']

    # Calculate 3 marks that are farther and father away from the center line
    marker_1 = 0.1 * track_width
    marker_2 = 0.25 * track_width
    marker_3 = 0.5 * track_width

    # Give higher reward if the car is closer to center line and vice versa
    if distance_from_center <= marker_1:
        reward = 1
    elif distance_from_center <= marker_2:
        reward = 0.5
    elif distance_from_center <= marker_3:
        reward = 0.1
    else:
        reward = 1e-3  # likely crashed/ close to off track

    return float(reward)
'''


# ============ 저장 함수들 ============

def save_simulation_main(data: Dict[str, Any]):
    """메인 시뮬레이션 설정 저장"""
    with _locks["simulation"]:
        _save_simulation_main_impl(data)


def _save_simulation_main_impl(data: Dict[str, Any]):
    """메인 시뮬레이션 설정 저장 (내부 구현)"""
    updates = {}
    
    # track_id와 direction이 함께 전달되면 encode_world_name 사용
    if "track_id" in data and "direction" in data:
        world_name = encode_world_name(data["track_id"], data["direction"])
        updates["DR_WORLD_NAME"] = world_name
    elif "track_id" in data:
        # track_id만 변경 시, 현재 direction 유지
        env = parse_env_file(RUN_ENV_PATH)
        current_world_name = env.get("DR_WORLD_NAME", "reInvent2019_wide")
        _, current_direction = decode_world_name(current_world_name)
        world_name = encode_world_name(data["track_id"], current_direction)
        updates["DR_WORLD_NAME"] = world_name
    elif "direction" in data:
        # direction만 변경 시, 현재 track_id 유지
        env = parse_env_file(RUN_ENV_PATH)
        current_world_name = env.get("DR_WORLD_NAME", "reInvent2019_wide")
        current_track_id, _ = decode_world_name(current_world_name)
        world_name = encode_world_name(current_track_id, data["direction"])
        updates["DR_WORLD_NAME"] = world_name
    
    if "race_type" in data:
        updates["DR_RACE_TYPE"] = data["race_type"]
    if "alternate_direction" in data:
        updates["DR_TRAIN_ALTERNATE_DRIVING_DIRECTION"] = "True" if data["alternate_direction"] else "False"
    if "best_model_metric" in data:
        updates["DR_TRAIN_BEST_MODEL_METRIC"] = data["best_model_metric"]
    
    # Object Avoidance 설정
    if "object_avoidance" in data:
        oa = data["object_avoidance"]
        env = parse_env_file(RUN_ENV_PATH)
        current_randomize = env.get("DR_OA_RANDOMIZE_OBSTACLE_LOCATIONS", "True") == "True"
        
        if "number_of_obstacles" in oa:
            updates["DR_OA_NUMBER_OF_OBSTACLES"] = str(oa["number_of_obstacles"])
            # randomize_locations=False 상태에서 개수 변경 시 object_positions 재생성
            new_randomize = oa.get("randomize_locations", current_randomize)
            if not new_randomize:
                num_obstacles = int(oa["number_of_obstacles"])
                default_positions = generate_default_object_positions(num_obstacles)
                updates["DR_OA_OBJECT_POSITIONS"] = encode_object_positions(default_positions)
        
        if "object_type" in oa:
            updates["DR_OA_OBSTACLE_TYPE"] = oa["object_type"]
        
        if "randomize_locations" in oa:
            updates["DR_OA_RANDOMIZE_OBSTACLE_LOCATIONS"] = "True" if oa["randomize_locations"] else "False"
            if oa["randomize_locations"]:
                # randomize_locations=True이면 object_positions를 비움
                updates["DR_OA_OBJECT_POSITIONS"] = ""
            else:
                # randomize_locations=False로 변경 시, 현재 positions가 비어있으면 기본값 생성
                current_positions = env.get("DR_OA_OBJECT_POSITIONS", "")
                if not current_positions or current_positions in ('', '""', "''"):
                    num_obstacles = int(oa.get("number_of_obstacles", env.get("DR_OA_NUMBER_OF_OBSTACLES", "3")))
                    default_positions = generate_default_object_positions(num_obstacles)
                    updates["DR_OA_OBJECT_POSITIONS"] = encode_object_positions(default_positions)
        
        if "object_positions" in oa and not oa.get("randomize_locations", current_randomize):
            updates["DR_OA_OBJECT_POSITIONS"] = encode_object_positions(oa["object_positions"])
    
    if updates:
        update_env_values(RUN_ENV_PATH, updates)


def save_simulation_sub(index: int, data: Dict[str, Any]):
    """서브 시뮬레이션 설정 저장 (index: 0-based, worker-2.env부터)"""
    with _locks["simulation"]:
        _save_simulation_sub_impl(index, data)


def _save_simulation_sub_impl(index: int, data: Dict[str, Any]):
    """서브 시뮬레이션 설정 저장 (내부 구현)"""
    worker_path = DRFC_DIR / f"worker-{index + 2}.env"
    
    updates = {}
    
    # track_id와 direction이 함께 전달되면 encode_world_name 사용
    if "track_id" in data and "direction" in data:
        world_name = encode_world_name(data["track_id"], data["direction"])
        updates["DR_WORLD_NAME"] = world_name
    elif "track_id" in data:
        # track_id만 변경 시, 현재 direction 유지
        env = parse_env_file(worker_path) if worker_path.exists() else {}
        current_world_name = env.get("DR_WORLD_NAME", "reInvent2019_wide")
        _, current_direction = decode_world_name(current_world_name)
        world_name = encode_world_name(data["track_id"], current_direction)
        updates["DR_WORLD_NAME"] = world_name
    elif "direction" in data:
        # direction만 변경 시, 현재 track_id 유지
        env = parse_env_file(worker_path) if worker_path.exists() else {}
        current_world_name = env.get("DR_WORLD_NAME", "reInvent2019_wide")
        current_track_id, _ = decode_world_name(current_world_name)
        world_name = encode_world_name(current_track_id, data["direction"])
        updates["DR_WORLD_NAME"] = world_name
    
    if "race_type" in data:
        updates["DR_RACE_TYPE"] = data["race_type"]
    if "alternate_direction" in data:
        updates["DR_TRAIN_ALTERNATE_DRIVING_DIRECTION"] = "True" if data["alternate_direction"] else "False"
    
    # Object Avoidance 설정
    if "object_avoidance" in data:
        oa = data["object_avoidance"]
        env = parse_env_file(worker_path) if worker_path.exists() else {}
        current_randomize = env.get("DR_OA_RANDOMIZE_OBSTACLE_LOCATIONS", "True") == "True"
        
        if "number_of_obstacles" in oa:
            updates["DR_OA_NUMBER_OF_OBSTACLES"] = str(oa["number_of_obstacles"])
            # randomize_locations=False 상태에서 개수 변경 시 object_positions 재생성
            new_randomize = oa.get("randomize_locations", current_randomize)
            if not new_randomize:
                num_obstacles = int(oa["number_of_obstacles"])
                default_positions = generate_default_object_positions(num_obstacles)
                updates["DR_OA_OBJECT_POSITIONS"] = encode_object_positions(default_positions)
        
        if "object_type" in oa:
            updates["DR_OA_OBSTACLE_TYPE"] = oa["object_type"]
        
        if "randomize_locations" in oa:
            updates["DR_OA_RANDOMIZE_OBSTACLE_LOCATIONS"] = "True" if oa["randomize_locations"] else "False"
            if oa["randomize_locations"]:
                # randomize_locations=True이면 object_positions를 비움
                updates["DR_OA_OBJECT_POSITIONS"] = ""
            else:
                # randomize_locations=False로 변경 시, 현재 positions가 비어있으면 기본값 생성
                current_positions = env.get("DR_OA_OBJECT_POSITIONS", "")
                if not current_positions or current_positions in ('', '""', "''"):
                    num_obstacles = int(oa.get("number_of_obstacles", env.get("DR_OA_NUMBER_OF_OBSTACLES", "3")))
                    default_positions = generate_default_object_positions(num_obstacles)
                    updates["DR_OA_OBJECT_POSITIONS"] = encode_object_positions(default_positions)
        
        if "object_positions" in oa and not oa.get("randomize_locations", current_randomize):
            updates["DR_OA_OBJECT_POSITIONS"] = encode_object_positions(oa["object_positions"])
    
    if updates:
        update_env_values(worker_path, updates)


def _update_hyperparameters_for_sub_sim_count(sub_sim_count: int):
    """
    서브 시뮬레이션 수에 따라 hyperparameters.json 업데이트 (MinIO API 사용)
    - num_episodes_between_training: (sub_count + 1) * 10
    - num_epochs: {0: 6, 1: 5, 2: 4, 3: 3, 4: 3, 5: 2, 6: 2}
    """
    # 기존 설정 로드 (MinIO)
    hp = minio_read_json(HYPERPARAMETERS_KEY) or {}
    
    # 값 계산 및 업데이트
    hp["num_episodes_between_training"] = get_num_episodes_between_training(sub_sim_count)
    hp["num_epochs"] = get_num_epochs(sub_sim_count)
    
    # 저장 (MinIO)
    minio_write_json(HYPERPARAMETERS_KEY, hp)


def save_sub_simulation_count(count: int):
    """서브 시뮬레이션 수 설정 (worker-*.env 파일 생성/삭제)"""
    with _locks["simulation"]:
        _save_sub_simulation_count_impl(count)


def _save_sub_simulation_count_impl(count: int):
    """서브 시뮬레이션 수 설정 (내부 구현)"""
    max_count = get_max_sub_simulation_count()
    count = min(count, max_count)
    
    # system.env에 DR_WORKERS 업데이트
    workers = count + 1  # main + sub
    update_env_value(SYSTEM_ENV_PATH, "DR_WORKERS", str(workers))
    
    # run.env에 DR_TRAIN_MULTI_CONFIG 업데이트 (항상 True - training-params/main.yaml 포맷 사용)
    update_env_value(RUN_ENV_PATH, "DR_TRAIN_MULTI_CONFIG", "True")
    
    # hyperparameters.json 업데이트 (num_episodes_between_training, num_epochs)
    _update_hyperparameters_for_sub_sim_count(count)
    
    # 필요한 worker-*.env 파일 생성 (기존 파일 유지)
    run_env = parse_env_file(RUN_ENV_PATH)
    for i in range(count):
        worker_path = DRFC_DIR / f"worker-{i + 2}.env"
        if not worker_path.exists():
            # 기본값으로 생성 (main 설정 복사)
            default_worker = {
                "DR_WORLD_NAME": run_env.get("DR_WORLD_NAME", "reInvent2019_wide"),
                "DR_RACE_TYPE": run_env.get("DR_RACE_TYPE", "TIME_TRIAL"),
                "DR_TRAIN_REVERSE_DIRECTION": "False",
                "DR_TRAIN_ALTERNATE_DRIVING_DIRECTION": "False",
                "DR_TRAIN_ROUND_ROBIN_ADVANCE_DIST": "0.1",
                "DR_ENABLE_DOMAIN_RANDOMIZATION": "False",
                "DR_OA_NUMBER_OF_OBSTACLES": "3",
                "DR_OA_MIN_DISTANCE_BETWEEN_OBSTACLES": "2.0",
                "DR_OA_RANDOMIZE_OBSTACLE_LOCATIONS": "True",
                "DR_OA_IS_OBSTACLE_BOT_CAR": "False",
                "DR_OA_OBSTACLE_TYPE": "box_obstacle",
                "DR_OA_OBJECT_POSITIONS": "",
                "DR_CAR_COLOR": ["Grey", "Blue", "Red", "Orange", "White", "Purple"][i % 6],
            }
            write_env_file(worker_path, default_worker)


def save_vehicles_settings(data: Dict[str, Any]):
    """차량 및 액션 스페이스 설정 저장"""
    with _locks["vehicles"]:
        _save_vehicles_settings_impl(data)


def _save_vehicles_settings_impl(data: Dict[str, Any]):
    """차량 및 액션 스페이스 설정 저장 (MinIO API 사용)"""
    # 기존 설정 로드 (MinIO)
    metadata = minio_read_json(MODEL_METADATA_KEY) or {}
    
    # 센서 설정
    if "lidar" in data:
        sensors = ["FRONT_FACING_CAMERA"]
        if data["lidar"]:
            sensors.append("LIDAR")
        metadata["sensor"] = sensors
    
    # vehicle_type - run.env의 DR_CAR_BODY_SHELL_TYPE만 업데이트 (근본)
    # metadata.json에는 저장하지 않음 (deepracer simapp에서 사용하지 않음)
    if "vehicle_type" in data:
        update_env_values(RUN_ENV_PATH, {"DR_CAR_BODY_SHELL_TYPE": data["vehicle_type"]})
    
    # 액션 스페이스
    if "action_space" in data:
        metadata["action_space"] = data["action_space"]
    
    if "action_space_type" in data:
        metadata["action_space_type"] = data["action_space_type"]
    
    if "neural_network" in data:
        metadata["neural_network"] = data["neural_network"]
    
    if "training_algorithm" in data:
        metadata["training_algorithm"] = data["training_algorithm"]
    
    # max_training_time (커스텀)
    if "max_training_time" in data:
        metadata["max_training_time"] = data["max_training_time"]
    
    # 버전
    metadata["version"] = metadata.get("version", "5")
    
    # 저장 (MinIO API)
    minio_write_json(MODEL_METADATA_KEY, metadata)


def save_hyperparameters(data: Dict[str, Any], sub_sim_count: int = 0):
    """하이퍼파라미터 저장"""
    with _locks["hyperparameters"]:
        _save_hyperparameters_impl(data, sub_sim_count)


def _save_hyperparameters_impl(data: Dict[str, Any], sub_sim_count: int = 0):
    """하이퍼파라미터 저장 (MinIO API 사용)"""
    # 기존 설정 로드 (MinIO)
    hp = minio_read_json(HYPERPARAMETERS_KEY) or {}
    
    # 업데이트
    if "batch_size" in data:
        hp["batch_size"] = data["batch_size"]
    if "discount_factor" in data:
        hp["discount_factor"] = data["discount_factor"]
    if "learning_rate" in data:
        hp["lr"] = data["learning_rate"]
    if "entropy" in data:
        hp["beta_entropy"] = data["entropy"]
    if "loss_type" in data:
        hp["loss_type"] = data["loss_type"]
    
    # 동적 계산 필드 (worker_count = main + sub_sim_count)
    worker_count = 1 + sub_sim_count
    hp["num_episodes_between_training"] = get_num_episodes_between_training(worker_count)
    hp["num_epochs"] = get_num_epochs(sub_sim_count)
    
    # SAC 알고리즘 체크
    algorithm = hp.get("exploration_type", "categorical")
    is_sac = algorithm == "additive_noise"
    
    # 기본값 설정
    hp.setdefault("e_greedy_value", 0.05 if is_sac else 1.0)
    hp.setdefault("epsilon_steps", 10000)
    hp.setdefault("exploration_type", "categorical")
    hp.setdefault("stack_size", 1)
    hp.setdefault("term_cond_avg_score", 350.0)
    hp.setdefault("term_cond_max_episodes", 1000)
    hp.setdefault("sac_alpha", 0.2)
    
    # 저장 (MinIO API)
    minio_write_json(HYPERPARAMETERS_KEY, hp)


def save_reward_function(code: str):
    """보상 함수 저장"""
    with _locks["reward_function"]:
        _save_reward_function_impl(code)


def _save_reward_function_impl(code: str):
    """보상 함수 저장 (MinIO API 사용)"""
    minio_write_text(REWARD_FUNCTION_KEY, code)


def save_model_name(model_name: str):
    """모델명 저장 (run.env에 DR_LOCAL_S3_MODEL_PREFIX)"""
    with _locks["simulation"]:
        update_env_values(RUN_ENV_PATH, {
            "DR_LOCAL_S3_MODEL_PREFIX": f"models/{model_name}",
        })


def load_model_name() -> str:
    """run.env에서 모델명 읽기"""
    run_env = parse_env_file(RUN_ENV_PATH)
    model_prefix = run_env.get("DR_LOCAL_S3_MODEL_PREFIX", "")
    
    if model_prefix.startswith("models/"):
        return model_prefix[7:]  # "models/" 제거
    return model_prefix


# ============ 모델 상태 판별 함수 ============

def get_model_status(model_name: str, active_jobs: dict = None) -> str:
    """
    모델 상태 판별 (Docker 기반 - active_jobs 없이도 동작)
    
    Args:
        model_name: 모델 이름
        active_jobs: (deprecated) 호환성을 위해 남겨둠, 사용 안함
    
    Returns:
        str: 모델 상태
            - "training": 훈련 중
            - "evaluating": 평가 중
            - "ready": 훈련 완료 (체크포인트 존재)
            - "failed": 훈련 실패 (체크포인트 없음)
    """
    # Docker 컨테이너에서 직접 상태 확인
    from physicar.cloud.deepracer.jobs import (
        get_run_id_by_model_name, get_training_status
    )
    
    run_id = get_run_id_by_model_name(model_name)
    if run_id is not None:
        status_info = get_training_status(run_id)
        docker_status = status_info.get("status", "unknown")
        
        if docker_status == "running":
            # 훈련인지 평가인지 구분 (컨테이너 이름으로)
            containers = status_info.get("containers", [])
            for c in containers:
                if "eval" in c:
                    return "evaluating"
            return "training"
    
    # 파일 기반 상태 판별 - 체크포인트 존재 여부로 판단
    if _has_checkpoints(model_name):
        return "ready"
    else:
        return "failed"


def _has_checkpoints(model_name: str) -> bool:
    """모델에 체크포인트가 있는지 확인"""
    try:
        checkpoints_key = f"models/{model_name}/model/deepracer_checkpoints.json"
        checkpoints = minio_read_json(checkpoints_key)
        if checkpoints and (checkpoints.get("best_checkpoint") or checkpoints.get("last_checkpoint")):
            return True
        return False
    except Exception:
        return False


def minio_file_exists(key: str) -> bool:
    """MinIO에 파일이 존재하는지 확인"""
    try:
        client = _get_minio_client()
        client.stat_object(MINIO_BUCKET, key)
        return True
    except Exception:
        return False


def is_model_clonable(model_name: str, active_jobs: dict = None) -> Tuple[bool, str]:
    """
    모델 Clone 가능 여부 확인
    
    Args:
        model_name: 모델 이름
        active_jobs: 활성 작업 딕셔너리
    
    Returns:
        Tuple[bool, str]: (Clone 가능 여부, 메시지)
    """
    model_prefix = f"models/{model_name}/"
    
    # 모델 존재 확인
    if not minio_prefix_exists(model_prefix):
        return False, f"Model '{model_name}' not found"
    
    # 상태 확인
    status = get_model_status(model_name, active_jobs)
    
    if status == "failed":
        return False, "Cannot clone a failed model. No checkpoints available."
    
    return True, "OK"


def get_model_list(active_jobs: dict = None) -> List[Dict[str, Any]]:
    """
    모든 모델 목록 조회
    
    Args:
        active_jobs: 활성 작업 딕셔너리
    
    Returns:
        List[Dict]: 모델 정보 리스트
    """
    models = []
    
    try:
        client = _get_minio_client()
        # models/ 폴더 내 모든 폴더 나열
        objects = client.list_objects(MINIO_BUCKET, prefix="models/", recursive=False)
        
        for obj in objects:
            # models/test1/ -> test1
            if obj.is_dir:
                model_name = obj.object_name.replace("models/", "").rstrip("/")
                if model_name:
                    model_info = get_model_summary(model_name, active_jobs)
                    if model_info:
                        models.append(model_info)
    except Exception as e:
        print(f"Error listing models: {e}")
    
    # 생성 시간 기준 정렬 (최신 먼저)
    models.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    
    return models


def get_model_summary(model_name: str, active_jobs: dict = None) -> Optional[Dict[str, Any]]:
    """
    모델 요약 정보 조회
    
    Args:
        model_name: 모델 이름
        active_jobs: 활성 작업 딕셔너리
    
    Returns:
        Dict: 모델 요약 정보
    """
    model_prefix = f"models/{model_name}/"
    
    if not minio_prefix_exists(model_prefix):
        return None
    
    status = get_model_status(model_name, active_jobs)
    
    # training-params/main.yaml에서 기본 정보 추출
    main_params = minio_read_yaml(f"{model_prefix}training-params/main.yaml") or {}
    
    # 센서 정보 (model_metadata.json에서)
    metadata = minio_read_json(f"{model_prefix}model/model_metadata.json") or {}
    sensors = metadata.get("sensor", [])
    has_lidar = "SECTOR_LIDAR" in sensors
    
    # 체크포인트 정보
    checkpoints = minio_read_json(f"{model_prefix}model/deepracer_checkpoints.json") or {}
    best_checkpoint = checkpoints.get("best_checkpoint", {})
    last_checkpoint = checkpoints.get("last_checkpoint", {})
    
    # 생성 시간 (training-params/main.yaml 파일의 수정 시간 사용)
    created_at = ""
    size_bytes = 0
    try:
        client = _get_minio_client()
        stat = client.stat_object(MINIO_BUCKET, f"{model_prefix}training-params/main.yaml")
        if stat.last_modified:
            created_at = stat.last_modified.isoformat()
        
        # 모델 폴더 전체 크기 계산
        objects = client.list_objects(MINIO_BUCKET, prefix=model_prefix, recursive=True)
        for obj in objects:
            if obj.size:
                size_bytes += obj.size
    except Exception:
        pass
    
    # CPU 사용량 정보 (Docker 기반)
    cpu_used = 0
    run_id = None
    if status in ("training", "evaluating"):
        from physicar.cloud.deepracer.jobs import (
            get_run_id_by_model_name, get_running_containers
        )
        run_id = get_run_id_by_model_name(model_name)
        if run_id is not None:
            # 해당 run_id의 컨테이너들 CPU 합산
            containers = get_running_containers()
            for c in containers:
                if c.get("run_id") == run_id:
                    cpu_used += c.get("cpu", 0)
    
    # 크기를 GB로 변환 (소수점 2자리)
    size_gb = round(size_bytes / (1024 ** 3), 2)
    
    return {
        "model_name": model_name,
        "status": status,
        "sensors": "Camera" + (", Lidar" if has_lidar else ""),
        "body_shell_type": main_params.get("BODY_SHELL_TYPE", "deepracer"),
        "best_checkpoint": best_checkpoint.get("name", ""),
        "last_checkpoint": last_checkpoint.get("name", ""),
        "created_at": created_at,
        "cpu_used": cpu_used,
        "run_id": run_id,
        "size_gb": size_gb,
    }


def get_model_main_simulation_config(model_name: str) -> Dict[str, Any]:
    """
    모델의 main 시뮬레이션 설정 조회
    
    Args:
        model_name: 모델 이름
    
    Returns:
        Dict: main 시뮬레이션 설정
            - track_id: 트랙 ID
            - direction: 방향 (clockwise/counterclockwise)
            - alternate_direction: 방향 변경 여부
            - race_type: 레이스 타입 (TIME_TRIAL/OBJECT_AVOIDANCE)
            - object_avoidance: Object Avoidance 설정 (race_type이 OBJECT_AVOIDANCE인 경우)
    """
    model_prefix = f"models/{model_name}/"
    
    # training-params/main.yaml에서 정보 추출
    main_params = minio_read_yaml(f"{model_prefix}training-params/main.yaml") or {}
    
    # WORLD_NAME에서 track_id와 direction 추출 (npy 이름 -> track_id)
    world_name = main_params.get("WORLD_NAME", "reinvent_base")
    decoded_track_id, decoded_direction = decode_world_name(world_name)
    
    # 기본값
    result = {
        "track_id": decoded_track_id,
        "direction": decoded_direction,
        "alternate_direction": False,
        "race_type": main_params.get("RACE_TYPE", "TIME_TRIAL"),
    }
    
    # 방향 정보 추출 - 이미 decode_world_name에서 추출했으므로 REVERSE_DIR로 덮어쓰기
    # (REVERSE_DIR이 있으면 우선 사용, 없으면 decode된 방향 유지)
    if "REVERSE_DIR" in main_params:
        reverse_direction = main_params.get("REVERSE_DIR", False)
        if isinstance(reverse_direction, str):
            reverse_direction = reverse_direction.lower() == "true"
        result["direction"] = "clockwise" if reverse_direction else "counterclockwise"
    
    change_start = main_params.get("CHANGE_START_POSITION", False)
    if isinstance(change_start, str):
        change_start = change_start.lower() == "true"
    result["alternate_direction"] = change_start
    
    # Object Avoidance 설정
    if result["race_type"] == "OBJECT_AVOIDANCE":
        result["object_avoidance"] = {
            "object_type": main_params.get("OBJECT_TYPE", "box"),
            "number_of_objects": int(main_params.get("NUMBER_OF_OBSTACLES", 3)),
            "randomize_locations": main_params.get("RANDOMIZE_OBSTACLE_LOCATIONS", True),
            "object_positions": main_params.get("OBJECT_POSITIONS", []),
        }
    
    return result
