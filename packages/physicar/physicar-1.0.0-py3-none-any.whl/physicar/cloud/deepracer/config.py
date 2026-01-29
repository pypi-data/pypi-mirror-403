"""
앱 설정 및 상수 관리
"""
import pytz
from datetime import datetime

# ============ 언어 설정 ============
SUPPORTED_LANGUAGES = {
    "en": "English",
    "ko": "한국어",
    "it": "Italiano",
    "nl": "Nederlands",
    "de": "Deutsch",
    "pt": "Português",
    "es": "Español",
    "fr": "Français",
    "hi": "हिन्दी",
    "vi": "Tiếng Việt",
    "ja": "日本語",
    "pl": "Polski",
    "ru": "Русский",
    "th": "ไทย",
    "tr": "Türkçe",
    "zh-hans": "简体中文",
    "zh-hant": "繁體中文",
    "id": "Bahasa Indonesia",
    "ar": "العربية",
    # "af": "Afrikaans",
    # "ar-dz": "العربية (الجزائر)",
    # "ast": "Asturianu",
    # "az": "Azərbaycanca",
    # "bg": "Български",
    # "be": "Беларуская",
    # "bn": "বাংলা",
    # "br": "Brezhoneg",
    # "bs": "Bosanski",
    # "ca": "Català",
    # "ckb": "کوردیی ناوەندی",
    # "cs": "Čeština",
    # "cy": "Cymraeg",
    # "da": "Dansk",
    # "dsb": "Dolnoserbšćina",
    # "el": "Ελληνικά",
    # "en-au": "Australian English",
    # "en-gb": "British English",
    # "eo": "Esperanto",
    # "es-ar": "Español de Argentina",
    # "es-co": "Español de Colombia",
    # "es-mx": "Español de México",
    # "es-ni": "Español de Nicaragua",
    # "es-ve": "Español de Venezuela",
    # "et": "Eesti",
    # "eu": "Euskara",
    # "fa": "فارسی",
    # "fi": "Suomi",
    # "fy": "Frysk",
    # "ga": "Gaeilge",
    # "gd": "Gàidhlig",
    # "gl": "Galego",
    # "he": "עברית",
    # "hr": "Hrvatski",
    # "hsb": "Hornjoserbšćina",
    # "hu": "Magyar",
    # "hy": "Հdelays",
    # "ia": "Interlingua",
    # "ig": "Igbo",
    # "io": "Ido",
    # "is": "Íslenska",
    # "ka": "ქართული",
    # "kab": "Taqbaylit",
    # "kk": "Қазақ тілі",
    # "km": "ភាសាខ្មែរ",
    # "kn": "ಕನ್ನಡ",
    # "ky": "Кыргызча",
    # "lb": "Lëtzebuergesch",
    # "lt": "Lietuvių",
    # "lv": "Latviešu",
    # "mk": "Македонски",
    # "ml": "മലയാളം",
    # "mn": "Монгол",
    # "mr": "मराठी",
    # "ms": "Bahasa Melayu",
    # "my": "မြန်မာဘာသာ",
    # "nb": "Norsk bokmål",
    # "ne": "नेपाली",
    # "nn": "Norsk nynorsk",
    # "os": "Ирон",
    # "pa": "ਪੰਜਾਬੀ",
    # "pt-br": "Português do Brasil",
    # "ro": "Română",
    # "sk": "Slovenčina",
    # "sl": "Slovenščina",
    # "sq": "Shqip",
    # "sr": "Српски",
    # "sr-latn": "Srpski (latinica)",
    # "sv": "Svenska",
    # "sw": "Kiswahili",
    # "ta": "தமிழ்",
    # "te": "తెలుగు",
    # "tg": "Тоҷикӣ",
    # "tk": "Türkmençe",
    # "tt": "Татарча",
    # "udm": "Удмурт",
    # "uk": "Українська",
    # "ur": "اردو",
    # "uz": "O'zbek",
}

DEFAULT_LANG = "en"

