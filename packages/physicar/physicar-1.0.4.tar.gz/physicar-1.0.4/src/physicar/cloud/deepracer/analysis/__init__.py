"""
DeepRacer Analysis Module

Simple data loading for analysis with pandas/numpy.

Usage:
    from physicar.cloud.deepracer.analysis import load
    
    # List models
    load.models()
    
    # Training data
    df = load.training("model_name")
    df = load.training("model_name", sim="main")
    
    # Evaluation data  
    df = load.evaluation("model_name")
    
    # Track data
    track = load.track("2024_reinvent_champ_ccw")
    
    # Metadata
    meta = load.metadata("model_name")
    hp = load.hyperparameters("model_name")
"""

from . import load

__all__ = ["load"]
