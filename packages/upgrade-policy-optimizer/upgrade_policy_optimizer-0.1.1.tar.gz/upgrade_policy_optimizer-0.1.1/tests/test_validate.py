"""Tests for validation utilities."""

import numpy as np
import pytest

from upo import MDP, ValidationError, validate_mdp


def test_validate_valid_mdp() -> None:
    """Test that a valid MDP passes validation."""
    mdp = MDP.from_dict(
        states=["s0", "s1"],
        terminal_states=["s1"],
        transitions_dict={
            "s0": {"a0": {"s1": 0.6, "s0": 0.4}},
        },
        costs_dict={
            "s0": {"a0": 1.0},
        },
    )

    # Should not raise
    validate_mdp(mdp)


def test_validate_probabilities_not_sum_to_one() -> None:
    """Test that invalid probability sums are caught."""
    # Manually create MDP with bad probabilities
    transitions = np.zeros((2, 1, 2))
    transitions[0, 0, 0] = 0.3
    transitions[0, 0, 1] = 0.5  # Sum = 0.8, not 1.0

    mdp = MDP(
        num_states=2,
        terminal_states={1},
        actions={0: [0]},
        costs=np.array([[1.0], [0.0]]),
        transitions=transitions,
    )

    with pytest.raises(ValidationError, match="transition probabilities sum"):
        validate_mdp(mdp)


def test_validate_negative_probabilities() -> None:
    """Test that negative probabilities are caught."""
    transitions = np.zeros((2, 1, 2))
    transitions[0, 0, 0] = -0.2
    transitions[0, 0, 1] = 1.2

    mdp = MDP(
        num_states=2,
        terminal_states={1},
        actions={0: [0]},
        costs=np.array([[1.0], [0.0]]),
        transitions=transitions,
    )

    with pytest.raises(ValidationError, match="negative transition probabilities"):
        validate_mdp(mdp)


def test_validate_negative_costs() -> None:
    """Test that negative costs are caught."""
    mdp = MDP(
        num_states=2,
        terminal_states={1},
        actions={0: [0]},
        costs=np.array([[-1.0], [0.0]]),  # Negative cost
        transitions=np.array([[[0.0, 1.0]], [[0.0, 1.0]]]),
    )

    with pytest.raises(ValidationError, match="Cost.*is negative"):
        validate_mdp(mdp)


def test_validate_terminal_state_out_of_range() -> None:
    """Test that invalid terminal state indices are caught."""
    mdp = MDP(
        num_states=2,
        terminal_states={5},  # Invalid: out of range
        actions={0: [0]},
        costs=np.array([[1.0], [0.0]]),
        transitions=np.array([[[0.0, 1.0]], [[0.0, 1.0]]]),
    )

    with pytest.raises(ValidationError, match="Terminal state.*out of range"):
        validate_mdp(mdp)


def test_validate_non_terminal_without_actions() -> None:
    """Test that non-terminal states without actions are caught."""
    mdp = MDP(
        num_states=3,
        terminal_states={2},
        actions={0: [0]},  # State 1 has no actions!
        costs=np.array([[1.0], [1.0], [0.0]]),
        transitions=np.zeros((3, 1, 3)),
    )

    with pytest.raises(ValidationError, match="has no available actions"):
        validate_mdp(mdp)


def test_validate_multiple_errors() -> None:
    """Test that multiple validation errors are reported together."""
    # Create MDP with multiple issues
    transitions = np.zeros((2, 1, 2))
    transitions[0, 0, 0] = 0.5  # Doesn't sum to 1

    mdp = MDP(
        num_states=2,
        terminal_states={5},  # Out of range
        actions={},  # No actions for state 0
        costs=np.array([[-1.0], [0.0]]),  # Negative cost
        transitions=transitions,
    )

    with pytest.raises(ValidationError) as exc_info:
        validate_mdp(mdp)

    error_msg = str(exc_info.value)
    # Should contain multiple error messages
    assert "Terminal state" in error_msg
    assert "no available actions" in error_msg or "negative" in error_msg
