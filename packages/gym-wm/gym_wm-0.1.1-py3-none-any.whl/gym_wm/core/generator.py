"""
Dataset generator for collecting offline RL datasets.

This module provides the main data collection functionality using
Minari's DataCollector wrapper around Gymnasium environments.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

import gymnasium as gym
import numpy as np
from gymnasium import spaces
from loguru import logger

from gym_wm.core.config import DatasetConfig
from gym_wm.core.environments import register_robotics_envs, validate_environment
from gym_wm.core.policies import random_policy

if TYPE_CHECKING:
    from minari import MinariDataset


def _resize_image(image: np.ndarray, target_height: int, target_width: int) -> np.ndarray:
    """Resize an image to the target dimensions using PIL.

    Args:
        image: RGB image as numpy array (H, W, 3).
        target_height: Target height in pixels.
        target_width: Target width in pixels.

    Returns:
        Resized image as numpy array.
    """
    from PIL import Image

    if image.shape[0] == target_height and image.shape[1] == target_width:
        return image

    pil_image = Image.fromarray(image)
    pil_image = pil_image.resize((target_width, target_height), Image.Resampling.LANCZOS)
    return np.array(pil_image)


def create_rgb_step_callback_class(
    img_height: int = 84, img_width: int = 84
) -> type:
    """Create a StepDataCallback class with specified image dimensions.

    Args:
        img_height: Target height for RGB images.
        img_width: Target width for RGB images.

    Returns:
        A class that can be used as step_data_callback for DataCollector.
    """

    class RGBStepDataCallback:
        """Callback to capture RGB frames and augment observations."""

        def __call__(
            self,
            env: gym.Env[Any, Any],
            obs: Any,
            info: dict[str, Any],
            action: np.ndarray | None = None,
            rew: float | None = None,
            terminated: bool | None = None,
            truncated: bool | None = None,
        ) -> dict[str, Any]:
            """Process step data and add RGB image to observation."""
            # Capture RGB frame
            rgb_frame = env.render()

            # Resize if necessary
            if rgb_frame is not None:
                rgb_frame = _resize_image(rgb_frame, img_height, img_width)

                if isinstance(obs, dict):
                    obs = {**obs, "image": rgb_frame}
                else:
                    obs = {"state": obs, "image": rgb_frame}

            step_data: dict[str, Any] = {
                "observation": obs,
                "info": info,
            }

            # Add step-specific data (not present during reset)
            if action is not None:
                step_data["action"] = action
            if rew is not None:
                step_data["reward"] = rew
            if terminated is not None:
                step_data["terminated"] = terminated
            if truncated is not None:
                step_data["truncated"] = truncated

            return step_data

    return RGBStepDataCallback


# Default callback class for backwards compatibility
RGBStepDataCallback = create_rgb_step_callback_class(84, 84)


def create_extended_observation_space(
    original_space: spaces.Space[Any],
    img_height: int,
    img_width: int,
) -> spaces.Dict:
    """Create an extended observation space that includes RGB images.

    Args:
        original_space: Original observation space from the environment.
        img_height: Height of RGB images.
        img_width: Width of RGB images.

    Returns:
        Extended Dict space with image key added.

    Raises:
        TypeError: If original space type is not supported.
    """
    image_space = spaces.Box(
        low=0,
        high=255,
        shape=(img_height, img_width, 3),
        dtype=np.uint8,
    )

    if isinstance(original_space, spaces.Dict):
        # Already a Dict space (e.g., Fetch, Maze environments)
        return spaces.Dict({**original_space.spaces, "image": image_space})
    if isinstance(original_space, spaces.Box):
        # Simple Box space (e.g., Reacher, basic MuJoCo)
        return spaces.Dict({"state": original_space, "image": image_space})

    raise TypeError(
        f"Unsupported observation space type: {type(original_space)}. "
        f"Expected spaces.Dict or spaces.Box."
    )


def collect_dataset(
    env_id: str,
    num_episodes: int = 100,
    dataset_name: str | None = None,
    img_height: int = 84,
    img_width: int = 84,
    data_path: Path | str | None = None,
    author: str = "Unknown",
    author_email: str = "unknown@example.com",
    code_permalink: str = "https://github.com/unknown",
    policy: Callable[[gym.Env[Any, Any], Any], np.ndarray] | None = None,
    record_infos: bool = False,
    seed: int | None = None,
    env_kwargs: dict[str, Any] | None = None,
) -> "MinariDataset":
    """Collect an offline dataset with RGB observations from a Gymnasium environment.

    This function creates a Minari dataset containing:
        - RGB image observations (visual states)
        - Original observations (proprioceptive states)
        - Actions taken
        - Rewards received
        - Episode termination information

    Args:
        env_id: Gymnasium environment ID (e.g., "PointMaze_UMaze-v3").
        num_episodes: Number of episodes to collect.
        dataset_name: Name for the Minari dataset. Defaults to "{env_id}/random-v0".
        img_height: Height of RGB images in pixels.
        img_width: Width of RGB images in pixels.
        data_path: Path where dataset will be saved. Defaults to ./data.
        author: Author name for dataset metadata.
        author_email: Author email for dataset metadata.
        code_permalink: URL to the code used for collection.
        policy: Policy function(env, obs) -> action. Defaults to random policy.
        record_infos: Whether to record environment info dicts.
        seed: Random seed for reproducibility.
        env_kwargs: Additional keyword arguments for environment creation.

    Returns:
        The created Minari dataset object.

    Raises:
        ValueError: If environment is invalid or parameters are incorrect.
        ImportError: If required dependencies are not installed.

    Example:
        >>> import gym_wm
        >>> dataset = gym_wm.collect_dataset(
        ...     env_id="PointMaze_UMaze-v3",
        ...     num_episodes=10,
        ...     dataset_name="pointmaze/test-v0",
        ... )
        >>> print(f"Collected {dataset.total_episodes} episodes")
    """
    if data_path is not None:
        data_path = Path(data_path)

    config = DatasetConfig(
        env_id=env_id,
        num_episodes=num_episodes,
        dataset_name=dataset_name,
        img_height=img_height,
        img_width=img_width,
        data_path=data_path,
        author=author,
        author_email=author_email,
        code_permalink=code_permalink,
        policy=policy,
        record_infos=record_infos,
        seed=seed,
        env_kwargs=env_kwargs or {},
    )

    return collect_dataset_from_config(config)


def collect_dataset_from_config(config: DatasetConfig) -> "MinariDataset":
    """Collect dataset using a DatasetConfig object.

    Args:
        config: Dataset configuration object.

    Returns:
        The created Minari dataset object.

    Raises:
        ImportError: If Minari is not installed.
        ValueError: If configuration is invalid.
    """
    try:
        from minari import DataCollector
    except ImportError as e:
        raise ImportError(
            "Minari is required for dataset collection. "
            "Install it with: pip install minari"
        ) from e

    # Validate configuration
    config.validate()

    # Register robotics environments
    register_robotics_envs()

    # Validate environment
    validate_environment(config.env_id)

    # Set up data path
    assert config.data_path is not None  # Set in __post_init__
    config.data_path.mkdir(parents=True, exist_ok=True)
    os.environ["MINARI_DATASETS_PATH"] = str(config.data_path.absolute())

    logger.info(f"Starting dataset collection for '{config.env_id}'")
    logger.info(
        f"Episodes: {config.num_episodes}, Image size: {config.img_height}x{config.img_width}"
    )
    logger.info(f"Save path: {config.data_path / config.dataset_name}")

    # Create environment
    env = _create_environment(config)

    # Create extended observation space
    extended_obs_space = create_extended_observation_space(
        env.observation_space,
        config.img_height,
        config.img_width,
    )

    # Create callback class with target dimensions
    CallbackClass = create_rgb_step_callback_class(
        img_height=config.img_height,
        img_width=config.img_width,
    )

    # Wrap with DataCollector
    collector_env = DataCollector(
        env,
        record_infos=config.record_infos,
        step_data_callback=CallbackClass,
        observation_space=extended_obs_space,
    )

    # Set policy
    policy = config.policy or random_policy

    # Collect episodes
    _collect_episodes(collector_env, config, policy)

    # Create and save dataset
    dataset = collector_env.create_dataset(
        dataset_id=config.dataset_name,
        algorithm_name="Random-Policy" if config.policy is None else "Custom-Policy",
        author=config.author,
        author_email=config.author_email,
        code_permalink=config.code_permalink,
    )

    collector_env.close()

    logger.success(f"Dataset saved: {config.data_path / config.dataset_name}")
    logger.info(f"Total episodes: {dataset.total_episodes}, Total steps: {dataset.total_steps}")

    return dataset


def _create_environment(config: DatasetConfig) -> gym.Env[Any, Any]:
    """Create and configure the gymnasium environment.

    Args:
        config: Dataset configuration.

    Returns:
        Configured gymnasium environment.
    """
    env_kwargs = {
        "render_mode": "rgb_array",
        "width": config.img_width,
        "height": config.img_height,
        **config.env_kwargs,
    }

    try:
        env = gym.make(config.env_id, **env_kwargs)
    except TypeError:
        # Some environments don't support width/height arguments
        logger.warning(
            f"Environment '{config.env_id}' may not support custom render dimensions. "
            "Using default render size."
        )
        env_kwargs.pop("width", None)
        env_kwargs.pop("height", None)
        env = gym.make(config.env_id, **env_kwargs)

    return env


def _collect_episodes(
    env: gym.Env[Any, Any],
    config: DatasetConfig,
    policy: Callable[[gym.Env[Any, Any], Any], np.ndarray],
) -> None:
    """Collect episodes from the environment.

    Args:
        env: The wrapped gymnasium environment.
        config: Dataset configuration.
        policy: Policy function for action selection.
    """
    for episode_idx in range(config.num_episodes):
        seed = config.seed + episode_idx if config.seed is not None else episode_idx
        obs, info = env.reset(seed=seed)

        # Reset PD controller if applicable
        if hasattr(policy, "reset"):
            policy.reset()

        terminated = False
        truncated = False
        episode_steps = 0
        episode_reward = 0.0

        while not (terminated or truncated):
            action = policy(env, obs)
            obs, reward, terminated, truncated, info = env.step(action)
            episode_steps += 1
            episode_reward += float(reward)

        log_interval = max(1, config.num_episodes // 10)
        if (episode_idx + 1) % log_interval == 0:
            logger.info(
                f"Episode {episode_idx + 1}/{config.num_episodes} - "
                f"Steps: {episode_steps}, Reward: {episode_reward:.2f}"
            )
