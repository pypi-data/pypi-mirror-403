# Algorithm Verification Tests

This document explains the sanity check tests that verify the algorithm works correctly.

## Why These Tests Matter

The value iteration algorithm is mathematically complex, but certain problems have **obvious, analytically verifiable solutions**. These tests ensure the implementation matches theoretical expectations.

---

## Test 1: Deterministic Chain

**Problem**: States 0 → 1 → 2 → 3 (terminal)

- Each step costs a fixed amount (1, 2, 3)
- Each transition succeeds with 100% probability

**Expected Result**:

```
V(0) = 1 + 2 + 3 = 6.0  (sum of all costs to reach goal)
V(1) = 2 + 3 = 5.0
V(2) = 3.0
V(3) = 0.0 (terminal)
```

**What This Tests**:

- Basic cost accumulation
- Correct handling of 100% probability transitions
- Terminal state has zero cost

**Result**: ✅ Algorithm computes exactly 6.0, 5.0, 3.0, 0.0

---

## Test 2: Geometric Series

**Problem**: Single state with retry mechanism

- State 0 → State 1 (terminal) with 70% success
- On failure (30%), stay at State 0 and retry
- Each attempt costs 1.0

**Expected Result**:

```
V(0) = 1/(1-0.3) = 1/0.7 ≈ 1.4286
```

This is a **geometric series**: 1 + 0.3 + 0.3² + 0.3³ + ... = 1/(1-0.3)

**What This Tests**:

- Correct handling of retry loops
- Stochastic transitions
- Geometric series convergence

**Result**: ✅ Algorithm computes 1.428571428...

---

## Test 3: Obviously Better Action

**Problem**: State 0 → State 1 (terminal), two choices:

- "expensive": costs 100, succeeds with 100%
- "cheap": costs 1, succeeds with 100%

**Expected Result**:

```
V(0) = 1.0 (choose "cheap")
Policy(0) = "cheap"
```

**What This Tests**:

- Action selection logic
- Argmin over Q-values works correctly
- Ties broken sensibly (both 100% success, choose cheaper)

**Result**: ✅ Algorithm chooses "cheap", V(0) = 1.0

---

## Test 4: Cost-Probability Trade-off

**Problem**: State 0 → State 1 (terminal), two choices:

- "safe": costs 10, succeeds with 100%
- "risky": costs 1, succeeds with 50% (retry on failure)

**Expected Result**:

```
Q(safe) = 10.0
Q(risky) = 1/(1-0.5) = 2.0
V(0) = 2.0 (choose "risky")
```

**What This Tests**:

- Solver balances cost vs success probability
- "Cheaper but riskier" can beat "expensive but safe"
- Expected cost calculation: risky costs 1 per attempt, expects 2 attempts → total 2

**Result**: ✅ Algorithm chooses "risky", V(0) = 2.0

---

## Test 5: Setback with Cascade

**Problem**: Three-tier upgrade with failure setback

- Tier 0 → Tier 1: costs 1, succeeds with 100%
- Tier 1 → Tier 2 (terminal): costs 1, succeeds with 50%
- On failure at Tier 1: fall back to Tier 0

**Expected Result**:

```
V(1) = 1 + 0.5×V(2) + 0.5×V(0)
     = 1 + 0.5×0 + 0.5×V(0)
     = 1 + 0.5×V(0)

V(0) = 1 + V(1)
     = 1 + 1 + 0.5×V(0)
     = 2 + 0.5×V(0)

Solving: V(0) = 4.0
```

**What This Tests**:

- Failure setbacks are properly handled
- Recursive cost calculation through cascades
- System of equations solved correctly by value iteration

**Result**: ✅ Algorithm computes V(0) = 4.0

---

## Test 6: Context-Dependent Strategy

**Problem**: Two states, two actions with different costs per state

- State 0: Action A costs 1, Action B costs 10
- State 1: Action A costs 10, Action B costs 1
- Both transitions are 100% success

**Expected Result**:

```
Policy(0) = "A"  (cheaper at state 0)
Policy(1) = "B"  (cheaper at state 1)
V(0) = 1 + 1 = 2.0
```

**What This Tests**:

- Optimal policy changes based on current state
- Context-aware decision making
- No "global best action" - depends on where you are

**Result**: ✅ Algorithm uses A at state 0, B at state 1, V(0) = 2.0

---

## Running the Tests

### With pytest (if installed):

```bash
pytest tests/test_sanity_checks.py -v
```

### Without pytest:

```bash
python3 test_sanity_manual.py
```

---

## What These Tests Prove

✅ **Correctness**: Algorithm computes mathematically exact results for simple cases

✅ **Stochastic Handling**: Correctly processes probabilistic transitions

✅ **Optimization**: Finds true minimum cost (not just any solution)

✅ **Policy Extraction**: Derives correct action choices from Q-values

✅ **Cascade Handling**: Properly accounts for failure setbacks and loops

✅ **Convergence**: Value iteration converges to optimal solution

---

## Additional Validation

Beyond these sanity checks, the library also has:

1. **`test_mdp.py`**: MDP data structure tests (creation, validation, labels)
2. **`test_validate.py`**: Input validation tests (probabilities sum to 1, etc.)
3. **`test_solver.py`**: Comprehensive solver tests (convergence, Q-values, etc.)

Together, these provide comprehensive coverage of the implementation.

---

## When to Run These Tests

- ✅ After any changes to `solver.py`
- ✅ After modifying `mdp.py` data structures
- ✅ Before deploying to production
- ✅ When debugging unexpected results
- ✅ As a sanity check on new installations

---

## Interpreting Results

### If All Tests Pass ✅

The algorithm is working correctly and you can trust the optimization results.

### If Any Test Fails ❌

**Stop!** There's a bug in the implementation. Common issues:

- Incorrect Bellman update formula
- Wrong policy extraction
- Probability normalization errors
- Terminal state handling bugs

Fix the issue before using the library for real problems.

---

## Mathematical Foundation

These tests verify the implementation of:

**Bellman Optimality Equation**:

```
V(s) = min_a [ C(s,a) + Σ P(s'|s,a) × V(s') ]
```

**Policy Extraction**:

```
π(s) = argmin_a Q(s,a)
where Q(s,a) = C(s,a) + Σ P(s'|s,a) × V(s')
```

**Terminal State Condition**:

```
V(t) = 0 for all t ∈ Terminal
```

---

## Conclusion

These sanity checks provide **high confidence** that the algorithm works correctly. The tests use problems with known analytical solutions, so any deviation would indicate a bug.

**Current Status**: All tests pass with machine precision (< 1e-9 error) ✅
