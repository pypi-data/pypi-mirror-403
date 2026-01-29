"""Tests for value iteration solver."""

import numpy as np
import pytest

from upo import MDP, solve_mdp_value_iteration


def test_solver_simple_deterministic() -> None:
    """Test solver on a simple deterministic MDP.

    States: 0 -> 1 -> 2 (terminal)
    Each transition costs 1.0
    Expected: V[0] = 2.0, V[1] = 1.0, V[2] = 0.0
    """
    mdp = MDP.from_dict(
        states=[0, 1, 2],
        terminal_states=[2],
        transitions_dict={
            0: {0: {1: 1.0}},
            1: {0: {2: 1.0}},
        },
        costs_dict={
            0: {0: 1.0},
            1: {0: 1.0},
        },
    )

    result = solve_mdp_value_iteration(mdp)

    assert result.converged
    assert result.iterations > 0
    np.testing.assert_allclose(result.V[0], 2.0, atol=1e-6)
    np.testing.assert_allclose(result.V[1], 1.0, atol=1e-6)
    np.testing.assert_allclose(result.V[2], 0.0, atol=1e-6)

    # Check policy
    assert result.policy[0] == 0
    assert result.policy[1] == 0
    assert result.policy[2] == -1  # Terminal state


def test_solver_stochastic() -> None:
    """Test solver on a stochastic MDP.

    State 0: action 0 -> 70% to state 1, 30% stay in state 0
    State 1: terminal
    Cost: 1.0 per action

    Expected V[0]: Should be finite and > 1.0
    """
    mdp = MDP.from_dict(
        states=[0, 1],
        terminal_states=[1],
        transitions_dict={
            0: {0: {1: 0.7, 0: 0.3}},
        },
        costs_dict={
            0: {0: 1.0},
        },
    )

    result = solve_mdp_value_iteration(mdp)

    assert result.converged
    # Expected value: geometric series sum
    # V[0] = 1 + 0.3*V[0] => V[0] = 1/0.7 ≈ 1.4286
    np.testing.assert_allclose(result.V[0], 1.0 / 0.7, atol=1e-6)
    np.testing.assert_allclose(result.V[1], 0.0, atol=1e-6)


def test_solver_multiple_actions() -> None:
    """Test solver chooses optimal action among multiple options.

    State 0 has two actions:
    - "expensive_safe": cost 10, goes to terminal with 100% probability
    - "cheap_risky": cost 1, goes to terminal with 50%, stays with 50%

    Expected: Choose cheap_risky (lower expected cost)
    V[0] ≈ 2.0 (on average takes 2 attempts at cost 1 each)
    """
    mdp = MDP.from_dict(
        states=[0, 1],
        terminal_states=[1],
        transitions_dict={
            0: {
                "expensive_safe": {1: 1.0},
                "cheap_risky": {1: 0.5, 0: 0.5},
            },
        },
        costs_dict={
            0: {
                "expensive_safe": 10.0,
                "cheap_risky": 1.0,
            },
        },
    )

    result = solve_mdp_value_iteration(mdp)

    assert result.converged

    # V[0] with cheap_risky: 1 + 0.5*V[0] => V[0] = 2.0
    np.testing.assert_allclose(result.V[0], 2.0, atol=1e-6)

    # Check that the optimal action is cheap_risky
    state_0_idx = 0
    optimal_action_idx = result.policy[state_0_idx]
    optimal_action_label = result.action_labels[state_0_idx][optimal_action_idx]
    assert optimal_action_label == "cheap_risky"


def test_solver_terminal_state_zero_cost() -> None:
    """Test that terminal states always have V=0."""
    mdp = MDP.from_dict(
        states=["normal", "terminal"],
        terminal_states=["terminal"],
        transitions_dict={
            "normal": {"go": {"terminal": 1.0}},
        },
        costs_dict={
            "normal": {"go": 5.0},
        },
    )

    result = solve_mdp_value_iteration(mdp)

    # Get terminal state index
    terminal_idx = None
    for idx, label in result.state_labels.items():
        if label == "terminal":
            terminal_idx = idx
            break

    assert terminal_idx is not None
    assert result.V[terminal_idx] == 0.0


def test_solver_convergence() -> None:
    """Test that solver converges within reasonable iterations."""
    mdp = MDP.from_dict(
        states=list(range(5)),
        terminal_states=[4],
        transitions_dict={
            0: {0: {1: 1.0}},
            1: {0: {2: 1.0}},
            2: {0: {3: 1.0}},
            3: {0: {4: 1.0}},
        },
        costs_dict={
            0: {0: 1.0},
            1: {0: 1.0},
            2: {0: 1.0},
            3: {0: 1.0},
        },
    )

    result = solve_mdp_value_iteration(mdp, tol=1e-9)

    assert result.converged
    assert result.residual < 1e-9
    assert result.iterations < 1000  # Should converge quickly for this simple case


def test_solver_result_methods() -> None:
    """Test MDPResult convenience methods with labels."""
    mdp = MDP.from_dict(
        states=["start", "goal"],
        terminal_states=["goal"],
        transitions_dict={
            "start": {"move": {"goal": 1.0}},
        },
        costs_dict={
            "start": {"move": 3.0},
        },
    )

    result = solve_mdp_value_iteration(mdp)

    # Test get_value with label
    assert result.get_value("start") == 3.0
    assert result.get_value("goal") == 0.0

    # Test get_policy with label
    policy = result.get_policy("start")
    assert policy == "move"

    # Test get_q_value
    q = result.get_q_value("start", "move")
    assert q == 3.0


def test_solver_q_values() -> None:
    """Test that Q-values are computed correctly."""
    mdp = MDP.from_dict(
        states=[0, 1],
        terminal_states=[1],
        transitions_dict={
            0: {
                0: {1: 1.0},
                1: {1: 0.8, 0: 0.2},
            },
        },
        costs_dict={
            0: {0: 2.0, 1: 1.0},
        },
    )

    result = solve_mdp_value_iteration(mdp)

    # Q[0, 0] = 2.0 + 1.0 * V[1] = 2.0 + 0 = 2.0
    # Q[0, 1] = 1.0 + 0.8 * V[1] + 0.2 * V[0]
    # V[0] should be min of the two Q values

    assert result.Q[0, 0] == pytest.approx(2.0, abs=1e-6)

    # Action 1 creates a loop, so V[0] > Q[0,0]
    # V[0] = 1.0 + 0.8*0 + 0.2*V[0] => V[0] = 1.25
    assert result.V[0] == pytest.approx(1.25, abs=1e-6)
    assert result.Q[0, 1] == pytest.approx(1.25, abs=1e-6)

    # Optimal action should be action 1
    assert result.policy[0] == 1


def test_solver_with_initial_value() -> None:
    """Test solver with custom initial value function."""
    mdp = MDP.from_dict(
        states=[0, 1],
        terminal_states=[1],
        transitions_dict={
            0: {0: {1: 1.0}},
        },
        costs_dict={
            0: {0: 5.0},
        },
    )

    # Provide initial guess
    initial_v = np.array([10.0, 0.0])
    result = solve_mdp_value_iteration(mdp, initial_v=initial_v)

    # Should still converge to correct answer
    assert result.converged
    np.testing.assert_allclose(result.V[0], 5.0, atol=1e-6)
