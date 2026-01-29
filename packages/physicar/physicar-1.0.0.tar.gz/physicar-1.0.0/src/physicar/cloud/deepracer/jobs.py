"""
훈련/평가 작업 관리 모듈
- CPU 모니터링
- 작업 상태 관리
- 타이머 기반 자동 종료
"""
import asyncio
import subprocess
import re
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from .settings_manager import update_env_values
from .config import MONITOR_INTERVAL_SECONDS


class JobType(str, Enum):
    TRAINING = "training"
    EVALUATION = "evaluation"


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class JobInfo:
    """작업 정보"""
    run_id: int
    job_type: JobType
    model_name: str
    status: JobStatus = JobStatus.PENDING
    worker_count: int = 1  # main + sub simulations
    cpu_usage: int = 0  # 예상 CPU 사용량
    started_at: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None  # 예약 종료 시간
    training_minutes: int = 60  # 훈련 시간 (분)
    eval_id: Optional[str] = None  # 평가 timestamp (YYYYMMDDHHmmss)
    
    def get_remaining_minutes(self) -> Optional[int]:
        """남은 시간 (분)"""
        if not self.scheduled_end:
            return None
        remaining = self.scheduled_end - datetime.now()
        return max(0, int(remaining.total_seconds() / 60))


# ============ 상수 ============
DRFC_DIR = Path.home() / "deepracer-for-cloud"
MAX_RUN_ID = 10  # 최대 동시 실행 가능한 RUN_ID 수

# CPU 계산 상수
CPU_PER_ROBOMAKER = 2
CPU_PER_SAGEMAKER = 1


# ============ 전역 상태 ============
_active_jobs: Dict[int, JobInfo] = {}
_stop_timers: Dict[int, asyncio.Task] = {}

# Public alias for external access
active_jobs = _active_jobs


# ============ CPU 모니터링 ============

def get_total_cpu_count() -> int:
    """총 CPU 코어 수"""
    return os.cpu_count() or 4


def get_running_containers() -> List[Dict]:
    """
    실행 중인 deepracer 관련 컨테이너 목록
    Returns: [{"name": str, "type": "robomaker"|"sagemaker"|"evaluation", "run_id": int, "cpu": int}]
    """
    try:
        result = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}"],
            capture_output=True, text=True, timeout=10
        )
        containers = []
        training_run_ids = set()  # 훈련 중인 run_id 수집
        sagemaker_containers = []  # sagemaker는 나중에 run_id 매핑
        
        for name in result.stdout.strip().split("\n"):
            if not name:
                continue
            
            # deepracer-{run_id}-robomaker-{n}
            match = re.match(r"deepracer-(\d+)-robomaker-\d+", name)
            if match:
                run_id = int(match.group(1))
                training_run_ids.add(run_id)
                containers.append({
                    "name": name,
                    "type": "robomaker",
                    "run_id": run_id,
                    "cpu": CPU_PER_ROBOMAKER,
                })
                continue
            
            # deepracer-eval-{run_id}-robomaker-{n}
            match = re.match(r"deepracer-eval-(\d+)-robomaker-\d+", name)
            if match:
                containers.append({
                    "name": name,
                    "type": "evaluation",
                    "run_id": int(match.group(1)),
                    "cpu": CPU_PER_ROBOMAKER,
                })
                continue
            
            # {random}-algo-{n}-{random} (Sagemaker)
            if "-algo-" in name and "deepracer" not in name:
                sagemaker_containers.append(name)
                continue
            
            # deepracer-{run_id}-rl_coach-{n}
            match = re.match(r"deepracer-(\d+)-rl_coach-\d+", name)
            if match:
                containers.append({
                    "name": name,
                    "type": "rl_coach",
                    "run_id": int(match.group(1)),
                    "cpu": 0,  # rl_coach는 CPU 거의 안씀
                })
                continue
        
        # Sagemaker 컨테이너를 훈련 중인 run_id에 매핑
        # (현재 구조상 동시에 하나의 sagemaker만 존재, 여러 훈련이면 공유)
        for name in sagemaker_containers:
            # 훈련 중인 run_id가 있으면 그 중 첫 번째에 매핑, 없으면 -1
            run_id = min(training_run_ids) if training_run_ids else -1
            containers.append({
                "name": name,
                "type": "sagemaker",
                "run_id": run_id,
                "cpu": CPU_PER_SAGEMAKER,
            })
        
        return containers
    except Exception as e:
        print(f"Error getting containers: {e}")
        return []


def get_current_cpu_usage() -> int:
    """현재 deepracer 관련 컨테이너들의 CPU 사용량 (코어 수)"""
    containers = get_running_containers()
    return sum(c["cpu"] for c in containers)


def get_cpu_status() -> Dict:
    """CPU 상태 반환"""
    total = get_total_cpu_count()
    used = get_current_cpu_usage()
    reserved = 1  # 시스템용 예약 코어
    available = max(0, total - used - reserved)
    
    return {
        "total": total,
        "used": used,
        "available": available,
        "reserved_for_system": reserved,
        "containers": get_running_containers(),
    }


def calculate_training_cpu(worker_count: int) -> int:
    """
    훈련에 필요한 CPU 계산
    worker_count = 1 + len(sub_simulations)
    CPU = worker_count * 2 (robomaker) + 1 (sagemaker)
    """
    return worker_count * CPU_PER_ROBOMAKER + CPU_PER_SAGEMAKER


def calculate_evaluation_cpu() -> int:
    """평가에 필요한 CPU"""
    return CPU_PER_ROBOMAKER


def can_start_job(job_type: JobType, worker_count: int = 1) -> Tuple[bool, str, int]:
    """
    작업 시작 가능 여부 확인
    Returns: (가능여부, 메시지, 필요 CPU)
    """
    if job_type == JobType.TRAINING:
        required_cpu = calculate_training_cpu(worker_count)
    else:
        required_cpu = calculate_evaluation_cpu()
    
    status = get_cpu_status()
    
    if required_cpu > status["available"]:
        return (
            False,
            f"Not enough CPU. Required: {required_cpu}, Available: {status['available']}",
            required_cpu,
        )
    
    return (True, "OK", required_cpu)


# ============ RUN_ID 관리 ============

