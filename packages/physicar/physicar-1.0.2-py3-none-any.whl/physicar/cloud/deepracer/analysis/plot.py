"""
Visualization utility module
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from typing import Optional, Union, List

from .track import Track


def plot_track_heatmap(
    df: pd.DataFrame,
    track: Track,
    value_field: str = "reward",
    figsize: tuple = (12, 8),
    cmap: str = "hot",
    alpha: float = 0.7,
    title: Optional[str] = None,
) -> plt.Figure:
    """
    Visualize heatmap on track
    
    Args:
        df: SimTrace dataframe
        track: Track object
        value_field: Field to represent as color
        figsize: Figure size
        cmap: Colormap
        alpha: Point transparency
        title: Plot title
        
    Returns:
        plt.Figure: matplotlib Figure object
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    # Draw track borders
    ax.plot(track.inner_border[:, 0], track.inner_border[:, 1], "b-", linewidth=2, alpha=0.5)
    ax.plot(track.outer_border[:, 0], track.outer_border[:, 1], "b-", linewidth=2, alpha=0.5)
    
    # Draw data points
    if value_field in df.columns:
        values = df[value_field]
        scatter = ax.scatter(
            df["x"], df["y"],
            c=values,
            cmap=cmap,
            alpha=alpha,
            s=3,
        )
        plt.colorbar(scatter, ax=ax, label=value_field)
    else:
        ax.scatter(df["x"], df["y"], alpha=alpha, s=3)
    
    ax.set_aspect("equal")
    ax.set_title(title or f"Track Heatmap ({value_field})")
    ax.set_xlabel("X (m)")
    ax.set_ylabel("Y (m)")
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig


