"""Result data structures for MDP solver."""

from dataclasses import dataclass
from typing import Any, Optional

import numpy as np
import numpy.typing as npt


@dataclass
class MDPResult:
    """Result from solving an MDP using value iteration.

    Attributes:
        V: Value function mapping states to expected cost-to-go.
           Shape: (num_states,)
        policy: Optimal policy mapping states to action indices.
                Shape: (num_states,). For terminal states, value is -1.
        Q: Q-function (state-action values). Q[s,a] = expected cost if taking
           action a in state s then following optimal policy.
           Shape: (num_states, max_actions). Entries are np.inf for invalid actions.
        iterations: Number of value iteration steps performed.
        converged: Whether the algorithm converged within tolerance.
        residual: Final maximum absolute difference in value function.
        state_labels: Optional mapping from state indices to string labels.
        action_labels: Optional mapping from action indices to string labels per state.
    """

    V: npt.NDArray[np.float64]
    policy: npt.NDArray[np.int64]
    Q: npt.NDArray[np.float64]
    iterations: int
    converged: bool
    residual: float
    state_labels: Optional[dict[int, Any]] = None
    action_labels: Optional[dict[int, dict[int, Any]]] = None

    def get_value(self, state: Any) -> float:
        """Get the optimal value for a state.

        Args:
            state: State index (int) or state label (if state_labels provided).

        Returns:
            Optimal expected cost from this state.
        """
        idx = self._state_to_idx(state)
        return float(self.V[idx])

    def get_policy(self, state: Any) -> Any:
        """Get the optimal action for a state.

        Args:
            state: State index (int) or state label (if state_labels provided).

        Returns:
            Optimal action index or action label (if action_labels provided).
            Returns -1 for terminal states.
        """
        idx = self._state_to_idx(state)
        action_idx = int(self.policy[idx])

        if action_idx == -1:
            return -1

        if self.action_labels is not None and idx in self.action_labels:
            return self.action_labels[idx].get(action_idx, action_idx)

        return action_idx

    def get_q_value(self, state: Any, action: Any) -> float:
        """Get Q-value for a state-action pair.

        Args:
            state: State index or label.
            action: Action index or label.

        Returns:
            Q(state, action) value. Returns np.inf for invalid actions.
        """
        state_idx = self._state_to_idx(state)
        action_idx = self._action_to_idx(state_idx, action)
        return float(self.Q[state_idx, action_idx])

    def _state_to_idx(self, state: Any) -> int:
        """Convert state label to index."""
        if isinstance(state, int):
            return state

        if self.state_labels is None:
            raise ValueError("State labels not available; use integer indices")

        # Reverse lookup
        for idx, label in self.state_labels.items():
            if label == state:
                return idx

        raise ValueError(f"State {state} not found in state labels")

    def _action_to_idx(self, state_idx: int, action: Any) -> int:
        """Convert action label to index for a given state."""
        if isinstance(action, int):
            return action

        if self.action_labels is None or state_idx not in self.action_labels:
            raise ValueError("Action labels not available; use integer indices")

        # Reverse lookup
        for idx, label in self.action_labels[state_idx].items():
            if label == action:
                return idx

        raise ValueError(f"Action {action} not found for state {state_idx}")

    def __repr__(self) -> str:
        """String representation of result."""
        return (
            f"MDPResult(states={len(self.V)}, "
            f"iterations={self.iterations}, "
            f"converged={self.converged}, "
            f"residual={self.residual:.2e})"
        )