# ============ 시간대 설정 ============
# 모든 시간대 (pytz 사용)
SUPPORTED_TIMEZONES = {tz: datetime.now(pytz.timezone(tz)).tzname() for tz in pytz.all_timezones}

DEFAULT_TZ = "Asia/Seoul"

# ============ 세션/보안 설정 ============
SECRET_KEY = "your-secret-key-change-this-in-production"

# ============ 서버 설정 ============
HOST = "0.0.0.0"
PORT = 8000
DEBUG = True

# ============ 스트리밍 설정 ============
STREAM_QUALITY = 25  # MJPEG 스트리밍 품질 (1-100)
TRAINING_STREAM_PORT_BASE = 8080  # 훈련 스트림 포트: 8080 + run_id
EVAL_STREAM_PORT_BASE = 8180  # 평가 스트림 포트: 8180 + run_id

# ============================================================================
# DeepRacer for Cloud 설정
# deepracer-for-cloud 파일 형식에 맞춤 (system.env, run.env, *.json)
# ============================================================================

# ============ system.env 고정값 ============
SYSTEM_ENV_LOCKED = {
    "DR_CLOUD": "local",
    "DR_AWS_APP_REGION": "us-east-1",
    "DR_UPLOAD_S3_PROFILE": "minio",
    "DR_UPLOAD_S3_BUCKET": "bucket",
    "DR_LOCAL_S3_BUCKET": "bucket",
    "DR_LOCAL_S3_PROFILE": "minio",
    "DR_GUI_ENABLE": "False",
    "DR_KINESIS_STREAM_NAME": "",
    "DR_CAMERA_MAIN_ENABLE": "True",
    "DR_CAMERA_SUB_ENABLE": "False",
    "DR_CAMERA_KVS_ENABLE": "True",
    "DR_ENABLE_EXTRA_KVS_OVERLAY": "False",
    "DR_SIMAPP_SOURCE": "awsdeepracercommunity/deepracer-simapp",
    "DR_SIMAPP_VERSION": "5.3.3-cpu",
    "DR_MINIO_IMAGE": "RELEASE.2025-09-07T16-13-09Z",
    "DR_ANALYSIS_IMAGE": "cpu",
    "DR_ROBOMAKER_MOUNT_LOGS": "False",
    "DR_CLOUD_WATCH_ENABLE": "False",
    "DR_DOCKER_STYLE": "compose",
    "DR_HOST_X": "False",
    "DR_WEBVIEWER_PORT": "8100",
    "DR_DISPLAY": ":99",
}

# ============ run.env 고정값 ============
RUN_ENV_LOCKED = {
    "DR_RUN_ID": "0",
    "DR_CAR_NAME": "FastCar",
    # DR_CAR_BODY_SHELL_TYPE는 vehicle_type에 따라 동적으로 설정됨
    "DR_DISPLAY_NAME": "$DR_CAR_NAME",
    "DR_RACER_NAME": "$DR_CAR_NAME",
    "DR_ENABLE_DOMAIN_RANDOMIZATION": "False",
    "DR_TRAIN_CHANGE_START_POSITION": "True",
    "DR_TRAIN_START_POSITION_OFFSET": "0.0",
    "DR_TRAIN_ROUND_ROBIN_ADVANCE_DIST": "0.1",
    "DR_TRAIN_MULTI_CONFIG": "True",
    "DR_TRAIN_MIN_EVAL_TRIALS": "3",
    # DR_LOCAL_S3_CUSTOM_FILES_PREFIX는 run.env에서 모델별로 설정
    # "$DR_LOCAL_S3_MODEL_PREFIX/custom_files" 형태로 생성됨
    "DR_LOCAL_S3_TRAINING_PARAMS_FILE": "training-params/main.yaml",
    "DR_LOCAL_S3_EVAL_PARAMS_FILE": "evaluation_params.yaml",
    # Object Avoidance 기본값
    "DR_OA_MIN_DISTANCE_BETWEEN_OBSTACLES": "2.0",
    "DR_OA_IS_OBSTACLE_BOT_CAR": "False",
    # Head to Bot (미사용)
    "DR_H2B_IS_LANE_CHANGE": "False",
    "DR_H2B_LOWER_LANE_CHANGE_TIME": "3.0",
    "DR_H2B_UPPER_LANE_CHANGE_TIME": "5.0",
    "DR_H2B_LANE_CHANGE_DISTANCE": "1.0",
    "DR_H2B_NUMBER_OF_BOT_CARS": "0",
    "DR_H2B_MIN_DISTANCE_BETWEEN_BOT_CARS": "2.0",
    "DR_H2B_RANDOMIZE_BOT_CAR_LOCATIONS": "False",
    "DR_H2B_BOT_CAR_SPEED": "0.2",
    "DR_H2B_BOT_CAR_PENALTY": "5.0",
}

