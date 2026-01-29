"""Sanity check tests with obvious, analytically verifiable results.

These tests verify the algorithm works correctly on simple cases where
the optimal solution is obvious and can be calculated by hand.
"""

import pytest

from upo import MDP, solve_mdp_value_iteration


def test_deterministic_chain_exact_cost() -> None:
    """Test deterministic chain: cost should be exactly sum of individual costs.

    Problem: 0 -> 1 -> 2 -> 3 (terminal)
    Each step costs a specific amount and always succeeds (100% probability).

    Expected: V(0) = 1 + 2 + 3 = 6
              V(1) = 2 + 3 = 5
              V(2) = 3
              V(3) = 0 (terminal)
    """
    mdp = MDP.from_dict(
        states=[0, 1, 2, 3],
        terminal_states=[3],
        transitions_dict={
            0: {"move": {1: 1.0}},  # 100% success
            1: {"move": {2: 1.0}},  # 100% success
            2: {"move": {3: 1.0}},  # 100% success
        },
        costs_dict={
            0: {"move": 1.0},
            1: {"move": 2.0},
            2: {"move": 3.0},
        },
    )

    result = solve_mdp_value_iteration(mdp)

    # Check exact values
    assert result.V[0] == pytest.approx(6.0, abs=1e-9), "V(0) should be exactly 6.0"
    assert result.V[1] == pytest.approx(5.0, abs=1e-9), "V(1) should be exactly 5.0"
    assert result.V[2] == pytest.approx(3.0, abs=1e-9), "V(2) should be exactly 3.0"
    assert result.V[3] == pytest.approx(0.0, abs=1e-9), "V(3) should be exactly 0.0"

    # Check policy (should all choose "move")
    assert result.policy[0] == 0
    assert result.policy[1] == 0
    assert result.policy[2] == 0
    assert result.policy[3] == -1  # Terminal


def test_geometric_series_single_state() -> None:
    """Test single-state retry with known geometric series solution.

    Problem: State 0, one action with cost 1.0
    - 70% chance success (go to terminal state 1)
    - 30% chance failure (stay at state 0)

    Expected: V(0) = 1/(1-0.3) = 1/0.7 ≈ 1.4286
    This is a geometric series: 1 + 0.3 + 0.3^2 + 0.3^3 + ... = 1/(1-0.3)
    """
    mdp = MDP.from_dict(
        states=[0, 1],
        terminal_states=[1],
        transitions_dict={0: {"try": {1: 0.7, 0: 0.3}}},
        costs_dict={0: {"try": 1.0}},
    )

    result = solve_mdp_value_iteration(mdp)

    expected = 1.0 / 0.7  # Geometric series sum
    assert result.V[0] == pytest.approx(expected, abs=1e-6)
    assert result.V[1] == pytest.approx(0.0, abs=1e-9)


def test_obviously_better_action() -> None:
    """Test that solver chooses obviously better action.

    Problem: State 0 -> State 1 (terminal)
    Two actions:
    - "expensive": costs 100, succeeds with 100% probability
    - "cheap": costs 1, succeeds with 100% probability

    Expected: Should always choose "cheap", V(0) = 1
    """
    mdp = MDP.from_dict(
        states=[0, 1],
        terminal_states=[1],
        transitions_dict={0: {"expensive": {1: 1.0}, "cheap": {1: 1.0}}},
        costs_dict={0: {"expensive": 100.0, "cheap": 1.0}},
    )

    result = solve_mdp_value_iteration(mdp)

    assert result.V[0] == pytest.approx(1.0, abs=1e-9)
    assert result.get_policy(0) == "cheap"


