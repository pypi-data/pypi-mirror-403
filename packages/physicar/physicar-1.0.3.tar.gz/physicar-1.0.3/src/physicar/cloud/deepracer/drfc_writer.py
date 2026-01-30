"""
deepracer-for-cloud 파일 생성 모듈
CreateModelRequest → system.env, run.env, worker-{n}.env + MinIO에 hyperparameters.json, model_metadata.json, reward_function.py
"""
import json
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional

from physicar.cloud.deepracer.config import (
    DRFC_DIR,
    DRFC_CUSTOM_FILES,
    DRFC_DEFAULTS,
    DRFC_SYSTEM_ENV,
    DRFC_RUN_ENV,
    TRACKS_INFO_PATH,
    SYSTEM_ENV_LOCKED,
    RUN_ENV_LOCKED,
    RUN_ENV_DEFAULTS,
    WORKER_ENV_TEMPLATE,
    WORKER_CAR_COLORS,
    MODEL_METADATA_LOCKED,
    MODEL_METADATA_DEFAULTS,
    HYPERPARAMETERS_LOCKED,
    HYPERPARAMETERS_DEFAULTS,
    get_num_episodes_between_training,
    get_num_epochs,
)
from physicar.cloud.deepracer.schemas import CreateModelRequest, SimulationConfig
from physicar.cloud.deepracer.settings_manager import minio_write_json, minio_write_text


# ============ 유틸리티 함수 ============

def read_env_file(file_path: Path) -> List[str]:
    """env 파일을 줄 단위 리스트로 읽기"""
    file_path = Path(file_path).expanduser()
    if not file_path.exists():
        return []
    with open(file_path, "r") as f:
        return f.readlines()


def write_env_file(file_path: Path, lines: List[str]):
    """env 파일 쓰기"""
    file_path = Path(file_path).expanduser()
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w") as f:
        f.writelines(lines)


def _quote_env_value(value: str) -> str:
    """env 값에 특수문자가 있으면 따옴표로 감싸기"""
    if ';' in value or ' ' in value or '&' in value or '|' in value:
        if (value.startswith('"') and value.endswith('"')) or \
           (value.startswith("'") and value.endswith("'")):
            return value
        return f'"{value}"'
    return value


def update_env_lines(lines: List[str], key: str, value: str) -> List[str]:
    """env 파일의 특정 키 값 업데이트 (없으면 추가)"""
    quoted_value = _quote_env_value(value)
    updated = False
    new_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(f"{key}=") or stripped.startswith(f"#{key}="):
            new_lines.append(f"{key}={quoted_value}\n")
            updated = True
        else:
            new_lines.append(line if line.endswith('\n') else line + '\n')
    
    if not updated:
        new_lines.append(f"{key}={quoted_value}\n")
    
    return new_lines


def read_json_file(file_path: Path) -> Dict[str, Any]:
    """JSON 파일 읽기"""
    file_path = Path(file_path).expanduser()
    if not file_path.exists():
        return {}
    with open(file_path, "r") as f:
        return json.load(f)


def write_json_file(file_path: Path, data: Dict[str, Any]):
    """JSON 파일 쓰기"""
    file_path = Path(file_path).expanduser()
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)


def write_text_file(file_path: Path, content: str):
    """텍스트 파일 쓰기"""
    file_path = Path(file_path).expanduser()
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w") as f:
        f.write(content)


def get_tracks_info() -> Dict[str, Any]:
    """트랙 정보 로드"""
    if not TRACKS_INFO_PATH.exists():
        return {}
    with open(TRACKS_INFO_PATH, "r") as f:
        return yaml.safe_load(f) or {}


def get_world_name(track_id: str, direction: str) -> str:
    """
    트랙 ID와 방향으로 DR_WORLD_NAME 값 생성
    예: track_id="2024_reinvent_champ", direction="counterclockwise" → "2024_reinvent_champ_ccw"
    """
    tracks_info = get_tracks_info()
    
    if track_id in tracks_info:
        npy_info = tracks_info[track_id].get("npy", {})
        npy_file = npy_info.get(direction)
        if npy_file:
            return npy_file.replace(".npy", "")
    
    # 기본 변환
    suffix = "_ccw" if direction == "counterclockwise" else "_cw"
    return f"{track_id}{suffix}"


# ============ 파일 생성 클래스 ============

