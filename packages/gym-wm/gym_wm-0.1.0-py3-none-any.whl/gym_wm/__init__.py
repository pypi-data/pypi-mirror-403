"""
Gym World Model Dataset Generator.

A toolbox for generating offline datasets from Gymnasium environments
for world-model research using Minari.

Example:
    >>> import gym_wm
    >>> # Generate a dataset with random policy
    >>> dataset = gym_wm.collect_dataset(
    ...     env_id="PointMaze_UMaze-v3",
    ...     num_episodes=100,
    ...     dataset_name="pointmaze/random-v0",
    ... )
    >>> print(f"Collected {dataset.total_episodes} episodes")

    >>> # List available environments
    >>> gym_wm.list_environments()

    >>> # Load and visualize a dataset
    >>> dataset = gym_wm.load_dataset("pointmaze/random-v0")
    >>> gym_wm.visualize_dataset(dataset)
"""

from gym_wm.core.config import DatasetConfig
from gym_wm.core.environments import (
    detect_env_family,
    get_supported_env_families,
    list_environments,
    register_robotics_envs,
    validate_environment,
)
from gym_wm.core.generator import collect_dataset, collect_dataset_from_config
from gym_wm.core.policies import PDController, create_pd_policy, random_policy
from gym_wm.core.visualize import (
    create_episode_video,
    list_datasets,
    load_dataset,
    plot_dataset_summary,
    plot_episode_frames,
    plot_episode_trajectory,
    visualize_comparison,
    visualize_dataset,
)
from gym_wm.utils.inspect import inspect_dataset

__version__ = "0.1.0"

__all__ = [
    # Version
    "__version__",
    # Config
    "DatasetConfig",
    # Environments
    "get_supported_env_families",
    "list_environments",
    "detect_env_family",
    "validate_environment",
    "register_robotics_envs",
    # Generator
    "collect_dataset",
    "collect_dataset_from_config",
    # Policies
    "random_policy",
    "PDController",
    "create_pd_policy",
    # Visualization
    "load_dataset",
    "list_datasets",
    "visualize_dataset",
    "plot_episode_frames",
    "plot_episode_trajectory",
    "plot_dataset_summary",
    "create_episode_video",
    "visualize_comparison",
    # Inspection
    "inspect_dataset",
]
