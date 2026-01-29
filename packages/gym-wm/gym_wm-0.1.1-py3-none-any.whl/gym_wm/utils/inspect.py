"""
Dataset inspection utilities.

This module provides utilities for inspecting and summarizing
collected datasets.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any


def inspect_dataset(
    dataset_name: str,
    data_path: Path | str | None = None,
) -> dict[str, Any]:
    """Inspect a collected dataset and return summary information.

    Args:
        dataset_name: Name of the dataset to inspect.
        data_path: Path to the Minari datasets directory.

    Returns:
        Dictionary containing dataset summary information including:
            - dataset_id: The dataset identifier
            - total_episodes: Number of episodes in the dataset
            - total_steps: Total number of steps across all episodes
            - observation_keys: Keys in the observation dictionary
            - has_images: Whether the dataset contains RGB images
            - image_shape: Shape of images (if present)
            - image_dtype: Data type of images (if present)
            - num_frames_episode_0: Number of frames in first episode (if images present)

    Raises:
        FileNotFoundError: If dataset does not exist.

    Example:
        >>> info = inspect_dataset("pointmaze/random-v0")
        >>> print(f"Episodes: {info['total_episodes']}")
        >>> print(f"Has images: {info['has_images']}")
    """
    import minari

    if data_path is None:
        data_path = Path.cwd() / "data"
    data_path = Path(data_path)

    os.environ["MINARI_DATASETS_PATH"] = str(data_path.absolute())

    try:
        dataset = minari.load_dataset(dataset_name)
    except Exception as e:
        raise FileNotFoundError(
            f"Dataset '{dataset_name}' not found at '{data_path}'"
        ) from e

    # Get first episode to inspect structure
    episode = dataset[0]

    info: dict[str, Any] = {
        "dataset_id": dataset.spec.dataset_id,
        "total_episodes": dataset.total_episodes,
        "total_steps": dataset.total_steps,
        "observation_keys": list(episode.observations.keys()),
        "has_images": "image" in episode.observations,
    }

    if info["has_images"]:
        images = episode.observations["image"]
        info["image_shape"] = images[0].shape
        info["image_dtype"] = str(images.dtype)
        info["num_frames_episode_0"] = len(images)

    return info
