"""JSON-based MDP solver for easy configuration and use.

This module provides a high-level interface for defining and solving MDPs
using JSON configuration files, making the library accessible without
requiring Python programming knowledge.
"""

import json
from pathlib import Path
from typing import Any, Union

from .mdp import MDP
from .result import MDPResult
from .solver import solve_mdp_value_iteration


class ConfigurationError(Exception):
    """Exception raised when configuration is invalid."""

    pass


def load_config_from_file(config_path: Union[str, Path]) -> dict[str, Any]:
    """Load and validate JSON configuration file.

    Args:
        config_path: Path to JSON config file

    Returns:
        Dictionary with configuration

    Raises:
        FileNotFoundError: If config file doesn't exist
        json.JSONDecodeError: If config is not valid JSON
        ConfigurationError: If config is missing required fields
    """
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(path) as f:
        config: dict[str, Any] = json.load(f)

    # Validate required fields
    required = ["states", "terminal_states", "transitions", "costs"]
    missing = [field for field in required if field not in config]
    if missing:
        raise ConfigurationError(f"Configuration missing required fields: {', '.join(missing)}")

    return config


def create_mdp_from_config(config: dict[str, Any]) -> MDP:
    """Create MDP from configuration dictionary.

    The configuration should have the following structure:

    {
        "states": [...],              # List of state identifiers
        "terminal_states": [...],     # List of terminal state identifiers
        "transitions": {              # Nested dict: state -> action -> {next_state: prob}
            "state1": {
                "action1": {"state2": 0.7, "state1": 0.3}
            }
        },
        "costs": {                    # Nested dict: state -> action -> cost
            "state1": {"action1": 1.0}
        },
        "actions": {...}              # Optional: action metadata
    }

    Args:
        config: Configuration dictionary

    Returns:
        MDP instance

    Raises:
        ConfigurationError: If configuration is invalid
    """
    try:
        states = config["states"]
        terminal_states = config["terminal_states"]
        transitions = config["transitions"]
        costs = config["costs"]

        # Create MDP using from_dict
        mdp = MDP.from_dict(
            states=states,
            terminal_states=terminal_states,
            transitions_dict=transitions,
            costs_dict=costs,
        )

        return mdp

    except KeyError as e:
        raise ConfigurationError(f"Missing required field in configuration: {e}")
    except (ValueError, TypeError) as e:
        raise ConfigurationError(f"Invalid configuration format: {e}")


def solve_from_json(
    config_path: Union[str, Path], tol: float = 1e-9, max_iter: int = 100000, validate: bool = True
) -> MDPResult:
    """Solve MDP from JSON configuration file.

    This is the main high-level function for solving MDPs without
    writing Python code. Just provide a JSON file with the problem
    definition and get the optimal solution.

    Args:
        config_path: Path to JSON configuration file
        tol: Convergence tolerance for value iteration
        max_iter: Maximum number of iterations
        validate: Whether to validate the MDP before solving

    Returns:
        MDPResult with optimal value function and policy

    Raises:
        FileNotFoundError: If config file doesn't exist
        json.JSONDecodeError: If JSON is invalid
        ConfigurationError: If configuration is invalid
        ValidationError: If validate=True and MDP is invalid

    Example:
        >>> result = solve_from_json("my_problem.json")
        >>> print(result.get_value("start"))
        >>> print(result.get_policy("start"))
    """
    # Load configuration
    config = load_config_from_file(config_path)

    # Create MDP
    mdp = create_mdp_from_config(config)

    # Solve
    result = solve_mdp_value_iteration(mdp, tol=tol, max_iter=max_iter, validate=validate)

    return result


def solve_from_dict(
    config: dict[str, Any], tol: float = 1e-9, max_iter: int = 100000, validate: bool = True
) -> MDPResult:
    """Solve MDP from configuration dictionary.

    Same as solve_from_json but takes a dictionary instead of a file path.
    Useful for programmatic use or when configuration is generated dynamically.

    Args:
        config: Configuration dictionary (see create_mdp_from_config for format)
        tol: Convergence tolerance for value iteration
        max_iter: Maximum number of iterations
        validate: Whether to validate the MDP before solving

    Returns:
        MDPResult with optimal value function and policy

    Example:
        >>> config = {
        ...     "states": ["idle", "working", "done"],
        ...     "terminal_states": ["done"],
        ...     "transitions": {
        ...         "idle": {"start": {"working": 1.0}},
        ...         "working": {"finish": {"done": 0.8, "idle": 0.2}}
        ...     },
        ...     "costs": {
        ...         "idle": {"start": 1.0},
        ...         "working": {"finish": 2.0}
        ...     }
        ... }
        >>> result = solve_from_dict(config)
    """
    # Create MDP
    mdp = create_mdp_from_config(config)

    # Solve
    result = solve_mdp_value_iteration(mdp, tol=tol, max_iter=max_iter, validate=validate)

    return result


def config_to_json_string(config: dict[str, Any], indent: int = 2) -> str:
    """Convert configuration dictionary to formatted JSON string.

    Args:
        config: Configuration dictionary
        indent: Number of spaces for indentation

    Returns:
        Formatted JSON string
    """
    return json.dumps(config, indent=indent)


def save_config(config: dict[str, Any], output_path: Union[str, Path]) -> None:
    """Save configuration dictionary to JSON file.

    Args:
        config: Configuration dictionary
        output_path: Path where to save the JSON file
    """
    path = Path(output_path)
    with open(path, "w") as f:
        json.dump(config, f, indent=2)
