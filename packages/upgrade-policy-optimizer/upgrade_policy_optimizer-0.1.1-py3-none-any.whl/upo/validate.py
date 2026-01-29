"""Validation utilities for MDP structures."""

import numpy as np

from .mdp import MDP


class ValidationError(Exception):
    """Exception raised when MDP validation fails."""

    pass


def validate_mdp(mdp: MDP, prob_tol: float = 1e-9) -> None:
    """Validate that an MDP is well-formed.

    Checks:
    1. Terminal states are valid (exist in state space)
    2. All non-terminal states have at least one action
    3. All costs are non-negative
    4. All transition probabilities sum to 1 (within tolerance)
    5. Transition probabilities are non-negative

    Args:
        mdp: The MDP to validate.
        prob_tol: Tolerance for probability sum checks.

    Raises:
        ValidationError: If any validation check fails.
    """
    errors: list[str] = []

    # Check 1: Terminal states are valid
    for t in mdp.terminal_states:
        if t < 0 or t >= mdp.num_states:
            errors.append(f"Terminal state {t} is out of range [0, {mdp.num_states})")

    # Check 2: Non-terminal states have at least one action
    for s in range(mdp.num_states):
        if not mdp.is_terminal(s):
            actions = mdp.get_actions(s)
            if not actions:
                errors.append(f"Non-terminal state {s} has no available actions")

    # Check 3: All costs are non-negative (for valid state-action pairs)
    for s in range(mdp.num_states):
        for a in mdp.get_actions(s):
            cost = mdp.get_cost(s, a)
            if cost < 0:
                errors.append(f"Cost for state {s}, action {a} is negative: {cost}")
            if not np.isfinite(cost):
                errors.append(f"Cost for state {s}, action {a} is not finite: {cost}")

    # Check 4 & 5: Transition probabilities
    for s in range(mdp.num_states):
        for a in mdp.get_actions(s):
            trans_probs = mdp.get_transition_probs(s, a)

            # Check non-negativity
            if np.any(trans_probs < 0):
                errors.append(f"State {s}, action {a} has negative transition probabilities")

            # Check sum to 1
            prob_sum: float = float(np.sum(trans_probs))
            if not np.isclose(prob_sum, 1.0, atol=prob_tol):
                errors.append(
                    f"State {s}, action {a}: transition probabilities sum to "
                    f"{prob_sum:.10f}, expected 1.0 (tolerance={prob_tol})"
                )

    # Raise all errors together
    if errors:
        error_msg = "MDP validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
        raise ValidationError(error_msg)


def validate_convergence(v_new: np.ndarray, v_old: np.ndarray, tol: float) -> tuple[float, bool]:
    """Check if value iteration has converged.

    Args:
        v_new: New value function.
        v_old: Previous value function.
        tol: Convergence tolerance (max absolute difference).

    Returns:
        Tuple of (residual, converged) where residual is the maximum
        absolute difference and converged is True if residual < tol.
    """
    residual = float(np.max(np.abs(v_new - v_old)))
    converged = residual < tol
    return residual, converged