# ============ run.env 사용자 설정 가능 (기본값) ============
RUN_ENV_DEFAULTS = {
    # 시뮬레이션
    "DR_WORLD_NAME": "2024_reinvent_champ_ccw",
    "DR_RACE_TYPE": "TIME_TRIAL",          # TIME_TRIAL, OBJECT_AVOIDANCE
    "DR_CAR_COLOR": "Black",
    "DR_TRAIN_REVERSE_DIRECTION": "False",
    "DR_TRAIN_ALTERNATE_DRIVING_DIRECTION": "False",
    "DR_TRAIN_BEST_MODEL_METRIC": "progress",
    # Object Avoidance
    "DR_OA_NUMBER_OF_OBSTACLES": "3",
    "DR_OA_RANDOMIZE_OBSTACLE_LOCATIONS": "True",
    "DR_OA_OBSTACLE_TYPE": "box_obstacle",
    "DR_OA_OBJECT_POSITIONS": "",
    # Evaluation
    "DR_EVAL_NUMBER_OF_TRIALS": "5",
    "DR_EVAL_IS_CONTINUOUS": "True",
    "DR_EVAL_MAX_RESETS": "30",
    "DR_EVAL_OFF_TRACK_PENALTY": "3.0",
    "DR_EVAL_COLLISION_PENALTY": "5.0",
    "DR_EVAL_SAVE_MP4": "True",
    "DR_EVAL_CHECKPOINT": "last",
    "DR_EVAL_RESET_BEHIND_DIST": "-0.5",
    "DR_EVAL_REVERSE_DIRECTION": "False",
}

# ============ worker-{n}.env 템플릿 (서브 시뮬레이션) ============
WORKER_ENV_TEMPLATE = {
    "DR_WORLD_NAME": "2024_reinvent_champ_ccw",
    "DR_RACE_TYPE": "TIME_TRIAL",
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
}

# ============ 워커별 자동차 색상 ============
WORKER_CAR_COLORS = ["Black", "Grey", "Blue", "Red", "Orange", "White", "Purple"]

# ============ model_metadata.json 고정값 ============
MODEL_METADATA_LOCKED = {
    "neural_network": "DEEP_CONVOLUTIONAL_NETWORK_SHALLOW",
    "training_algorithm": "clipped_ppo",
    "action_space_type": "discrete",
    "version": "5",
}

# ============ model_metadata.json 기본값 ============
MODEL_METADATA_DEFAULTS = {
    "sensor": ["FRONT_FACING_CAMERA"],  # + "SECTOR_LIDAR" if lidar enabled
    "action_space": [
        {"steering_angle": -25, "speed": 0.5},
        {"steering_angle": -15, "speed": 1.0},
        {"steering_angle": 0, "speed": 2.0},
        {"steering_angle": 15, "speed": 1.0},
        {"steering_angle": 25, "speed": 0.5},
    ],
}

# ============ hyperparameters.json 고정값 ============
HYPERPARAMETERS_LOCKED = {
    "e_greedy_value": 0.05,
    "epsilon_steps": 10000,
    "exploration_type": "categorical",
    # num_epochs: 워커 수에 따라 동적 계산 (get_num_epochs 함수 사용)
    "stack_size": 1,
    "term_cond_avg_score": 100000.0,
    "term_cond_max_episodes": 100000,
    "sac_alpha": 0.2,
}

