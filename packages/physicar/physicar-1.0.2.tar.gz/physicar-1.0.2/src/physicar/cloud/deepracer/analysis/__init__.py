"""
DeepRacer Log Analysis Module

Usage Example:
    from physicar.cloud.deepracer import analysis
    
    # Load training logs
    df = analysis.training.load("my-model")
    
    # Analyze training progress
    analysis.training.plot_progress(df)
    
    # Load and visualize track
    track = analysis.track.load("2024_reinvent_champ_cw")
    analysis.plot.plot_track_heatmap(df, track)
"""

from . import training
from . import evaluation
from . import track
from . import plot
from . import action_space
from .config import get_minio_client, BUCKET, ROUTES_PATH, list_models
from .log import load_simtrace, load_metrics

__all__ = [
    "training",
    "evaluation", 
    "track",
    "plot",
    "action_space",
    "get_minio_client",
    "BUCKET",
    "ROUTES_PATH",
    "list_models",
    "load_simtrace",
    "load_metrics",
]
