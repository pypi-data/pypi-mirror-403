"""
Log file loading utilities (MinIO SDK based)
"""
import io
import json
import pandas as pd
from typing import Optional, Literal

from .config import (
    get_minio_client, 
    BUCKET, 
    get_model_prefix,
    list_s3_objects,
    get_s3_object,
    get_s3_object_text,
    s3_object_exists,
)


# SimTrace column definitions
SIMTRACE_COLUMNS = [
    "episode", "steps", "x", "y", "heading", "steering_angle", "speed",
    "action", "reward", "done", "all_wheels_on_track", "progress",
    "closest_waypoint", "track_len", "tstamp", "episode_status",
    "pause_duration", "yaw", "pitch", "roll", "lidar_1", "lidar_2",
    "lidar_3", "lidar_4", "lidar_5", "lidar_6", "lidar_7", "lidar_8"
]


def _parse_simtrace_line(line: str) -> Optional[dict]:
    """Parse SimTrace log line"""
    if not line.startswith("SIM_TRACE_LOG:"):
        return None
    
    try:
        parts = line[14:].strip().split(",")
        row = {}
        for i, col in enumerate(SIMTRACE_COLUMNS):
            if i < len(parts):
                val = parts[i]
                # Type conversion
                if col in ("episode", "steps", "action", "closest_waypoint"):
                    row[col] = int(val)
                elif col in ("done", "all_wheels_on_track"):
                    row[col] = val.lower() == "true"
                elif col in ("x", "y", "heading", "steering_angle", "speed", 
                           "reward", "progress", "track_len", "tstamp",
                           "pause_duration", "yaw", "pitch", "roll",
                           "lidar_1", "lidar_2", "lidar_3", "lidar_4",
                           "lidar_5", "lidar_6", "lidar_7", "lidar_8"):
                    row[col] = float(val) if val else 0.0
                else:
                    row[col] = val
        return row
    except Exception:
        return None


def load_simtrace(
    model_name: str,
    worker: Optional[Literal["main", "sub1", "sub2", "sub3", "sub4", "sub5", "sub6"]] = None,
    is_eval: bool = False,
    eval_timestamp: Optional[str] = None,
) -> pd.DataFrame:
    """
    Load SimTrace logs from MinIO
    
    Args:
        model_name: Model name
        worker: Worker name (None for all workers)
        is_eval: Whether to load evaluation logs
        eval_timestamp: Evaluation timestamp (when is_eval=True)
        
    Returns:
        pd.DataFrame: SimTrace dataframe
    """
    model_prefix = get_model_prefix(model_name)
    
    if is_eval:
        # Evaluation logs
        if eval_timestamp:
            simtrace_prefix = f"{model_prefix}evaluation/{eval_timestamp}/simtrace/"
        else:
            # Select latest evaluation
            eval_prefix = f"{model_prefix}evaluation/"
            eval_dirs = list_s3_objects(eval_prefix, delimiter="/")
            
            if not eval_dirs:
                raise FileNotFoundError(f"No evaluation results: {model_name}")
            
            # Get timestamps and sort
            timestamps = sorted([d.rstrip("/").split("/")[-1] for d in eval_dirs], reverse=True)
            if not timestamps:
                raise FileNotFoundError(f"No evaluation results: {model_name}")
            
            simtrace_prefix = f"{model_prefix}evaluation/{timestamps[0]}/simtrace/"
    else:
        # Training logs
        simtrace_prefix = f"{model_prefix}training-simtrace/"
    
    # Get worker directories
    if worker:
        worker_prefixes = [f"{simtrace_prefix}{worker}/"]
    else:
        # List all worker directories
        worker_dirs = list_s3_objects(simtrace_prefix, delimiter="/")
        worker_prefixes = []
        
        for d in worker_dirs:
            worker_name = d.rstrip("/").split("/")[-1]
            if worker_name in ("main", "sub1", "sub2", "sub3", "sub4", "sub5", "sub6"):
                worker_prefixes.append(d)
        
        # Fallback: single worker (old format)
        if not worker_prefixes:
            worker_prefixes = [simtrace_prefix]
    
    # Load CSV files from each worker
    all_dfs = []
    
    for wp in worker_prefixes:
        worker_name = wp.rstrip("/").split("/")[-1]
        if worker_name == "training-simtrace" or worker_name == "simtrace":
            worker_name = "main"
        
        # List CSV files
        csv_keys = [k for k in list_s3_objects(wp) if k.endswith("-iteration.csv")]
        csv_keys = sorted(csv_keys)
        
        for csv_key in csv_keys:
            try:
                csv_content = get_s3_object(csv_key)
                if csv_content is None:
                    continue
                
                df = pd.read_csv(
                    io.BytesIO(csv_content), 
                    names=SIMTRACE_COLUMNS[:15], 
                    header=None
                )
                df["worker"] = worker_name
                
                # Extract iteration number from filename
                filename = csv_key.split("/")[-1]
                iteration = int(filename.split("-")[0])
                df["iteration"] = iteration
                
                all_dfs.append(df)
            except Exception as e:
                print(f"Warning: Failed to load {csv_key} - {e}")
    
    if not all_dfs:
        raise FileNotFoundError(f"No SimTrace files found: {simtrace_prefix}")
    
    df = pd.concat(all_dfs, ignore_index=True)
    
    # Add unique_episode (for multi-worker)
    df["unique_episode"] = df["worker"] + "_" + df["episode"].astype(str)
    
    return df


