"""
DeepRacer Data Loader (MinIO SDK based)

Provides simple data loading functions only.
Use pandas/numpy for analysis.

Usage:
    from physicar.cloud.deepracer.analysis import load
    
    # Training data
    df = load.training("model_name")  # All workers
    df = load.training("model_name", sim="main")  # Specific worker
    
    # Evaluation data
    df = load.evaluation("model_name")  # Latest
    df = load.evaluation("model_name", timestamp="20260125120000")
    
    # Track data
    track = load.track("2024_reinvent_champ_ccw")
"""
import io
import json
import os
from pathlib import Path
from typing import Optional, List, Literal
from functools import lru_cache
from dataclasses import dataclass

import numpy as np
import pandas as pd


# ============ Configuration ============

MINIO_ENDPOINT = os.environ.get("MINIO_HOST_URL", "localhost:9000")
if MINIO_ENDPOINT.startswith("http://"):
    MINIO_ENDPOINT = MINIO_ENDPOINT[7:]
elif MINIO_ENDPOINT.startswith("https://"):
    MINIO_ENDPOINT = MINIO_ENDPOINT[8:]

MINIO_ACCESS_KEY = os.environ.get("MINIO_ACCESS_KEY", "physicar")
MINIO_SECRET_KEY = os.environ.get("MINIO_SECRET_KEY", "physicar")
MINIO_BUCKET = os.environ.get("DR_LOCAL_S3_BUCKET", "bucket")
MINIO_SECURE = os.environ.get("MINIO_SECURE", "false").lower() == "true"

ROUTES_PATH = Path(os.environ.get(
    "DR_ROUTES_PATH",
    os.path.expanduser("~/deepracer-simapp-mount/deepracer_simulation_environment/share/deepracer_simulation_environment/routes")
))


# ============ MinIO Client ============

@lru_cache(maxsize=1)
def _get_client():
    """Get MinIO client (cached)"""
    from minio import Minio
    return Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=MINIO_SECURE,
    )


def _list_objects(prefix: str, recursive: bool = False) -> List[str]:
    """List objects in bucket"""
    client = _get_client()
    objects = client.list_objects(MINIO_BUCKET, prefix=prefix, recursive=recursive)
    return [obj.object_name for obj in objects if not obj.is_dir]


def _list_dirs(prefix: str) -> List[str]:
    """List directories (prefixes) in bucket"""
    client = _get_client()
    objects = client.list_objects(MINIO_BUCKET, prefix=prefix, recursive=False)
    return [obj.object_name for obj in objects if obj.is_dir]


def _get_object(key: str) -> Optional[bytes]:
    """Get object content"""
    client = _get_client()
    try:
        response = client.get_object(MINIO_BUCKET, key)
        content = response.read()
        response.close()
        response.release_conn()
        return content
    except Exception:
        return None


def _get_text(key: str, encoding: str = "utf-8") -> Optional[str]:
    """Get object as text"""
    content = _get_object(key)
    if content:
        return content.decode(encoding)
    return None


def _get_json(key: str) -> Optional[dict]:
    """Get object as JSON"""
    text = _get_text(key)
    if text:
        return json.loads(text)
    return None


# ============ Model List ============

def models() -> List[str]:
    """
    List available models
    
    Returns:
        List of model names
    """
    dirs = _list_dirs("models/")
    result = []
    for d in dirs:
        name = d.rstrip("/").split("/")[-1]
        # Skip hidden and "models" itself
        if not name.startswith(".") and name != "models":
            result.append(name)
    return sorted(result)


# ============ Training Data ============

# CSV columns (matches actual MinIO data)
SIMTRACE_COLUMNS = [
    "episode", "steps", "x", "y", "yaw", "steering_angle", "speed",
    "action", "reward", "done", "all_wheels_on_track", "progress",
    "closest_waypoint", "track_len", "tstamp", "episode_status",
    "pause_duration", "obstacle_crash_counter"
]

SIMTRACE_DTYPES = {
    "episode": "int32",
    "steps": "int32",
    "x": "float64",
    "y": "float64",
    "yaw": "float64",
    "steering_angle": "float64",
    "speed": "float64",
    "action": "int32",
    "reward": "float64",
    "done": "bool",
    "all_wheels_on_track": "bool",
    "progress": "float64",
    "closest_waypoint": "int32",
    "track_len": "float64",
    "tstamp": "float64",
    "episode_status": "str",
    "pause_duration": "float64",
    "obstacle_crash_counter": "int32",
}