def plot_episode_path(
    df: pd.DataFrame,
    track: Track,
    episode: int,
    value_field: str = "reward",
    figsize: tuple = (12, 8),
    show_arrows: bool = True,
) -> plt.Figure:
    """
    Visualize specific episode path
    
    Args:
        df: SimTrace dataframe
        track: Track object
        episode: Episode number
        value_field: Field to represent as color
        figsize: Figure size
        show_arrows: Show direction arrows
        
    Returns:
        plt.Figure: matplotlib Figure object
    """
    episode_df = df[df["episode"] == episode].copy()
    
    if len(episode_df) == 0:
        raise ValueError(f"Episode {episode} not found")
    
    fig, ax = plt.subplots(figsize=figsize)
    
    # Draw track borders
    ax.plot(track.inner_border[:, 0], track.inner_border[:, 1], "gray", linewidth=2, alpha=0.5)
    ax.plot(track.outer_border[:, 0], track.outer_border[:, 1], "gray", linewidth=2, alpha=0.5)
    
    # Draw path
    if value_field in episode_df.columns:
        values = episode_df[value_field]
        scatter = ax.scatter(
            episode_df["x"], episode_df["y"],
            c=values,
            cmap="viridis",
            s=20,
            zorder=5,
        )
        plt.colorbar(scatter, ax=ax, label=value_field)
    else:
        ax.plot(episode_df["x"], episode_df["y"], "b-", linewidth=2, alpha=0.7)
        ax.scatter(episode_df["x"], episode_df["y"], s=10, zorder=5)
    
    # Mark start/end
    ax.scatter(episode_df["x"].iloc[0], episode_df["y"].iloc[0], c="green", s=100, marker="o", zorder=10, label="Start")
    ax.scatter(episode_df["x"].iloc[-1], episode_df["y"].iloc[-1], c="red", s=100, marker="x", zorder=10, label="End")
    
    # Direction arrows
    if show_arrows and len(episode_df) > 10:
        step = max(1, len(episode_df) // 20)
        for i in range(0, len(episode_df) - 1, step):
            dx = episode_df["x"].iloc[i + 1] - episode_df["x"].iloc[i]
            dy = episode_df["y"].iloc[i + 1] - episode_df["y"].iloc[i]
            ax.arrow(
                episode_df["x"].iloc[i], episode_df["y"].iloc[i],
                dx * 0.5, dy * 0.5,
                head_width=0.1, head_length=0.05,
                fc="blue", ec="blue", alpha=0.5
            )
    
    progress = episode_df["progress"].max()
    ax.set_aspect("equal")
    ax.set_title(f"Episode {episode} Path (Progress: {progress:.1f}%)")
    ax.set_xlabel("X (m)")
    ax.set_ylabel("Y (m)")
    ax.legend(loc="upper right")
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig


def plot_selected_episodes(
    df: pd.DataFrame,
    track: Track,
    episodes: List[int],
    figsize: tuple = (12, 8),
) -> plt.Figure:
    """
    Compare multiple episode paths
    
    Args:
        df: SimTrace dataframe
        track: Track object
        episodes: List of episode numbers
        figsize: Figure size
        
    Returns:
        plt.Figure: matplotlib Figure object
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    # Draw track borders
    ax.plot(track.inner_border[:, 0], track.inner_border[:, 1], "gray", linewidth=2, alpha=0.5)
    ax.plot(track.outer_border[:, 0], track.outer_border[:, 1], "gray", linewidth=2, alpha=0.5)
    
    colors = cm.rainbow(np.linspace(0, 1, len(episodes)))
    
    for episode, color in zip(episodes, colors):
        episode_df = df[df["episode"] == episode]
        if len(episode_df) == 0:
            continue
        
        progress = episode_df["progress"].max()
        ax.plot(
            episode_df["x"], episode_df["y"],
            color=color,
            linewidth=2,
            alpha=0.7,
            label=f"Ep {episode} ({progress:.0f}%)"
        )
    
    ax.set_aspect("equal")
    ax.set_title("Episode Path Comparison")
    ax.set_xlabel("X (m)")
    ax.set_ylabel("Y (m)")
    ax.legend(loc="upper right", fontsize=8)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig


def plot_iteration_heatmap(
    df: pd.DataFrame,
    track: Track,
    iteration: int,
    value_field: str = "reward",
    figsize: tuple = (12, 8),
) -> plt.Figure:
    """
    Visualize specific iteration heatmap
    
    Args:
        df: SimTrace dataframe
        track: Track object
        iteration: Iteration number
        value_field: Field to represent as color
        figsize: Figure size
        
    Returns:
        plt.Figure: matplotlib Figure object
    """
    iter_df = df[df["iteration"] == iteration]
    
    if len(iter_df) == 0:
        raise ValueError(f"Iteration {iteration} not found")
    
    return plot_track_heatmap(
        iter_df,
        track,
        value_field=value_field,
        figsize=figsize,
        title=f"Iteration {iteration} Heatmap ({value_field})"
    )


def plot_reward_per_waypoint(
    df: pd.DataFrame,
    episode: Optional[int] = None,
    figsize: tuple = (14, 5),
) -> plt.Figure:
    """
    Reward distribution per waypoint

    Args:
        df: SimTrace dataframe
        episode: Specific episode (None for all)
        figsize: Figure size
        
    Returns:
        plt.Figure: matplotlib Figure object
    """
    if episode is not None:
        plot_df = df[df["episode"] == episode]
        title = f"Reward per Waypoint (Episode {episode})"
    else:
        plot_df = df
        title = "Reward per Waypoint (All Episodes)"
    
    fig, ax = plt.subplots(figsize=figsize)
    
    wp_reward = plot_df.groupby("closest_waypoint")["reward"].agg(["mean", "std"]).reset_index()
    
    ax.bar(wp_reward["closest_waypoint"], wp_reward["mean"], yerr=wp_reward["std"], alpha=0.7, capsize=2)
    ax.set_xlabel("Waypoint")
    ax.set_ylabel("Mean Reward")
    ax.set_title(title)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig


def plot_speed_distribution(
    df: pd.DataFrame,
    by_action: bool = False,
    figsize: tuple = (12, 5),
) -> plt.Figure:
    """
    Speed distribution visualization
    
    Args:
        df: SimTrace dataframe
        by_action: Group by action
        figsize: Figure size
        
    Returns:
        plt.Figure: matplotlib Figure object
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    if by_action and "action" in df.columns:
        actions = df["action"].unique()
        for action in sorted(actions):
            action_df = df[df["action"] == action]
            ax.hist(action_df["speed"], bins=30, alpha=0.5, label=f"Action {int(action)}")
        ax.legend()
    else:
        ax.hist(df["speed"], bins=50, edgecolor="black", alpha=0.7)
    
    ax.set_xlabel("Speed")
    ax.set_ylabel("Count")
    ax.set_title("Speed Distribution")
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig


def plot_steering_distribution(
    df: pd.DataFrame,
    by_action: bool = False,
    figsize: tuple = (12, 5),
) -> plt.Figure:
    """
    Steering angle distribution visualization
    
    Args:
        df: SimTrace dataframe
        by_action: Group by action
        figsize: Figure size
        
    Returns:
        plt.Figure: matplotlib Figure object
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    if by_action and "action" in df.columns:
        actions = df["action"].unique()
        for action in sorted(actions):
            action_df = df[df["action"] == action]
            ax.hist(action_df["steering_angle"], bins=30, alpha=0.5, label=f"Action {int(action)}")
        ax.legend()
    else:
        ax.hist(df["steering_angle"], bins=50, edgecolor="black", alpha=0.7)
    
    ax.set_xlabel("Steering Angle")
    ax.set_ylabel("Count")
    ax.set_title("Steering Angle Distribution")
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig
