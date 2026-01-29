"""
DeepRacer 모델 생성 스키마
Pydantic 모델로 API 요청 검증
deepracer-for-cloud 형식에 맞춤
"""
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, field_validator, model_validator
import re

from physicar.cloud.deepracer.config import (
    USER_INPUT_LIMITS,
    MODEL_METADATA_DEFAULTS,
    HYPERPARAMETERS_DEFAULTS,
    RUN_ENV_DEFAULTS,
)


# ============ Action Space ============
class ActionItem(BaseModel):
    """단일 액션 (model_metadata.json의 action_space 항목)"""
    steering_angle: int = Field(
        ge=USER_INPUT_LIMITS["action_space"]["min_steering_angle"],
        le=USER_INPUT_LIMITS["action_space"]["max_steering_angle"],
    )
    speed: float = Field(
        ge=USER_INPUT_LIMITS["action_space"]["min_speed"],
        le=USER_INPUT_LIMITS["action_space"]["max_speed"],
    )


# ============ Object Avoidance ============
class ObjectLocation(BaseModel):
    """장애물 위치 (DR_OA_OBJECT_POSITIONS 용)"""
    progress: float = Field(ge=0.0, le=100.0, description="트랙 진행률 %")
    lane: Literal["inside", "outside"] = "inside"
    
    def to_drfc_format(self) -> str:
        """deepracer-for-cloud 형식으로 변환: 'progress,lane_value'"""
        lane_value = 1 if self.lane == "inside" else -1
        return f"{self.progress / 100},{lane_value}"


class ObjectAvoidanceConfig(BaseModel):
    """장애물 회피 설정 (DR_OA_* 환경변수용)"""
    object_type: Literal["box_obstacle", "deepracer_box_obstacle", "amazon_box_obstacle"] = "box_obstacle"
    number_of_objects: int = Field(default=3, ge=1, le=10)
    randomize_locations: bool = True
    object_locations: Optional[List[ObjectLocation]] = None


# ============ Simulation (단일) ============
class SimulationConfig(BaseModel):
    """시뮬레이션 설정 (run.env 또는 worker-{n}.env용)"""
    track_id: str
    track_direction: Literal["clockwise", "counterclockwise"] = "counterclockwise"
    alternate_direction: bool = False
    race_type: Literal["TIME_TRIAL", "OBJECT_AVOIDANCE"] = "TIME_TRIAL"
    object_avoidance: Optional[ObjectAvoidanceConfig] = None


# ============ Vehicle ============
class VehicleConfig(BaseModel):
    """차량 설정 (model_metadata.json용)"""
    vehicle_type: Literal["deepracer", "physicar"] = "deepracer"
    lidar: bool = False
    action_space: List[ActionItem] = Field(
        default_factory=lambda: [ActionItem(**a) for a in MODEL_METADATA_DEFAULTS["action_space"]],
        min_length=USER_INPUT_LIMITS["action_space"]["min_actions"],
        max_length=USER_INPUT_LIMITS["action_space"]["max_actions"],
    )

    @model_validator(mode='after')
    def enforce_lidar_for_physicar(self) -> 'VehicleConfig':
        """PhysiCar 차량은 항상 Lidar 사용"""
        if self.vehicle_type == 'physicar':
            self.lidar = True
        return self

    def get_sensor_list(self) -> List[str]:
        """model_metadata.json의 sensor 배열 생성"""
        sensors = ["FRONT_FACING_CAMERA"]
        if self.lidar:
            sensors.append("SECTOR_LIDAR")
        return sensors


# ============ Hyperparameters ============
class HyperparametersConfig(BaseModel):
    """하이퍼파라미터 설정 (hyperparameters.json용)"""
    batch_size: Literal[32, 64, 128, 256, 512] = HYPERPARAMETERS_DEFAULTS["batch_size"]
    discount_factor: float = Field(
        default=HYPERPARAMETERS_DEFAULTS["discount_factor"],
        ge=USER_INPUT_LIMITS["discount_factor"]["min"],
        le=USER_INPUT_LIMITS["discount_factor"]["max"],
    )
    learning_rate: float = Field(
        default=HYPERPARAMETERS_DEFAULTS["lr"],
        ge=USER_INPUT_LIMITS["learning_rate"]["min"],
        le=USER_INPUT_LIMITS["learning_rate"]["max"],
    )
    loss_type: Literal["huber", "mean_squared_error"] = HYPERPARAMETERS_DEFAULTS["loss_type"]
    entropy: float = Field(
        default=HYPERPARAMETERS_DEFAULTS["beta_entropy"],
        ge=USER_INPUT_LIMITS["entropy"]["min"],
        le=USER_INPUT_LIMITS["entropy"]["max"],
    )


