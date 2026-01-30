"""
Action space analysis module
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from typing import Optional, List
from dataclasses import dataclass

from .track import Track
from .log import load_model_metadata


@dataclass
class Action:
    """Action data class"""
    index: int
    steering_angle: float
    speed: float
    
    @property
    def steering(self) -> float:
        """Alias for steering_angle"""
        return self.steering_angle
    
    @property
    def color(self) -> tuple:
        """Color for action (RGB 0-1)"""
        # Red(left turn) - Green(straight) - Blue(right turn)
        if self.steering_angle > 0:
            r = min(1.0, abs(self.steering_angle) / 30)
            g = max(0, 1 - abs(self.steering_angle) / 30)
            b = 0
        elif self.steering_angle < 0:
            r = 0
            g = max(0, 1 - abs(self.steering_angle) / 30)
            b = min(1.0, abs(self.steering_angle) / 30)
        else:
            r, g, b = 0, 1, 0
        return (r, g, b)


def extract_action_space(df: pd.DataFrame) -> List[Action]:
    """
    Extract action space from dataframe
    
    Args:
        df: SimTrace dataframe
        
    Returns:
        List[Action]: List of actions
    """
    # Calculate median steering_angle and speed per action number
    action_stats = df[df["steps"] != 0].groupby("action")[["steering_angle", "speed"]].median().reset_index()
    
    actions = []
    for _, row in action_stats.iterrows():
        actions.append(Action(
            index=int(row["action"]),
            steering_angle=round(row["steering_angle"], 2),
            speed=round(row["speed"], 2),
        ))
    
    return sorted(actions, key=lambda a: a.index)


def load_action_space(model_name: str) -> List[Action]:
    """
    Load action space from model metadata
    
    Args:
        model_name: Model name
        
    Returns:
        List[Action]: List of actions
    """
    metadata = load_model_metadata(model_name)
    action_space = metadata.get("action_space", [])
    
    actions = []
    for i, action in enumerate(action_space):
        actions.append(Action(
            index=i,
            steering_angle=action.get("steering_angle", 0),
            speed=action.get("speed", 0),
        ))
    
    return actions


def plot_action_map(
    actions: List[Action],
    figsize: tuple = (8, 5),
) -> plt.Figure:
    """
    Visualize action map
    
    Args:
        actions: List of actions
        figsize: Figure size
        
    Returns:
        plt.Figure: matplotlib Figure object
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    max_speed = max(a.speed for a in actions)
    
    for action in actions:
        size = (action.speed / max_speed) ** 2 * 1000
        ax.scatter(
            action.steering_angle,
            action.speed,
            c=[action.color],
            s=size,
            alpha=0.8,
            edgecolors="black",
            linewidth=1,
        )
        ax.annotate(
            str(action.index),
            (action.steering_angle, action.speed),
            ha="center",
            va="center",
            fontsize=10,
            fontweight="bold",
            color="white",
        )
    
    ax.set_xlim(35, -35)  # Flip since left turn is positive
    ax.set_ylim(0, max_speed * 1.2)
    ax.set_xlabel("Steering Angle (°)")
    ax.set_ylabel("Speed (m/s)")
    ax.set_title("Action Space Map")
    ax.grid(True, alpha=0.3)
    ax.axvline(x=0, color="gray", linestyle="--", alpha=0.5)
    
    plt.tight_layout()
    return fig


