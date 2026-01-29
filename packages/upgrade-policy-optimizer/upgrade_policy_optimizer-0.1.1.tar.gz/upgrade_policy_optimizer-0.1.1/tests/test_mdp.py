"""Tests for MDP data structures."""

import numpy as np
import pytest

from upo import MDP


def test_mdp_creation_basic() -> None:
    """Test basic MDP creation with integer states."""
    # Simple 3-state MDP: 0 -> 1 -> 2 (terminal)
    num_states = 3
    terminal_states = {2}
    actions = {0: [0], 1: [0]}  # Only action 0 available in states 0 and 1

    costs = np.array(
        [
            [1.0, np.inf],  # State 0: action 0 costs 1, action 1 invalid
            [2.0, np.inf],  # State 1: action 0 costs 2, action 1 invalid
            [0.0, np.inf],  # State 2: terminal (costs don't matter)
        ]
    )

    transitions = np.zeros((3, 2, 3))
    transitions[0, 0, 1] = 1.0  # State 0, action 0 -> always go to state 1
    transitions[1, 0, 2] = 1.0  # State 1, action 0 -> always go to state 2
    transitions[2, 0, 2] = 1.0  # State 2, action 0 -> stay (terminal)

    mdp = MDP(
        num_states=num_states,
        terminal_states=terminal_states,
        actions=actions,
        costs=costs,
        transitions=transitions,
    )

    assert mdp.num_states == 3
    assert mdp.max_actions == 2
    assert mdp.is_terminal(2)
    assert not mdp.is_terminal(0)
    assert mdp.get_actions(0) == [0]
    assert mdp.get_cost(0, 0) == 1.0
    assert mdp.get_cost(1, 0) == 2.0


def test_mdp_from_dict() -> None:
    """Test MDP creation from dictionary specification."""
    mdp = MDP.from_dict(
        states=["start", "middle", "goal"],
        terminal_states=["goal"],
        transitions_dict={
            "start": {"try": {"middle": 0.7, "start": 0.3}},
            "middle": {"try": {"goal": 1.0}},
        },
        costs_dict={
            "start": {"try": 1.0},
            "middle": {"try": 2.0},
        },
    )

    assert mdp.num_states == 3
    assert len(mdp.terminal_states) == 1

    # Check state labels
    assert mdp.state_labels[0] == "start"
    assert mdp.state_labels[1] == "middle"
    assert mdp.state_labels[2] == "goal"

    # Check terminal state
    goal_idx = 2
    assert mdp.is_terminal(goal_idx)

    # Check actions and costs
    start_idx = 0
    middle_idx = 1
    assert len(mdp.get_actions(start_idx)) == 1
    assert mdp.get_cost(start_idx, 0) == 1.0
    assert mdp.get_cost(middle_idx, 0) == 2.0


def test_mdp_from_dict_multiple_actions() -> None:
    """Test MDP with multiple actions per state."""
    mdp = MDP.from_dict(
        states=["s0", "s1"],
        terminal_states=["s1"],
        transitions_dict={
            "s0": {
                "risky": {"s1": 0.8, "s0": 0.2},
                "safe": {"s1": 0.5, "s0": 0.5},
            },
        },
        costs_dict={
            "s0": {"risky": 1.0, "safe": 2.0},
        },
    )

    assert mdp.num_states == 2
    s0_idx = 0
    actions = mdp.get_actions(s0_idx)
    assert len(actions) == 2

    # Check that both actions exist and have different costs
    costs_set = {mdp.get_cost(s0_idx, a) for a in actions}
    assert costs_set == {1.0, 2.0}


def test_mdp_invalid_shapes() -> None:
    """Test that invalid array shapes raise errors."""
    with pytest.raises(ValueError, match="costs must be 2D"):
        MDP(
            num_states=2,
            terminal_states={1},
            actions={0: [0]},
            costs=np.array([1.0, 2.0]),  # 1D instead of 2D
            transitions=np.zeros((2, 1, 2)),
        )

    with pytest.raises(ValueError, match="transitions must be 3D"):
        MDP(
            num_states=2,
            terminal_states={1},
            actions={0: [0]},
            costs=np.array([[1.0]]),
            transitions=np.zeros((2, 2)),  # 2D instead of 3D
        )


def test_mdp_repr() -> None:
    """Test string representation."""
    mdp = MDP(
        num_states=3,
        terminal_states={2},
        actions={0: [0], 1: [0]},
        costs=np.ones((3, 1)),
        transitions=np.zeros((3, 1, 3)),
    )

    repr_str = repr(mdp)
    assert "MDP" in repr_str
    assert "states=3" in repr_str
    assert "terminal=1" in repr_str