# ============ hyperparameters.json 기본값 (사용자 변경 가능) ============
HYPERPARAMETERS_DEFAULTS = {
    "batch_size": 64,
    "beta_entropy": 0.01,
    "discount_factor": 0.99,
    "loss_type": "huber",
    "lr": 0.0003,
    "num_episodes_between_training": 20,  # 서브시뮬레이션 수에 따라 자동 계산
}

# ============ 사용자 입력 제한/옵션 ============
USER_INPUT_LIMITS = {
    # 모델명
    "model_name": {
        "min_length": 1,
        "max_length": 100,
        "pattern": r"^[a-zA-Z0-9_.-]+$",
    },
    # Action Space
    "action_space": {
        "min_speed": 0.5,
        "max_speed": 4.0,
        "min_steering_angle": -25,
        "max_steering_angle": 25,
        "min_actions": 1,
        "max_actions": 30,
    },
    # Hyperparameters
    "batch_size_options": [32, 64, 128, 256, 512],
    "discount_factor": {"min": 0.0, "max": 1.0},
    "learning_rate": {"min": 1e-8, "max": 1e-3},
    "loss_type_options": ["huber", "mean_squared_error"],
    "entropy": {"min": 0.0, "max": 1.0},
    "best_model_metric_options": ["progress", "reward"],
    # Evaluation
    "number_of_trials": {"min": 1, "max": 20},
    "checkpoint_options": ["best", "last"],
    "penalty": {"min": 0.0, "max": 60.0},
    # Simulation
    "race_type_options": ["TIME_TRIAL", "OBJECT_AVOIDANCE"],
    "direction_options": ["clockwise", "counterclockwise"],
    "object_type_options": ["box_obstacle", "deepracer_box_obstacle", "amazon_box_obstacle"],
    "number_of_obstacles": {"min": 1, "max": 10},
    # Training time
    "training_time_minutes": {"min": 5, "max": 1440, "default": 60},
    # Vehicle Type
    "vehicle_type_options": ["deepracer", "physicar"],
}

# ============ 백그라운드 모니터 설정 ============
MONITOR_INTERVAL_SECONDS = 10  # 훈련 모니터링 간격 (초)

# ============ num_episodes_between_training 계산 ============
def get_num_episodes_between_training(worker_count: int) -> int:
    """
    워커 수(main 포함)에 따른 num_episodes_between_training 값 (PPO 기준)
    worker_count = 1 (main only, sub=0) → 10
    worker_count = 2 (main + 1 sub) → 20
    worker_count = 3 (main + 2 sub) → 30
    ...
    공식: worker_count * 10
    
    참고: SAC의 경우 구버전에서는 sub_count + 1을 사용했으나,
    현재 버전은 PPO만 지원하므로 단순화함.
    """
    return worker_count * 10


def get_num_epochs(worker_count: int) -> int:
    """
    워커 수(main 포함)에 따른 num_epochs 값 (PPO 기준)
    worker_count = 1 (sub=0) → 6
    worker_count = 2 (sub=1) → 5
    worker_count = 3 (sub=2) → 4
    worker_count = 4 (sub=3) → 3
    worker_count = 5 (sub=4) → 3
    worker_count = 6 (sub=5) → 2
    worker_count = 7+ (sub=6+) → 2
    """
    epochs_map = {1: 6, 2: 5, 3: 4, 4: 3, 5: 3, 6: 2, 7: 2}
    return epochs_map.get(worker_count, 2)


# ============ 서브 시뮬레이션 제한 ============
# CPU 계산 공식 (jobs.py와 동일):
#   시스템 예약: 1 CPU
#   Sagemaker: 1 CPU
#   Robomaker: 2 CPU × (1 main + sub_count)
#   훈련 CPU = 1 + (1 + sub_count) * 2
#   최대 sub_count = (total - 4) / 2

CPU_RESERVED_FOR_SYSTEM = 1
CPU_PER_SAGEMAKER = 1
CPU_PER_ROBOMAKER = 2

