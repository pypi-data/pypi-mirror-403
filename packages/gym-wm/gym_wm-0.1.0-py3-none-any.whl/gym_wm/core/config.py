"""
Configuration classes for dataset collection.

This module provides dataclass-based configuration objects for
controlling dataset collection parameters.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

import numpy as np

if TYPE_CHECKING:
    import gymnasium as gym


@dataclass(slots=True)
class DatasetConfig:
    """Configuration for dataset collection.

    Attributes:
        env_id: Gymnasium environment ID (e.g., "PointMaze_UMaze-v3").
        num_episodes: Number of episodes to collect.
        dataset_name: Name for the Minari dataset (e.g., "pointmaze/random-v0").
        img_height: Height of RGB images in pixels.
        img_width: Width of RGB images in pixels.
        data_path: Path where dataset will be saved.
        author: Author name for dataset metadata.
        author_email: Author email for dataset metadata.
        code_permalink: URL to the code used for collection.
        policy: Policy function for action selection. Defaults to random.
        record_infos: Whether to record environment info dicts.
        seed: Random seed for reproducibility.
        env_kwargs: Additional keyword arguments for environment creation.

    Example:
        >>> config = DatasetConfig(
        ...     env_id="PointMaze_UMaze-v3",
        ...     num_episodes=100,
        ...     dataset_name="pointmaze/random-v0",
        ... )
    """

    env_id: str
    num_episodes: int = 100
    dataset_name: str | None = None
    img_height: int = 84
    img_width: int = 84
    data_path: Path | None = None
    author: str = "Unknown"
    author_email: str = "unknown@example.com"
    code_permalink: str = "https://github.com/unknown"
    policy: Callable[["gym.Env[Any, Any]", Any], np.ndarray] | None = None
    record_infos: bool = False
    seed: int | None = None
    env_kwargs: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate and set defaults after initialization."""
        if self.data_path is None:
            # Default to project_root/data
            self.data_path = Path.cwd() / "data"

        if isinstance(self.data_path, str):
            self.data_path = Path(self.data_path)

        if self.dataset_name is None:
            # Generate default dataset name from env_id
            env_base = self.env_id.lower().replace("-", "_").replace("_", "-")
            self.dataset_name = f"{env_base}/random-v0"

    def validate(self) -> None:
        """Validate configuration parameters.

        Raises:
            ValueError: If any parameter is invalid.
        """
        from loguru import logger

        if not self.env_id:
            raise ValueError("env_id cannot be empty")

        if self.num_episodes <= 0:
            raise ValueError(f"num_episodes must be positive, got {self.num_episodes}")

        if self.img_height <= 0 or self.img_width <= 0:
            raise ValueError(
                f"Image dimensions must be positive, got {self.img_height}x{self.img_width}"
            )

        if self.img_height > 1024 or self.img_width > 1024:
            logger.warning(
                f"Large image dimensions ({self.img_height}x{self.img_width}) "
                "may cause memory issues"
            )
