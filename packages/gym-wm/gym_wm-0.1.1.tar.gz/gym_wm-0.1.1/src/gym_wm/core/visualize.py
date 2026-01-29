"""
Dataset visualization utilities.

This module provides functions for visualizing collected datasets,
including frame grids, trajectory plots, and video generation.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, Any

import matplotlib.pyplot as plt
import numpy as np
from loguru import logger

if TYPE_CHECKING:
    from minari import MinariDataset


def load_dataset(dataset_name: str, data_path: Path | str | None = None) -> "MinariDataset":
    """Load a Minari dataset.

    Args:
        dataset_name: Name of the dataset (e.g., "pointmaze/random-v0").
        data_path: Path to the datasets directory. Defaults to ./data.

    Returns:
        Loaded Minari dataset object.

    Raises:
        FileNotFoundError: If dataset does not exist.

    Example:
        >>> dataset = load_dataset("pointmaze/random-v0")
        >>> print(f"Episodes: {dataset.total_episodes}")
    """
    import minari

    if data_path is None:
        data_path = Path.cwd() / "data"
    data_path = Path(data_path)

    os.environ["MINARI_DATASETS_PATH"] = str(data_path.absolute())

    try:
        return minari.load_dataset(dataset_name)
    except Exception as e:
        raise FileNotFoundError(
            f"Dataset '{dataset_name}' not found at '{data_path}'"
        ) from e


def list_datasets(data_path: Path | str | None = None) -> list[str]:
    """List all available datasets in the data directory.

    Args:
        data_path: Path to the datasets directory.

    Returns:
        List of dataset names.

    Example:
        >>> datasets = list_datasets()
        >>> for ds in datasets:
        ...     print(ds)
    """
    import minari

    if data_path is None:
        data_path = Path.cwd() / "data"
    data_path = Path(data_path)

    if not data_path.exists():
        return []

    os.environ["MINARI_DATASETS_PATH"] = str(data_path.absolute())

    return minari.list_local_datasets()


def visualize_dataset(
    dataset: "MinariDataset",
    episode_idx: int = 0,
    show: bool = True,
    save_dir: Path | str | None = None,
) -> tuple[plt.Figure, plt.Figure]:
    """Visualize a dataset episode with frames and trajectory.

    Args:
        dataset: Loaded Minari dataset.
        episode_idx: Index of the episode to visualize.
        show: Whether to display the plots.
        save_dir: Optional directory to save figures.

    Returns:
        Tuple of (frames_figure, trajectory_figure).

    Example:
        >>> dataset = load_dataset("pointmaze/random-v0")
        >>> fig1, fig2 = visualize_dataset(dataset, episode_idx=0)
    """
    fig1 = plot_episode_frames(dataset, episode_idx)
    fig2 = plot_episode_trajectory(dataset, episode_idx)

    if save_dir:
        save_dir = Path(save_dir)
        save_dir.mkdir(parents=True, exist_ok=True)
        fig1.savefig(save_dir / f"episode{episode_idx}_frames.png", dpi=200, bbox_inches="tight")
        fig2.savefig(
            save_dir / f"episode{episode_idx}_trajectory.png", dpi=200, bbox_inches="tight"
        )
        logger.info(f"Saved figures to {save_dir}")

    if show:
        plt.show()

    return fig1, fig2


def plot_episode_frames(
    dataset: "MinariDataset",
    episode_idx: int = 0,
    num_frames: int = 16,
    figsize: tuple[int, int] = (20, 10),
    dpi: int = 200,
    save_path: Path | str | None = None,
) -> plt.Figure:
    """Plot a grid of frames from an episode.

    Args:
        dataset: Loaded Minari dataset.
        episode_idx: Index of the episode to visualize.
        num_frames: Number of frames to show in the grid.
        figsize: Figure size (width, height).
        dpi: DPI for saved figure.
        save_path: Optional path to save the figure.

    Returns:
        Matplotlib figure object.

    Raises:
        ValueError: If dataset does not contain RGB images.
    """
    episode = dataset[episode_idx]
    images = episode.observations.get("image")

    if images is None:
        raise ValueError("Dataset does not contain RGB images")

    total_frames = len(images)
    indices = np.linspace(0, total_frames - 1, min(num_frames, total_frames), dtype=int)

    # Calculate grid dimensions
    cols = min(8, len(indices))
    rows = (len(indices) + cols - 1) // cols

    fig, axes = plt.subplots(rows, cols, figsize=figsize)
    if rows == 1 and cols == 1:
        axes = np.array([[axes]])
    elif rows == 1:
        axes = axes.reshape(1, -1)
    elif cols == 1:
        axes = axes.reshape(-1, 1)

    fig.suptitle(
        f"Episode {episode_idx} - {dataset.spec.dataset_id}\n" f"Total Steps: {total_frames - 1}",
        fontsize=14,
    )

    for idx, ax in enumerate(axes.flat):
        if idx < len(indices):
            frame_idx = indices[idx]
            ax.imshow(images[frame_idx])
            ax.set_title(f"t={frame_idx}", fontsize=10)
        ax.axis("off")

    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=dpi, bbox_inches="tight")
        logger.info(f"Saved figure to {save_path}")

    return fig


def plot_episode_trajectory(
    dataset: "MinariDataset",
    episode_idx: int = 0,
    figsize: tuple[int, int] = (16, 5),
    dpi: int = 200,
    save_path: Path | str | None = None,
) -> plt.Figure:
    """Plot trajectory data (rewards, actions) from an episode.

    Args:
        dataset: Loaded Minari dataset.
        episode_idx: Index of the episode to visualize.
        figsize: Figure size (width, height).
        dpi: DPI for saved figure.
        save_path: Optional path to save the figure.

    Returns:
        Matplotlib figure object.
    """
    episode = dataset[episode_idx]

    fig, axes = plt.subplots(1, 3, figsize=figsize)

    # Rewards over time
    rewards = episode.rewards
    axes[0].plot(rewards, "b-", linewidth=1)
    axes[0].fill_between(range(len(rewards)), rewards, alpha=0.3)
    axes[0].set_xlabel("Step")
    axes[0].set_ylabel("Reward")
    axes[0].set_title(f"Rewards (Total: {rewards.sum():.2f})")
    axes[0].grid(True, alpha=0.3)

    # Actions distribution
    actions = episode.actions
    if actions.ndim == 1:
        actions = actions.reshape(-1, 1)

    for i in range(min(actions.shape[1], 4)):  # Show up to 4 action dimensions
        axes[1].plot(actions[:, i], label=f"a[{i}]", alpha=0.7)
    axes[1].set_xlabel("Step")
    axes[1].set_ylabel("Action Value")
    axes[1].set_title("Actions Over Time")
    axes[1].legend(loc="upper right", fontsize=8)
    axes[1].grid(True, alpha=0.3)

    # Action histogram
    axes[2].hist(actions.flatten(), bins=30, edgecolor="black", alpha=0.7)
    axes[2].set_xlabel("Action Value")
    axes[2].set_ylabel("Frequency")
    axes[2].set_title("Action Distribution")
    axes[2].grid(True, alpha=0.3)

    plt.suptitle(f"Episode {episode_idx} Trajectory - {dataset.spec.dataset_id}", fontsize=14)
    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=dpi, bbox_inches="tight")
        logger.info(f"Saved figure to {save_path}")

    return fig


def plot_dataset_summary(
    dataset: "MinariDataset",
    figsize: tuple[int, int] = (18, 12),
    dpi: int = 200,
    save_path: Path | str | None = None,
) -> plt.Figure:
    """Plot summary statistics for the entire dataset.

    Args:
        dataset: Loaded Minari dataset.
        figsize: Figure size (width, height).
        dpi: DPI for saved figure.
        save_path: Optional path to save the figure.

    Returns:
        Matplotlib figure object.
    """
    # Collect statistics from all episodes
    episode_rewards: list[float] = []
    episode_lengths: list[int] = []
    all_rewards: list[float] = []

    for i in range(dataset.total_episodes):
        episode = dataset[i]
        rewards = episode.rewards
        episode_rewards.append(float(rewards.sum()))
        episode_lengths.append(len(rewards))
        all_rewards.extend(rewards.tolist())

    # Get sample images from different episodes
    sample_images: list[tuple[int, Any]] = []
    for i in range(min(4, dataset.total_episodes)):
        images = dataset[i].observations.get("image")
        if images is not None and len(images) > 0:
            mid_idx = len(images) // 2
            sample_images.append((i, images[mid_idx]))

    fig = plt.figure(figsize=figsize)
    gs = fig.add_gridspec(3, 4, hspace=0.35, wspace=0.3)

    # Sample images
    for idx, (ep_idx, img) in enumerate(sample_images):
        ax = fig.add_subplot(gs[0, idx])
        ax.imshow(img)
        ax.set_title(f"Episode {ep_idx}", fontsize=10)
        ax.axis("off")

    # Episode rewards
    ax1 = fig.add_subplot(gs[1, :2])
    ax1.bar(range(len(episode_rewards)), episode_rewards, color="steelblue", alpha=0.7)
    ax1.set_xlabel("Episode")
    ax1.set_ylabel("Total Reward")
    ax1.set_title("Episode Returns")
    ax1.axhline(
        np.mean(episode_rewards),
        color="red",
        linestyle="--",
        label=f"Mean: {np.mean(episode_rewards):.2f}",
    )
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Episode lengths
    ax2 = fig.add_subplot(gs[1, 2:])
    ax2.bar(range(len(episode_lengths)), episode_lengths, color="forestgreen", alpha=0.7)
    ax2.set_xlabel("Episode")
    ax2.set_ylabel("Steps")
    ax2.set_title("Episode Lengths")
    ax2.axhline(
        np.mean(episode_lengths),
        color="red",
        linestyle="--",
        label=f"Mean: {np.mean(episode_lengths):.1f}",
    )
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    # Reward distribution
    ax3 = fig.add_subplot(gs[2, :2])
    ax3.hist(all_rewards, bins=50, edgecolor="black", alpha=0.7, color="coral")
    ax3.set_xlabel("Reward")
    ax3.set_ylabel("Frequency")
    ax3.set_title("Step Reward Distribution")
    ax3.grid(True, alpha=0.3)

    # Text summary
    ax4 = fig.add_subplot(gs[2, 2:])
    ax4.axis("off")

    image_shape = sample_images[0][1].shape if sample_images else "N/A"

    summary_text = f"""
