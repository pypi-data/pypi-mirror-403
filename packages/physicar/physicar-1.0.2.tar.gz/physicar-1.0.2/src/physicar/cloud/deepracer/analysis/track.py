"""
Track utility module
"""
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Optional, Tuple
from dataclasses import dataclass
from functools import lru_cache

from .config import ROUTES_PATH


@dataclass
class Track:
    """Track data class"""
    name: str
    center_line: np.ndarray
    inner_border: np.ndarray
    outer_border: np.ndarray
    
    @property
    def waypoints(self) -> np.ndarray:
        """Center line waypoints (alias for center_line)"""
        return self.center_line
    
    @property
    def length(self) -> float:
        """Track length (m)"""
        diffs = np.diff(self.center_line, axis=0)
        distances = np.sqrt(np.sum(diffs ** 2, axis=1))
        return float(np.sum(distances))
    
    @property
    def width(self) -> float:
        """Track average width (m)"""
        inner_to_outer = self.outer_border - self.inner_border
        widths = np.sqrt(np.sum(inner_to_outer ** 2, axis=1))
        return float(np.mean(widths))


def list_tracks() -> list[str]:
    """
    List available tracks
    
    Returns:
        list[str]: List of track names (without .npy extension)
    """
    if not ROUTES_PATH.exists():
        return []
    
    return sorted([
        f.stem for f in ROUTES_PATH.glob("*.npy")
    ])


@lru_cache(maxsize=32)
def load(track_name: str) -> Track:
    """
    Load track data
    
    Args:
        track_name: Track name (without .npy extension)
        
    Returns:
        Track: Track data object
    """
    # Handle .npy extension
    if track_name.endswith(".npy"):
        track_name = track_name[:-4]
    
    npy_path = ROUTES_PATH / f"{track_name}.npy"
    
    if not npy_path.exists():
        # Find similar tracks
        available = list_tracks()
        similar = [t for t in available if track_name.lower() in t.lower()]
        if similar:
            raise FileNotFoundError(
                f"Track '{track_name}' not found. Similar tracks: {similar[:5]}"
            )
        raise FileNotFoundError(f"Track '{track_name}' not found")
    
    data = np.load(npy_path)
    
    # npy file format:
    # - 2D (N, 6): [center_x, center_y, inner_x, inner_y, outer_x, outer_y]
    # - 3D (3, N, 2): [center, inner, outer] each with (x, y)
    if len(data.shape) == 2:
        if data.shape[1] >= 6:
            # (N, 6) format: center, inner, outer order
            center_line = data[:, 0:2]
            inner_border = data[:, 2:4]
            outer_border = data[:, 4:6]
        else:
            # (N, 2) format: only center
            center_line = data[:, :2]
            inner_border = center_line.copy()
            outer_border = center_line.copy()
    else:
        # 3D data: (3, N, 2) format
        center_line = data[0][:, :2] if data.shape[2] >= 2 else data[0]
        inner_border = data[1][:, :2] if len(data) > 1 else center_line.copy()
        outer_border = data[2][:, :2] if len(data) > 2 else center_line.copy()
    
    return Track(
        name=track_name,
        center_line=center_line,
        inner_border=inner_border,
        outer_border=outer_border,
    )


def plot(
    track: Track,
    figsize: tuple = (12, 8),
    show_waypoints: bool = True,
    waypoint_interval: int = 10,
) -> plt.Figure:
    """
    Visualize track
    
    Args:
        track: Track object
        figsize: Figure size
        show_waypoints: Show waypoint numbers
        waypoint_interval: Waypoint number display interval
        
    Returns:
        plt.Figure: matplotlib Figure object
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    # Draw track borders
    ax.plot(track.inner_border[:, 0], track.inner_border[:, 1], "b-", linewidth=2, label="Inner")
    ax.plot(track.outer_border[:, 0], track.outer_border[:, 1], "b-", linewidth=2, label="Outer")
    ax.plot(track.center_line[:, 0], track.center_line[:, 1], "g--", linewidth=1, alpha=0.5, label="Center")
    
    # Mark start point
    ax.scatter(track.center_line[0, 0], track.center_line[0, 1], c="red", s=100, marker="o", zorder=5, label="Start")
    
    # Show waypoint numbers
    if show_waypoints:
        for i in range(0, len(track.center_line), waypoint_interval):
            ax.annotate(
                str(i),
                (track.center_line[i, 0], track.center_line[i, 1]),
                fontsize=8,
                alpha=0.7,
            )
    
    ax.set_aspect("equal")
    ax.set_title(f"Track: {track.name} (Length: {track.length:.1f}m, Width: {track.width:.2f}m)")
    ax.set_xlabel("X (m)")
    ax.set_ylabel("Y (m)")
    ax.legend(loc="upper right")
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig


def get_closest_waypoint(
    track: Track,
    x: float,
    y: float,
) -> int:
    """
    Get closest waypoint index
    
    Args:
        track: Track object
        x: x coordinate
        y: y coordinate
        
    Returns:
        int: Closest waypoint index
    """
    distances = np.sqrt(
        (track.center_line[:, 0] - x) ** 2 +
        (track.center_line[:, 1] - y) ** 2
    )
    return int(np.argmin(distances))


def get_track_width_at(track: Track, waypoint_idx: int) -> float:
    """
    Get track width at specific waypoint
    
    Args:
        track: Track object
        waypoint_idx: Waypoint index
        
    Returns:
        float: Track width (m)
    """
    inner = track.inner_border[waypoint_idx]
    outer = track.outer_border[waypoint_idx]
    return float(np.sqrt(np.sum((outer - inner) ** 2)))


def get_heading_at(track: Track, waypoint_idx: int) -> float:
    """
    Get heading at specific waypoint (radians)
    
    Args:
        track: Track object
        waypoint_idx: Waypoint index
        
    Returns:
        float: Heading (radians, -pi to pi)
    """
    n = len(track.center_line)
    next_idx = (waypoint_idx + 1) % n
    
    dx = track.center_line[next_idx, 0] - track.center_line[waypoint_idx, 0]
    dy = track.center_line[next_idx, 1] - track.center_line[waypoint_idx, 1]
    
    return float(np.arctan2(dy, dx))
