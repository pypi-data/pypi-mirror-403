"""Command-line interface for the MDP solver."""

import argparse
import sys
from typing import Optional

from . import __version__
from .json_solver import ConfigurationError, solve_from_json
from .result import MDPResult
from .validate import ValidationError


def display_results(result: MDPResult, config: dict, verbose: bool = False) -> None:
    """Display optimization results.

    Args:
        result: MDPResult from solver
        config: Original configuration dictionary
        verbose: Whether to show detailed output
    """
    print("=" * 70)
    print("MDP OPTIMIZATION RESULTS")
    print("=" * 70)
    print()

    # Display configuration summary
    if "name" in config:
        print(f"Problem: {config['name']}")
    if "description" in config:
        print(f"Description: {config['description']}")
    print()

    # Solver info
    print("Solution Status:")
    print(f"  Converged: {'Yes' if result.converged else 'No'}")
    print(f"  Iterations: {result.iterations}")
    print(f"  Residual: {result.residual:.2e}")
    print()

    # Get start state (first non-terminal state)
    start_state = None
    for idx in range(len(result.V)):
        if result.policy[idx] != -1:  # Not terminal
            start_state = idx
            break

    if start_state is not None:
        total_cost = result.V[start_state]
        print(f"Expected Total Cost from Initial State: {total_cost:.2f}")
        print()

    # Display optimal policy
    print("Optimal Policy:")
    print(f"{'State':<20} {'Optimal Action':<20} {'Expected Cost':<15}")
    print("-" * 70)

    for idx in range(len(result.V)):
        state_label = result.state_labels.get(idx, idx) if result.state_labels else idx
        policy_idx = result.policy[idx]

        if policy_idx == -1:
            action_label = "(TERMINAL)"
        elif result.action_labels and idx in result.action_labels:
            action_label = result.action_labels[idx].get(policy_idx, f"action_{policy_idx}")
        else:
            action_label = f"action_{policy_idx}"

        cost = result.V[idx]
        print(f"{str(state_label):<20} {str(action_label):<20} {cost:<15.2f}")

    print()

    # Verbose output: show Q-values
    if verbose:
        print("=" * 70)
        print("DETAILED Q-VALUES")
        print("=" * 70)
        print()

        for idx in range(len(result.V)):
            if result.policy[idx] == -1:  # Skip terminal states
                continue

            state_label = result.state_labels.get(idx, idx) if result.state_labels else idx
            print(f"State: {state_label}")

            # Show Q-values for all actions
            if result.action_labels and idx in result.action_labels:
                for action_idx, action_label in result.action_labels[idx].items():
                    q_val = result.Q[idx, action_idx]
                    if q_val != float("inf"):
                        is_optimal = action_idx == result.policy[idx]
                        marker = " ✓ OPTIMAL" if is_optimal else ""
                        print(f"  {action_label:<20}: {q_val:>8.2f}{marker}")
            print()


def main(argv: Optional[list] = None) -> int:
    """Main entry point for the CLI.

    Args:
        argv: Command-line arguments (defaults to sys.argv)

    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    parser = argparse.ArgumentParser(
        description="Solve Markov Decision Processes from JSON configuration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Solve from a configuration file
  upo-solve problem.json

  # Solve with custom tolerance
  upo-solve problem.json --tol 1e-12

  # Show detailed Q-values
  upo-solve problem.json --verbose

  # Skip validation for faster solving
  upo-solve problem.json --no-validate

For configuration format and examples, see:
https://github.com/eonof/upgrade-policy-optimizer
        """,
    )

    parser.add_argument("config", type=str, help="Path to JSON configuration file")

    parser.add_argument(
        "--tol", type=float, default=1e-9, help="Convergence tolerance (default: 1e-9)"
    )

    parser.add_argument(
        "--max-iter", type=int, default=100000, help="Maximum iterations (default: 100000)"
    )

    parser.add_argument(
        "--no-validate",
        action="store_true",
        help="Skip MDP validation (faster but potentially unsafe)",
    )

    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Show detailed output including Q-values"
    )

    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    args = parser.parse_args(argv)

    # Solve the problem
    try:
        print(f"Loading configuration from: {args.config}")
        print()

        # Import config to get metadata
        import json

        with open(args.config) as f:
            config = json.load(f)

        print("Solving...")
        result = solve_from_json(
            args.config, tol=args.tol, max_iter=args.max_iter, validate=not args.no_validate
        )
        print()

        # Display results
        display_results(result, config, verbose=args.verbose)

        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    except (ConfigurationError, ValidationError) as e:
        print(f"Configuration Error: {e}", file=sys.stderr)
        return 1

    except Exception as e:
        print(f"Unexpected Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
