# Unified Test Runner and Test Case Hierarchy Framework for PropTech E2E.
import sys
import time
import traceback
from typing import Callable, List, Dict, Any, Optional

class TestCase:
    def __init__(self, test_id: str, name: str, tier: int, feature_id: str, authoritative_source: str, fn: Callable):
        self.test_id = test_id
        self.name = name
        self.tier = tier
        self.feature_id = feature_id
        self.authoritative_source = authoritative_source
        self.fn = fn

class TestResult:
    def __init__(self, case: TestCase, passed: bool, error: Optional[str] = None, duration_ms: float = 0.0):
        self.case = case
        self.passed = passed
        self.error = error
        self.duration_ms = duration_ms

class TestRegistry:
    _cases: List[TestCase] = []

    @classmethod
    def register(cls, test_id: str, name: str, tier: int, feature_id: str, authoritative_source: str):
        def decorator(fn: Callable):
            case = TestCase(test_id, name, tier, feature_id, authoritative_source, fn)
            cls._cases.append(case)
            return fn
        return decorator

    @classmethod
    def get_cases(cls, tier: Optional[int] = None, feature_id: Optional[str] = None) -> List[TestCase]:
        cases = cls._cases
        if tier is not None:
            cases = [c for c in cases if c.tier == tier]
        if feature_id is not None:
            cases = [c for c in cases if c.feature_id == feature_id]
        return cases

    @classmethod
    def clear(cls):
        cls._cases.clear()

def run_suite(tier: Optional[int] = None, feature_id: Optional[str] = None, verbose: bool = False, fail_fast: bool = False) -> int:
    cases = TestRegistry.get_cases(tier=tier, feature_id=feature_id)
    print("\n=======================================================================")
    print(f" PROPTECH E2E TEST SUITE EXECUTION (Python {sys.version.split()[0]})")
    print(f" Selected Tests: {len(cases)} (Filter: tier={tier or 'all'}, feature={feature_id or 'all'})")
    print("=======================================================================\n")

    passed_count = 0
    failed_count = 0
    results: List[TestResult] = []
    start_all = time.perf_counter()

    for idx, case in enumerate(cases, 1):
        start_t = time.perf_counter()
        passed = False
        err_msg = None
        try:
            case.fn()
            passed = True
            passed_count += 1
        except AssertionError as ae:
            passed = False
            failed_count += 1
            err_msg = f"AssertionError: {str(ae)}"
        except Exception as e:
            passed = False
            failed_count += 1
            err_msg = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"

        duration = (time.perf_counter() - start_t) * 1000.0
        res = TestResult(case, passed, err_msg, duration)
        results.append(res)

        status_tag = "[PASS]" if passed else "[FAIL]"
        print(f"{status_tag} {case.test_id} [{case.feature_id}] {case.name} ({duration:.2f} ms)")
        if not passed:
            print(f"       Error: {err_msg}")
            print(f"       Source: {case.authoritative_source}")
            if fail_fast:
                print("\n[FAIL FAST] Aborting immediately on first test failure.\n")
                break

    total_duration = time.perf_counter() - start_all

    tier_stats: Dict[int, Dict[str, int]] = {}
    for r in results:
        t = r.case.tier
        if t not in tier_stats:
            tier_stats[t] = {"pass": 0, "fail": 0}
        if r.passed:
            tier_stats[t]["pass"] += 1
        else:
            tier_stats[t]["fail"] += 1

    print("\n-----------------------------------------------------------------------")
    print(" SUMMARY BY TEST TIER")
    print("-----------------------------------------------------------------------")
    for t in sorted(tier_stats.keys()):
        p = tier_stats[t]["pass"]
        f = tier_stats[t]["fail"]
        total = p + f
        pct = (p / total) * 100 if total > 0 else 0
        print(f" Tier {t}: {p}/{total} passed ({pct:.1f}%)")

    feature_stats: Dict[str, Dict[str, int]] = {}
    for r in results:
        feat = r.case.feature_id
        if feat not in feature_stats:
            feature_stats[feat] = {"pass": 0, "fail": 0}
        if r.passed:
            feature_stats[feat]["pass"] += 1
        else:
            feature_stats[feat]["fail"] += 1

    print("\n-----------------------------------------------------------------------")
    print(" SUMMARY BY FEATURE")
    print("-----------------------------------------------------------------------")
    for feat in sorted(feature_stats.keys()):
        p = feature_stats[feat]["pass"]
        f = feature_stats[feat]["fail"]
        total = p + f
        print(f" {feat:12s}: {p}/{total} passed")

    print("\n=======================================================================")
    print(f" TOTAL TESTS: {len(results)} | PASSED: {passed_count} | FAILED: {failed_count} | DURATION: {total_duration:.2f}s")
    print(f" OVERALL STATUS: {'SUCCESS - ALL TESTS PASSED' if failed_count == 0 else 'FAILURE - SOME TESTS FAILED'}")
    print("=======================================================================\n")

    return 0 if failed_count == 0 else 1
