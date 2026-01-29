"""
Reward Function 디버그/검증 모듈
Docker 컨테이너에서 격리된 환경으로 reward function을 실행하여 검증
"""
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Tuple

from physicar.cloud.deepracer.config import DRFC_DIR


class DebugRewardFunctionError(Exception):
    """Reward Function 검증 에러"""
    def __init__(self, message: str, error_line: Optional[int] = None):
        super().__init__(message)
        self.error_line = error_line


# params_logs 경로 (패키지 data 폴더)
PARAMS_LOGS_DIR = Path(__file__).parent / "data" / "params_logs"

# Docker 컨테이너 내에서 실행될 스크립트
RUNNER_SCRIPT = '''
import pickle
import time
try:
    from reward_function import reward_function
except Exception as e:
    raise e

with open("params_logs.pkl", "rb") as f:
    params_logs = pickle.load(f)

start_time = time.time()
for params in params_logs["params_list"]:
    params['waypoints'] = params_logs["waypoints"]
    
    result = reward_function(params)
    if not isinstance(result, (int, float)):
        raise ValueError(f"Reward function must return a number (int or float), got {type(result).__name__}")
    
    # 3초 타임아웃
    if time.time() - start_time > 3:
        break

print("OK")
'''


def get_docker_env_vars() -> dict:
    """DRFC의 system.env에서 Docker 이미지 정보 가져오기"""
    system_env = DRFC_DIR / "system.env"
    env_vars = {
        "DR_SIMAPP_SOURCE": "awsdeepracercommunity/deepracer-simapp",
        "DR_SIMAPP_VERSION": "5.3.3-cpu",
    }
    
    if system_env.exists():
        with open(system_env) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    if key in env_vars:
                        env_vars[key] = value.strip('"').strip("'")
    
    return env_vars


def normalize_race_type(race_type: str) -> str:
    """race_type 정규화"""
    race_type = race_type.lower().strip()
    if race_type in ["tt", "time_trial"]:
        return "TT"
    elif race_type in ["oa", "object_avoidance"]:
        return "OA"
    elif race_type in ["hb", "head_to_bot", "hh", "head_to_head"]:
        return "HB"
    return "TT"  # 기본값


def run_debug_reward_function(
    reward_function_script: str,
    race_type: str = "TT",
    action_space_type: str = "discrete"
) -> Tuple[bool, Optional[str]]:
    """
    Reward function을 Docker 컨테이너에서 검증
    
    Args:
        reward_function_script: reward function 코드
        race_type: TT, OA, HB
        action_space_type: discrete, continuous
    
    Returns:
        (success, error_message)
    
    Raises:
        DebugRewardFunctionError: 검증 실패 시
    """
    # race_type 정규화
    race_type = normalize_race_type(race_type)
    action_space_type = action_space_type.lower().strip()
    if action_space_type not in ["discrete", "continuous"]:
        action_space_type = "discrete"
    
    # params_logs 파일 확인
    params_logs_path = PARAMS_LOGS_DIR / f"{race_type}-{action_space_type}.pkl"
    if not params_logs_path.exists():
        # 폴백: TT-discrete
        params_logs_path = PARAMS_LOGS_DIR / "TT-discrete.pkl"
        if not params_logs_path.exists():
            raise DebugRewardFunctionError(
                f"params_logs file not found: {params_logs_path}",
                error_line=None
            )
    
    # 임시 디렉토리에 파일 생성
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # reward_function.py 저장
        reward_func_path = tmpdir / "reward_function.py"
        reward_func_path.write_text(reward_function_script)
        
        # runner 스크립트 저장
        runner_path = tmpdir / "runner.py"
        runner_path.write_text(RUNNER_SCRIPT)
        
        # Docker 환경 변수
        env_vars = get_docker_env_vars()
        docker_image = f"{env_vars['DR_SIMAPP_SOURCE']}:{env_vars['DR_SIMAPP_VERSION']}"
        
        # Docker 명령어 구성
        cmd = [
            "docker", "run",
            "--rm",
            "--network", "none",
            "-v", f"{runner_path}:/debug_reward/runner.py:ro",
            "-v", f"{reward_func_path}:/debug_reward/reward_function.py:ro",
            "-v", f"{params_logs_path}:/debug_reward/params_logs.pkl:ro",
            "-w", "/debug_reward",
            "--read-only",
            "--cap-drop", "ALL",
            "--security-opt", "no-new-privileges",
            "--entrypoint", "python3",
            docker_image,
            "runner.py"
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30  # 30초 타임아웃
            )
            
            if result.returncode != 0:
                error_str = result.stderr
                
                # 에러 라인 파싱
                error_line = None
                if 'File "/debug_reward/reward_function.py"' in error_str:
                    # 에러 메시지에서 라인 번호 추출
                    error_part = error_str.split('File "/debug_reward/reward_function.py", ')[-1]
                    try:
                        error_line = int(
                            error_part.split("line ", 1)[-1]
                            .split(",")[0]
                            .split("\n")[0]
                            .strip()
                        )
                    except (ValueError, IndexError):
                        pass
                    
                    # 에러 메시지 정리
                    error_str = error_part
                
                raise DebugRewardFunctionError(error_str.strip(), error_line=error_line)
            
            return True, None
            
        except subprocess.TimeoutExpired:
            raise DebugRewardFunctionError(
                "Reward function execution timed out (30s)",
                error_line=None
            )
        except FileNotFoundError:
            raise DebugRewardFunctionError(
                "Docker not found. Please ensure Docker is installed and running.",
                error_line=None
            )
