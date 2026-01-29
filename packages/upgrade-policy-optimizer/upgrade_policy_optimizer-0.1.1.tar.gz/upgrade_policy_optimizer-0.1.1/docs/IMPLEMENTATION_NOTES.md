# Implementation Notes

## Design Decisions

### State Representation

**Choice**: Support both integer indices (internal) and arbitrary labels (user-facing).

**Rationale**: Integer indexing is efficient for numpy arrays, but users want to work with meaningful labels like "start", "level_5", etc. The `MDP.from_dict()` constructor handles the mapping transparently.

**Implementation**:

- Internal arrays indexed by integers
- Optional `state_labels` and `action_labels` dictionaries
- `MDPResult` provides label-aware getter methods

### Transition Probability Storage

**Choice**: Dense 3D numpy array of shape (num_states, max_actions, num_states).

**Rationale**:

- Simple and fast for value iteration (no sparse indexing overhead)
- Reasonable for finite MDPs with <10k states
- Easy to validate (sum along axis 2 should equal 1)

**Trade-off**: Memory inefficient for very large or sparse MDPs. For such cases, consider sparse matrix formats.

### Cost Storage

**Choice**: 2D numpy array with `np.inf` for invalid (state, action) pairs.

**Rationale**:

- Natural representation (invalid actions have infinite cost)
- Simplifies Bellman update (min over actions automatically excludes invalid ones)
- Clear error propagation if validation is skipped

### Convergence Criterion

**Choice**: Max absolute difference in value function < tolerance.

**Rationale**:

- Standard in RL literature (Bellman operator is a contraction)
- Guarantees uniform convergence across all states
- Alternative L2 norm would be less intuitive

### Policy Representation

**Choice**: Store optimal action index per state, with -1 for terminal states.

**Rationale**:

- Compact representation
- -1 is a natural sentinel value
- Policy can be reconstructed from Q-values if needed

## Algorithm Details

### Value Iteration Pseudocode

```
Initialize V[s] = 0 for all s
Set V[t] = 0 for all terminal states t

repeat until convergence:
    V_old = copy(V)

    for each non-terminal state s:
        for each action a available in s:
            Q[s,a] = C[s,a] + sum over s': P[s,a,s'] * V_old[s']

        V[s] = min over a: Q[s,a]

    residual = max |V[s] - V_old[s]| over all s

    if residual < tolerance:
        break

Extract policy: π[s] = argmin over a: Q[s,a]
```

### Computational Complexity

**Time per iteration**: O(|S| × max_A × |S|) where:

- |S| = number of states
- max_A = maximum actions per state
- Inner sum over |S| for each (state, action) pair

**Space**: O(|S|² × max_A) for transition array

**Convergence**: Typically O(log(1/ε)) iterations for tolerance ε, but problem-dependent.

## Validation Design

### Why Validate

Common errors in MDP specification:

1. Transition probabilities don't sum to 1 (typos, rounding)
2. Negative costs (usually a mistake)
3. Non-terminal states without actions (unreachable goal)
4. Terminal states outside state space

### Validation Strategy

**Default**: Validate before solving (`validate=True` in solver).

**Opt-out**: Allow `validate=False` for performance in production after thorough testing.

**Error reporting**: Collect ALL validation errors before raising, so user sees complete list.

## Testing Strategy

### Test Categories

1. **Unit tests** (`test_mdp.py`, `test_validate.py`):

   - Data structure creation
   - Label mapping
   - Validation logic
   - Edge cases (empty actions, single state, etc.)

2. **Integration tests** (`test_solver.py`):

   - Simple deterministic MDPs with known solutions
   - Stochastic MDPs with analytical solutions
   - Multi-action choice
   - Convergence behavior

3. **Examples** (`examples/`):
   - Real-world patterns (upgrade systems)
   - Runnable demonstrations
   - Documentation by example

### Test Principles

- Each test should be **self-contained** and **independent**
- Use **deterministic examples** where possible for exact assertions
- Test **both success and failure paths**
- Include **edge cases** (empty sets, single elements, boundary values)

## Future Extensions

### Potential Enhancements

1. **Sparse MDP support**: Use scipy sparse matrices for large, sparse MDPs

2. **Policy iteration**: Alternative algorithm that may converge faster

3. **Modified policy iteration**: Hybrid approach with configurable partial evaluation

4. **Finite-horizon MDPs**: Currently assumes infinite horizon (discount factor could be added)

5. **Discount factor**: Support γ < 1 for reinforcement learning applications

6. **Gauss-Seidel value iteration**: In-place updates for faster convergence

7. **Visualization tools**: Plot value functions, policies, Q-values

8. **MDP builder utilities**: Common patterns (grid worlds, graphs, etc.)

### Non-Goals

- **Infinite state spaces**: Library is for finite MDPs only
- **Continuous actions**: Discrete actions only
- **Deep RL**: Use PyTorch/TensorFlow for function approximation
- **Partially observable MDPs**: Would require belief state tracking

## Performance Considerations

### When Performance Matters

- Large state spaces (>1000 states)
- Many actions per state (>10)
- Tight tolerance requirements (< 1e-12)

### Optimization Strategies

1. **Vectorization**: Current implementation uses numpy vectorization
2. **Numba/Cython**: Could JIT-compile Bellman updates
3. **Parallel updates**: States can be updated in parallel (careful with synchronization)
4. **Early termination**: Track per-state residuals, skip converged states
5. **Better initialization**: Use heuristic initial V to reduce iterations

### Benchmarks

For a typical upgrade system (10 states, 2 actions, 70% success rate):

- Convergence: ~50 iterations to 1e-9 tolerance
- Time: <1ms on modern hardware (without Numba)

## Code Quality

### Type Safety

- Full type hints throughout
- Strict mypy configuration
- No `Any` types in public API (except for labels)

### Documentation

- Google-style docstrings for all public APIs
- Inline comments for complex logic
- Examples in docstrings where helpful
- Comprehensive README and walkthrough

### Testing

- Aim for >90% coverage (where practical)
- Test edge cases and error paths
- Validate against analytical solutions where possible