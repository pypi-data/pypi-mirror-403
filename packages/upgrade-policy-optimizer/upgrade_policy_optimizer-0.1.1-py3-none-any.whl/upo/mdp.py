"""Core MDP data structures and utilities."""

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import numpy.typing as npt


@dataclass
class MDP:
    """Markov Decision Process definition.

    An MDP is defined by:
    - A finite set of states S (indexed 0..num_states-1)
    - A set of terminal/absorbing states T ⊂ S
    - For each non-terminal state s, a set of available actions A(s)
    - For each (state, action) pair, an immediate cost C(s,a) >= 0
    - For each (state, action) pair, transition probabilities P(s'|s,a)

    The goal is to minimize expected total cost to reach a terminal state.

    Attributes:
        num_states: Total number of states.
        terminal_states: Set of terminal state indices.
        actions: Dictionary mapping state index to list of available action indices.
        costs: 2D array of shape (num_states, max_actions) containing C(s,a).
               Use np.inf for invalid (state, action) pairs.
        transitions: 3D array of shape (num_states, max_actions, num_states)
                    containing P(s'|s,a). transitions[s,a,s'] is the probability
                    of transitioning to s' when taking action a in state s.
        state_labels: Optional dictionary mapping state indices to readable labels.
        action_labels: Optional nested dict mapping state index -> action index -> label.
    """

    num_states: int
    terminal_states: set[int]
    actions: dict[int, list[int]]
    costs: npt.NDArray[np.float64]
    transitions: npt.NDArray[np.float64]
    state_labels: dict[int, Any] = field(default_factory=dict)
    action_labels: dict[int, dict[int, Any]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate the MDP structure."""
        # Ensure arrays are correct type
        self.costs = np.asarray(self.costs, dtype=np.float64)
        self.transitions = np.asarray(self.transitions, dtype=np.float64)

        # Check shapes
        if self.costs.ndim != 2:
            raise ValueError(f"costs must be 2D, got shape {self.costs.shape}")

        if self.transitions.ndim != 3:
            raise ValueError(f"transitions must be 3D, got shape {self.transitions.shape}")

        if self.costs.shape[0] != self.num_states:
            raise ValueError(
                f"costs first dimension {self.costs.shape[0]} "
                f"must match num_states {self.num_states}"
            )

        if self.transitions.shape != (self.num_states, self.costs.shape[1], self.num_states):
            raise ValueError(
                f"transitions shape {self.transitions.shape} must be "
                f"(num_states={self.num_states}, max_actions={self.costs.shape[1]}, "
                f"num_states={self.num_states})"
            )

    @property
    def max_actions(self) -> int:
        """Maximum number of actions across all states."""
        return int(self.costs.shape[1])

    def is_terminal(self, state: int) -> bool:
        """Check if a state is terminal."""
        return state in self.terminal_states

    def get_actions(self, state: int) -> list[int]:
        """Get available actions for a state."""
        return self.actions.get(state, [])

    def get_cost(self, state: int, action: int) -> float:
        """Get immediate cost for taking an action in a state."""
        return float(self.costs[state, action])

    def get_transition_probs(self, state: int, action: int) -> npt.NDArray[np.float64]:
        """Get transition probability distribution for (state, action)."""
        return self.transitions[state, action, :]

    @classmethod
    def from_dict(
        cls,
        states: list[Any],
        terminal_states: list[Any],
        transitions_dict: dict[Any, dict[Any, dict[Any, float]]],
        costs_dict: dict[Any, dict[Any, float]],
    ) -> "MDP":
        """Construct MDP from dictionary-based specification.

        This convenience constructor allows defining MDPs with arbitrary state
        and action labels, which are internally mapped to integer indices.

        Args:
            states: List of state labels (can be any hashable type).
            terminal_states: List of terminal state labels.
            transitions_dict: Nested dict {state: {action: {next_state: prob}}}.
            costs_dict: Nested dict {state: {action: cost}}.

        Returns:
            MDP with internal integer indexing and label mappings preserved.

        Example:
            >>> mdp = MDP.from_dict(
            ...     states=["s0", "s1", "s2"],
            ...     terminal_states=["s2"],
            ...     transitions_dict={
            ...         "s0": {"a0": {"s1": 0.8, "s0": 0.2}},
            ...         "s1": {"a0": {"s2": 1.0}},
            ...     },
            ...     costs_dict={
            ...         "s0": {"a0": 1.0},
            ...         "s1": {"a0": 2.0},
            ...     }
            ... )
        """
        # Create state index mapping
        state_to_idx = {s: i for i, s in enumerate(states)}
        idx_to_state = {i: s for i, s in enumerate(states)}
        num_states = len(states)

        # Convert terminal states to indices
        terminal_indices = {state_to_idx[s] for s in terminal_states}

        # Collect all unique actions and create action mappings per state
        state_actions: dict[int, list[Any]] = {}
        action_to_idx: dict[int, dict[Any, int]] = {}
        idx_to_action: dict[int, dict[int, Any]] = {}
        max_actions = 0

        for state_label, actions_dict in transitions_dict.items():
            state_idx = state_to_idx[state_label]
            actions_list = list(actions_dict.keys())
            state_actions[state_idx] = actions_list

            action_to_idx[state_idx] = {a: i for i, a in enumerate(actions_list)}
            idx_to_action[state_idx] = {i: a for i, a in enumerate(actions_list)}
            max_actions = max(max_actions, len(actions_list))

        # Initialize cost and transition arrays with inf/zeros
        costs: npt.NDArray[np.float64] = np.full(
            (num_states, max_actions), np.inf, dtype=np.float64
        )
        transitions: npt.NDArray[np.float64] = np.zeros(
            (num_states, max_actions, num_states), dtype=np.float64
        )

        # Fill in costs and transitions
        for state_label, actions_dict in transitions_dict.items():
            state_idx = state_to_idx[state_label]

            for action_label, next_states_dict in actions_dict.items():
                action_idx = action_to_idx[state_idx][action_label]

                # Set cost
                cost = costs_dict[state_label][action_label]
                costs[state_idx, action_idx] = cost

                # Set transition probabilities
                for next_state_label, prob in next_states_dict.items():
                    next_state_idx = state_to_idx[next_state_label]
                    transitions[state_idx, action_idx, next_state_idx] = prob

        # Convert action mappings to integer lists
        actions_int: dict[int, list[int]] = {
            state_idx: list(range(len(actions_list)))
            for state_idx, actions_list in state_actions.items()
        }

        return cls(
            num_states=num_states,
            terminal_states=terminal_indices,
            actions=actions_int,
            costs=costs,
            transitions=transitions,
            state_labels=idx_to_state,
            action_labels=idx_to_action,
        )

    def __repr__(self) -> str:
        """String representation of MDP."""
        return (
            f"MDP(states={self.num_states}, "
            f"terminal={len(self.terminal_states)}, "
            f"max_actions={self.max_actions})"
        )
