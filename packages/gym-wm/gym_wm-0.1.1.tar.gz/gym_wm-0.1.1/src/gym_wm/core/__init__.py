"""Core module for gym_wm package."""

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

__all__ = [
    "DatasetConfig",
    "get_supported_env_families",
    "list_environments",
    "detect_env_family",
    "validate_environment",
    "register_robotics_envs",
    "collect_dataset",
    "collect_dataset_from_config",
    "random_policy",
    "PDController",
    "create_pd_policy",
    "load_dataset",
    "list_datasets",
    "visualize_dataset",
    "plot_episode_frames",
    "plot_episode_trajectory",
    "plot_dataset_summary",
    "create_episode_video",
    "visualize_comparison",
]