class DRFCWriter:
    """deepracer-for-cloud 설정 파일 생성기"""
    
    def __init__(self, request: CreateModelRequest):
        self.request = request
        self.model_name = request.model_name
        self.worker_count = request.get_worker_count()
    
    def generate_all(self) -> Dict[str, Path]:
        """모든 설정 파일 생성"""
        files = {}
        
        # 1. system.env
        files["system.env"] = self.generate_system_env()
        
        # 2. run.env (main simulation)
        files["run.env"] = self.generate_run_env()
        
        # 3. worker-{n}.env (sub simulations)
        for i, sub_sim in enumerate(self.request.sub_simulations):
            worker_num = i + 2  # worker-2.env, worker-3.env, ...
            files[f"worker-{worker_num}.env"] = self.generate_worker_env(worker_num, sub_sim)
        
        # 4. custom_files/hyperparameters.json
        files["hyperparameters.json"] = self.generate_hyperparameters()
        
        # 5. custom_files/model_metadata.json
        files["model_metadata.json"] = self.generate_model_metadata()
        
        # 6. custom_files/reward_function.py
        files["reward_function.py"] = self.generate_reward_function()
        
        return files
    
    def generate_system_env(self) -> Path:
        """system.env 생성/업데이트"""
        file_path = DRFC_SYSTEM_ENV
        
        # 기존 파일 읽기 또는 기본 템플릿
        if file_path.exists():
            lines = read_env_file(file_path)
        else:
            template_path = DRFC_DEFAULTS / "template-system.env"
            lines = read_env_file(template_path) if template_path.exists() else []
        
        # 고정값 적용
        for key, value in SYSTEM_ENV_LOCKED.items():
            lines = update_env_lines(lines, key, value)
        
        # 워커 수 설정
        lines = update_env_lines(lines, "DR_WORKERS", str(self.worker_count))
        
        write_env_file(file_path, lines)
        return file_path
    
    def generate_run_env(self) -> Path:
        """run.env 생성 (main simulation 설정)"""
        file_path = DRFC_RUN_ENV
        
        # 기존 파일 읽기 또는 기본 템플릿
        if file_path.exists():
            lines = read_env_file(file_path)
        else:
            template_path = DRFC_DEFAULTS / "template-run.env"
            lines = read_env_file(template_path) if template_path.exists() else []
        
        # 고정값 적용
        for key, value in RUN_ENV_LOCKED.items():
            lines = update_env_lines(lines, key, value)
        
        # 모델명 (DR_UPLOAD_S3_PREFIX는 $DR_LOCAL_S3_MODEL_PREFIX 참조 유지)
        lines = update_env_lines(lines, "DR_LOCAL_S3_MODEL_PREFIX", f"models/{self.model_name}")
        
        # Custom files 경로 (공통 경로)
        lines = update_env_lines(lines, "DR_LOCAL_S3_CUSTOM_FILES_PREFIX", "custom_files")
        
        # S3 키 경로
        lines = update_env_lines(lines, "DR_LOCAL_S3_MODEL_METADATA_KEY", 
                                  "$DR_LOCAL_S3_CUSTOM_FILES_PREFIX/model_metadata.json")
        lines = update_env_lines(lines, "DR_LOCAL_S3_HYPERPARAMETERS_KEY", 
                                  "$DR_LOCAL_S3_CUSTOM_FILES_PREFIX/hyperparameters.json")
        lines = update_env_lines(lines, "DR_LOCAL_S3_REWARD_KEY", 
                                  "$DR_LOCAL_S3_CUSTOM_FILES_PREFIX/reward_function.py")
        lines = update_env_lines(lines, "DR_LOCAL_S3_METRICS_PREFIX", 
                                  "$DR_LOCAL_S3_MODEL_PREFIX")
        
        # Main Simulation 설정
        sim = self.request.simulation
        world_name = get_world_name(sim.track_id, sim.track_direction)
        lines = update_env_lines(lines, "DR_WORLD_NAME", world_name)
        lines = update_env_lines(lines, "DR_RACE_TYPE", sim.race_type)
        lines = update_env_lines(lines, "DR_CAR_COLOR", WORKER_CAR_COLORS[0])
        
        # Vehicle type (deepracer/physicar) 설정
        vehicle_type = self.request.vehicle.vehicle_type
        lines = update_env_lines(lines, "DR_CAR_BODY_SHELL_TYPE", vehicle_type)
        
        # 방향 설정
        reverse = "True" if sim.track_direction == "clockwise" else "False"
        lines = update_env_lines(lines, "DR_TRAIN_REVERSE_DIRECTION", reverse)
        lines = update_env_lines(lines, "DR_TRAIN_ALTERNATE_DRIVING_DIRECTION", 
                                  str(sim.alternate_direction))
        
        # Best model metric
        lines = update_env_lines(lines, "DR_TRAIN_BEST_MODEL_METRIC", 
                                  self.request.training.best_model_metric)
        
        # Object Avoidance 설정
        if sim.race_type == "OBJECT_AVOIDANCE" and sim.object_avoidance:
            oa = sim.object_avoidance
            lines = update_env_lines(lines, "DR_OA_NUMBER_OF_OBSTACLES", str(oa.number_of_objects))
            lines = update_env_lines(lines, "DR_OA_RANDOMIZE_OBSTACLE_LOCATIONS", 
                                      str(oa.randomize_locations))
            lines = update_env_lines(lines, "DR_OA_OBSTACLE_TYPE", oa.object_type)
            
            # Bot car 체크
            is_bot_car = "deepracer_car" in oa.object_type
            lines = update_env_lines(lines, "DR_OA_IS_OBSTACLE_BOT_CAR", str(is_bot_car))
            
            # Object positions (수동 배치 시)
            if not oa.randomize_locations and oa.object_locations:
                positions = ";".join([loc.to_drfc_format() for loc in oa.object_locations])
                lines = update_env_lines(lines, "DR_OA_OBJECT_POSITIONS", f'"{positions}"')
            else:
                lines = update_env_lines(lines, "DR_OA_OBJECT_POSITIONS", "")
        
        # Evaluation 설정
        if self.request.evaluation:
            ev = self.request.evaluation
            lines = update_env_lines(lines, "DR_EVAL_NUMBER_OF_TRIALS", str(ev.number_of_trials))
            lines = update_env_lines(lines, "DR_EVAL_CHECKPOINT", ev.checkpoint)
            lines = update_env_lines(lines, "DR_EVAL_OFF_TRACK_PENALTY", str(ev.offtrack_penalty))
            lines = update_env_lines(lines, "DR_EVAL_COLLISION_PENALTY", str(ev.collision_penalty))
        
        write_env_file(file_path, lines)
        return file_path
    
    def generate_worker_env(self, worker_num: int, sim: SimulationConfig) -> Path:
        """worker-{n}.env 생성 (sub simulation 설정)"""
        file_path = DRFC_DIR / f"worker-{worker_num}.env"
        
        # 템플릿에서 시작
        lines = []
        for key, value in WORKER_ENV_TEMPLATE.items():
            lines.append(f"{key}={value}\n")
        
        # 시뮬레이션 설정
        world_name = get_world_name(sim.track_id, sim.track_direction)
        lines = update_env_lines(lines, "DR_WORLD_NAME", world_name)
        lines = update_env_lines(lines, "DR_RACE_TYPE", sim.race_type)
        
        # 워커별 색상
        color_idx = min(worker_num - 1, len(WORKER_CAR_COLORS) - 1)
        lines = update_env_lines(lines, "DR_CAR_COLOR", WORKER_CAR_COLORS[color_idx])
        
        # 방향 설정
        reverse = "True" if sim.track_direction == "clockwise" else "False"
        lines = update_env_lines(lines, "DR_TRAIN_REVERSE_DIRECTION", reverse)
        lines = update_env_lines(lines, "DR_TRAIN_ALTERNATE_DRIVING_DIRECTION", 
                                  str(sim.alternate_direction))
        
        # Object Avoidance 설정
        if sim.race_type == "OBJECT_AVOIDANCE" and sim.object_avoidance:
            oa = sim.object_avoidance
            lines = update_env_lines(lines, "DR_OA_NUMBER_OF_OBSTACLES", str(oa.number_of_objects))
            lines = update_env_lines(lines, "DR_OA_RANDOMIZE_OBSTACLE_LOCATIONS", 
                                      str(oa.randomize_locations))
            lines = update_env_lines(lines, "DR_OA_OBSTACLE_TYPE", oa.object_type)
            
            is_bot_car = "deepracer_car" in oa.object_type
            lines = update_env_lines(lines, "DR_OA_IS_OBSTACLE_BOT_CAR", str(is_bot_car))
            
            if not oa.randomize_locations and oa.object_locations:
                positions = ";".join([loc.to_drfc_format() for loc in oa.object_locations])
                lines = update_env_lines(lines, "DR_OA_OBJECT_POSITIONS", f'"{positions}"')
        
        write_env_file(file_path, lines)
        return file_path
    
    def generate_hyperparameters(self) -> str:
        """hyperparameters.json 생성 → MinIO에 저장"""
        minio_key = "custom_files/hyperparameters.json"
        
        hp = self.request.training.hyperparameters
        
        data = {
            # 사용자 설정 가능
            "batch_size": hp.batch_size,
            "beta_entropy": hp.entropy,
            "discount_factor": hp.discount_factor,
            "loss_type": hp.loss_type,
            "lr": hp.learning_rate,
            # 워커 수에 따라 자동 계산
            "num_episodes_between_training": get_num_episodes_between_training(self.worker_count),
            "num_epochs": get_num_epochs(self.worker_count),
            # 고정값
            **HYPERPARAMETERS_LOCKED,
        }
        
        minio_write_json(minio_key, data)
        return minio_key
    
    def generate_model_metadata(self) -> str:
        """model_metadata.json 생성 → MinIO에 저장"""
        minio_key = "custom_files/model_metadata.json"
        
        vehicle = self.request.vehicle
        training = self.request.training
        
        # Action space 변환
        action_space = [
            {"steering_angle": a.steering_angle, "speed": a.speed}
            for a in vehicle.action_space
        ]
        
        # DEBUG
        print(f"=== generate_model_metadata ===")
        print(f"vehicle.action_space count: {len(vehicle.action_space)}")
        print(f"action_space to write: {action_space}")
        print(f"max_training_time: {training.training_time_minutes}")
        print(f"================================")
        
        data = {
            "action_space": action_space,
            "sensor": vehicle.get_sensor_list(),
            "max_training_time": training.training_time_minutes,
            # 고정값
            **MODEL_METADATA_LOCKED,
            # vehicle_type은 run.env의 DR_CAR_BODY_SHELL_TYPE에서 관리 (metadata.json에 저장하지 않음)
        }
        
        print(f"=== WRITING TO MINIO ===")
        print(f"minio_key: {minio_key}")
        print(f"data: {data}")
        print(f"========================")
        
        minio_write_json(minio_key, data)
        return minio_key
    
    def generate_reward_function(self) -> str:
        """reward_function.py 생성 → MinIO에 저장"""
        minio_key = "custom_files/reward_function.py"
        minio_write_text(minio_key, self.request.reward_function)
        return minio_key


