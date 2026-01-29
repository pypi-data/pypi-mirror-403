"""
Policy implementations for data collection.

This module provides policy functions for action selection during
dataset collection, including random policies and PD controllers.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

import numpy as np

if TYPE_CHECKING:
    import gymnasium as gym


class PolicyProtocol(Protocol):
    """Protocol for policy functions."""

    def __call__(self, env: "gym.Env[Any, Any]", obs: Any) -> np.ndarray:
        """Select an action given the environment and observation.

        Args:
            env: The gymnasium environment.
            obs: Current observation from the environment.

        Returns:
            Action to take in the environment.
        """
        ...


def random_policy(env: "gym.Env[Any, Any]", obs: Any) -> np.ndarray:
    """Sample a random action from the environment's action space.

    Args:
        env: The gymnasium environment.
        obs: Current observation (unused for random policy).

    Returns:
        Randomly sampled action.

    Example:
        >>> action = random_policy(env, obs)
    """
    return env.action_space.sample()


class PDController:
    """Proportional-Derivative (PD) controller for goal-reaching tasks.

    This controller computes actions to move towards a goal position using
    proportional and derivative terms. Suitable for environments with
    goal-conditioned observations (e.g., Fetch, Maze environments).

    Attributes:
        kp: Proportional gain.
        kd: Derivative gain.
        action_scale: Scale factor for output actions.
        noise_scale: Scale of random noise added for exploration.
        prev_error: Previous error for derivative computation.

    Example:
        >>> controller = PDController(kp=2.0, kd=0.2)
        >>> dataset = collect_dataset(
        ...     env_id="FetchReach-v4",
        ...     policy=controller,
        ... )
    """

    def __init__(
        self,
        kp: float = 1.0,
        kd: float = 0.1,
        action_scale: float = 1.0,
        noise_scale: float = 0.1,
    ) -> None:
        """Initialize the PD controller.

        Args:
            kp: Proportional gain (higher = more aggressive).
            kd: Derivative gain (higher = more damping).
            action_scale: Scale factor for output actions.
            noise_scale: Scale of random noise added for exploration.
        """
        self.kp = kp
        self.kd = kd
        self.action_scale = action_scale
        self.noise_scale = noise_scale
        self.prev_error: np.ndarray | None = None

    def reset(self) -> None:
        """Reset controller state for new episode."""
        self.prev_error = None

    def __call__(self, env: "gym.Env[Any, Any]", obs: Any) -> np.ndarray:
        """Compute action using PD control.

        Args:
            env: The gymnasium environment.
            obs: Current observation (dict with goal info or array).

        Returns:
            Computed action clipped to action space bounds.
        """
        action_space = env.action_space
        action_dim = action_space.shape[0]

        # Extract position and goal from observation
        current_pos, goal_pos = self._extract_positions(obs, action_dim)

        if current_pos is None or goal_pos is None:
            # Fallback to random if we can't extract positions
            return action_space.sample()

        # Compute error (goal - current position)
        error = goal_pos - current_pos

        # Proportional term
        p_term = self.kp * error

        # Derivative term
        if self.prev_error is not None:
            d_term = self.kd * (error - self.prev_error)
        else:
            d_term = np.zeros_like(error)

        self.prev_error = error.copy()

        # Compute action from PD control
        pd_action = self.action_scale * (p_term + d_term)

        # Create full action vector
        action = np.zeros(action_dim, dtype=np.float32)

        # Fill with PD action (for position control dimensions)
        control_dims = min(len(pd_action), action_dim)
        action[:control_dims] = pd_action[:control_dims]

        # Add exploration noise
        if self.noise_scale > 0:
            noise = np.random.randn(action_dim) * self.noise_scale
            action = action + noise

        # Clip to action space bounds
        action = np.clip(action, action_space.low, action_space.high)

        return action.astype(action_space.dtype)

    def _extract_positions(
        self, obs: Any, action_dim: int
    ) -> tuple[np.ndarray | None, np.ndarray | None]:
        """Extract current and goal positions from observation.

        Args:
            obs: Observation from environment.
            action_dim: Dimension of action space.

        Returns:
            Tuple of (current_position, goal_position) or (None, None).
        """
        if isinstance(obs, dict):
            # Goal-conditioned environments (Fetch, Maze)
            if "achieved_goal" in obs and "desired_goal" in obs:
                return obs["achieved_goal"], obs["desired_goal"]
            if "observation" in obs and "desired_goal" in obs:
                # Use first few dims of observation as position
                obs_flat = obs["observation"]
                goal = obs["desired_goal"]
                return obs_flat[: len(goal)], goal

        # For simple environments, try to use first few dimensions
        if isinstance(obs, np.ndarray):
            # Assume first action_dim elements are controllable
            n = min(action_dim, len(obs) // 2)
            return obs[:n], np.zeros(n)  # Move towards origin

        return None, None


def create_pd_policy(
    kp: float = 1.0,
    kd: float = 0.1,
    action_scale: float = 1.0,
    noise_scale: float = 0.1,
) -> PDController:
    """Create a PD controller policy.

    Args:
        kp: Proportional gain.
        kd: Derivative gain.
        action_scale: Scale factor for output actions.
        noise_scale: Scale of random noise for exploration.

    Returns:
        Configured PDController instance.

    Example:
        >>> policy = create_pd_policy(kp=2.0, kd=0.2)
        >>> dataset = collect_dataset(
        ...     env_id="FetchReach-v4",
        ...     policy=policy,
        ... )
    """
    return PDController(kp=kp, kd=kd, action_scale=action_scale, noise_scale=noise_scale)
