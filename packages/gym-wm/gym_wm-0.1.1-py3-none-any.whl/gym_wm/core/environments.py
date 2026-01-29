"""
Environment utilities for Gymnasium and Gymnasium-Robotics.

This module provides utilities for working with supported environments,
including environment detection, validation, and listing.
"""

from __future__ import annotations

import gymnasium as gym
from loguru import logger


def get_supported_env_families() -> dict[str, list[str]]:
    """Return dictionary of supported environment families with examples.

    Returns:
        Dictionary mapping family names to example environment IDs.

    Example:
        >>> families = get_supported_env_families()
        >>> print(families.keys())
        dict_keys(['mujoco', 'fetch', 'maze', 'hand', 'classic_control'])
    """
    return {
        "mujoco": [
            "Reacher-v5",
            "Ant-v5",
            "HalfCheetah-v5",
            "Hopper-v5",
            "Walker2d-v5",
            "Humanoid-v5",
            "Swimmer-v5",
            "Pusher-v5",
            "InvertedPendulum-v5",
            "InvertedDoublePendulum-v5",
        ],
        "fetch": [
            "FetchReach-v4",
            "FetchPush-v3",
            "FetchSlide-v3",
            "FetchPickAndPlace-v3",
        ],
        "maze": [
            "PointMaze_UMaze-v3",
            "PointMaze_Medium-v3",
            "PointMaze_Large-v3",
            "AntMaze_UMaze-v5",
            "AntMaze_Medium-v5",
            "AntMaze_Large-v5",
        ],
        "hand": [
            "AdroitHandDoor-v1",
            "AdroitHandHammer-v1",
            "AdroitHandPen-v1",
            "AdroitHandRelocate-v1",
        ],
        "classic_control": [
            "CartPole-v1",
            "Pendulum-v1",
            "Acrobot-v1",
            "MountainCar-v0",
            "MountainCarContinuous-v0",
        ],
    }


def list_environments() -> dict[str, list[str]]:
    """List all supported environment families and their environments.

    This is an alias for get_supported_env_families() for convenience.

    Returns:
        Dictionary mapping family names to environment IDs.

    Example:
        >>> import gym_wm
        >>> envs = gym_wm.list_environments()
        >>> for family, env_list in envs.items():
        ...     print(f"{family}: {len(env_list)} environments")
    """
    return get_supported_env_families()


def detect_env_family(env_id: str) -> str:
    """Detect the environment family from the environment ID.

    Args:
        env_id: Gymnasium environment ID.

    Returns:
        Environment family name (mujoco, fetch, maze, hand, classic_control, or unknown).

    Example:
        >>> detect_env_family("FetchReach-v4")
        'fetch'
        >>> detect_env_family("Ant-v5")
        'mujoco'
    """
    env_id_lower = env_id.lower()

    if "fetch" in env_id_lower:
        return "fetch"
    if "maze" in env_id_lower:
        return "maze"
    if "adroit" in env_id_lower or "hand" in env_id_lower:
        return "hand"

    # Classic control environments
    classic_envs = ["cartpole", "pendulum", "acrobot", "mountaincar"]
    for classic_env in classic_envs:
        if classic_env in env_id_lower:
            return "classic_control"

    # MuJoCo environments
    mujoco_envs = [
        "reacher",
        "ant",
        "halfcheetah",
        "hopper",
        "walker",
        "humanoid",
        "swimmer",
        "pusher",
    ]
    for mj_env in mujoco_envs:
        if mj_env in env_id_lower:
            return "mujoco"

    return "unknown"


def validate_environment(env_id: str) -> bool:
    """Validate that the environment exists and can be created.

    Args:
        env_id: Gymnasium environment ID.

    Returns:
        True if environment is valid.

    Raises:
        ValueError: If environment does not exist.

    Example:
        >>> validate_environment("PointMaze_UMaze-v3")
        True
    """
    try:
        gym.spec(env_id)
    except gym.error.NameNotFound as e:
        supported = get_supported_env_families()
        examples = [env for family in supported.values() for env in family[:2]]
        raise ValueError(
            f"Environment '{env_id}' not found. "
            f"Example supported environments: {examples}"
        ) from e

    # Check if environment is from an unknown family
    env_family = detect_env_family(env_id)
    if env_family == "unknown":
        logger.warning(
            f"Environment '{env_id}' is from an unknown family. "
            "RGB rendering may not work as expected."
        )

    return True


def register_robotics_envs() -> None:
    """Register gymnasium-robotics environments if available.

    This function safely imports and registers gymnasium-robotics
    environments. If the package is not installed, it logs a debug
    message and continues without error.

    Example:
        >>> register_robotics_envs()
    """
    try:
        import gymnasium_robotics

        gym.register_envs(gymnasium_robotics)
        logger.debug("Registered gymnasium-robotics environments")
    except ImportError:
        logger.debug("gymnasium-robotics not installed, skipping registration")


def get_env_info(env_id: str) -> dict[str, str | int | tuple[int, ...]]:
    """Get information about an environment.

    Args:
        env_id: Gymnasium environment ID.

    Returns:
        Dictionary with environment information including:
            - family: Environment family name
            - action_space_type: Type of action space
            - action_space_shape: Shape of action space
            - observation_space_type: Type of observation space

    Example:
        >>> info = get_env_info("Ant-v5")
        >>> print(info["family"])
        'mujoco'
    """
    register_robotics_envs()
    validate_environment(env_id)

    env = gym.make(env_id)
    try:
        info: dict[str, str | int | tuple[int, ...]] = {
            "family": detect_env_family(env_id),
            "action_space_type": type(env.action_space).__name__,
            "observation_space_type": type(env.observation_space).__name__,
        }

        if hasattr(env.action_space, "shape"):
            info["action_space_shape"] = env.action_space.shape

        if hasattr(env.observation_space, "shape"):
            info["observation_space_shape"] = env.observation_space.shape

        return info
    finally:
        env.close()