# ============ Training ============
class TrainingConfig(BaseModel):
    """훈련 설정"""
    training_time_minutes: int = Field(
        default=USER_INPUT_LIMITS["training_time_minutes"]["default"],
        ge=USER_INPUT_LIMITS["training_time_minutes"]["min"],
        le=USER_INPUT_LIMITS["training_time_minutes"]["max"],
    )
    best_model_metric: Literal["progress", "reward"] = "progress"
    hyperparameters: HyperparametersConfig = Field(default_factory=HyperparametersConfig)


# ============ Evaluation ============
class EvaluationConfig(BaseModel):
    """평가 설정 (DR_EVAL_* 환경변수용)"""
    number_of_trials: int = Field(
        default=int(RUN_ENV_DEFAULTS["DR_EVAL_NUMBER_OF_TRIALS"]),
        ge=USER_INPUT_LIMITS["number_of_trials"]["min"],
        le=USER_INPUT_LIMITS["number_of_trials"]["max"],
    )
    checkpoint: Literal["best", "last"] = RUN_ENV_DEFAULTS["DR_EVAL_CHECKPOINT"]
    offtrack_penalty: float = Field(
        default=float(RUN_ENV_DEFAULTS["DR_EVAL_OFF_TRACK_PENALTY"]),
        ge=USER_INPUT_LIMITS["penalty"]["min"],
        le=USER_INPUT_LIMITS["penalty"]["max"],
    )
    collision_penalty: float = Field(
        default=float(RUN_ENV_DEFAULTS["DR_EVAL_COLLISION_PENALTY"]),
        ge=USER_INPUT_LIMITS["penalty"]["min"],
        le=USER_INPUT_LIMITS["penalty"]["max"],
    )


# ============ 전체 모델 생성 요청 ============
class CreateModelRequest(BaseModel):
    """
    모델 생성 요청 스키마
    Web UI → API → deepracer-for-cloud 파일 생성
    """
    model_name: str = Field(
        min_length=USER_INPUT_LIMITS["model_name"]["min_length"],
        max_length=USER_INPUT_LIMITS["model_name"]["max_length"],
    )
    
    # 시뮬레이션 (main + subs)
    simulation: SimulationConfig
    sub_simulations: List[SimulationConfig] = Field(default_factory=list, max_length=6)
    
    # 차량
    vehicle: VehicleConfig = Field(default_factory=VehicleConfig)
    
    # 훈련
    training: TrainingConfig = Field(default_factory=TrainingConfig)
    
    # 평가 (선택)
    evaluation: Optional[EvaluationConfig] = None
    
    # 보상함수
    reward_function: str = Field(min_length=10)

    @field_validator("model_name")
    @classmethod
    def validate_model_name(cls, v):
        pattern = USER_INPUT_LIMITS["model_name"]["pattern"]
        if not re.match(pattern, v):
            raise ValueError("Model name: alphanumeric, underscore, dash, dot only")
        return v

    @field_validator("reward_function")
    @classmethod
    def validate_reward_function(cls, v):
        if "def reward_function" not in v:
            raise ValueError("Reward function must contain 'def reward_function'")
        return v
    
    def get_worker_count(self) -> int:
        """전체 워커 수 (main + sub simulations)"""
        return 1 + len(self.sub_simulations)


# ============ 모델 복제 요청 ============
class CloneModelRequest(CreateModelRequest):
    """
    모델 복제 요청 스키마
    CreateModelRequest + pretrained 설정
    """
    pretrained_model_name: str = Field(
        min_length=USER_INPUT_LIMITS["model_name"]["min_length"],
        max_length=USER_INPUT_LIMITS["model_name"]["max_length"],
        description="복제 원본 모델 이름"
    )
    pretrained_checkpoint: Literal["best", "last"] = Field(
        default="last",
        description="사전 훈련된 체크포인트 (best/last)"
    )


# ============ 기본 보상함수 ============
DEFAULT_REWARD_FUNCTION = '''def reward_function(params):
    """
    Example: Center line following
    """
    distance_from_center = params['distance_from_center']
    track_width = params['track_width']

    marker_1 = 0.1 * track_width
    marker_2 = 0.25 * track_width
    marker_3 = 0.5 * track_width

    if distance_from_center <= marker_1:
        reward = 1.0
    elif distance_from_center <= marker_2:
        reward = 0.5
    elif distance_from_center <= marker_3:
        reward = 0.1
    else:
        reward = 1e-3

    return float(reward)
'''


# ============ 평가 시작 요청 ============
class StartEvaluationRequest(BaseModel):
    """평가 시작 요청 스키마"""
    model_name: str = Field(
        min_length=USER_INPUT_LIMITS["model_name"]["min_length"],
        max_length=USER_INPUT_LIMITS["model_name"]["max_length"],
        description="평가할 모델 이름"
    )
    
    # 시뮬레이션 설정
    simulation: SimulationConfig = Field(
        default_factory=SimulationConfig,
        description="시뮬레이션 설정 (트랙, 방향, 레이스 타입 등)"
    )
    
    # 평가 설정
    evaluation: EvaluationConfig = Field(
        default_factory=EvaluationConfig,
        description="평가 설정 (시도 횟수, 체크포인트, 패널티)"
    )