Dataset Summary
{'='*40}

Dataset ID:     {dataset.spec.dataset_id}
Total Episodes: {dataset.total_episodes}
Total Steps:    {dataset.total_steps}

Episode Statistics:
  Mean Return:    {np.mean(episode_rewards):>10.2f}
  Std Return:     {np.std(episode_rewards):>10.2f}
  Min Return:     {np.min(episode_rewards):>10.2f}
  Max Return:     {np.max(episode_rewards):>10.2f}

  Mean Length:    {np.mean(episode_lengths):>10.1f}
  Min Length:     {int(np.min(episode_lengths)):>10d}
  Max Length:     {int(np.max(episode_lengths)):>10d}

Image Shape:    {image_shape}
"""
    ax4.text(
        0.1,
        0.95,
        summary_text,
        transform=ax4.transAxes,
        fontsize=10,
        verticalalignment="top",
        fontfamily="monospace",
        bbox={"boxstyle": "round", "facecolor": "wheat", "alpha": 0.5},
    )

    plt.suptitle(f"Dataset Summary: {dataset.spec.dataset_id}", fontsize=16, fontweight="bold")

    if save_path:
        fig.savefig(save_path, dpi=dpi, bbox_inches="tight")
        logger.info(f"Saved figure to {save_path}")

    return fig


def create_episode_video(
    dataset: "MinariDataset",
    episode_idx: int = 0,
    save_path: Path | str | None = None,
    fps: int = 30,
) -> Path:
    """Create a video from episode frames.

    Args:
        dataset: Loaded Minari dataset.
        episode_idx: Index of the episode to visualize.
        save_path: Path to save the video. Defaults to dataset_episode.mp4.
        fps: Frames per second for the video.

    Returns:
        Path to the saved video.

    Raises:
        ImportError: If imageio is not installed.
        ValueError: If dataset does not contain RGB images.
    """
    try:
        import imageio.v3 as iio
    except ImportError as e:
        raise ImportError(
            "imageio is required for video creation. Install with: pip install imageio[ffmpeg]"
        ) from e

    episode = dataset[episode_idx]
    images = episode.observations.get("image")

    if images is None:
        raise ValueError("Dataset does not contain RGB images")

    if save_path is None:
        dataset_name = dataset.spec.dataset_id.replace("/", "_")
        save_path = Path(f"{dataset_name}_episode{episode_idx}.mp4")
    save_path = Path(save_path)

    # Create video
    iio.imwrite(str(save_path), images, fps=fps)

    logger.success(f"Saved video to {save_path}")
    return save_path


def visualize_comparison(
    dataset_names: list[str],
    data_path: Path | str | None = None,
    figsize: tuple[int, int] = (20, 8),
    dpi: int = 200,
    save_path: Path | str | None = None,
) -> plt.Figure:
    """Compare multiple datasets side by side.

    Args:
        dataset_names: List of dataset names to compare.
        data_path: Path to the datasets directory.
        figsize: Figure size (width, height).
        dpi: DPI for saved figure.
        save_path: Optional path to save the figure.

    Returns:
        Matplotlib figure object.
    """
    datasets = [load_dataset(name, data_path) for name in dataset_names]
    n_datasets = len(datasets)

    fig, axes = plt.subplots(2, n_datasets, figsize=figsize)
    if n_datasets == 1:
        axes = axes.reshape(-1, 1)

    for i, (ds, name) in enumerate(zip(datasets, dataset_names, strict=True)):
        # Sample image
        images = ds[0].observations.get("image")
        if images is not None:
            mid_idx = len(images) // 2
            axes[0, i].imshow(images[mid_idx])
        axes[0, i].set_title(name.split("/")[-1], fontsize=11)
        axes[0, i].axis("off")

        # Episode returns
        returns = [ds[j].rewards.sum() for j in range(ds.total_episodes)]
        axes[1, i].bar(range(len(returns)), returns, alpha=0.7)
        axes[1, i].set_xlabel("Episode")
        axes[1, i].set_ylabel("Return")
        axes[1, i].set_title(f"Mean: {np.mean(returns):.1f}")
        axes[1, i].grid(True, alpha=0.3)

    plt.suptitle("Dataset Comparison", fontsize=14, fontweight="bold")
    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=dpi, bbox_inches="tight")
        logger.info(f"Saved figure to {save_path}")

    return fig
