# Testing Guide

This guide shows you how to test and use the `upgrade-policy-optimizer` library.

## Quick Start (5 minutes)

**👉 For installation instructions, see [QUICKSTART.md](QUICKSTART.md)**

### Step 1: Install Dependencies

If you haven't installed yet:

```bash
# Option A: Install just numpy (minimal)
pip3 install numpy

# Option B: Install all dev dependencies (recommended)
pip3 install -r requirements-dev.txt
```

### Step 2: Run Example Script

```bash
# Try a general-purpose example
python3 -m upo.cli examples/configs/manufacturing_process.json

```

These demonstrate complete MDP systems with optimal policy display.

## Full Test Suite (pytest)

### Install pytest

```bash
pip3 install pytest pytest-cov
```

### Run All Tests

```bash
# Basic run
pytest tests/

# With verbose output
pytest tests/ -v

# With coverage report
pytest tests/ --cov=upo --cov-report=term-missing

# Run specific test file
pytest tests/test_solver.py -v
```

### Expected Output

```
tests/test_mdp.py ............          [ 44%]
tests/test_solver.py ..........          [ 81%]
tests/test_validate.py .......           [100%]

======== 27 passed in 0.25s ========
```

## Manual Testing (Interactive Python)

### Test 1: Simple MDP

```bash
python3
```

```python
import sys
sys.path.insert(0, 'src')

from upo import MDP, solve_mdp_value_iteration

# Create a simple MDP
mdp = MDP.from_dict(
    states=["idle", "working", "done"],
    terminal_states=["done"],
    transitions_dict={
        "idle": {"start": {"working": 1.0}},
        "working": {"finish": {"done": 0.8, "idle": 0.2}},
    },
    costs_dict={
        "idle": {"start": 1.0},
        "working": {"finish": 2.0},
    }
)

# Solve it
result = solve_mdp_value_iteration(mdp)

# Check results
print(f"V(idle) = {result.get_value('idle'):.2f}")
print(f"Optimal action at idle: {result.get_policy('idle')}")
print(f"Converged in {result.iterations} iterations")
```

### Test 2: Upgrade System

```python
import sys
sys.path.insert(0, 'src')

from upo import MDP, solve_mdp_value_iteration

# Build custom upgrade system: level 0 -> 10
states = list(range(11))
transitions_dict = {}
costs_dict = {}

for level in range(10):
    transitions_dict[level] = {
        "risky": {
            level + 1: 0.7,  # 70% success
            max(0, level - 2): 0.3  # 30% failure, lose 2 levels
        },
        "safe": {
            level + 1: 0.95,  # 95% success
            level: 0.05  # 5% failure, no setback
        }
    }
    costs_dict[level] = {
        "risky": 1.0,
        "safe": 5.0
    }

mdp = MDP.from_dict(
    states=states,
    terminal_states=[10],
    transitions_dict=transitions_dict,
    costs_dict=costs_dict
)

result = solve_mdp_value_iteration(mdp)

# See optimal policy
for level in range(11):
    if level < 10:
        action = result.get_policy(level)
        cost = result.get_value(level)
        print(f"Level {level}: {action:10s} (cost={cost:.1f})")
```

## Validation Testing

Test that the library catches errors:

```python
import sys
sys.path.insert(0, 'src')

from upo import MDP, validate_mdp, ValidationError
import numpy as np

# Create an INVALID MDP (probabilities don't sum to 1)
try:
    transitions = np.zeros((2, 1, 2))
    transitions[0, 0, 0] = 0.5  # Only 0.5, not 1.0!

    mdp = MDP(
        num_states=2,
        terminal_states={1},
        actions={0: [0]},
        costs=np.array([[1.0], [0.0]]),
        transitions=transitions
    )

    validate_mdp(mdp)
except ValidationError as e:
    print("✓ Correctly caught validation error:")
    print(e)
```

## Performance Testing

Test on larger MDPs:

```python
import sys
import time
sys.path.insert(0, 'src')

from upo import MDP, solve_mdp_value_iteration

# Test with larger state space: 50-level upgrade system
states = list(range(51))
transitions_dict = {}
costs_dict = {}

for level in range(50):
    transitions_dict[level] = {
        "upgrade": {
            level + 1: 0.7,  # 70% success
            max(0, level - 1): 0.3  # 30% failure, lose 1 level
        }
    }
    costs_dict[level] = {"upgrade": 1.0}

mdp = MDP.from_dict(
    states=states,
    terminal_states=[50],
    transitions_dict=transitions_dict,
    costs_dict=costs_dict
)

start = time.time()
result = solve_mdp_value_iteration(mdp, tol=1e-9)
elapsed = time.time() - start

print(f"States: {mdp.num_states}")
print(f"Iterations: {result.iterations}")
print(f"Time: {elapsed:.3f} seconds")
print(f"Converged: {result.converged}")
```

## Type Checking

Verify type safety with mypy:

```bash
pip3 install mypy

# Check the library code
mypy src/upo/

# Check a specific file
mypy src/upo/solver.py
```

## Code Quality Checks

```bash
# Install tools
pip3 install black ruff

# Format code (if you make changes)
black src/ tests/ examples/

# Lint code
ruff check src/ tests/ examples/
```

## Common Issues

### Issue: "No module named 'numpy'"

**Solution:** Install numpy first:

```bash
pip3 install numpy
```

### Issue: "No module named 'upo'"

**Solution:** Either:

- Run from project root directory
- Or install package: `pip3 install -e .`
- Or add path: `sys.path.insert(0, 'src')`

### Issue: pytest not found

**Solution:** Install pytest:

```bash
pip3 install pytest
```

## What Each Test Verifies

### tests/test_mdp.py

- MDP creation with integer and label-based states
- from_dict() constructor
- Multiple actions per state
- Invalid shape detection
- State and action queries

### tests/test_solver.py

- Deterministic MDP solutions
- Stochastic MDP solutions
- Optimal action selection
- Terminal state handling (V=0)
- Convergence behavior
- Q-value computation
- Result accessor methods

### tests/test_validate.py

- Probability sum validation
- Negative probability detection
- Negative cost detection
- Terminal state validity
- Non-terminal states have actions
- Multiple error reporting

## Next Steps

1. ✅ Run `pytest tests/` for full test suite
2. ✅ Try `python3 -m upo.cli examples/configs/manufacturing_process.json`
3. ✅ Build your own MDP following the examples
4. ✅ Read `docs/WALKTHROUGH.md` for algorithm details

## Getting Help

- Check `README.md` for API reference
- Read `docs/WALKTHROUGH.md` for mathematical background
- See `examples/configs/README.md` for usage patterns
- Look at `tests/` for more usage examples