# ============ 편의 함수 ============

def create_model_files(request: CreateModelRequest) -> Dict[str, Path]:
    """
    모델 생성 요청으로 모든 deepracer-for-cloud 파일 생성
    
    Args:
        request: CreateModelRequest 스키마
    
    Returns:
        생성된 파일들의 경로 딕셔너리
    """
    writer = DRFCWriter(request)
    return writer.generate_all()


def _get_minio_client():
    """MinIO 클라이언트 생성"""
    from minio import Minio
    return Minio(
        "localhost:9000",
        access_key="physicar",
        secret_key="physicar",
        secure=False
    )


def _minio_model_exists(model_name: str) -> bool:
    """MinIO에서 모델 폴더 존재 여부 확인"""
    client = _get_minio_client()
    prefix = f"models/{model_name}/"
    
    # 해당 prefix로 시작하는 객체가 하나라도 있으면 존재
    for _ in client.list_objects("bucket", prefix=prefix):
        return True
    return False


def validate_model_name_available(model_name: str) -> tuple[bool, str]:
    """
    모델명 중복 체크 (MinIO API 사용)
    
    Returns:
        (사용가능 여부, 대안 이름 또는 에러 메시지)
    """
    if not _minio_model_exists(model_name):
        return True, model_name
    
    # 중복 시 대안 이름 생성
    i = 1
    while True:
        new_name = f"{model_name}-{i}"
        if not _minio_model_exists(new_name):
            return False, new_name
        i += 1
        if i > 100:
            return False, f"{model_name}-{i}"
