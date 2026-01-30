"""
Evaluation log analysis module
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import Optional

from .log import load_simtrace
from .config import get_model_prefix, list_s3_objects


def list_evaluations(model_name: str) -> list[str]:
    """
    List evaluations for a model
    
    Args:
        model_name: Model name
        
    Returns:
        list[str]: Evaluation timestamps (newest first)
    """
    model_prefix = get_model_prefix(model_name)
    eval_prefix = f"{model_prefix}evaluation/"
    
    eval_dirs = list_s3_objects(eval_prefix, delimiter="/")
    
    timestamps = [d.rstrip("/").split("/")[-1] for d in eval_dirs]
    return sorted(timestamps, reverse=True)


def load(
    model_name: str,
    timestamp: Optional[str] = None,
) -> pd.DataFrame:
    """
    Load evaluation SimTrace logs
    
    Args:
        model_name: Model name
        timestamp: Evaluation timestamp (None for latest)
        
    Returns:
        pd.DataFrame: SimTrace dataframe
    """
    return load_simtrace(model_name, is_eval=True, eval_timestamp=timestamp)


def aggregate(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate by episode (trial)
    
    Args:
        df: SimTrace dataframe
        
    Returns:
        pd.DataFrame: Aggregated dataframe
    """
    agg_dict = {
        "reward": ["sum", "mean", "max"],
        "progress": "max",
        "steps": "max",
        "speed": "mean",
        "x": ["first", "last"],
        "y": ["first", "last"],
    }
    
    grouped = df.groupby("episode")
    result = grouped.agg(agg_dict)
    result.columns = ["_".join(col).strip("_") for col in result.columns]
    result = result.reset_index()
    
    # Calculate time
    if "tstamp" in df.columns:
        time_df = grouped["tstamp"].agg(["min", "max"])
        result["time"] = time_df["max"] - time_df["min"]
    
    # Completion flag
    result["completed"] = result["progress_max"] >= 100
    
    return result


def summary(df: pd.DataFrame) -> dict:
    """
    Evaluation summary statistics
    
    Args:
        df: SimTrace dataframe
        
    Returns:
        dict: Summary statistics
    """
    eval_agg = aggregate(df)
    completed = eval_agg[eval_agg["completed"]]
    
    stats = {
        "total_trials": len(eval_agg),
        "completed_trials": len(completed),
        "completion_rate": len(completed) / len(eval_agg) if len(eval_agg) > 0 else 0,
        "avg_progress": eval_agg["progress_max"].mean(),
    }
    
    if len(completed) > 0 and "time" in completed.columns:
        stats["best_time"] = completed["time"].min()
        stats["avg_time"] = completed["time"].mean()
        stats["worst_time"] = completed["time"].max()
    
    return stats


def plot_results(
    df: pd.DataFrame,
    title: str = "Evaluation Results",
    figsize: tuple = (14, 8),
) -> plt.Figure:
    """
    Plot evaluation results
    
    Args:
        df: SimTrace dataframe
        title: Plot title
        figsize: Figure size
        
    Returns:
        plt.Figure: matplotlib Figure object
    """
    eval_agg = aggregate(df)
    completed = eval_agg[eval_agg["completed"]]
    
    fig, axes = plt.subplots(2, 2, figsize=figsize)
    fig.suptitle(title, fontsize=14)
    
    # 1. Progress per trial
    ax1 = axes[0, 0]
    colors = ["green" if c else "red" for c in eval_agg["completed"]]
    ax1.bar(eval_agg["episode"], eval_agg["progress_max"], color=colors, alpha=0.7)
    ax1.set_xlabel("Trial")
    ax1.set_ylabel("Progress (%)")
    ax1.set_title("Progress per Trial (Green=Complete)")
    ax1.axhline(y=100, color="blue", linestyle="--", alpha=0.5)
    ax1.grid(True, alpha=0.3)
    
    # 2. Time per completed trial
    ax2 = axes[0, 1]
    if len(completed) > 0 and "time" in completed.columns:
        ax2.bar(completed["episode"], completed["time"], color="blue", alpha=0.7)
        ax2.set_xlabel("Trial")
        ax2.set_ylabel("Time (s)")
        ax2.set_title("Lap Time (Completed Trials)")
        ax2.axhline(y=completed["time"].mean(), color="red", linestyle="--", alpha=0.5, label="Mean")
        ax2.legend()
    else:
        ax2.text(0.5, 0.5, "No completed trials", ha="center", va="center", transform=ax2.transAxes)
        ax2.set_title("Lap Time (Completed Trials)")
    ax2.grid(True, alpha=0.3)
    
    # 3. Speed distribution
    ax3 = axes[1, 0]
    ax3.hist(df["speed"], bins=30, edgecolor="black", alpha=0.7)
    ax3.set_xlabel("Speed")
    ax3.set_ylabel("Count")
    ax3.set_title("Speed Distribution")
    ax3.grid(True, alpha=0.3)
    
    # 4. Summary text
    ax4 = axes[1, 1]
    ax4.axis("off")
    stats = summary(df)
    
    text = f"""
    === Evaluation Summary ===
    
    Total Trials: {stats['total_trials']}
    Completed: {stats['completed_trials']}
    Completion Rate: {stats['completion_rate']:.1%}
    Avg Progress: {stats['avg_progress']:.1f}%
    """
    
    if "best_time" in stats:
        text += f"""
    Best Time: {stats['best_time']:.2f}s
    Avg Time: {stats['avg_time']:.2f}s
    Worst Time: {stats['worst_time']:.2f}s
    """
    
    ax4.text(0.1, 0.5, text, fontsize=12, family="monospace", va="center", transform=ax4.transAxes)
    
    plt.tight_layout()
    return fig


def get_best_lap(df: pd.DataFrame) -> pd.DataFrame:
    """
    Get the fastest completed lap
    
    Args:
        df: SimTrace dataframe
        
    Returns:
        pd.DataFrame: Step data for the best lap
    """
    eval_agg = aggregate(df)
    completed = eval_agg[eval_agg["completed"]]
    
    if len(completed) == 0:
        raise ValueError("No completed laps")
    
    if "time" in completed.columns:
        best_episode = completed.loc[completed["time"].idxmin(), "episode"]
    else:
        best_episode = completed.iloc[0]["episode"]
    
    return df[df["episode"] == best_episode].copy()


def get_lap(df: pd.DataFrame, episode: int) -> pd.DataFrame:
    """
    Get specific lap data
    
    Args:
        df: SimTrace dataframe
        episode: Episode number
        
    Returns:
        pd.DataFrame: Step data for the episode
    """
    lap_df = df[df["episode"] == episode].copy()
    
    if len(lap_df) == 0:
        raise ValueError(f"Episode {episode} not found")
    
    # Additional calculations
    lap_df["distance"] = np.sqrt(
        (lap_df["x"].diff() ** 2) + (lap_df["y"].diff() ** 2)
    )
    lap_df["time_diff"] = lap_df["tstamp"].diff() if "tstamp" in lap_df.columns else None
    
    return lap_df