def _load_csv(key: str) -> Optional[pd.DataFrame]:
    """Load CSV from MinIO"""
    content = _get_object(key)
    if content is None:
        return None
    
    # Read CSV with header
    df = pd.read_csv(io.BytesIO(content))
    
    # Rename columns to standard names (handle case differences)
    col_map = {
        "X": "x",
        "Y": "y",
        "steer": "steering_angle",
        "throttle": "speed",
    }
    df.rename(columns=col_map, inplace=True)
    
    # Convert bool columns
    for col in ["done", "all_wheels_on_track"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.lower() == "true"
    
    return df


SimName = Literal["main", "sub1", "sub2", "sub3", "sub4", "sub5", "sub6"]


def training(
    model_name: str,
    sim: Optional[SimName] = None,
) -> pd.DataFrame:
    """
    Load training SimTrace data
    
    Args:
        model_name: Model name
        sim: Simulation worker name ("main", "sub1", ...). None for all.
        
    Returns:
        DataFrame with columns:
            iteration, sim, episode, steps, x, y, yaw, steering_angle, speed,
            action, reward, done, all_wheels_on_track, progress, 
            closest_waypoint, track_len, tstamp, episode_status,
            pause_duration, obstacle_crash_counter
    
    Example:
        df = load.training("my-model")
        df = load.training("my-model", sim="main")
    """
    prefix = f"models/{model_name}/training-simtrace/"
    
    # Get worker directories
    if sim:
        sim_dirs = [f"{prefix}{sim}/"]
    else:
        sim_dirs = _list_dirs(prefix)
        if not sim_dirs:
            raise FileNotFoundError(f"No training data: {prefix}")
    
    all_dfs = []
    
    for sim_dir in sim_dirs:
        sim_name = sim_dir.rstrip("/").split("/")[-1]
        
        # List CSV files
        csv_keys = [k for k in _list_objects(sim_dir) if k.endswith(".csv")]
        csv_keys = sorted(csv_keys, key=lambda x: int(x.split("/")[-1].split("-")[0]))
        
        for csv_key in csv_keys:
            df = _load_csv(csv_key)
            if df is None:
                continue
            
            # Extract iteration from filename (0-iteration.csv -> 0)
            filename = csv_key.split("/")[-1]
            iteration = int(filename.split("-")[0])
            
            df.insert(0, "iteration", iteration)
            df.insert(1, "sim", sim_name)
            
            all_dfs.append(df)
    
    if not all_dfs:
        raise FileNotFoundError(f"No CSV files found: {prefix}")
    
    df = pd.concat(all_dfs, ignore_index=True)
    
    # Sort by iteration, sim, episode, steps
    df.sort_values(["iteration", "sim", "episode", "steps"], inplace=True)
    df.reset_index(drop=True, inplace=True)
    
    return df


# ============ Evaluation Data ============

def evaluations(model_name: str) -> List[str]:
    """
    List evaluation timestamps for a model
    
    Args:
        model_name: Model name
        
    Returns:
        List of timestamps (newest first)
    """
    prefix = f"models/{model_name}/evaluation/"
    dirs = _list_dirs(prefix)
    timestamps = [d.rstrip("/").split("/")[-1] for d in dirs]
    return sorted(timestamps, reverse=True)


def evaluation(
    model_name: str,
    timestamp: Optional[str] = None,
) -> pd.DataFrame:
    """
    Load evaluation SimTrace data
    
    Args:
        model_name: Model name
        timestamp: Evaluation timestamp. None for latest.
        
    Returns:
        DataFrame (same columns as training())
    
    Example:
        df = load.evaluation("my-model")
        df = load.evaluation("my-model", timestamp="20260125120000")
    """
    if timestamp is None:
        timestamps = evaluations(model_name)
        if not timestamps:
            raise FileNotFoundError(f"No evaluation data: {model_name}")
        timestamp = timestamps[0]
    
    prefix = f"models/{model_name}/evaluation/{timestamp}/simtrace/"
    
    csv_keys = [k for k in _list_objects(prefix) if k.endswith(".csv")]
    if not csv_keys:
        raise FileNotFoundError(f"No evaluation CSV: {prefix}")
    
    csv_keys = sorted(csv_keys, key=lambda x: int(x.split("/")[-1].split("-")[0]))
    
    all_dfs = []
    for csv_key in csv_keys:
        df = _load_csv(csv_key)
        if df is None:
            continue
        
        filename = csv_key.split("/")[-1]
        iteration = int(filename.split("-")[0])
        
        df.insert(0, "iteration", iteration)
        df.insert(1, "sim", "eval")
        
        all_dfs.append(df)
    
    if not all_dfs:
        raise FileNotFoundError(f"No CSV files found: {prefix}")
    
    df = pd.concat(all_dfs, ignore_index=True)
    df.sort_values(["iteration", "episode", "steps"], inplace=True)
    df.reset_index(drop=True, inplace=True)
    
    return df


# ============ Track Data ============

@dataclass
class Track:
    """Track data"""
    name: str
    center: np.ndarray  # (N, 2) waypoints
    inner: np.ndarray   # (N, 2) inner border
    outer: np.ndarray   # (N, 2) outer border
    
    @property
    def waypoints(self) -> np.ndarray:
        """Alias for center"""
        return self.center
    
    @property
    def length(self) -> float:
        """Track length (m)"""
        diffs = np.diff(self.center, axis=0)
        return float(np.sum(np.sqrt(np.sum(diffs ** 2, axis=1))))
    
    @property
    def width(self) -> float:
        """Average track width (m)"""
        widths = np.sqrt(np.sum((self.outer - self.inner) ** 2, axis=1))
        return float(np.mean(widths))


def tracks() -> List[str]:
    """List available track names"""
    if not ROUTES_PATH.exists():
        return []
    return sorted([f.stem for f in ROUTES_PATH.glob("*.npy")])


@lru_cache(maxsize=32)
def track(name: str) -> Track:
    """
    Load track data
    
    Args:
        name: Track name (without .npy)
        
    Returns:
        Track object with center, inner, outer arrays
    
    Example:
        t = load.track("2024_reinvent_champ_ccw")
        plt.plot(t.center[:, 0], t.center[:, 1])
    """
    if name.endswith(".npy"):
        name = name[:-4]
    
    path = ROUTES_PATH / f"{name}.npy"
    
    if not path.exists():
        available = tracks()
        similar = [t for t in available if name.lower() in t.lower()][:5]
        if similar:
            raise FileNotFoundError(f"Track '{name}' not found. Similar: {similar}")
        raise FileNotFoundError(f"Track '{name}' not found")
    
    data = np.load(path)
    
    # Parse npy format
    if len(data.shape) == 2 and data.shape[1] >= 6:
        # (N, 6): center_x, center_y, inner_x, inner_y, outer_x, outer_y
        center = data[:, 0:2]
        inner = data[:, 2:4]
        outer = data[:, 4:6]
    elif len(data.shape) == 3:
        # (3, N, 2): [center, inner, outer]
        center = data[0][:, :2]
        inner = data[1][:, :2] if len(data) > 1 else center.copy()
        outer = data[2][:, :2] if len(data) > 2 else center.copy()
    else:
        # Fallback: only center
        center = data[:, :2]
        inner = center.copy()
        outer = center.copy()
    
    return Track(name=name, center=center, inner=inner, outer=outer)


# ============ Metadata ============

def metadata(model_name: str) -> dict:
    """Load model metadata (action space, sensors)"""
    # Try model folder first
    data = _get_json(f"models/{model_name}/model/model_metadata.json")
    if data:
        return data
    
    # Try custom_files
    data = _get_json(f"models/{model_name}/custom_files/model_metadata.json")
    if data:
        return data
    
    raise FileNotFoundError(f"Model metadata not found: {model_name}")


def hyperparameters(model_name: str) -> dict:
    """Load hyperparameters"""
    data = _get_json(f"models/{model_name}/ip/hyperparameters.json")
    if data:
        return data
    
    data = _get_json(f"models/{model_name}/custom_files/hyperparameters.json")
    if data:
        return data
    
    raise FileNotFoundError(f"Hyperparameters not found: {model_name}")


def reward_function(model_name: str) -> str:
    """Load reward function code"""
    code = _get_text(f"models/{model_name}/reward_function.py")
    if code:
        return code
    
    code = _get_text(f"models/{model_name}/custom_files/reward_function.py")
    if code:
        return code
    
    raise FileNotFoundError(f"Reward function not found: {model_name}")


def training_params(model_name: str, sim: SimName = "main") -> dict:
    """Load training parameters YAML"""
    import yaml
    text = _get_text(f"models/{model_name}/training-params/{sim}.yaml")
    if text:
        return yaml.safe_load(text)
    raise FileNotFoundError(f"Training params not found: {model_name}/{sim}")


def metrics(model_name: str, sim: Optional[SimName] = None) -> pd.DataFrame:
    """
    Load training metrics JSON
    
    Args:
        model_name: Model name
        sim: Worker name. None for all.
        
    Returns:
        DataFrame with metrics per episode
    """
    prefix = f"models/{model_name}/training-metrics/"
    
    if sim:
        json_keys = [f"{prefix}{sim}.json"]
    else:
        json_keys = [k for k in _list_objects(prefix) if k.endswith(".json")]
    
    all_data = []
    for key in json_keys:
        content = _get_text(key)
        if content is None:
            continue
        
        sim_name = key.split("/")[-1].replace(".json", "")
        
        for line in content.strip().split("\n"):
            try:
                data = json.loads(line.strip())
                data["sim"] = sim_name
                all_data.append(data)
            except json.JSONDecodeError:
                continue
    
    if not all_data:
        raise FileNotFoundError(f"No metrics found: {prefix}")
    
    return pd.DataFrame(all_data)