def get_container_rollout_idx(container_name: str) -> Optional[int]:
    """
    컨테이너의 ROLLOUT_IDX 조회 (로그에서 파싱)
    
    ⚠️ 컨테이너 이름의 번호(robomaker-1, robomaker-2)는 ROLLOUT_IDX와 무관함!
    docker compose --scale이 번호를 임의 할당하므로,
    실제 워커 인덱스는 컨테이너 로그에서 ROLLOUT_IDX를 확인해야 함.
    
    Returns:
        0 = 메인 워커
        1 = 서브 워커 1
        2 = 서브 워커 2
        None = 확인 불가
    """
    try:
        result = subprocess.run(
            ["docker", "logs", container_name],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            return None
        
        # 로그에서 "ROLLOUT_IDX=0" 또는 "+ ROLLOUT_IDX=0" 패턴 찾기
        combined = result.stdout + result.stderr
        match = re.search(r'ROLLOUT_IDX=(\d+)', combined)
        if match:
            return int(match.group(1))
        return None
    except Exception:
        return None


def get_robomaker_containers_with_rollout(run_id: int) -> List[Dict]:
    """
    RUN_ID의 robomaker 컨테이너 목록과 ROLLOUT_IDX 반환
    
    Returns: [{"name": str, "rollout_idx": int, "ports": str}, ...]
             rollout_idx 기준 정렬됨 (0=메인 먼저)
    """
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", f"name=deepracer-{run_id}-robomaker",
             "--format", "{{.Names}}\t{{.Ports}}"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0 or not result.stdout.strip():
            return []
        
        containers = []
        for line in result.stdout.strip().split('\n'):
            parts = line.split('\t')
            if len(parts) < 2:
                continue
            
            container_name = parts[0]
            ports_str = parts[1]
            rollout_idx = get_container_rollout_idx(container_name)
            
            containers.append({
                "name": container_name,
                "rollout_idx": rollout_idx if rollout_idx is not None else 999,
                "ports": ports_str,
            })
        
        # rollout_idx 기준 정렬 (0=메인 먼저)
        containers.sort(key=lambda x: x["rollout_idx"])
        return containers
    except Exception:
        return []


def get_model_name_by_run_id(run_id: int) -> Optional[str]:
    """
    RUN_ID로 훈련/평가 중인 모델명 조회
    Docker 컨테이너의 MODEL_S3_PREFIX 환경변수에서 추출
    
    훈련: deepracer-{run_id}-rl_coach-1
    평가: deepracer-eval-{run_id}-robomaker-1
    """
    # 1. 먼저 _active_jobs에서 찾기 (가장 정확)
    if run_id in _active_jobs:
        return _active_jobs[run_id].model_name
    
    # 2. 훈련 컨테이너 확인
    try:
        container_name = f"deepracer-{run_id}-rl_coach-1"
        result = subprocess.run(
            ["docker", "inspect", container_name, 
             "--format", "{{range .Config.Env}}{{println .}}{{end}}"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            for line in result.stdout.strip().split("\n"):
                if line.startswith("MODEL_S3_PREFIX="):
                    prefix = line.split("=", 1)[1]
                    if prefix.startswith("models/"):
                        return prefix[7:]
                    return prefix
    except Exception:
        pass
    
    # 3. 평가 컨테이너 확인
    try:
        container_name = f"deepracer-eval-{run_id}-robomaker-1"
        result = subprocess.run(
            ["docker", "inspect", container_name, 
             "--format", "{{range .Config.Env}}{{println .}}{{end}}"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            for line in result.stdout.strip().split("\n"):
                if line.startswith("MODEL_S3_PREFIX="):
                    prefix = line.split("=", 1)[1]
                    if prefix.startswith("models/"):
                        return prefix[7:]
                    return prefix
    except Exception:
        pass
    
    return None


def get_run_id_by_model_name(model_name: str) -> Optional[int]:
    """
    모델명으로 RUN_ID 조회
    """
    for run_id in get_used_run_ids():
        if get_model_name_by_run_id(run_id) == model_name:
            return run_id
    return None


def get_all_running_models() -> Dict[int, str]:
    """
    실행 중인 모든 RUN_ID와 모델명 매핑
    Returns: {run_id: model_name, ...}
    """
    result = {}
    for run_id in get_used_run_ids():
        model_name = get_model_name_by_run_id(run_id)
        if model_name:
            result[run_id] = model_name
    return result


def get_used_run_ids(include_exited: bool = True) -> List[int]:
    """
    사용 중인 RUN_ID 목록
    
    Args:
        include_exited: True면 종료된 컨테이너도 포함 (RUN_ID 충돌 방지용)
    """
    try:
        # include_exited가 True면 docker ps -a, 아니면 docker ps
        cmd = ["docker", "ps", "-a" if include_exited else "", "--format", "{{.Names}}"]
        cmd = [c for c in cmd if c]  # 빈 문자열 제거
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        run_ids = set()
        for name in result.stdout.strip().split("\n"):
            if not name:
                continue
            # deepracer-{run_id}-*
            match = re.match(r"deepracer-(\d+)-", name)
            if match:
                run_ids.add(int(match.group(1)))
            # deepracer-eval-{run_id}-*
            match = re.match(r"deepracer-eval-(\d+)-", name)
            if match:
                run_ids.add(int(match.group(1)))
        return sorted(run_ids)
    except Exception:
        return []


def get_available_run_id() -> Optional[int]:
    """사용 가능한 RUN_ID 반환 (종료된 컨테이너 포함하여 충돌 방지)"""
    used = set(get_used_run_ids(include_exited=True))
    for i in range(MAX_RUN_ID):
        if i not in used:
            return i
    return None


def get_training_status(run_id: int) -> Dict:
    """
    특정 RUN_ID의 훈련 상태 확인 (Docker 기반)
    
    Returns:
        {
            "status": "running" | "failed" | "stopped" | "not_found",
            "robomaker_running": int,  # 실행 중인 robomaker 수
            "robomaker_exited": int,   # 종료된 robomaker 수
            "sagemaker_running": bool, # sagemaker/rl_coach 실행 여부
            "containers": [...],       # 관련 컨테이너 정보
            "started_at": str | None,  # 훈련 시작 시간 (ISO 형식)
            "message": str
        }
    """
    try:
        # docker ps -a로 모든 컨테이너 (종료된 것 포함) 확인
        # --format에 시작 시간 추가: {{.Names}}\t{{.Status}}\t{{.CreatedAt}}
        result = subprocess.run(
            ["docker", "ps", "-a", "--filter", f"name=deepracer-{run_id}-", 
             "--format", "{{.Names}}\t{{.Status}}\t{{.CreatedAt}}"],
            capture_output=True, text=True, timeout=10
        )
        
        containers = []
        robomaker_running = 0
        robomaker_exited = 0
        sagemaker_running = False
        earliest_start = None
        
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            parts = line.split("\t")
            if len(parts) < 2:
                continue
            name = parts[0]
            status = parts[1]
            created_at = parts[2] if len(parts) > 2 else None
            
            is_running = status.startswith("Up")
            container_info = {"name": name, "status": status, "running": is_running}
            if created_at:
                container_info["created_at"] = created_at
                # Docker CreatedAt 형식: "2025-12-18 10:30:00 +0000 UTC"
                # UTC로 파싱하여 ISO 형식으로 변환
                try:
                    from datetime import datetime, timezone
                    # "2025-12-18 10:30:00" 부분만 파싱 후 UTC로 설정
                    dt_str = created_at.split(" +")[0] if " +" in created_at else created_at[:19]
                    dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                    if earliest_start is None or dt < earliest_start:
                        earliest_start = dt
                except Exception:
                    pass
            containers.append(container_info)
            
            if "robomaker" in name:
                if is_running:
                    robomaker_running += 1
                else:
                    robomaker_exited += 1
            elif "rl_coach" in name or "algo" in name:
                if is_running:
                    sagemaker_running = True
        
        if not containers:
            return {
                "status": "not_found",
                "robomaker_running": 0,
                "robomaker_exited": 0,
                "sagemaker_running": False,
                "containers": [],
                "started_at": None,
                "message": f"No containers found for run_id={run_id}"
            }
        
        # 상태 판단 (단순화: 종료된 컨테이너가 하나라도 있으면 비정상)
        total_running = robomaker_running + (1 if sagemaker_running else 0)
        total_exited = robomaker_exited + (1 if not sagemaker_running and containers else 0)
        
        if total_exited > 0 and total_running > 0:
            # 일부만 죽음 → 비정상
            status = "failed"
            message = f"Training failed: {total_exited} container(s) exited, {total_running} still running"
        elif total_exited > 0 and total_running == 0:
            # 모두 죽음 → 종료됨
            status = "stopped"
            message = f"Training stopped: all containers exited"
        elif total_running > 0 and total_exited == 0:
            # 모두 살아있음 → 정상
            status = "running"
            message = f"Training running: {total_running} container(s)"
        else:
            status = "unknown"
            message = f"Unknown state: running={total_running}, exited={total_exited}"
        
        return {
            "status": status,
            "robomaker_running": robomaker_running,
            "robomaker_exited": robomaker_exited,
            "sagemaker_running": sagemaker_running,
            "containers": containers,
            "started_at": earliest_start.isoformat() if earliest_start else None,
            "message": message
        }
    except Exception as e:
        return {
            "status": "error",
            "robomaker_running": 0,
            "robomaker_exited": 0,
            "sagemaker_running": False,
            "containers": [],
            "started_at": None,
            "message": str(e)
        }


def get_all_training_status() -> Dict[int, Dict]:
    """모든 RUN_ID의 훈련 상태 확인"""
    statuses = {}
    for run_id in range(MAX_RUN_ID):
        status = get_training_status(run_id)
        if status["status"] != "not_found":
            statuses[run_id] = status
    return statuses


# ============ 작업 실행 ============

async def _run_shell_command(cmd: str, env: Dict[str, str] = None) -> Tuple[int, str, str]:
    """쉘 명령 실행 (비동기) - bash 사용"""
    full_env = os.environ.copy()
    if env:
        full_env.update(env)
    
    # bash로 실행 (source 명령 사용을 위해)
    process = await asyncio.create_subprocess_exec(
        "/bin/bash", "-c", cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=full_env,
        cwd=str(DRFC_DIR),
    )
    
    stdout, stderr = await process.communicate()
    return process.returncode, stdout.decode(), stderr.decode()


async def _stop_timer(run_id: int, minutes: int):
    """지정된 시간 후 훈련 중지"""
    try:
        await asyncio.sleep(minutes * 60)
        print(f"[Timer] Auto-stopping training run_id={run_id} after {minutes} minutes")
        await stop_training(run_id)
    except asyncio.CancelledError:
        print(f"[Timer] Timer cancelled for run_id={run_id}")





async def start_training(
    model_name: str,
    worker_count: int = 1,
    training_minutes: int = 60,
    run_id: Optional[int] = None,
    pretrained_model_name: Optional[str] = None,
    pretrained_checkpoint: str = "last",
) -> Tuple[bool, str, Optional[JobInfo]]:
    """
    훈련 시작
    
    Args:
        model_name: 모델 이름
        worker_count: 워커 수 (1 + sub_simulations)
        training_minutes: 훈련 시간 (분)
        run_id: RUN_ID (없으면 자동 할당)
        pretrained_model_name: 사전 훈련된 모델 이름 (clone 시)
        pretrained_checkpoint: 사전 훈련 체크포인트 (best/last)
    
    Returns:
        (성공여부, 메시지, JobInfo)
    """
    # CPU 체크
    can_start, message, required_cpu = can_start_job(JobType.TRAINING, worker_count)
    if not can_start:
        return (False, message, None)
    
    # RUN_ID 할당
    if run_id is None:
        run_id = get_available_run_id()
        if run_id is None:
            return (False, "No available RUN_ID", None)
    
    # 이미 실행 중인지 확인 (Docker 상태 기준 - 메모리 상태보다 정확)
    used_run_ids = get_used_run_ids(include_exited=False)  # 실행 중인 컨테이너만
    if run_id in used_run_ids:
        return (False, f"RUN_ID {run_id} is already in use", None)
    
    # _active_jobs에서 stale 항목 정리 (Docker에서 실행 중이 아닌 RUN_ID 제거)
    stale_run_ids = [rid for rid in _active_jobs if rid not in used_run_ids]
    for rid in stale_run_ids:
        del _active_jobs[rid]
    
    # run.env 업데이트 (DR_RUN_ID, DR_LOCAL_S3_MODEL_PREFIX, DR_LOCAL_S3_PRETRAINED)
    # DR_WORKERS는 UI에서 서브 시뮬레이션 수 변경 시 이미 업데이트됨
    env_updates = {
        "DR_RUN_ID": str(run_id),
        "DR_LOCAL_S3_MODEL_PREFIX": f"models/{model_name}",
    }
    
    # Clone (pretrained) vs Create
    if pretrained_model_name:
        env_updates["DR_LOCAL_S3_PRETRAINED"] = "True"
        env_updates["DR_LOCAL_S3_PRETRAINED_PREFIX"] = f"models/{pretrained_model_name}"
        env_updates["DR_LOCAL_S3_PRETRAINED_CHECKPOINT"] = pretrained_checkpoint
    else:
        env_updates["DR_LOCAL_S3_PRETRAINED"] = "False"
    
    update_env_values(DRFC_DIR / "run.env", env_updates)
    
    # JobInfo 생성
    job = JobInfo(
        run_id=run_id,
        job_type=JobType.TRAINING,
        model_name=model_name,
        status=JobStatus.RUNNING,
        worker_count=worker_count,
        cpu_usage=required_cpu,
        started_at=datetime.now(),
        scheduled_end=datetime.now() + timedelta(minutes=training_minutes),
        training_minutes=training_minutes,
    )
    
    # 훈련 시작
    cmd = f"source {DRFC_DIR}/bin/activate.sh && dr-start-training -q -w"
    returncode, stdout, stderr = await _run_shell_command(cmd)
    
    if returncode != 0:
        return (False, f"Failed to start training: {stderr}", None)
    
    # 작업 등록
    _active_jobs[run_id] = job
    
    return (True, f"Training started (run_id={run_id})", job)


async def stop_training(run_id: int) -> Tuple[bool, str]:
    """훈련 중지 - 컨테이너 이름에 -{run_id}- 포함된 것 모두 정리"""
    import subprocess
    
    stopped_containers = []
    model_name = None
    
    # 작업에서 모델명 가져오기 (체크포인트 인덱스 초기화용)
    if run_id in _active_jobs:
        model_name = _active_jobs[run_id].model_name
    
    # 컨테이너 종료 전 최종 작업
    if model_name:
        # 1. physical-car-model 최종 동기화
        try:
            await _sync_best_physical_car_model(model_name)
        except Exception as e:
            print(f"[stop_training] Final physical-car-model sync failed: {e}")
        
        # 2. 컨테이너 로그 S3 저장 (컨테이너 종료 전!)
        try:
            _sync_container_logs(model_name, run_id)
        except Exception as e:
            print(f"[stop_training] Container logs sync failed: {e}")
    
    try:
        # 모든 컨테이너 목록
        result = subprocess.run(
            ["docker", "ps", "-a", "--format", "{{.Names}}"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            for container in result.stdout.strip().split('\n'):
                # 컨테이너 이름에 -{run_id}- 가 포함되면 정리
                if f"-{run_id}-" in container:
                    subprocess.run(["docker", "stop", container], capture_output=True, timeout=30)
                    subprocess.run(["docker", "rm", "-f", container], capture_output=True, timeout=10)
                    stopped_containers.append(container)
    except Exception as e:
        pass
    
    # 작업 상태 업데이트
    if run_id in _active_jobs:
        _active_jobs[run_id].status = JobStatus.STOPPED
        del _active_jobs[run_id]
    
    # 체크포인트 인덱스 초기화 (다음 훈련 시 처음부터 다시 추적)
    if model_name and model_name in _last_checkpoint_indices:
        del _last_checkpoint_indices[model_name]
    
    return (True, f"Training stopped (run_id={run_id}, containers: {len(stopped_containers)})")


async def start_evaluation(
    model_name: str,
    run_id: Optional[int] = None,
    track_name: str = "",
    direction: str = "counterclockwise",
    race_type: str = "TIME_TRIAL",
    object_avoidance: Optional[dict] = None,
    number_of_trials: int = 5,
    checkpoint: str = "last",
    offtrack_penalty: float = 5.0,
    collision_penalty: float = 5.0,
) -> Tuple[bool, str, Optional[JobInfo]]:
    """평가 시작
    
    Args:
        model_name: 모델 이름
        run_id: RUN_ID (없으면 자동 할당)
        track_name: 트랙 ID (빈 값이면 run.env의 기존 값 유지)
        direction: 방향 (clockwise/counterclockwise)
        race_type: 레이스 타입 (TIME_TRIAL/OBJECT_AVOIDANCE)
        object_avoidance: Object Avoidance 설정 (race_type이 OBJECT_AVOIDANCE인 경우)
        number_of_trials: 평가 라운드 수
        checkpoint: 체크포인트 (best/last)
        offtrack_penalty: 오프트랙 패널티 (초)
        collision_penalty: 충돌 패널티 (초)
    """
    # CPU 체크
    can_start, message, required_cpu = can_start_job(JobType.EVALUATION)
    if not can_start:
        return (False, message, None)
    
    # RUN_ID 할당
    if run_id is None:
        run_id = get_available_run_id()
        if run_id is None:
            return (False, "No available RUN_ID", None)
    
    # eval_id 생성 (DRFC prepare-config.py와 동일한 포맷)
    eval_id = datetime.now().strftime('%Y%m%d%H%M%S')
    
    # run.env 업데이트 (evaluation 옵션 포함)
    env_updates = {
        "DR_RUN_ID": str(run_id),
        "DR_LOCAL_S3_MODEL_PREFIX": f"models/{model_name}",
        "DR_EVAL_NUMBER_OF_TRIALS": str(number_of_trials),
        "DR_EVAL_CHECKPOINT": checkpoint,
        "DR_EVAL_OFF_TRACK_PENALTY": str(offtrack_penalty),
        "DR_EVAL_COLLISION_PENALTY": str(collision_penalty),
        # 시뮬레이션 설정
        "DR_RACE_TYPE": race_type,
        "DR_TRAIN_REVERSE_DIRECTION": str(direction == "clockwise"),
        # 평가 params 파일 경로 (evaluation/{eval_id}/ 폴더에 저장)
        "DR_LOCAL_S3_EVAL_PARAMS_FILE": f"evaluation/{eval_id}/evaluation_params.yaml",
    }
    
    # 트랙이 지정되면 DR_WORLD_NAME도 업데이트 (track_id + direction -> npy 이름)
    if track_name:
        from physicar.cloud.deepracer.settings_manager import encode_world_name
        env_updates["DR_WORLD_NAME"] = encode_world_name(track_name, direction)
    
    # Object Avoidance 설정 (drfc_writer.py와 동일한 패턴)
    if race_type == "OBJECT_AVOIDANCE" and object_avoidance:
        env_updates["DR_OA_NUMBER_OF_OBSTACLES"] = str(object_avoidance.get("number_of_objects", 3))
        env_updates["DR_OA_OBSTACLE_TYPE"] = object_avoidance.get("object_type", "box_obstacle")
        randomize = object_avoidance.get("randomize_locations", True)
        env_updates["DR_OA_RANDOMIZE_OBSTACLE_LOCATIONS"] = str(randomize)
        
        # Bot car 체크 (drfc_writer.py 참조)
        is_bot_car = "deepracer_car" in object_avoidance.get("object_type", "")
        env_updates["DR_OA_IS_OBSTACLE_BOT_CAR"] = str(is_bot_car)
        
        # 고정 위치인 경우 - drfc_writer.py와 동일한 포맷
        # DRFC 형식: "progress,lane_value;progress,lane_value;..." (세미콜론 구분, 따옴표 감싸기)
        # lane: "inside" -> 1, "outside" -> -1
        if not randomize:
            locations = object_avoidance.get("object_locations", [])
            if locations:
                pos_parts = []
                for loc in locations:
                    progress = loc.get("progress", 0)
                    lane_str = loc.get("lane", "inside")
                    # 스키마의 to_drfc_format()과 동일: progress/100, lane_value
                    lane_value = 1 if lane_str == "inside" else -1
                    pos_parts.append(f"{progress / 100},{lane_value}")
                if pos_parts:
                    positions = ";".join(pos_parts)
                    env_updates["DR_OA_OBJECT_POSITIONS"] = f'"{positions}"'
                else:
                    env_updates["DR_OA_OBJECT_POSITIONS"] = ""
            else:
                env_updates["DR_OA_OBJECT_POSITIONS"] = ""
        else:
            # Randomize true면 OBJECT_POSITIONS 비우기
            env_updates["DR_OA_OBJECT_POSITIONS"] = ""
    
    update_env_values(DRFC_DIR / "run.env", env_updates)
    
    # JobInfo 생성
    job = JobInfo(
        run_id=run_id,
        job_type=JobType.EVALUATION,
        model_name=model_name,
        status=JobStatus.RUNNING,
        worker_count=1,
        cpu_usage=required_cpu,
        started_at=datetime.now(),
        eval_id=eval_id,
    )
    
    # 평가 시작
    cmd = f"source {DRFC_DIR}/bin/activate.sh && dr-start-evaluation -q"
    returncode, stdout, stderr = await _run_shell_command(cmd)
    
    if returncode != 0:
        return (False, f"Failed to start evaluation: {stderr}", None)
    
    # 작업 등록
    _active_jobs[run_id] = job
    
    return (True, f"Evaluation started (run_id={run_id}, eval_id={eval_id})", job)


async def stop_evaluation(run_id: int) -> Tuple[bool, str]:
    """평가 중지 - 컨테이너 이름에 deepracer-eval-{run_id}- 포함된 것 모두 정리"""
    import subprocess
    
    stopped_containers = []
    model_name = None
    eval_id = None
    
    # 작업에서 정보 가져오기
    if run_id in _active_jobs:
        job = _active_jobs[run_id]
        model_name = job.model_name
        eval_id = job.eval_id
    
    # 컨테이너 로그 저장 (컨테이너 종료 전!)
    if model_name and eval_id:
        try:
            _sync_eval_container_logs(model_name, eval_id, run_id)
        except Exception as e:
            print(f"[stop_evaluation] Container logs sync failed: {e}")
        
        # 평가 비디오 H.264 변환
        try:
            _convert_eval_video_to_h264(model_name, eval_id)
        except Exception as e:
            print(f"[stop_evaluation] Video conversion failed: {e}")
    
    # 컨테이너 직접 정리: deepracer-eval-{run_id}-* 패턴
    try:
        result = subprocess.run(
            ["docker", "ps", "-a", "--format", "{{.Names}}"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            for container in result.stdout.strip().split('\n'):
                # 평가 컨테이너 패턴: deepracer-eval-{run_id}-*
                if f"deepracer-eval-{run_id}-" in container:
                    subprocess.run(["docker", "stop", container], capture_output=True, timeout=30)
                    subprocess.run(["docker", "rm", "-f", container], capture_output=True, timeout=10)
                    stopped_containers.append(container)
    except Exception as e:
        print(f"[stop_evaluation] Container cleanup error: {e}")
    
    # 작업 상태 업데이트
    if run_id in _active_jobs:
        _active_jobs[run_id].status = JobStatus.STOPPED
        del _active_jobs[run_id]
    
    return (True, f"Evaluation stopped (run_id={run_id}, containers: {len(stopped_containers)})")


# ============ 작업 조회 ============

def get_active_jobs() -> List[JobInfo]:
    """활성 작업 목록"""
    return list(_active_jobs.values())


def get_job(run_id: int) -> Optional[JobInfo]:
    """특정 작업 조회"""
    return _active_jobs.get(run_id)


def get_jobs_summary() -> Dict:
    """작업 요약"""
    jobs = get_active_jobs()
    cpu_status = get_cpu_status()
    
    return {
        "jobs": [
            {
                "run_id": j.run_id,
                "job_type": j.job_type.value,
                "model_name": j.model_name,
                "status": j.status.value,
                "worker_count": j.worker_count,
                "cpu_usage": j.cpu_usage,
                "started_at": j.started_at.isoformat() if j.started_at else None,
                "remaining_minutes": j.get_remaining_minutes(),
            }
            for j in jobs
        ],
        "cpu": cpu_status,
    }


async def stop_all_jobs() -> List[Dict]:
    """모든 활성 작업 중지"""
    results = []
    active = get_active_jobs()
    
    for job in active:
        try:
            if job.job_type == JobType.TRAINING:
                success, message = await stop_training(job.run_id)
            else:
                success, message = await stop_evaluation(job.run_id)
            
            results.append({
                "run_id": job.run_id,
                "job_type": job.job_type.value,
                "model_name": job.model_name,
                "success": success,
                "message": message,
            })
        except Exception as e:
            results.append({
                "run_id": job.run_id,
                "job_type": job.job_type.value,
                "model_name": job.model_name,
                "success": False,
                "message": str(e),
            })
    
    return results


# ============ 고아 컨테이너 정리 ============

# 정리 간격 (초)
CLEANUP_INTERVAL_SECONDS = 60  # 1분


def _get_algo_run_id(container_id: str) -> Optional[int]:
    """algo 컨테이너의 환경변수에서 RUN_ID 추출"""
    try:
        result = subprocess.run(
            ["docker", "inspect", container_id, "--format", "{{range .Config.Env}}{{println .}}{{end}}"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                if line.startswith('RUN_ID='):
                    return int(line.split('=')[1])
    except Exception:
        pass
    return None


def _get_all_deepracer_containers() -> List[Dict]:
    """
    모든 DeepRacer 관련 컨테이너 조회 (Up + Exited)
    
    Returns: [{"id": str, "name": str, "status": str, "running": bool, "run_id": int|None, "type": str}]
    """
    containers = []
    try:
        # 모든 컨테이너 조회 (Up + Exited)
        result = subprocess.run(
            ["docker", "ps", "-a", "--format", "{{.ID}}\t{{.Names}}\t{{.Status}}"],
            capture_output=True, text=True, timeout=10
        )
        
        if result.returncode != 0 or not result.stdout.strip():
            return []
        
        for line in result.stdout.strip().split('\n'):
            if not line or '\t' not in line:
                continue
            
            parts = line.split('\t')
            if len(parts) < 3:
                continue
            
            container_id, name, status = parts[0], parts[1], parts[2]
            
            # s3-minio 제외
            if 's3-minio' in name or 'minio' in name.lower():
                continue
            
            is_running = status.startswith("Up")
            run_id = None
            container_type = None
            
            # deepracer-{run_id}-robomaker-*
            match = re.match(r'deepracer-(\d+)-robomaker-', name)
            if match:
                run_id = int(match.group(1))
                container_type = "robomaker"
            
            # deepracer-eval-{run_id}-robomaker-*
            if not container_type:
                match = re.match(r'deepracer-eval-(\d+)-robomaker-', name)
                if match:
                    run_id = int(match.group(1))
                    container_type = "eval_robomaker"
            
            # deepracer-eval-{run_id}-rl_coach-*
            if not container_type:
                match = re.match(r'deepracer-eval-(\d+)-rl_coach-', name)
                if match:
                    run_id = int(match.group(1))
                    container_type = "eval_rl_coach"
            
            # deepracer-{run_id}-rl_coach-*
            if not container_type:
                match = re.match(r'deepracer-(\d+)-rl_coach-', name)
                if match:
                    run_id = int(match.group(1))
                    container_type = "rl_coach"
            
            # {random}-algo-{n}-{random}
            if not container_type and '-algo-' in name and 'deepracer' not in name:
                container_type = "algo"
                # algo는 환경변수에서 RUN_ID 추출
                run_id = _get_algo_run_id(container_id)
            
            # DeepRacer 관련 컨테이너만 추가
            if container_type:
                containers.append({
                    "id": container_id,
                    "name": name,
                    "status": status,
                    "running": is_running,
                    "run_id": run_id,
                    "type": container_type,
                })
        
        return containers
        
    except Exception as e:
        print(f"[Cleanup] Error getting containers: {e}")
        return []


def _group_containers_by_run_id(containers: List[Dict]) -> Dict[int, Dict[str, List[Dict]]]:
    """
    컨테이너를 run_id별로 그룹핑
    
    Returns: {run_id: {"robomaker": [...], "rl_coach": [...], "algo": [...], "eval_robomaker": [...], "eval_rl_coach": [...]}}
    """
    groups = {}
    
    for c in containers:
        run_id = c.get("run_id")
        if run_id is None:
            continue
        
        if run_id not in groups:
            groups[run_id] = {"robomaker": [], "rl_coach": [], "algo": [], "eval_robomaker": [], "eval_rl_coach": []}
        
        c_type = c.get("type", "")
        if c_type in groups[run_id]:
            groups[run_id][c_type].append(c)
    
    return groups


def _is_orphaned_group(group: Dict[str, List[Dict]]) -> Tuple[bool, str]:
    """
    run_id 그룹이 좀비/고아 상태인지 판별
    
    좀비 조건:
    1. robomaker가 있는데 일부가 Exited → 훈련 실패
    2. robomaker가 없는데 algo만 Up → 고아 algo
    3. 모든 컨테이너가 Exited → 종료됨, 정리 대상
    
    Returns: (is_orphaned, reason)
    """
    robomakers = group.get("robomaker", [])
    rl_coaches = group.get("rl_coach", [])
    algos = group.get("algo", [])
    eval_robomakers = group.get("eval_robomaker", [])
    eval_rl_coaches = group.get("eval_rl_coach", [])
    
    # 훈련 관련 컨테이너 체크
    if robomakers:
        running = [c for c in robomakers if c["running"]]
        exited = [c for c in robomakers if not c["running"]]
        
        # robomaker 일부가 죽음 → 비정상
        if exited and running:
            return (True, f"partial_failure: {len(exited)}/{len(robomakers)} robomaker exited")
        
        # robomaker 전체가 죽음 → 종료됨
        if exited and not running:
            return (True, f"all_exited: all {len(robomakers)} robomaker exited")
    
    # robomaker 없는데 algo만 살아있음 → 고아
    if not robomakers and not eval_robomakers:
        running_algos = [c for c in algos if c["running"]]
        if running_algos:
            return (True, f"orphan_algo: {len(running_algos)} algo without robomaker")
        
        # rl_coach만 남음
        running_coaches = [c for c in rl_coaches if c["running"]]
        if running_coaches:
            return (True, f"orphan_rl_coach: {len(running_coaches)} rl_coach without robomaker")
    
    # 평가 관련 컨테이너 체크
    if eval_robomakers:
        running = [c for c in eval_robomakers if c["running"]]
        exited = [c for c in eval_robomakers if not c["running"]]
        
        # 평가 robomaker가 죽음
        if exited and not running:
            return (True, f"eval_exited: all {len(eval_robomakers)} eval robomaker exited")
    
    # 평가 rl_coach만 남아있고 (Exited), robomaker는 없거나 전부 Exited
    # eval_rl_coach는 평가 시작 후 바로 종료되므로, 이것만 남아있으면 정리 대상
    if eval_rl_coaches and not eval_robomakers:
        return (True, f"orphan_eval_rl_coach: {len(eval_rl_coaches)} eval_rl_coach without robomaker")
    
    # 모든 컨테이너가 Exited인 경우도 정리 대상
    all_containers = robomakers + rl_coaches + algos + eval_robomakers + eval_rl_coaches
    if all_containers:
        all_exited = all(not c["running"] for c in all_containers)
        if all_exited:
            return (True, f"all_stopped: {len(all_containers)} containers all exited")
    
    return (False, "healthy")


async def cleanup_orphaned_containers() -> int:
    """
    고아/좀비 컨테이너 정리
    
    로직:
    1. 모든 DeepRacer 컨테이너 조회 및 RUN_ID별 그룹핑
    2. 각 그룹이 orphan 상태인지 판별 (_is_orphaned_group 사용)
    3. orphan 그룹의 모든 컨테이너 정리
    
    Returns: 정리된 컨테이너 수
    """
    try:
        # 1. 모든 DeepRacer 관련 컨테이너 조회
        all_containers = _get_all_deepracer_containers()
        
        if not all_containers:
            return 0
        
        # 2. RUN_ID별로 그룹핑
        groups = _group_containers_by_run_id(all_containers)
        
        # 3. 정리 대상 RUN_ID 식별 - orphan 상태인 경우
        cleanup_run_ids = set()
        for run_id, group in groups.items():
            is_orphan, reason = _is_orphaned_group(group)
            if is_orphan:
                cleanup_run_ids.add(run_id)
                print(f"[Cleanup] run_id={run_id}: {reason}, marking for cleanup")
        
        if not cleanup_run_ids:
            return 0
        
        # 4. 로그 저장 (삭제 전) + 평가 비디오 변환
        for run_id in cleanup_run_ids:
            model_name = get_model_name_by_run_id(run_id)
            group = groups.get(run_id, {})
            
            if model_name:
                # 평가 컨테이너 여부 확인
                is_eval = bool(group.get("eval_robomaker", []))
                
                if is_eval:
                    # 평가 로그 저장
                    job_info = _active_jobs.get(run_id)
                    eval_id = job_info.eval_id if job_info else None
                    if eval_id:
                        try:
                            _sync_eval_container_logs(model_name, eval_id, run_id)
                        except Exception as e:
                            print(f"[Cleanup] Failed to save eval logs for run_id={run_id}: {e}")
                        
                        # 평가 비디오 H.264 변환
                        try:
                            _convert_eval_video_to_h264(model_name, eval_id)
                        except Exception as e:
                            print(f"[Cleanup] Failed to convert video for run_id={run_id}: {e}")
                else:
                    # 훈련 로그 저장
                    try:
                        _sync_container_logs(model_name, run_id)
                    except Exception as e:
                        print(f"[Cleanup] Failed to save logs for run_id={run_id}: {e}")
        
        # 5. 해당 RUN_ID의 모든 컨테이너 정리
        cleaned_count = 0
        for c in all_containers:
            if c["run_id"] in cleanup_run_ids:
                try:
                    subprocess.run(
                        ["docker", "rm", "-f", c["id"]],
                        capture_output=True, timeout=10
                    )
                    cleaned_count += 1
                    status_str = "running" if c["running"] else "exited"
                    print(f"[Cleanup] Removed {status_str} container: {c['name']} (run_id={c['run_id']})")
                except Exception as e:
                    print(f"[Cleanup] Failed to remove {c['name']}: {e}")
        
        # 6. _active_jobs에서도 제거
        for run_id in cleanup_run_ids:
            if run_id in _active_jobs:
                del _active_jobs[run_id]
                print(f"[Cleanup] Removed run_id={run_id} from active jobs")
        
        if cleaned_count > 0:
            print(f"[Cleanup] Total {cleaned_count} containers removed")
        
        return cleaned_count
        
    except Exception as e:
        print(f"[Cleanup] Error during cleanup: {e}")
        return 0


def cleanup_orphaned_containers_sync() -> int:
    """동기 버전 - 앱 시작 시 사용"""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # 이미 이벤트 루프가 실행 중이면 새 태스크로
            return 0  # startup에서 async 버전 사용
        return loop.run_until_complete(cleanup_orphaned_containers())
    except Exception:
        return 0


# ============ 백그라운드 모니터링 ============

_monitor_task: Optional[asyncio.Task] = None
_last_cleanup_time: Optional[datetime] = None
_last_log_sync_time: Optional[datetime] = None

# 로그 동기화 간격 (초)
LOG_SYNC_INTERVAL_SECONDS = 60  # 1분

# MinIO 설정
MINIO_ENDPOINT = "localhost:9000"
MINIO_ACCESS_KEY = "physicar"
MINIO_SECRET_KEY = "physicar"
MINIO_BUCKET = "bucket"

# 모델별 마지막 체크포인트 인덱스 추적 (last.tar.gz 생성 여부 판단용)
_last_checkpoint_indices: Dict[str, int] = {}


def _get_max_training_time(model_name: str) -> int:
    """model_metadata.json에서 max_training_time(분) 가져오기 (MinIO API)"""
    try:
        client = _get_minio_client()
        key = f"models/{model_name}/model/model_metadata.json"
        response = client.get_object(MINIO_BUCKET, key)
        import json
        data = json.loads(response.read().decode('utf-8'))
        response.close()
        response.release_conn()
        return data.get("max_training_time", 60)
    except Exception:
        return 60


def _get_training_start_time(run_id: int) -> Optional[datetime]:
    """Docker 컨테이너 생성 시간에서 훈련 시작 시간 가져오기"""
    try:
        result = subprocess.run(
            ["docker", "ps", "-a", "--filter", f"name=deepracer-{run_id}-",
             "--format", "{{.CreatedAt}}", "--no-trunc"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            # 첫 번째 컨테이너의 시작 시간
            created_at = result.stdout.strip().split('\n')[0]
            # "2025-12-18 10:30:00 +0000 UTC" 형식
            from datetime import timezone
            dt_str = created_at.split(" +")[0] if " +" in created_at else created_at[:19]
            return datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    except Exception:
        pass
    return None


def _get_minio_client():
    """MinIO 클라이언트 생성"""
    from minio import Minio
    return Minio('localhost:9000', access_key='physicar', secret_key='physicar', secure=False)


def _sync_best_physical_car_model(model_name: str, run_id: int) -> bool:
    """
    체크포인트 변경 시 물리적 차량 모델 동기화 (MinIO API 사용)
    1. 체크포인트가 이전보다 올라갔으면 dr-upload-car-zip -fL로 last.tar.gz 생성
    2. best == last이고 파일이 다르면 last.tar.gz를 best.tar.gz로 복사
    
    Returns: True if any action taken, False otherwise
    """
    import json
    from io import BytesIO
    
    bucket = "bucket"
    checkpoint_key = f"models/{model_name}/model/deepracer_checkpoints.json"
    last_tar_key = f"models/{model_name}/physical-car-model/last.tar.gz"
    best_tar_key = f"models/{model_name}/physical-car-model/best.tar.gz"
    
    try:
        client = _get_minio_client()
        
        # checkpoint 파일 읽기 (MinIO API)
        try:
            response = client.get_object(bucket, checkpoint_key)
            data = json.loads(response.read().decode('utf-8'))
            response.close()
            response.release_conn()
        except Exception as e:
            # 체크포인트 파일 없음
            return False
        
        last_checkpoint = data.get("last_checkpoint", {}).get("name", "")
        best_checkpoint = data.get("best_checkpoint", {}).get("name", "")
        
        if not last_checkpoint or not best_checkpoint:
            return False
        
        # checkpoint 인덱스 추출 (예: "15_Step-2345.ckpt" -> 15)
        last_idx = int(last_checkpoint.split("_")[0])
        best_idx = int(best_checkpoint.split("_")[0])
        
        action_taken = False
        
        # 1. 체크포인트가 이전보다 올라갔으면 last.tar.gz 생성
        prev_idx = _last_checkpoint_indices.get(model_name, -1)
        if last_idx > prev_idx:
            print(f"[Monitor] New checkpoint detected for {model_name}: #{prev_idx} -> #{last_idx}")
            
            # dr-upload-car-zip -fL 실행 (Last 모델 업로드)
            try:
                cmd = f"source {DRFC_DIR}/bin/activate.sh && dr-upload-car-zip -fL"
                env = {"DR_RUN_ID": str(run_id)}
                result = subprocess.run(
                    ["/bin/bash", "-c", cmd],
                    capture_output=True, text=True, timeout=120,
                    env={**os.environ, **env},
                    cwd=str(DRFC_DIR)
                )
                if result.returncode == 0:
                    print(f"[Monitor] Generated last.tar.gz for {model_name}")
                    action_taken = True
                else:
                    print(f"[Monitor] Failed to generate last.tar.gz: {result.stderr}")
            except Exception as e:
                print(f"[Monitor] Error running dr-upload-car-zip: {e}")
            
            # 체크포인트 인덱스 업데이트
            _last_checkpoint_indices[model_name] = last_idx
        
        # 2. best == last이고 파일이 다르면 last.tar.gz를 best.tar.gz로 복사
        if last_idx == best_idx:
            try:
                # last.tar.gz 메타데이터 확인
                last_stat = client.stat_object(bucket, last_tar_key)
                last_etag = last_stat.etag
                last_size = last_stat.size
                
                # best.tar.gz 존재 여부 및 메타데이터 확인
                need_copy = False
                try:
                    best_stat = client.stat_object(bucket, best_tar_key)
                    # ETag(MD5) 또는 크기로 비교
                    if best_stat.etag != last_etag or best_stat.size != last_size:
                        need_copy = True
                except Exception:
                    # best.tar.gz 없음
                    need_copy = True
                
                if need_copy:
                    # MinIO copy_object로 서버 사이드 복사
                    from minio.commonconfig import CopySource
                    client.copy_object(
                        bucket, best_tar_key,
                        CopySource(bucket, last_tar_key)
                    )
                    print(f"[Monitor] Synced best.tar.gz for {model_name} (checkpoint #{best_idx})")
                    action_taken = True
                    
            except Exception as e:
                # last.tar.gz 없음 또는 복사 실패
                print(f"[Monitor] Error copying best.tar.gz: {e}")
        
        return action_taken
        
    except Exception as e:
        print(f"[Monitor] Error syncing physical car model for {model_name}: {e}")
        return False


def _sync_container_logs(model_name: str, run_id: int) -> bool:
    """
    컨테이너 로그를 S3에 저장
    
    저장 경로: models/{model_name}/training-logs/
    - robomaker-main.log   (ROLLOUT_IDX=0)
    - robomaker-sub1.log   (ROLLOUT_IDX=1)
    - robomaker-sub2.log   (ROLLOUT_IDX=2)
    - rl_coach.log
    
    Returns:
        True if any logs were saved
    """
    from minio import Minio
    from io import BytesIO
    
    try:
        client = Minio(
            "localhost:9000",
            access_key="physicar",
            secret_key="physicar",
            secure=False
        )
        bucket = "bucket"
        logs_prefix = f"models/{model_name}/training-logs"
        
        saved_any = False
        
        # 1. Robomaker 컨테이너 로그 저장
        containers = get_robomaker_containers_with_rollout(run_id)
        for container in containers:
            container_name = container["name"]
            rollout_idx = container["rollout_idx"]
            
            # 파일명 결정
            if rollout_idx == 0:
                log_filename = "robomaker-main.log"
            elif rollout_idx == 999:
                # ROLLOUT_IDX 확인 못함 - 컨테이너 이름으로 fallback
                log_filename = f"robomaker-{container_name.split('-')[-1]}.log"
            else:
                log_filename = f"robomaker-sub{rollout_idx}.log"
            
            # docker logs 실행
            try:
                result = subprocess.run(
                    ["docker", "logs", container_name],
                    capture_output=True, timeout=60
                )
                # stdout + stderr 합쳐서 저장
                log_content = result.stdout + result.stderr
                
                if log_content:
                    log_key = f"{logs_prefix}/{log_filename}"
                    client.put_object(
                        bucket, log_key,
                        BytesIO(log_content),
                        length=len(log_content),
                        content_type="text/plain"
                    )
                    print(f"[Logs] Saved {log_filename} ({len(log_content)} bytes)")
                    saved_any = True
            except Exception as e:
                print(f"[Logs] Error saving {container_name} logs: {e}")
        
        # 2. rl_coach 컨테이너 로그 저장
        rl_coach_name = f"deepracer-{run_id}-rl_coach-1"
        try:
            result = subprocess.run(
                ["docker", "logs", rl_coach_name],
                capture_output=True, timeout=60
            )
            log_content = result.stdout + result.stderr
            
            if log_content:
                log_key = f"{logs_prefix}/rl_coach.log"
                client.put_object(
                    bucket, log_key,
                    BytesIO(log_content),
                    length=len(log_content),
                    content_type="text/plain"
                )
                print(f"[Logs] Saved rl_coach.log ({len(log_content)} bytes)")
                saved_any = True
        except Exception as e:
            print(f"[Logs] Error saving rl_coach logs: {e}")
        
        return saved_any
        
    except Exception as e:
        print(f"[Logs] Error syncing container logs for {model_name}: {e}")
        return False


def _sync_eval_container_logs(model_name: str, eval_id: str, run_id: int) -> bool:
    """
    평가 컨테이너 로그를 S3에 저장
    
    저장 경로: models/{model_name}/evaluation/{eval_id}/logs/
    - robomaker.log
    
    Returns:
        True if logs were saved
    """
    from minio import Minio
    from io import BytesIO
    
    try:
        client = Minio(
            "localhost:9000",
            access_key="physicar",
            secret_key="physicar",
            secure=False
        )
        bucket = "bucket"
        logs_prefix = f"models/{model_name}/evaluation/{eval_id}/logs"
        
        saved_any = False
        
        # 평가 robomaker 컨테이너: deepracer-eval-{run_id}-robomaker-1
        container_name = f"deepracer-eval-{run_id}-robomaker-1"
        try:
            result = subprocess.run(
                ["docker", "logs", container_name],
                capture_output=True, timeout=60
            )
            log_content = result.stdout + result.stderr
            
            if log_content:
                log_key = f"{logs_prefix}/robomaker.log"
                client.put_object(
                    bucket, log_key,
                    BytesIO(log_content),
                    length=len(log_content),
                    content_type="text/plain"
                )
                print(f"[Logs] Saved evaluation robomaker.log ({len(log_content)} bytes)")
                saved_any = True
        except Exception as e:
            print(f"[Logs] Error saving eval robomaker logs: {e}")
        
        return saved_any
        
    except Exception as e:
        print(f"[Logs] Error syncing eval container logs for {model_name}/{eval_id}: {e}")
        return False


def _convert_eval_video_to_h264(model_name: str, eval_id: str) -> bool:
    """
    평가 비디오를 H.264 코덱으로 변환 (웹 재생 호환)
    
    mp4v 코덱 → H.264 (libx264)로 변환
    
    Args:
        model_name: 모델 이름
        eval_id: 평가 ID (timestamp)
        
    Returns:
        True if conversion successful
    """
    import tempfile
    from minio import Minio
    
    try:
        client = Minio(
            "localhost:9000",
            access_key="physicar",
            secret_key="physicar",
            secure=False
        )
        bucket = "bucket"
        video_key = f"models/{model_name}/evaluation/{eval_id}/video.mp4"
        
        # 1. MinIO에서 원본 비디오 확인
        try:
            stat = client.stat_object(bucket, video_key)
            if stat.size == 0:
                print(f"[Video] video.mp4 is empty, skipping conversion")
                return False
        except Exception:
            print(f"[Video] video.mp4 not found: {video_key}")
            return False
        
        # 2. 임시 파일로 다운로드
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "input.mp4")
            output_path = os.path.join(tmpdir, "output.mp4")
            
            # 다운로드
            client.fget_object(bucket, video_key, input_path)
            input_size = os.path.getsize(input_path)
            print(f"[Video] Downloaded {video_key} ({input_size} bytes)")
            
            # 3. ffmpeg로 변환
            # -movflags +faststart: 웹 스트리밍 최적화 (moov atom을 앞으로)
            result = subprocess.run([
                "ffmpeg", "-y",  # overwrite
                "-i", input_path,
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "23",
                "-c:a", "aac",
                "-movflags", "+faststart",
                output_path
            ], capture_output=True, timeout=300)  # 5분 타임아웃
            
            if result.returncode != 0:
                print(f"[Video] ffmpeg failed: {result.stderr.decode()[:200]}")
                return False
            
            output_size = os.path.getsize(output_path)
            print(f"[Video] Converted to H.264 ({output_size} bytes)")
            
            # 4. 변환된 파일을 MinIO에 업로드 (덮어쓰기)
            client.fput_object(
                bucket, video_key, output_path,
                content_type="video/mp4"
            )
            print(f"[Video] Uploaded converted video: {video_key}")
            
        return True
        
    except Exception as e:
        print(f"[Video] Error converting video for {model_name}/{eval_id}: {e}")
        return False


async def _monitor_trainings():
    """
    백그라운드 모니터링 태스크
    - 30초마다 실행: 훈련 상태 체크
    - 1분마다 실행: 고아 컨테이너 정리, 로그 동기화
    - 최대 훈련 시간 초과 체크
    - 비정상 컨테이너 (일부 stop됨) 체크
    """
    global _last_cleanup_time, _last_log_sync_time
    
    print("[Monitor] Background training monitor started")
    
    # 시작 시 고아 컨테이너 정리
    await cleanup_orphaned_containers()
    _last_cleanup_time = datetime.now()
    _last_log_sync_time = datetime.now()
    
    while True:
        try:
            await asyncio.sleep(MONITOR_INTERVAL_SECONDS)
            
            # 1분마다 고아 컨테이너 정리
            if _last_cleanup_time is None or \
               (datetime.now() - _last_cleanup_time).total_seconds() >= CLEANUP_INTERVAL_SECONDS:
                await cleanup_orphaned_containers()
                _last_cleanup_time = datetime.now()
            
            # 실행 중인 RUN_ID 목록
            run_ids = get_used_run_ids(include_exited=False)
            
            for run_id in run_ids:
                try:
                    # 모델명 조회
                    model_name = get_model_name_by_run_id(run_id)
                    if not model_name:
                        continue
                    
                    # 훈련 상태 조회
                    status = get_training_status(run_id)
                    
                    # 1. 비정상 상태 체크 (일부 컨테이너가 죽음)
                    if status["status"] == "failed":
                        print(f"[Monitor] Abnormal training detected: run_id={run_id}, model={model_name}")
                        print(f"[Monitor] Reason: {status['message']}")
                        await stop_training(run_id)
                        continue
                    
                    # 2. 최대 훈련 시간 초과 체크
                    max_minutes = _get_max_training_time(model_name)
                    start_time = _get_training_start_time(run_id)
                    
                    if start_time:
                        from datetime import timezone
                        elapsed = (datetime.now(timezone.utc) - start_time).total_seconds() / 60
                        
                        if elapsed > max_minutes:
                            print(f"[Monitor] Max training time exceeded: run_id={run_id}, model={model_name}")
                            print(f"[Monitor] Elapsed: {elapsed:.1f}min, Max: {max_minutes}min")
                            await stop_training(run_id)
                            continue
                    
                    # 3. 체크포인트 변경 시 물리적 차량 모델 동기화
                    _sync_best_physical_car_model(model_name, run_id)
                    
                    # 4. 1분마다 로그 동기화
                    if _last_log_sync_time is None or \
                       (datetime.now() - _last_log_sync_time).total_seconds() >= LOG_SYNC_INTERVAL_SECONDS:
                        try:
                            _sync_container_logs(model_name, run_id)
                        except Exception as e:
                            print(f"[Monitor] Error syncing logs for {model_name}: {e}")
                
                except Exception as e:
                    print(f"[Monitor] Error checking run_id={run_id}: {e}")
            
            # 로그 동기화 시간 업데이트 (루프 밖에서 한 번만)
            if _last_log_sync_time is None or \
               (datetime.now() - _last_log_sync_time).total_seconds() >= LOG_SYNC_INTERVAL_SECONDS:
                _last_log_sync_time = datetime.now()
        
        except asyncio.CancelledError:
            print("[Monitor] Background monitor stopped")
            break
        except Exception as e:
            print(f"[Monitor] Error in monitor loop: {e}")


def start_monitor():
    """백그라운드 모니터 시작"""
    global _monitor_task
    if _monitor_task is None or _monitor_task.done():
        _monitor_task = asyncio.create_task(_monitor_trainings())
        return True
    return False


def stop_monitor():
    """백그라운드 모니터 중지"""
    global _monitor_task
    if _monitor_task and not _monitor_task.done():
        _monitor_task.cancel()
        _monitor_task = None
        return True
    return False
