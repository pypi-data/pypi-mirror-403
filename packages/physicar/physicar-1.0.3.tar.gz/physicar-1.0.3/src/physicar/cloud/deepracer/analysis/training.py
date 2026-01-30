"""
Training log analysis module
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import Optional, Literal

from .log import load_simtrace, load_metrics, load_hyperparameters, load_model_metadata


def load(
    model_name: str,
    worker: Optional[Literal["main", "sub1", "sub2", "sub3", "sub4", "sub5", "sub6"]] = None,
) -> pd.DataFrame:
    """
    Load training SimTrace logs
    
    Args:
        model_name: Model name
        worker: Worker name (None for all workers)
        
    Returns:
        pd.DataFrame: SimTrace dataframe
    """
    return load_simtrace(model_name, worker=worker, is_eval=False)


def aggregate(
    df: pd.DataFrame,
    group_by: str = "episode",
) -> pd.DataFrame:
    """
    Aggregate by episode/iteration
    
    Args:
        df: SimTrace dataframe
        group_by: Grouping criterion ("episode", "iteration", "unique_episode")
        
    Returns:
        pd.DataFrame: Aggregated dataframe
    """
    # Detect multi-worker
    has_multiple_workers = df["worker"].nunique() > 1 if "worker" in df.columns else False
    
    if has_multiple_workers and group_by == "episode":
        group_by = "unique_episode"
    
    agg_dict = {
        "reward": ["sum", "mean", "max", "min"],
        "progress": "max",
        "steps": "max",
        "speed": "mean",
        "x": ["first", "last"],
        "y": ["first", "last"],
    }
    
    if group_by == "unique_episode":
        grouped = df.groupby(["worker", "episode"])
    else:
        grouped = df.groupby(group_by)
    
    result = grouped.agg(agg_dict)
    result.columns = ["_".join(col).strip("_") for col in result.columns]
    result = result.reset_index()
    
    # Calculate time (first step ~ last step)
    if "tstamp" in df.columns:
        time_df = grouped["tstamp"].agg(["min", "max"])
        result["time"] = time_df["max"] - time_df["min"]
    
    # Completion flag
    result["completed"] = result["progress_max"] >= 100
    
    # Add iteration info
    if "iteration" in df.columns and group_by != "iteration":
        result["iteration"] = grouped["iteration"].first().values
    
    # Quintile (training progress quintiles)
    if group_by != "iteration":
        result["quintile"] = pd.qcut(
            result.index, 5, labels=["Q1", "Q2", "Q3", "Q4", "Q5"]
        )
    
    return result


def analyze_progress(
    df: pd.DataFrame,
    title: str = "Training Progress",
    figsize: tuple = (16, 12),
) -> plt.Figure:
    """
    Training progress analysis graph
    
    Args:
        df: SimTrace dataframe
        title: Plot title
        figsize: Figure size
        
    Returns:
        plt.Figure: matplotlib Figure object
    """
    sim_agg = aggregate(df)
    
    # Aggregate by iteration
    iter_agg = df.groupby("iteration").agg({
        "reward": ["sum", "mean"],
        "progress": "max",
        "steps": "max",
    }).reset_index()
    iter_agg.columns = ["iteration", "reward_sum", "reward_mean", "progress", "steps"]
    
    # Calculate completion rate
    completed_by_iter = sim_agg.groupby("iteration").agg({
        "completed": ["sum", "count"]
    }).reset_index()
    completed_by_iter.columns = ["iteration", "completed_count", "total_count"]
    completed_by_iter["completion_rate"] = completed_by_iter["completed_count"] / completed_by_iter["total_count"]
    
    # Mean completion time
    completed_df = sim_agg[sim_agg["completed"]]
    if len(completed_df) > 0 and "time" in completed_df.columns:
        completed_time_by_iter = completed_df.groupby("iteration")["time"].mean().reset_index()
        completed_time_by_iter.columns = ["iteration", "mean_time"]
    else:
        completed_time_by_iter = pd.DataFrame(columns=["iteration", "mean_time"])
    
    # Create figure
    fig, axes = plt.subplots(3, 2, figsize=figsize)
    fig.suptitle(title, fontsize=14)
    
    # 1. Reward per iteration
    ax1 = axes[0, 0]
    ax1.plot(iter_agg["iteration"], iter_agg["reward_mean"], "b-", alpha=0.7)
    ax1.fill_between(iter_agg["iteration"], 
                      iter_agg["reward_mean"] - iter_agg["reward_mean"].std(),
                      iter_agg["reward_mean"] + iter_agg["reward_mean"].std(),
                      alpha=0.2)
    ax1.set_xlabel("Iteration")
    ax1.set_ylabel("Mean Reward")
    ax1.set_title("Reward per Iteration")
    ax1.grid(True, alpha=0.3)
    
    # 2. Progress per iteration
    ax2 = axes[0, 1]
    ax2.plot(iter_agg["iteration"], iter_agg["progress"], "g-", alpha=0.7)
    ax2.set_xlabel("Iteration")
    ax2.set_ylabel("Max Progress (%)")
    ax2.set_title("Progress per Iteration")
    ax2.grid(True, alpha=0.3)
    
    # 3. Total reward per episode (scatter)
    ax3 = axes[1, 0]
    ax3.scatter(sim_agg.index, sim_agg["reward_sum"], alpha=0.3, s=5)
    ax3.set_xlabel("Episode")
    ax3.set_ylabel("Total Reward")
    ax3.set_title("Total Reward per Episode")
    ax3.grid(True, alpha=0.3)
    
    # 4. Progress histogram
    ax4 = axes[1, 1]
    ax4.hist(sim_agg["progress_max"], bins=50, edgecolor="black", alpha=0.7)
    ax4.set_xlabel("Progress (%)")
    ax4.set_ylabel("Count")
    ax4.set_title("Progress Distribution")
    ax4.grid(True, alpha=0.3)
    
    # 5. Completion rate per iteration
    ax5 = axes[2, 0]
    ax5.bar(completed_by_iter["iteration"], completed_by_iter["completion_rate"], alpha=0.7)
    ax5.set_xlabel("Iteration")
    ax5.set_ylabel("Completion Rate")
    ax5.set_title("Completion Rate per Iteration")
    ax5.set_ylim(0, 1)
    ax5.grid(True, alpha=0.3)
    
    # 6. Completion time per iteration
    ax6 = axes[2, 1]
    if len(completed_time_by_iter) > 0:
        ax6.plot(completed_time_by_iter["iteration"], completed_time_by_iter["mean_time"], "r-", alpha=0.7)
        ax6.set_xlabel("Iteration")
        ax6.set_ylabel("Mean Time (s)")
        ax6.set_title("Mean Completion Time per Iteration")
    else:
        ax6.text(0.5, 0.5, "No completed laps yet", ha="center", va="center", transform=ax6.transAxes)
        ax6.set_title("Mean Completion Time per Iteration")
    ax6.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig


def scatter_stats(
    df: pd.DataFrame,
    title: str = "Training Stats",
    figsize: tuple = (16, 10),
) -> plt.Figure:
    """
    Training stats scatter plot
    
    Args:
        df: SimTrace dataframe
        title: Plot title
        figsize: Figure size
        
    Returns:
        plt.Figure: matplotlib Figure object
    """
    sim_agg = aggregate(df)
    
    fig, axes = plt.subplots(2, 3, figsize=figsize)
    fig.suptitle(title, fontsize=14)
    
    # 1. Reward vs Time
    ax1 = axes[0, 0]
    if "time" in sim_agg.columns:
        ax1.scatter(sim_agg["time"], sim_agg["reward_sum"], alpha=0.3, s=10)
        ax1.set_xlabel("Time (s)")
        ax1.set_ylabel("Total Reward")
        ax1.set_title("Reward vs Time")
    ax1.grid(True, alpha=0.3)
    
    # 2. Progress vs Time
    ax2 = axes[0, 1]
    if "time" in sim_agg.columns:
        ax2.scatter(sim_agg["time"], sim_agg["progress_max"], alpha=0.3, s=10)
        ax2.set_xlabel("Time (s)")
        ax2.set_ylabel("Progress (%)")
        ax2.set_title("Progress vs Time")
    ax2.grid(True, alpha=0.3)
    
    # 3. Steps histogram
    ax3 = axes[0, 2]
    ax3.hist(sim_agg["steps_max"], bins=50, edgecolor="black", alpha=0.7)
    ax3.set_xlabel("Steps")
    ax3.set_ylabel("Count")
    ax3.set_title("Steps Distribution")
    ax3.grid(True, alpha=0.3)
    
    # 4. Reward histogram
    ax4 = axes[1, 0]
    ax4.hist(sim_agg["reward_sum"], bins=50, edgecolor="black", alpha=0.7)
    ax4.set_xlabel("Total Reward")
    ax4.set_ylabel("Count")
    ax4.set_title("Reward Distribution")
    ax4.grid(True, alpha=0.3)
    
    # 5. Speed distribution
    ax5 = axes[1, 1]
    ax5.hist(df["speed"], bins=50, edgecolor="black", alpha=0.7)
    ax5.set_xlabel("Speed")
    ax5.set_ylabel("Count")
    ax5.set_title("Speed Distribution")
    ax5.grid(True, alpha=0.3)
    
    # 6. Steering distribution
    ax6 = axes[1, 2]
    ax6.hist(df["steering_angle"], bins=50, edgecolor="black", alpha=0.7)
    ax6.set_xlabel("Steering Angle")
    ax6.set_ylabel("Count")
    ax6.set_title("Steering Distribution")
    ax6.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig


def summary(df: pd.DataFrame) -> dict:
    """
    Training summary statistics
    
    Args:
        df: SimTrace dataframe
        
    Returns:
        dict: Summary statistics
    """
    sim_agg = aggregate(df)
    completed = sim_agg[sim_agg["completed"]]
    
    stats = {
        "total_episodes": len(sim_agg),
        "total_iterations": df["iteration"].max() + 1 if "iteration" in df.columns else 0,
        "completed_laps": len(completed),
        "completion_rate": len(completed) / len(sim_agg) if len(sim_agg) > 0 else 0,
        "avg_progress": sim_agg["progress_max"].mean(),
        "max_progress": sim_agg["progress_max"].max(),
        "avg_reward": sim_agg["reward_sum"].mean(),
        "max_reward": sim_agg["reward_sum"].max(),
        "avg_steps": sim_agg["steps_max"].mean(),
    }
    
    if len(completed) > 0 and "time" in completed.columns:
        stats["best_time"] = completed["time"].min()
        stats["avg_time"] = completed["time"].mean()
        stats["worst_time"] = completed["time"].max()
    
    return stats


def plot_progress(*args, **kwargs):
    """Alias for analyze_progress"""
    return analyze_progress(*args, **kwargs)
