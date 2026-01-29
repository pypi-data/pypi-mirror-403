# JSON Configuration Guide - General Purpose MDP Format

## Overview

This guide covers the **MDP JSON format** used by the core library (`src/upo/json_solver.py` and `python3 -m upo.cli`). This format works for any sequential decision-making problem: manufacturing, DevOps, finance, healthcare, etc.

**No Python programming required!** Just define your problem in JSON and get optimal strategy.

## 📊 **Perfect for Data-Driven Decision Making**

**This tool excels when you have real numbers!**

If you already track:

- ✅ **Success rates** from logs/analytics (e.g., "85% deployment success")
- ✅ **Costs** from time tracking (e.g., "25 person-hours per test")
- ✅ **Failure rates** from incident reports (e.g., "15% require rollback")
- ✅ **Historical data** from past projects

**→ Just plug your numbers into JSON and get optimal strategy!**

### **Example: Real Data → JSON**

You have 6 months of deployment data:

```
Standard testing: 150 deploys, 22 rollbacks (15% failure), avg 25 hrs
Comprehensive: 50 deploys, 3 rollbacks (6% failure), avg 50 hrs
Rollback cost: avg 100 hrs
```

**Convert to JSON:**

```json
{
  "transitions": {
    "staging": {
      "standard_test": { "production": 0.85, "rollback": 0.15 },
      "comprehensive_test": { "production": 0.94, "rollback": 0.06 }
    }
  },
  "costs": {
    "staging": { "standard_test": 25.0, "comprehensive_test": 50.0 },
    "rollback": { "fix": 100.0 }
  }
}
```

**Result**: Data-backed optimal strategy with quantified ROI!

---

## JSON Format

```json
{
  "name": "Problem Name",
  "description": "Brief description",

  "states": ["state1", "state2", "goal"],
  "terminal_states": ["goal"],

  "transitions": {
    "state1": {
      "action1": { "state2": 0.7, "state1": 0.3 },
      "action2": { "state2": 1.0 }
    },
    "state2": {
      "action1": { "goal": 0.9, "state1": 0.1 }
    }
  },

  "costs": {
    "state1": { "action1": 10.0, "action2": 20.0 },
    "state2": { "action1": 15.0 }
  },

  "currency": {
    "name": "dollars",
    "symbol": "$"
  }
}
```

## Usage

### From Python:

```python
from upo import solve_from_json

# Solve from file
result = solve_from_json("my_problem.json")

# Get results
print(f"Expected cost: {result.get_value('state1')}")
print(f"Optimal action: {result.get_policy('state1')}")
```

### From Command Line:

```bash
# Basic usage
python3 -m upo.cli problem.json

# With options
python3 -m upo.cli problem.json --verbose --tol 1e-12
```

## Real-World Applications

### 1. Manufacturing & Operations

**Problem**: Multi-stage production with quality control

```json
{
  "name": "Manufacturing Process",
  "states": ["raw", "stage1", "stage2", "qc", "finished", "rework"],
  "terminal_states": ["finished"],
  "transitions": {
    "stage1": {
      "standard": { "stage2": 0.9, "rework": 0.1 },
      "careful": { "stage2": 0.98, "rework": 0.02 }
    }
  }
}
```

**Questions Answered**:

- When to use careful processing vs standard?
- What's the expected cost to completion?
- Where are the bottlenecks?

### 2. Software & DevOps

**Problem**: CI/CD pipeline with testing strategies

```json
{
  "name": "Deployment Pipeline",
  "states": ["dev", "staging", "production", "rollback"],
  "terminal_states": ["production"],
  "transitions": {
    "staging": {
      "minimal_test": { "production": 0.7, "rollback": 0.3 },
      "full_test": { "production": 0.95, "rollback": 0.05 }
    }
  }
}
```

**Questions Answered**:

- How much testing is optimal?
- Expected deployment cost (person-hours)?
- When is comprehensive testing worth it?

### 3. Finance & Investment

**Problem**: Portfolio rebalancing with transaction costs

```json
{
  "name": "Investment Strategy",
  "states": ["cash", "low_risk", "medium_risk", "high_risk", "target"],
  "terminal_states": ["target"],
  "transitions": {
    "medium_risk": {
      "hold": { "target": 0.25, "medium_risk": 0.65, "low_risk": 0.1 },
      "rebalance": { "low_risk": 1.0 }
    }
  }
}
```

**Questions Answered**:

- When to rebalance portfolio?
- Expected transaction costs?
- Optimal risk level by stage?

### 4. Healthcare & Treatment

**Problem**: Treatment protocols with recovery probabilities