def plot_action_histogram(
    df: pd.DataFrame,
    actions: Optional[List[Action]] = None,
    figsize: tuple = (14, 10),
    iteration: Optional[int] = None,
    episode: Optional[int] = None,
) -> plt.Figure:
    """
    Action distribution histogram (4-in-1)
    
    Args:
        df: SimTrace dataframe
        actions: List of actions (optional)
        figsize: Figure size
        iteration: Specific iteration (None for all)
        episode: Specific episode (None for all)
        
    Returns:
        plt.Figure: matplotlib Figure object
    """
    if iteration is not None:
        plot_df = df[df["iteration"] == iteration]
        title_suffix = f"(Iteration {iteration})"
    elif episode is not None:
        plot_df = df[df["episode"] == episode]
        title_suffix = f"(Episode {episode})"
    else:
        plot_df = df
        title_suffix = "(All)"
    
    max_speed = plot_df["speed"].max()
    
    fig, axes = plt.subplots(2, 2, figsize=figsize, gridspec_kw={"hspace": 0.05, "wspace": 0.05})
    (ax1, ax2), (ax3, ax4) = axes
    
    # Bottom-left: 2D histogram
    ax3.hist2d(
        plot_df["steering_angle"],
        plot_df["speed"],
        bins=(60, 50),
        cmap="hot",
    )
    ax3.set_xlabel("Steering Angle")
    ax3.set_ylabel("Speed")
    ax3.set_xlim(30, -30)
    
    # Top-right: Polar histogram
    ax2.remove()
    ax2 = fig.add_subplot(222, polar=True)
    ax2.set_theta_zero_location("N")
    ax2.hist2d(
        np.deg2rad(plot_df["steering_angle"]),
        plot_df["speed"],
        bins=(90, 25),
        range=[[-np.pi/2, np.pi/2], [0, max_speed * 1.1]],
        cmap="hot",
    )
    
    # Top-left: Steering histogram
    ax1.hist(plot_df["steering_angle"], bins=60, edgecolor="black", alpha=0.7)
    ax1.set_xlabel("")
    ax1.set_ylabel("Count")
    ax1.set_xlim(30, -30)
    ax1.tick_params(labelbottom=False)
    
    # Bottom-right: Speed histogram
    ax4.hist(plot_df["speed"], bins=50, orientation="horizontal", edgecolor="black", alpha=0.7)
    ax4.set_xlabel("Count")
    ax4.set_ylabel("")
    ax4.tick_params(labelleft=False)
    
    fig.suptitle(f"Action Distribution {title_suffix}", fontsize=14)
    
    plt.tight_layout()
    return fig


def plot_polar_histogram(
    df: pd.DataFrame,
    figsize: tuple = (8, 8),
    iteration: Optional[int] = None,
    episode: Optional[int] = None,
) -> plt.Figure:
    """
    Polar action distribution visualization
    
    Args:
        df: SimTrace dataframe
        figsize: Figure size
        iteration: Specific iteration (None for all)
        episode: Specific episode (None for all)
        
    Returns:
        plt.Figure: matplotlib Figure object
    """
    if iteration is not None:
        plot_df = df[df["iteration"] == iteration]
        title = f"Action Distribution (Iteration {iteration})"
    elif episode is not None:
        plot_df = df[df["episode"] == episode]
        title = f"Action Distribution (Episode {episode})"
    else:
        plot_df = df
        title = "Action Distribution (All)"
    
    max_speed = plot_df["speed"].max()
    
    fig = plt.figure(figsize=figsize)
    ax = fig.add_subplot(111, polar=True)
    ax.set_theta_zero_location("N")
    
    ax.hist2d(
        np.deg2rad(plot_df["steering_angle"]),
        plot_df["speed"],
        bins=(90, 25),
        range=[[-np.pi/2, np.pi/2], [0, max_speed * 1.1]],
        cmap="hot",
    )
    
    ax.set_title(title)
    
    plt.tight_layout()
    return fig