def load_metrics(
    model_name: str,
    worker: Optional[Literal["main", "sub1", "sub2", "sub3", "sub4", "sub5", "sub6"]] = None,
) -> pd.DataFrame:
    """
    Load training metrics from MinIO
    
    Args:
        model_name: Model name
        worker: Worker name (None for all workers)
        
    Returns:
        pd.DataFrame: Metrics dataframe
    """
    model_prefix = get_model_prefix(model_name)
    metrics_prefix = f"{model_prefix}training-metrics/"
    
    all_data = []
    
    if worker:
        json_keys = [f"{metrics_prefix}{worker}.json"]
    else:
        json_keys = [k for k in list_s3_objects(metrics_prefix) if k.endswith(".json")]
    
    for json_key in json_keys:
        content = get_s3_object_text(json_key)
        if content is None:
            continue
        
        worker_name = json_key.split("/")[-1].replace(".json", "")
        
        for line in content.strip().split("\n"):
            try:
                data = json.loads(line.strip())
                data["worker"] = worker_name
                all_data.append(data)
            except json.JSONDecodeError:
                continue
    
    if not all_data:
        raise FileNotFoundError(f"No metrics files found: {metrics_prefix}")
    
    return pd.DataFrame(all_data)


def load_hyperparameters(model_name: str) -> dict:
    """Load hyperparameters from MinIO"""
    model_prefix = get_model_prefix(model_name)
    hp_key = f"{model_prefix}custom_files/hyperparameters.json"
    
    content = get_s3_object_text(hp_key)
    if content is None:
        raise FileNotFoundError(f"Hyperparameters file not found: {hp_key}")
    
    return json.loads(content)


def load_model_metadata(model_name: str) -> dict:
    """Load model metadata from MinIO"""
    model_prefix = get_model_prefix(model_name)
    
    # Try custom_files first
    md_key = f"{model_prefix}custom_files/model_metadata.json"
    content = get_s3_object_text(md_key)
    
    if content is None:
        # Try model folder
        md_key = f"{model_prefix}model/model_metadata.json"
        content = get_s3_object_text(md_key)
    
    if content is None:
        raise FileNotFoundError(f"Model metadata file not found")
    
    return json.loads(content)


def load_reward_function(model_name: str) -> str:
    """Load reward function from MinIO"""
    model_prefix = get_model_prefix(model_name)
    
    # Try root first
    rf_key = f"{model_prefix}reward_function.py"
    content = get_s3_object_text(rf_key)
    
    if content is None:
        # Try custom_files folder
        rf_key = f"{model_prefix}custom_files/reward_function.py"
        content = get_s3_object_text(rf_key)
    
    if content is None:
        raise FileNotFoundError(f"Reward function file not found")
    
    return content