def get_max_sub_simulation_count(cpu_count: int = None) -> int:
    """CPU 수에 따른 최대 서브 시뮬레이션 수
    
    훈련 시 CPU 사용: 1 (sagemaker) + (1 + sub_count) * 2 (robomaker)
    사용 가능 CPU: total - 시스템 예약(1)
    
    역산: sub_count = (available - sagemaker) / robomaker - 1
                    = (total - 1 - 1) / 2 - 1
                    = (total - 4) / 2
    """
    import os
    cpu_count = cpu_count or os.cpu_count() or 4
    available = cpu_count - CPU_RESERVED_FOR_SYSTEM
    # 훈련에 필요한 최소 CPU: sagemaker(1) + robomaker(2) for main = 3
    if available < (CPU_PER_SAGEMAKER + CPU_PER_ROBOMAKER):
        return 0
    # 역산: (available - sagemaker) / robomaker - 1 (main 제외)
    max_sub = (available - CPU_PER_SAGEMAKER) // CPU_PER_ROBOMAKER - 1
    return max(0, max_sub)

# ============ 경로 설정 ============
from pathlib import Path

# 홈 디렉토리 (심링크로 ~/physicar-cloud/home → ~ 연결됨)
HOME_DIR = Path.home()

# 패키지 경로
PACKAGE_DIR = Path(__file__).parent
STATIC_DIR = PACKAGE_DIR / "static"
PACKAGE_DATA_DIR = PACKAGE_DIR / "data"

# deepracer-for-cloud 경로
DRFC_DIR = HOME_DIR / "deepracer-for-cloud"
DRFC_SYSTEM_ENV = DRFC_DIR / "system.env"
DRFC_RUN_ENV = DRFC_DIR / "run.env"
DRFC_CUSTOM_FILES = DRFC_DIR / "custom_files"
DRFC_DEFAULTS = DRFC_DIR / "defaults"

# 트랙 데이터 (패키지 data/)
TRACKS_DIR = PACKAGE_DATA_DIR / "tracks"
TRACKS_INFO_PATH = TRACKS_DIR / "tracks_info.yml"
TRACKS_NPY_DIR = TRACKS_DIR / "npy"

# 트랙 썸네일 (정적 파일)
TRACKS_THUMBNAIL_DIR = STATIC_DIR / "tracks" / "thumbnail"


