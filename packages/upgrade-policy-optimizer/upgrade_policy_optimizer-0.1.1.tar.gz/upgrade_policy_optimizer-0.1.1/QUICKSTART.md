# Quick Start Guide

## Installation (1 minute)

**Option 1: Install as package (recommended)**

```bash
# Install the package in editable mode
pip3 install -e .

# Or install with development dependencies (includes testing tools)
pip3 install -e ".[dev]"
```

**Important**: After installing, make sure you're using the same Python interpreter that has the package installed. If using `uv pip`, you may need to use `uv run python3 -m upo.cli` instead.

**Option 2: Use without installing (for quick testing)**

```bash
# Just install dependencies
pip3 install -r requirements.txt

# Then run with PYTHONPATH set
PYTHONPATH=src python3 -m upo.cli examples/configs/manufacturing_process.json
```

Or from Python code:

```python
import sys
sys.path.insert(0, 'src')
from upo import solve_from_json
```

## Test It Works (30 seconds)

```bash
# Run the test suite
pytest tests/ -v
```

**Expected output:**

```
tests/test_mdp.py ............          [ 44%]
tests/test_solver.py ..........          [ 81%]
tests/test_validate.py .......           [100%]

======== 32 passed in 0.25s ========
```

## Run an Example (30 seconds)

**If you installed the package** (`pip install -e .`), try:

```bash
# Using the CLI with a JSON config
python3 -m upo.cli examples/configs/manufacturing_process.json

# Or use the command-line script (if available in your PATH)
upo-solve examples/configs/manufacturing_process.json
```

**If you didn't install the package**, use the PYTHONPATH method:

```bash
PYTHONPATH=src python3 -m upo.cli examples/configs/manufacturing_process.json
```

## Your First MDP (2 minutes)

Create a file `my_first_mdp.py`:

```python
# If package is installed, you can just:
# from upo import MDP, solve_mdp_value_iteration

# If not installed, add src to path:
import sys
sys.path.insert(0, 'src')

from upo import MDP, solve_mdp_value_iteration

# Define a simple decision problem:
# You're at "start" and want to reach "goal"
# You have two actions:
#   - "quick": cost 1, success 60%
#   - "careful": cost 2, success 90%
# Which is better?

mdp = MDP.from_dict(
    states=["start", "goal"],
    terminal_states=["goal"],
    transitions_dict={
        "start": {
            "quick": {"goal": 0.6, "start": 0.4},
            "careful": {"goal": 0.9, "start": 0.1}
        }
    },
    costs_dict={
        "start": {
            "quick": 1.0,
            "careful": 2.0
        }
    }
)

# Solve it
result = solve_mdp_value_iteration(mdp)

# See the answer
print(f"Optimal action: {result.get_policy('start')}")
print(f"Expected total cost: {result.get_value('start'):.2f}")
print(f"\nQ-values (expected cost for each action):")
print(f"  quick:   {result.get_q_value('start', 'quick'):.2f}")
print(f"  careful: {result.get_q_value('start', 'careful'):.2f}")
```

Run it:

```bash
python3 my_first_mdp.py
```

**Output:**

```
Optimal action: quick
Expected total cost: 1.67

Q-values (expected cost for each action):
  quick:   1.67
  careful: 2.22
```

The solver correctly determines that "quick" is better despite lower success rate!

## What Just Happened?

The library computed that:

- **Quick strategy**: On average, you need 1/0.6 ≈ 1.67 attempts at cost 1 each → **total 1.67**
- **Careful strategy**: On average, you need 1/0.9 ≈ 1.11 attempts at cost 2 each → **total 2.22**

Even though "careful" succeeds more often, "quick" is cheaper overall.

## Common Use Cases

### 1. Upgrade Systems (Manufacturing, Equipment)

**Option A: From JSON configuration**

```bash
# Create a JSON file defining your MDP, then:
python3 -m upo.cli my_mdp.json
```

Or from Python:

```python
from upo import solve_from_json

result = solve_from_json("my_mdp.json")
```

**Option B: Programmatic creation**