def test_zero_cost_deterministic() -> None:
    """Test system with zero costs - should return zero.

    Problem: 0 -> 1 -> 2 (terminal), all costs are 0
    Expected: V(0) = V(1) = 0, V(2) = 0
    """
    mdp = MDP.from_dict(
        states=[0, 1, 2],
        terminal_states=[2],
        transitions_dict={
            0: {"move": {1: 1.0}},
            1: {"move": {2: 1.0}},
        },
        costs_dict={
            0: {"move": 0.0},
            1: {"move": 0.0},
        },
    )

    result = solve_mdp_value_iteration(mdp)

    assert result.V[0] == pytest.approx(0.0, abs=1e-9)
    assert result.V[1] == pytest.approx(0.0, abs=1e-9)
    assert result.V[2] == pytest.approx(0.0, abs=1e-9)


def test_immediate_terminal() -> None:
    """Test starting at terminal state.

    Problem: State 0 is terminal
    Expected: V(0) = 0, no actions needed
    """
    mdp = MDP.from_dict(states=[0], terminal_states=[0], transitions_dict={}, costs_dict={})

    result = solve_mdp_value_iteration(mdp)

    assert result.V[0] == pytest.approx(0.0, abs=1e-9)
    assert result.policy[0] == -1  # No action (terminal)


def test_two_step_deterministic() -> None:
    """Test simple two-step path.

    Problem: 0 -> 1 (terminal)
    Cost: 5.0, probability: 100%

    Expected: V(0) = 5.0, V(1) = 0
    """
    mdp = MDP.from_dict(
        states=[0, 1],
        terminal_states=[1],
        transitions_dict={0: {"go": {1: 1.0}}},
        costs_dict={0: {"go": 5.0}},
    )

    result = solve_mdp_value_iteration(mdp)

    assert result.V[0] == pytest.approx(5.0, abs=1e-9)
    assert result.V[1] == pytest.approx(0.0, abs=1e-9)


def test_cheaper_with_lower_success_rate() -> None:
    """Test that cheaper action with lower success can still be optimal.

    Problem: 0 -> 1 (terminal)
    Actions:
    - "safe": cost=10, success=100%
    - "risky": cost=1, success=50% (retry on failure)

    Expected: V(0) with risky = 1/(1-0.5) = 2.0
              V(0) with safe = 10.0
              Should choose "risky", V(0) = 2.0
    """
    mdp = MDP.from_dict(
        states=[0, 1],
        terminal_states=[1],
        transitions_dict={
            0: {"safe": {1: 1.0}, "risky": {1: 0.5, 0: 0.5}}  # 50% success, 50% retry
        },
        costs_dict={0: {"safe": 10.0, "risky": 1.0}},
    )

    result = solve_mdp_value_iteration(mdp)

    expected_risky = 1.0 / 0.5  # = 2.0
    assert result.V[0] == pytest.approx(expected_risky, abs=1e-6)
    assert result.get_policy(0) == "risky"

    # Verify Q-values
    assert result.get_q_value(0, "safe") == pytest.approx(10.0, abs=1e-6)
    assert result.get_q_value(0, "risky") == pytest.approx(2.0, abs=1e-6)


def test_three_tier_with_setback() -> None:
    """Test upgrade system with failure setback.

    Problem: 0 -> 1 -> 2 (terminal)
    From tier 1: 50% success to tier 2, 50% failure back to tier 0

    This tests that setbacks are properly handled.
    """
    mdp = MDP.from_dict(
        states=[0, 1, 2],
        terminal_states=[2],
        transitions_dict={
            0: {"try": {1: 1.0}},  # First upgrade always succeeds
            1: {"try": {2: 0.5, 0: 0.5}},  # Second upgrade: 50% to goal, 50% back to start
        },
        costs_dict={
            0: {"try": 1.0},
            1: {"try": 1.0},
        },
    )

    result = solve_mdp_value_iteration(mdp)

    # V(1) = 1 + 0.5*0 + 0.5*V(0)
    # V(0) = 1 + V(1)
    # Substituting: V(0) = 1 + 1 + 0.5*V(0)
    # V(0) = 2 + 0.5*V(0)
    # 0.5*V(0) = 2
    # V(0) = 4

    assert result.V[0] == pytest.approx(4.0, abs=1e-6)
    assert result.V[2] == pytest.approx(0.0, abs=1e-9)