# ============ AI 보상함수 생성 프롬프트 ============
REWARD_FUNCTION_SYSTEM_PROMPT = """You are an expert DeepRacer reward function developer.
Generate a Python reward function based on the user's description.

## RULES
1. The function MUST be named `reward_function` and take `params` as the only argument
2. The function MUST return a float value (the reward)
3. The reward should typically be between 1e-3 (0.001) and 1.0
4. NEVER return 0 or negative rewards (use 1e-3 as minimum)
5. Return ONLY the Python code, no explanations before or after
6. Include helpful comments in the code
7. Always use `float(reward)` when returning

## INPUT PARAMETERS (params dict)

### Common Parameters (All Race Types)
| Parameter | Type | Description | Range |
|-----------|------|-------------|-------|
| all_wheels_on_track | bool | All wheels on track? | True/False |
| x, y | float | Agent position (meters) | 0:N |
| heading | float | Agent yaw (degrees) | -180:180 |
| progress | float | Track completion % | 0:100 |
| steps | int | Steps completed | 2:N (starts at 2) |
| speed | float | Speed (m/s) | 0:5.0 |
| steering_angle | float | Steering angle (degrees) | -25:25 |
| track_width | float | Track width (meters) | 0:D |
| track_length | float | Total track length (meters) | 0:Lmax |
| distance_from_center | float | Distance from center | 0:track_width/2 |
| is_left_of_center | bool | Left of center? | True/False |
| is_offtrack | bool | Off track? (episode ends) | True/False |
| is_crashed | bool | Crashed? (episode ends) | True/False |
| is_reversed | bool | Driving backwards? | True/False |
| waypoints | list[(x,y)] | Track center waypoints | First and last are same (circular) |
| closest_waypoints | [int,int] | [prev_idx, next_idx] | [0:Max-1, 0:Max-1] |

### Object Avoidance / Head-to-Bot Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| objects_location | list[(x,y)] | Object positions |
| objects_left_of_center | list[bool] | Objects left of center? |
| objects_speed | list[float] | Object speeds (0 for boxes, >0 for bots) |
| objects_heading | list[float] | Object headings |
| objects_distance | list[float] | Distance from track start |
| objects_distance_from_center | list[float] | Object distance from center |
| closest_objects | [int,int] | [behind_idx, ahead_idx] |

## TIPS
- Episode ends when: is_offtrack=True, is_crashed=True, or progress=100
- steps starts at 2 (not 0 or 1)
- waypoints[0] == waypoints[-1] for circular tracks, so real_len = len(waypoints) - 1
- Each step is theoretically 1/15 second (15 fps)
- To calculate track direction: use math.atan2(dy, dx) between waypoints
- To penalize zig-zag: check if abs(steering_angle) > 15

## EXAMPLE 1: Follow center line
```python
def reward_function(params):
    track_width = params['track_width']
    distance_from_center = params['distance_from_center']
    
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
```

## EXAMPLE 2: Prevent zig-zag with speed reward
```python
def reward_function(params):
    distance_from_center = params['distance_from_center']
    track_width = params['track_width']
    speed = params['speed']
    abs_steering = abs(params['steering_angle'])
    
    # Center reward
    if distance_from_center <= 0.1 * track_width:
        reward = 1.0
    elif distance_from_center <= 0.25 * track_width:
        reward = 0.5
    else:
        reward = 0.1
    
    # Speed bonus
    reward += speed / 4.0
    
    # Steering penalty
    if abs_steering > 15:
        reward *= 0.8
    
    return float(reward)
```

## EXAMPLE 3: Heading alignment with waypoints
```python
import math

def reward_function(params):
    waypoints = params['waypoints']
    closest_waypoints = params['closest_waypoints']
    heading = params['heading']
    
    next_point = waypoints[closest_waypoints[1]]
    prev_point = waypoints[closest_waypoints[0]]
    
    track_direction = math.degrees(math.atan2(
        next_point[1] - prev_point[1],
        next_point[0] - prev_point[0]
    ))
    
    direction_diff = abs(track_direction - heading)
    if direction_diff > 180:
        direction_diff = 360 - direction_diff
    
    reward = max(1.0 - (direction_diff / 50.0), 0.1)
    
    return float(reward)
```

## EXAMPLE 4: Object avoidance (for OBJECT_AVOIDANCE race type)
```python
import math

def reward_function(params):
    all_wheels_on_track = params['all_wheels_on_track']
    distance_from_center = params['distance_from_center']
    track_width = params['track_width']
    objects_location = params['objects_location']
    agent_x = params['x']
    agent_y = params['y']
    _, next_object_index = params['closest_objects']
    objects_left_of_center = params['objects_left_of_center']
    is_left_of_center = params['is_left_of_center']
    
    reward = 1e-3
    
    # Lane reward
    if all_wheels_on_track and (0.5 * track_width - distance_from_center) >= 0.05:
        reward_lane = 1.0
    else:
        reward_lane = 1e-3
    
    # Avoid reward
    reward_avoid = 1.0
    if len(objects_location) > 0:
        next_object_loc = objects_location[next_object_index]
        distance_closest_object = math.sqrt(
            (agent_x - next_object_loc[0])**2 + 
            (agent_y - next_object_loc[1])**2
        )
        
        is_same_lane = objects_left_of_center[next_object_index] == is_left_of_center
        if is_same_lane:
            if 0.5 <= distance_closest_object < 0.8:
                reward_avoid *= 0.5
            elif 0.3 <= distance_closest_object < 0.5:
                reward_avoid *= 0.2
            elif distance_closest_object < 0.3:
                reward_avoid = 1e-3
    
    reward = 1.0 * reward_lane + 4.0 * reward_avoid
    
    return float(reward)
```
"""