```json
{
  "name": "Treatment Protocol",
  "states": ["diagnosis", "mild", "moderate", "severe", "recovered", "relapse"],
  "terminal_states": ["recovered"],
  "transitions": {
    "moderate": {
      "standard_treatment": {
        "recovered": 0.6,
        "severe": 0.2,
        "moderate": 0.2
      },
      "aggressive_treatment": {
        "recovered": 0.8,
        "severe": 0.1,
        "moderate": 0.1
      }
    }
  }
}
```

**Questions Answered**:

- Which treatment protocol minimizes total cost?
- Expected patient recovery time?
- When to escalate treatment?

### 5. Project Management

**Problem**: Resource allocation under uncertainty

```json
{
  "name": "Project Milestones",
  "states": ["planning", "dev", "testing", "review", "complete", "revision"],
  "terminal_states": ["complete"],
  "transitions": {
    "testing": {
      "standard_qa": { "review": 0.7, "revision": 0.3 },
      "thorough_qa": { "review": 0.9, "revision": 0.1 }
    }
  }
}
```

**Questions Answered**:

- Optimal resource allocation per phase?
- Expected project completion cost?
- Where to invest in quality?

## Example Workflow

### 1. Define Your Problem

Identify:

- **States**: Distinct stages or conditions
- **Actions**: Decisions you can make
- **Probabilities**: Likely outcomes
- **Costs**: Resources consumed
- **Goal**: Terminal state(s)

### 2. Create JSON Configuration

```json
{
  "name": "My Problem",
  "states": [...],
  "terminal_states": [...],
  "transitions": {...},
  "costs": {...}
}
```

### 3. Solve

```bash
python3 -m upo.cli my_problem.json
```

### 4. Interpret Results

The solver gives you:

- **Optimal Policy**: Best action at each state
- **Expected Costs**: Total expected cost from each state
- **Q-Values** (--verbose): Cost comparison for all actions

### 5. Make Decisions

Use the optimal policy in your real-world system!

## Common Patterns

### Pattern 1: Binary Outcomes (Success/Failure)

```json
"transitions": {
  "current_state": {
    "risky_action": {"goal": 0.3, "current_state": 0.7},
    "safe_action": {"goal": 0.8, "fallback": 0.2}
  }
}
```

### Pattern 2: Multi-Stage Pipeline

```json
"states": ["stage1", "stage2", "stage3", "done"],
"terminal_states": ["done"],
"transitions": {
  "stage1": {"proceed": {"stage2": 1.0}},
  "stage2": {"proceed": {"stage3": 0.9, "stage1": 0.1}},
  "stage3": {"proceed": {"done": 0.95, "stage2": 0.05}}
}
```

### Pattern 3: Quality vs Cost Trade-off

```json
"costs": {
  "state": {
    "cheap": 10.0,
    "standard": 25.0,
    "premium": 50.0
  }
},
"transitions": {
  "state": {
    "cheap": {"goal": 0.6, "state": 0.4},
    "standard": {"goal": 0.8, "state": 0.2},
    "premium": {"goal": 0.95, "state": 0.05}
  }
}
```

## Tips for Success

### 1. Start Simple

- Begin with 3-5 states
- Add complexity incrementally
- Validate each step

### 2. Realistic Probabilities

- Base on historical data
- Be conservative with estimates
- Test sensitivity to assumptions

### 3. Meaningful Costs

- Use consistent units
- Include all relevant costs
- Consider opportunity costs

### 4. Validate Results

- Does the policy make intuitive sense?
- Run with different parameters
- Compare to current approach

## Troubleshooting

### "Probabilities don't sum to 1"

Each action must have probabilities that sum to 1.0:

```json
// ❌ Wrong
"action": {"next": 0.7, "stay": 0.2}  // Sums to 0.9

// ✅ Correct
"action": {"next": 0.7, "stay": 0.3}  // Sums to 1.0
```

### "No path to terminal state"

Every non-terminal state needs a path to reach a terminal state:

```json
// ❌ Wrong - state2 can't reach terminal
"state1": {"go": {"state2": 1.0}},
"state2": {"go": {"state1": 1.0}}

// ✅ Correct
"state1": {"go": {"state2": 1.0}},
"state2": {"go": {"terminal": 0.8, "state1": 0.2}}
```

### "Unexpected optimal policy"

If results seem wrong:

1. Verify all probabilities and costs
2. Check that terminal states are truly terminal
3. Run with `--verbose` to see Q-values
4. Test with simpler version first

## See Also

### General-Purpose Examples (This Format)

- **Manufacturing example**: `examples/configs/manufacturing_process.json`
- **DevOps example**: `examples/configs/deployment_pipeline.json`
- **Finance example**: `examples/configs/investment_strategy.json`

## Getting Help

1. Check example configurations
2. Verify JSON syntax at jsonlint.com
3. Start with a simplified version
4. Use `--verbose` flag for debugging