def test_two_actions_obvious_crossover() -> None:
    """Test scenario where best action is clearly different at different states.

    Problem: 0 -> 1 -> 2 (terminal)
    At state 0: action A costs 1, action B costs 10 (both 100% success to state 1)
    At state 1: action A costs 10, action B costs 1 (both 100% success to state 2)

    Expected: Use A at state 0, use B at state 1
    """
    mdp = MDP.from_dict(
        states=[0, 1, 2],
        terminal_states=[2],
        transitions_dict={0: {"A": {1: 1.0}, "B": {1: 1.0}}, 1: {"A": {2: 1.0}, "B": {2: 1.0}}},
        costs_dict={0: {"A": 1.0, "B": 10.0}, 1: {"A": 10.0, "B": 1.0}},
    )

    result = solve_mdp_value_iteration(mdp)

    # Optimal: Use A at 0 (cost 1), use B at 1 (cost 1), total = 2
    assert result.V[0] == pytest.approx(2.0, abs=1e-9)
    assert result.V[1] == pytest.approx(1.0, abs=1e-9)
    assert result.get_policy(0) == "A"
    assert result.get_policy(1) == "B"


def test_single_state_two_actions_different_probabilities() -> None:
    """Test choice between two actions with different cost/probability trade-offs.

    Problem: 0 -> 1 (terminal)
    - "cheap": cost=1, success=25% (expected cost: 4)
    - "expensive": cost=2, success=100% (expected cost: 2)

    Expected: Should choose "expensive", V(0) = 2
    """
    mdp = MDP.from_dict(
        states=[0, 1],
        terminal_states=[1],
        transitions_dict={0: {"cheap": {1: 0.25, 0: 0.75}, "expensive": {1: 1.0}}},
        costs_dict={0: {"cheap": 1.0, "expensive": 2.0}},
    )

    result = solve_mdp_value_iteration(mdp)

    # Expected cost with expensive: 2 (chosen as optimal)
    # V(0) = 2.0
    assert result.V[0] == pytest.approx(2.0, abs=1e-6)
    assert result.get_policy(0) == "expensive"

    # Verify Q-values
    # Q(cheap) = 1 + 0.25*0 + 0.75*V(0) = 1 + 0.75*2 = 2.5
    # Q(expensive) = 2 + 1.0*0 = 2.0
    assert result.get_q_value(0, "cheap") == pytest.approx(2.5, abs=1e-6)
    assert result.get_q_value(0, "expensive") == pytest.approx(2.0, abs=1e-6)


def test_convergence_flag() -> None:
    """Test that convergence flag is set correctly."""
    mdp = MDP.from_dict(
        states=[0, 1],
        terminal_states=[1],
        transitions_dict={0: {"go": {1: 1.0}}},
        costs_dict={0: {"go": 5.0}},
    )

    result = solve_mdp_value_iteration(mdp, tol=1e-9)

    assert result.converged is True
    assert result.residual < 1e-9
    assert result.iterations > 0


def test_all_paths_lead_to_terminal() -> None:
    """Test diamond-shaped graph where all paths lead to terminal.

    Problem: 0 can go to 1 or 2, both lead to terminal 3
    Expected: Choose cheaper path
    """
    mdp = MDP.from_dict(
        states=[0, 1, 2, 3],
        terminal_states=[3],
        transitions_dict={
            0: {"path1": {1: 1.0}, "path2": {2: 1.0}},  # Go through state 1  # Go through state 2
            1: {"finish": {3: 1.0}},
            2: {"finish": {3: 1.0}},
        },
        costs_dict={
            0: {"path1": 1.0, "path2": 5.0},  # path1 is cheaper
            1: {"finish": 1.0},
            2: {"finish": 1.0},
        },
    )

    result = solve_mdp_value_iteration(mdp)

    # Optimal: path1 costs 1+1=2, path2 costs 5+1=6
    assert result.V[0] == pytest.approx(2.0, abs=1e-9)
    assert result.get_policy(0) == "path1"
