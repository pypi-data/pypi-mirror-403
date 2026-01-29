# Walkthrough: Understanding the Value Iteration Algorithm

This document walks through how the library solves MDPs using the Bellman optimality equation.

## Problem Setup

Consider a simple upgrade system with 3 levels (0, 1, 2) where 2 is the goal:

- **Level 0**: Starting point
- **Level 1**: Middle checkpoint  
- **Level 2**: Goal (terminal state)

At each level, you can take an action with:
- Cost: 1.0 per attempt
- Success probability: 70% (move to next level)
- Failure probability: 30% (stay at current level)

## Question

**What is the expected total cost to reach level 2 starting from level 0?**

## Mathematical Model

This is an MDP with:
- States: S = {0, 1, 2}
- Terminal: T = {2}
- Actions: A(0) = A(1) = {"try"}
- Costs: C(s, "try") = 1.0 for s ∈ {0, 1}
- Transitions:
  - P(1|0, "try") = 0.7, P(0|0, "try") = 0.3
  - P(2|1, "try") = 0.7, P(1|1, "try") = 0.3

## Bellman Optimality Equation

For terminal states:
```
V(2) = 0  (already at goal, no cost)
```

For non-terminal states (only one action, so "min" is trivial):
```
V(s) = C(s,a) + Σ P(s'|s,a) × V(s')
```

Specifically:
```
V(1) = 1.0 + 0.7×V(2) + 0.3×V(1)
     = 1.0 + 0.7×0 + 0.3×V(1)
     = 1.0 + 0.3×V(1)

Solving: V(1) = 1.0 / (1 - 0.3) = 1.0 / 0.7 ≈ 1.4286

V(0) = 1.0 + 0.7×V(1) + 0.3×V(0)
     = 1.0 + 0.7×1.4286 + 0.3×V(0)
     = 2.0 + 0.3×V(0)

Solving: V(0) = 2.0 / 0.7 ≈ 2.8571
```

## Value Iteration Algorithm

Since we can't solve the equations directly in general, we use **value iteration**:

### Iteration 0 (Initialization)
```
V⁰(0) = 0
V⁰(1) = 0  
V⁰(2) = 0  (fixed, terminal)
```

### Iteration 1
```
V¹(1) = 1.0 + 0.7×0 + 0.3×0 = 1.0
V¹(0) = 1.0 + 0.7×0 + 0.3×0 = 1.0
V¹(2) = 0  (terminal)
```

### Iteration 2
```
V²(1) = 1.0 + 0.7×0 + 0.3×1.0 = 1.3
V²(0) = 1.0 + 0.7×1.0 + 0.3×1.0 = 2.0
V²(2) = 0
```

### Iteration 3
```
V³(1) = 1.0 + 0.7×0 + 0.3×1.3 = 1.39
V³(0) = 1.0 + 0.7×1.3 + 0.3×2.0 = 2.51
```

### Iteration 4
```
V⁴(1) = 1.0 + 0.7×0 + 0.3×1.39 = 1.417
V⁴(0) = 1.0 + 0.7×1.39 + 0.3×2.51 = 2.726
```

The values converge toward V(1) ≈ 1.4286 and V(0) ≈ 2.8571.

## Why Multiple Actions Make It Interesting

Now suppose we add a "protected" action:
- Cost: 3.0
- Success probability: 70% (same)
- Failure: **stay at current level** (no downgrade)

Now the Bellman equation becomes:
```
V(s) = min {
    Q(s, "basic"),      # Original action
    Q(s, "protected")   # New action
}

where Q(s,a) = C(s,a) + Σ P(s'|s,a) × V(s')
```

At each state, the algorithm chooses whichever action has lower expected cost.

## Key Insight

The power of this approach is that it automatically handles:

1. **Cascading failures**: If failing in state 7 drops you to state 5, and failing in state 5 drops you to state 3, the expected cost naturally includes all possible failure chains.

2. **Context-dependent decisions**: The optimal action might be "protected" at state 9 (where failure is expensive) but "basic" at state 3 (where failure is cheap).

3. **Non-obvious policies**: Sometimes the optimal strategy is surprising! The algorithm finds it without manual analysis.

## Running the Code

```python
from upo import MDP, solve_mdp_value_iteration

# Define the simple 3-state MDP
mdp = MDP.from_dict(
    states=[0, 1, 2],
    terminal_states=[2],
    transitions_dict={
        0: {"try": {1: 0.7, 0: 0.3}},
        1: {"try": {2: 0.7, 1: 0.3}},
    },
    costs_dict={
        0: {"try": 1.0},
        1: {"try": 1.0},
    }
)

# Solve it
result = solve_mdp_value_iteration(mdp, tol=1e-9)

print(f"V(0) = {result.V[0]:.4f}")  # ≈ 2.8571
print(f"V(1) = {result.V[1]:.4f}")  # ≈ 1.4286
print(f"V(2) = {result.V[2]:.4f}")  # = 0.0000
print(f"Converged in {result.iterations} iterations")
```
