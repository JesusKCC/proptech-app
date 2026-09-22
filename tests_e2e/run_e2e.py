#!/usr/bin/env python3
"""
PropTech Commercial Asset Platform (Peru) - Master E2E Test Suite Runner
Executes 4-Tier Test Harness covering all 21 system features.

Usage:
    py -3.14 tests_e2e/run_e2e.py [options]

Options:
    --tier <1|2|3|4>     Run tests only for the specified tier
    --feature <FEATURE>  Run tests matching a specific feature ID (e.g. FEAT-R1-01)
    --fail-fast, -x      Stop test execution on first failure
    --verbose, -v        Enable verbose per-test reporting
    --live               Run in live integration mode against running backend
    --url <URL>          Target base URL for live testing (default: http://localhost:8000)
"""

import sys
import os
import argparse

# Ensure project root and backend are in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_ROOT = os.path.join(PROJECT_ROOT, "backend")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

# Import test registry and core runner
from tests_e2e.core.runner import TestRegistry, run_suite

# Import all test suites to register test cases
def register_all_tests():
    # Tier 1: Feature Coverage
    import tests_e2e.tier1_features.test_r1_backend
    import tests_e2e.tier1_features.test_ac_backend
    import tests_e2e.tier1_features.test_r2_viewer
    import tests_e2e.tier1_features.test_r3_frontend
    import tests_e2e.tier1_features.test_r4_security
    import tests_e2e.tier1_features.test_ac_integration

    # Tier 2: Boundary & Corner Cases
    import tests_e2e.tier2_boundaries.test_r1_boundaries
    import tests_e2e.tier2_boundaries.test_ac_boundaries
    import tests_e2e.tier2_boundaries.test_r2_boundaries
    import tests_e2e.tier2_boundaries.test_r3_boundaries
    import tests_e2e.tier2_boundaries.test_r4_boundaries
    import tests_e2e.tier2_boundaries.test_ac_int_boundaries

    # Tier 3: Cross-Feature Combinations
    import tests_e2e.tier3_combinations.test_cross_features

    # Tier 4: Real-World Scenarios
    import tests_e2e.tier4_scenarios.test_peru_workflows


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="PropTech Peru E2E Test Suite Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--tier",
        type=int,
        choices=[1, 2, 3, 4],
        help="Filter tests by tier (1: Features, 2: Boundaries, 3: Combinations, 4: Scenarios)",
    )
    parser.add_argument(
        "--feature",
        type=str,
        help="Filter tests by Feature ID (e.g., FEAT-R1-01, FEAT-AC-04)",
    )
    parser.add_argument(
        "--fail-fast", "-x",
        action="store_true",
        help="Stop execution on first failing test",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show verbose output including assertion details",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Run live API tests against running server",
    )
    parser.add_argument(
        "--url",
        type=str,
        default="http://localhost:8000",
        help="Base URL for live tests (default: http://localhost:8000)",
    )
    return parser.parse_args()


def main():
    args = parse_arguments()

    print("=" * 80)
    print("PROPTECH COMMERCIAL ASSET PLATFORM (PERU) - E2E TEST RUNNER")
    print(f"Python: {sys.version.split()[0]} | Platform: {sys.platform}")
    print(f"Target: {'Live Server (' + args.url + ')' if args.live else 'Opaque-Box Contract Suite'}")
    print("=" * 80)

    # Register all tests
    register_all_tests()

    total_registered = len(TestRegistry.get_cases())
    print(f"Discovered {total_registered} total registered test cases across 4 Tiers.")
    if args.tier:
        print(f"Filter active: Tier {args.tier}")
    if args.feature:
        print(f"Filter active: Feature {args.feature}")

    # Execute test suite
    exit_code = run_suite(
        tier=args.tier,
        feature_id=args.feature,
        verbose=args.verbose,
        fail_fast=args.fail_fast,
    )

    sys.exit(exit_code)


if __name__ == "__main__":
    main()