def plot_episode_actions(
    df: pd.DataFrame,
    track: Track,
    episode: int,
    actions: Optional[List[Action]] = None,
    figsize: tuple = (12, 8),
) -> plt.Figure:
    """
    Visualize actions per episode (on track)
    
    Args:
        df: SimTrace dataframe
        track: Track object
        episode: Episode number
        actions: List of actions (None to extract from data)
        figsize: Figure size
        
    Returns:
        plt.Figure: matplotlib Figure object
    """
    episode_df = df[df["episode"] == episode].copy()
    
    if len(episode_df) == 0:
        raise ValueError(f"Episode {episode} not found")
    
    if actions is None:
        actions = extract_action_space(df)
    
    # Action index -> color mapping
    action_colors = {a.index: a.color for a in actions}
    max_speed = max(a.speed for a in actions)
    
    fig, ax = plt.subplots(figsize=figsize)
    
    # Track borders
    ax.plot(track.inner_border[:, 0], track.inner_border[:, 1], "gray", linewidth=2, alpha=0.5)
    ax.plot(track.outer_border[:, 0], track.outer_border[:, 1], "gray", linewidth=2, alpha=0.5)
    
    # Show each step's action with color and size
    for _, row in episode_df.iterrows():
        action_idx = int(row["action"])
        color = action_colors.get(action_idx, (0.5, 0.5, 0.5))
        size = (row["speed"] / max_speed) ** 2 * 50
        
        ax.scatter(row["x"], row["y"], c=[color], s=size, alpha=0.7)
    
    ax.set_aspect("equal")
    ax.set_title(f"Episode {episode} Actions (Green=Straight, Red=Left, Blue=Right)")
    ax.set_xlabel("X (m)")
    ax.set_ylabel("Y (m)")
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig


def plot_action_per_waypoint(
    df: pd.DataFrame,
    track: Optional[Track] = None,
    actions: Optional[List[Action]] = None,
    figsize: tuple = (16, 6),
) -> plt.Figure:
    """
    Visualize action distribution per waypoint
    
    Args:
        df: SimTrace dataframe
        track: Track object (optional)
        actions: List of actions (optional)
        figsize: Figure size
        
    Returns:
        plt.Figure: matplotlib Figure object
    """
    fig, axes = plt.subplots(1, 2, figsize=figsize)
    
    # Steering per waypoint
    ax1 = axes[0]
    wp_steering = df.groupby("closest_waypoint")["steering_angle"].agg(["mean", "std"]).reset_index()
    ax1.bar(wp_steering["closest_waypoint"], wp_steering["mean"], yerr=wp_steering["std"], alpha=0.7, capsize=1)
    ax1.set_xlabel("Waypoint")
    ax1.set_ylabel("Mean Steering Angle")
    ax1.set_title("Steering per Waypoint")
    ax1.axhline(y=0, color="gray", linestyle="--", alpha=0.5)
    ax1.grid(True, alpha=0.3)
    
    # Speed per waypoint
    ax2 = axes[1]
    wp_speed = df.groupby("closest_waypoint")["speed"].agg(["mean", "std"]).reset_index()
    ax2.bar(wp_speed["closest_waypoint"], wp_speed["mean"], yerr=wp_speed["std"], alpha=0.7, capsize=1, color="green")
    ax2.set_xlabel("Waypoint")
    ax2.set_ylabel("Mean Speed")
    ax2.set_title("Speed per Waypoint")
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig


def summary(df: pd.DataFrame, actions: Optional[List[Action]] = None) -> dict:
    """
    Action space usage summary
    
    Args:
        df: SimTrace dataframe
        actions: List of actions (optional)
        
    Returns:
        dict: Summary statistics
    """
    action_counts = df["action"].value_counts().sort_index()
    total = len(df)
    
    if actions is None:
        actions = extract_action_space(df)
    
    # Most used and least used
    most_used = [(int(idx), int(cnt), cnt/total*100) for idx, cnt in action_counts.nlargest(5).items()]
    least_used = [(int(idx), int(cnt), cnt/total*100) for idx, cnt in action_counts.nsmallest(3).items()]
    
    return {
        "total_actions": len(actions),
        "total_steps": total,
        "most_used": most_used,
        "least_used": least_used,
        "avg_steering": df["steering_angle"].mean(),
        "avg_speed": df["speed"].mean(),
    }
