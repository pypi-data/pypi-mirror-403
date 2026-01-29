"""Value iteration solver for MDPs."""

from typing import Optional

import numpy as np
import numpy.typing as npt

from .mdp import MDP
from .result import MDPResult
from .validate import validate_convergence, validate_mdp


def solve_mdp_value_iteration(
    mdp: MDP,
    tol: float = 1e-9,
    max_iter: int = 100000,
    initial_v: Optional[np.ndarray] = None,
    validate: bool = True,
) -> MDPResult:
    """Solve an MDP using value iteration.

    Implements the Bellman optimality equation:
        V(s) = min_a [ C(s,a) + sum_{s'} P(s'|s,a) * V(s') ]

    For terminal states, V(s) = 0 (absorbing, zero cost).

    Algorithm:
    1. Initialize V with zeros (or provided initial_v)
    2. For each iteration:
       - For each non-terminal state s:
         - Compute Q(s,a) = C(s,a) + sum_{s'} P(s'|s,a) * V(s')
         - Update V(s) = min_a Q(s,a)
    3. Stop when max|V_new - V_old| < tol or iterations exhausted
    4. Extract policy: π(s) = argmin_a Q(s,a)

    Args:
        mdp: The MDP to solve.
        tol: Convergence tolerance. Stop when max absolute value change < tol.
        max_iter: Maximum number of iterations.
        initial_v: Optional initial value function. If None, starts with zeros.
        validate: Whether to validate the MDP before solving.

    Returns:
        MDPResult containing:
        - V: optimal value function (expected cost-to-go)
        - policy: optimal action for each state
        - Q: Q-function (state-action values)
        - convergence information

    Raises:
        ValidationError: If validate=True and MDP is invalid.
        RuntimeError: If value iteration fails to converge within max_iter.
    """
    # Validate MDP structure
    if validate:
        validate_mdp(mdp)

    # Initialize value function
    if initial_v is not None:
        v = np.array(initial_v, dtype=np.float64)
        if v.shape != (mdp.num_states,):
            raise ValueError(f"initial_v shape {v.shape} must match (num_states={mdp.num_states},)")
    else:
        v = np.zeros(mdp.num_states, dtype=np.float64)

    # Ensure terminal states have v=0
    for t in mdp.terminal_states:
        v[t] = 0.0

    # Prepare Q-function array (will be filled at the end)
    q: npt.NDArray[np.float64] = np.full(
        (mdp.num_states, mdp.max_actions), np.inf, dtype=np.float64
    )

    # Value iteration loop
    converged = False
    residual = np.inf

    for iteration in range(max_iter):
        v_old = v.copy()

        # Update each non-terminal state
        for s in range(mdp.num_states):
            if mdp.is_terminal(s):
                continue

            actions = mdp.get_actions(s)
            if not actions:
                continue

            min_q = np.inf

            for a in actions:
                # Q(s,a) = C(s,a) + sum_{s'} P(s'|s,a) * V(s')
                cost = mdp.get_cost(s, a)
                trans_probs = mdp.get_transition_probs(s, a)
                expected_future_cost = np.dot(trans_probs, v_old)
                q_value = cost + expected_future_cost

                if q_value < min_q:
                    min_q = q_value

            v[s] = min_q

        # Check convergence
        residual, converged = validate_convergence(v, v_old, tol)

        if converged:
            break

    # Compute Q-function and extract policy
    policy: npt.NDArray[np.int64] = np.full(mdp.num_states, -1, dtype=np.int64)

    for s in range(mdp.num_states):
        if mdp.is_terminal(s):
            # Terminal states: v=0, no action needed
            q[s, :] = 0.0
            policy[s] = -1
            continue

        actions = mdp.get_actions(s)
        if not actions:
            continue

        best_action = -1
        best_q = np.inf

        for a in actions:
            cost = mdp.get_cost(s, a)
            trans_probs = mdp.get_transition_probs(s, a)
            expected_future_cost = np.dot(trans_probs, v)
            q_value = cost + expected_future_cost
            q[s, a] = q_value

            if q_value < best_q:
                best_q = q_value
                best_action = a

        policy[s] = best_action

    # Return result
    return MDPResult(
        V=v,
        policy=policy,
        Q=q,
        iterations=iteration + 1,
        converged=converged,
        residual=residual,
        state_labels=mdp.state_labels if mdp.state_labels else None,
        action_labels=mdp.action_labels if mdp.action_labels else None,
    )