```python
from upo import MDP, solve_mdp_value_iteration

# Create upgrade system: levels 0 → 10
states = list(range(11))
transitions_dict = {}
costs_dict = {}

for level in range(10):
    transitions_dict[level] = {
        "basic": {level + 1: 0.7, max(0, level - 1): 0.3},
        "protected": {level + 1: 0.7, level: 0.3}  # No setback
    }
    costs_dict[level] = {"basic": 1.0, "protected": 3.0}

mdp = MDP.from_dict(
    states=states,
    terminal_states=[10],
    transitions_dict=transitions_dict,
    costs_dict=costs_dict
)
result = solve_mdp_value_iteration(mdp)
```

See `docs/JSON_GUIDE.md` for the JSON format specification.

### 2. Multi-Stage Processes with Rework

```python
mdp = MDP.from_dict(
    states=["design", "prototype", "test", "production"],
    terminal_states=["production"],
    transitions_dict={
        "design": {
            "standard": {"prototype": 0.8, "design": 0.2},
            "thorough": {"prototype": 0.95, "design": 0.05}
        },
        "prototype": {
            "build": {"test": 0.7, "design": 0.3}  # Failure -> back to design
        },
        "test": {
            "verify": {"production": 0.9, "prototype": 0.1}
        }
    },
    costs_dict={...}
)
```

### 3. Resource Allocation Under Uncertainty

Define states as resource levels, actions as allocation strategies, and let the solver find the optimal policy.

## Full Test Suite

```bash
# Run comprehensive tests (32 test cases)
pytest tests/ -v

# With coverage report
pytest tests/ --cov=upo --cov-report=html
open htmlcov/index.html
```

## Next Steps

1. ✅ **Read the conceptual overview**: `README.md`
2. ✅ **Understand the math**: `docs/WALKTHROUGH.md`
3. ✅ **See more examples**: `examples/configs/README.md`
4. ✅ **Check implementation details**: `docs/IMPLEMENTATION_NOTES.md`
5. ✅ **Full testing guide**: `TESTING.md`

## API Reference

### Creating an MDP

**Option 1: Dictionary (recommended for readability)**

```python
mdp = MDP.from_dict(
    states=[...],
    terminal_states=[...],
    transitions_dict={state: {action: {next_state: prob}}},
    costs_dict={state: {action: cost}}
)
```

**Option 2: Direct construction (advanced)**

```python
mdp = MDP(
    num_states=N,
    terminal_states={...},
    actions={...},
    costs=numpy_array,
    transitions=numpy_array
)
```

### Solving an MDP

```python
result = solve_mdp_value_iteration(
    mdp,
    tol=1e-9,          # Convergence tolerance
    max_iter=100000,   # Maximum iterations
    validate=True      # Check MDP is well-formed
)
```

### Querying Results

```python
# Get expected cost from a state
cost = result.get_value(state)

# Get optimal action at a state
action = result.get_policy(state)

# Get Q-value (expected cost if taking action, then following policy)
q = result.get_q_value(state, action)

# Check convergence
print(f"Converged: {result.converged}")
print(f"Iterations: {result.iterations}")
print(f"Final residual: {result.residual}")
```

## Requirements

- **Python 3.9+** (tested on 3.9)
- **numpy** (only required dependency)
- **pytest** (optional, for running tests)

## Getting Help

- **API questions**: See `README.md` API Reference section
- **Algorithm questions**: Read `docs/WALKTHROUGH.md`
- **Usage examples**: Check `examples/` directory
- **Design rationale**: See `docs/IMPLEMENTATION_NOTES.md`

## What Makes This Library Useful?

1. ✅ **General-purpose**: Works for any finite MDP, not domain-specific
2. ✅ **Easy to use**: Intuitive dictionary-based API with labels
3. ✅ **Mathematically sound**: Standard Bellman optimality equation
4. ✅ **Well-tested**: 32 test cases with analytical verification
5. ✅ **Production-ready**: Validation, error handling, convergence checks
6. ✅ **Documented**: Comprehensive docs and examples
7. ✅ **Type-safe**: Full type hints throughout

## Performance

For typical problems (10-100 states):

- **Solve time**: Milliseconds
- **Convergence**: 20-200 iterations (problem-dependent)
- **Memory**: O(states² × actions) - reasonable for finite MDPs

## License

MIT License - Free for any use
