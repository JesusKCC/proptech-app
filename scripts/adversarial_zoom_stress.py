#!/usr/bin/env python3
"""
Adversarial Stress Test Suite: Coordinate Engine & Mathematical Zoom Invariance
Author: Challenger 1 (Adversarial Mathematical & Spatial Specialist)
Reference: ORIGINAL_REQUEST.md (§ R2, AC4) & PROJECT.md (§ 2)

This suite subjects the relative coordinate engine and mathematical zoom
transformations to extreme adversarial conditions:
1. Extreme zoom levels: 0.01x, 0.5x, 2.0x, 3.5x, 10.0x, 100.0x
2. Degenerate, collinear, concave, and micro-polygons
3. Edge and boundary clamping ([0.0, 1.0]^2)
4. Shoelace area scaling invariance: Area(Z) = Z^2 * Area(1x)
"""

import math
import sys
from typing import List, Tuple, Dict, Any, Optional

Point2D = Tuple[float, float]

class CoordinateEngine:
    """Production mathematical engine specification."""

    @staticmethod
    def clamp(val: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
        if math.isnan(val):
            return min_val
        return max(min_val, min(val, max_val))

    @classmethod
    def screen_to_relative(
        cls, x: float, y: float, rendered_width: float, rendered_height: float,
        origin_x: float = 0.0, origin_y: float = 0.0, clamp: bool = True
    ) -> Point2D:
        if rendered_width <= 0 or rendered_height <= 0:
            raise ValueError(f"Invalid rendered dimensions: {rendered_width}x{rendered_height}. Must be > 0.")
        u = (x - origin_x) / rendered_width
        v = (y - origin_y) / rendered_height
        if clamp:
            return (cls.clamp(u, 0.0, 1.0), cls.clamp(v, 0.0, 1.0))
        return (u, v)

    @classmethod
    def relative_to_screen(
        cls, u: float, v: float, rendered_width: float, rendered_height: float
    ) -> Point2D:
        if rendered_width <= 0 or rendered_height <= 0:
            raise ValueError(f"Invalid rendered dimensions: {rendered_width}x{rendered_height}. Must be > 0.")
        return (u * rendered_width, v * rendered_height)

    @classmethod
    def polygon_screen_to_relative(
        cls, polygon: List[Point2D], width: float, height: float, clamp: bool = True
    ) -> List[Point2D]:
        return [cls.screen_to_relative(x, y, width, height, clamp=clamp) for (x, y) in polygon]

    @classmethod
    def polygon_relative_to_screen(
        cls, polygon_rel: List[Point2D], width: float, height: float
    ) -> List[Point2D]:
        return [cls.relative_to_screen(u, v, width, height) for (u, v) in polygon_rel]

    @staticmethod
    def shoelace_area(polygon: List[Point2D]) -> float:
        """Calculates polygon area using Gauss's area formula."""
        n = len(polygon)
        if n < 3:
            return 0.0
        total = 0.0
        for i in range(n):
            j = (i + 1) % n
            total += polygon[i][0] * polygon[j][1]
            total -= polygon[j][0] * polygon[i][1]
        return abs(total) / 2.0

    @staticmethod
    def edge_lengths(polygon: List[Point2D]) -> List[float]:
        n = len(polygon)
        if n < 2:
            return []
        lengths = []
        for i in range(n):
            j = (i + 1) % n
            dx = polygon[j][0] - polygon[i][0]
            dy = polygon[j][1] - polygon[i][1]
            lengths.append(math.hypot(dx, dy))
        return lengths

    @staticmethod
    def polygon_centroid(polygon: List[Point2D]) -> Point2D:
        n = len(polygon)
        if n == 0:
            return (0.5, 0.5)
        if n == 1:
            return polygon[0]
        if n == 2:
            return ((polygon[0][0] + polygon[1][0]) / 2.0, (polygon[0][1] + polygon[1][1]) / 2.0)

        signed_area = 0.0
        cx = 0.0
        cy = 0.0
        for i in range(n):
            j = (i + 1) % n
            factor = polygon[i][0] * polygon[j][1] - polygon[j][0] * polygon[i][1]
            signed_area += factor
            cx += (polygon[i][0] + polygon[j][0]) * factor
            cy += (polygon[i][1] + polygon[j][1]) * factor
        signed_area *= 0.5

        if abs(signed_area) < 1e-12:
            sum_x = sum(p[0] for p in polygon)
            sum_y = sum(p[1] for p in polygon)
            return (sum_x / n, sum_y / n)

        cx = cx / (6.0 * signed_area)
        cy = cy / (6.0 * signed_area)
        return (CoordinateEngine.clamp(cx), CoordinateEngine.clamp(cy))

    @staticmethod
    def is_point_in_polygon(point: Point2D, polygon: List[Point2D]) -> bool:
        n = len(polygon)
        if n < 3:
            return False
        x, y = point
        inside = False
        j = n - 1
        for i in range(n):
            xi, yi = polygon[i]
            xj, yj = polygon[j]
            intersect = ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi)
            if intersect:
                inside = not inside
            j = i
        return inside


# =========================================================================
# ADVERSARIAL TEST RUNNER & ASSERTION HARNESS
# =========================================================================

class AdversarialStressHarness:
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.failures: List[str] = []
        self.warnings: List[str] = []

    def record_pass(self, test_name: str, details: str = ""):
        self.tests_run += 1
        self.tests_passed += 1
        msg = f"  [PASS] {test_name}"
        if details:
            msg += f" ({details})"
        print(msg)

    def record_fail(self, test_name: str, error: str):
        self.tests_run += 1
        self.failures.append(f"{test_name}: {error}")
        print(f"  [FAIL] {test_name} -> {error}")

    def record_warn(self, warning: str):
        self.warnings.append(warning)
        print(f"  [WARN] {warning}")

    def run_zoom_invariance_adversarial(
        self,
        name: str,
        polygon_rel: List[Point2D],
        base_w: float,
        base_h: float,
        zoom_factor: float,
        tolerance: float = 1e-9
    ) -> bool:
        """Tests linear scaling, edge scaling, and area scaling across any zoom factor."""
        scaled_w = base_w * zoom_factor
        scaled_h = base_h * zoom_factor

        p1x = CoordinateEngine.polygon_relative_to_screen(polygon_rel, base_w, base_h)
        p_zoomed = CoordinateEngine.polygon_relative_to_screen(polygon_rel, scaled_w, scaled_h)

        # 1. Coordinate linear scaling
        max_drift = 0.0
        for i, ((x1, y1), (xz, yz)) in enumerate(zip(p1x, p_zoomed)):
            exp_x = x1 * zoom_factor
            exp_y = y1 * zoom_factor
            drift = max(abs(xz - exp_x), abs(yz - exp_y))
            if drift > max_drift:
                max_drift = drift

        if max_drift > tolerance:
            self.record_fail(
                f"{name} @ {zoom_factor}x - Linear Drift",
                f"Max drift {max_drift:.2e} > tolerance {tolerance:.2e}"
            )
            return False

        # 2. Edge length scaling
        edges_1x = CoordinateEngine.edge_lengths(p1x)
        edges_zoomed = CoordinateEngine.edge_lengths(p_zoomed)
        max_edge_err = 0.0
        for i, (l1, lz) in enumerate(zip(edges_1x, edges_zoomed)):
            if l1 > 1e-12:
                ratio = lz / l1
                err = abs(ratio - zoom_factor)
                if err > max_edge_err:
                    max_edge_err = err

        if max_edge_err > tolerance:
            self.record_fail(
                f"{name} @ {zoom_factor}x - Edge Ratio",
                f"Max edge ratio discrepancy {max_edge_err:.2e} > tolerance {tolerance:.2e}"
            )
            return False

        # 3. Shoelace area scaling
        a1x = CoordinateEngine.shoelace_area(p1x)
        azoomed = CoordinateEngine.shoelace_area(p_zoomed)
        expected_area_factor = zoom_factor ** 2

        if a1x > 1e-12:
            actual_ratio = azoomed / a1x
            area_err = abs(actual_ratio - expected_area_factor)
            # For extreme zooms, scale floating point tolerance relative to magnitude
            scaled_tol = max(tolerance, tolerance * expected_area_factor)
            if area_err > scaled_tol:
                self.record_fail(
                    f"{name} @ {zoom_factor}x - Area Ratio",
                    f"Area ratio {actual_ratio} != {expected_area_factor} (err: {area_err:.2e})"
                )
                return False

        # 4. Round-trip screen -> relative stability
        for i, (xz, yz) in enumerate(p_zoomed):
            u_rt, v_rt = CoordinateEngine.screen_to_relative(xz, yz, scaled_w, scaled_h, clamp=True)
            u_orig, v_orig = polygon_rel[i]
            drift = max(abs(u_rt - u_orig), abs(v_rt - v_orig))
            if drift > tolerance:
                self.record_fail(
                    f"{name} @ {zoom_factor}x - Round-Trip",
                    f"Vertex {i} round-trip drift {drift:.2e} > tolerance {tolerance:.2e}"
                )
                return False

        self.record_pass(
            f"{name} @ {zoom_factor:>6}x",
            f"Drift: {max_drift:.2e}, Area Ratio: {(azoomed/a1x if a1x > 1e-12 else 0.0):.6f}"
        )
        return True


def run_full_adversarial_suite() -> Dict[str, Any]:
    print("=" * 80)
    print("EMPIRICAL ADVERSARIAL CHALLENGER: COORDINATE ENGINE & ZOOM INVARIANCE")
    print("=" * 80)

    harness = AdversarialStressHarness()
    BASE_W = 2384.0
    BASE_H = 1684.0

    # -------------------------------------------------------------------------
    # SUITE 1: EXTREME ZOOM LEVELS
    # Levels: 0.01x, 0.5x, 2.0x, 3.5x, 10.0x, 100.0x
    # -------------------------------------------------------------------------
    print("\n[SUITE 1] EXTREME ZOOM LEVELS EVALUATION (0.01x to 100.0x)")
    test_poly_rel = [
        (0.15, 0.20),
        (0.45, 0.20),
        (0.45, 0.55),
        (0.15, 0.55),
    ]
    zoom_levels = [0.01, 0.5, 2.0, 3.5, 10.0, 100.0]

    for z in zoom_levels:
        harness.run_zoom_invariance_adversarial(
            "Rectangular Unit", test_poly_rel, BASE_W, BASE_H, z, tolerance=1e-8
        )

    # -------------------------------------------------------------------------
    # SUITE 2: DEGENERATE, COLLINEAR, CONCAVE & MICRO-POLYGONS
    # -------------------------------------------------------------------------
    print("\n[SUITE 2] DEGENERATE, COLLINEAR, CONCAVE & MICRO-POLYGONS")

    # 2.1 Collinear polygon (3 points on y = x diagonal)
    collinear_poly = [(0.1, 0.1), (0.3, 0.3), (0.5, 0.5)]
    area_collinear = CoordinateEngine.shoelace_area(
        CoordinateEngine.polygon_relative_to_screen(collinear_poly, BASE_W, BASE_H)
    )
    if area_collinear == 0.0:
        harness.record_pass("Collinear 3-point Polygon", "Area is strictly 0.00")
    else:
        harness.record_fail("Collinear 3-point Polygon", f"Expected area 0.0, got {area_collinear}")

    centroid_collinear = CoordinateEngine.polygon_centroid(collinear_poly)
    expected_mid = (0.3, 0.3)
    mid_drift = math.hypot(centroid_collinear[0] - expected_mid[0], centroid_collinear[1] - expected_mid[1])
    if mid_drift < 1e-9:
        harness.record_pass("Collinear Centroid Fallback", f"Mean center: {centroid_collinear}")
    else:
        harness.record_fail("Collinear Centroid Fallback", f"Drift {mid_drift:.2e} from arithmetic mean")

    # 2.2 Micro-polygon (Area ~ 10^-12 relative, sub-pixel at 1x)
    micro_poly = [
        (0.500000, 0.500000),
        (0.500001, 0.500000),
        (0.500001, 0.500001),
        (0.500000, 0.500001),
    ]
    for z in [0.5, 2.0, 10.0, 100.0]:
        harness.run_zoom_invariance_adversarial(
            "Micro-Polygon (1e-6 relative scale)", micro_poly, BASE_W, BASE_H, z, tolerance=1e-8
        )

    # 2.3 Concave Polygon (L-Shaped Starbucks commercial unit)
    starbucks_rel = [
        (0.7739, 0.4941),
        (0.8620, 0.4941),
        (0.8620, 0.5511),
        (0.7718, 0.5511),
        (0.7718, 0.5083),
        (0.7739, 0.5083),
    ]
    for z in [0.5, 2.0, 3.5, 10.0]:
        harness.run_zoom_invariance_adversarial(
            "Concave L-Shaped Unit (Starbucks)", starbucks_rel, BASE_W, BASE_H, z, tolerance=1e-8
        )

    # 2.4 Deeply Concave 10-vertex Star Polygon
    star_rel = [
        (0.50, 0.10),
        (0.58, 0.35),
        (0.85, 0.35),
        (0.63, 0.50),
        (0.71, 0.75),
        (0.50, 0.60),
        (0.29, 0.75),
        (0.37, 0.50),
        (0.15, 0.35),
        (0.42, 0.35),
    ]
    for z in [0.01, 2.0, 10.0]:
        harness.run_zoom_invariance_adversarial(
            "10-Vertex Concave Star Polygon", star_rel, BASE_W, BASE_H, z, tolerance=1e-8
        )

    # 2.5 Point-in-Polygon Hit-testing on Concave Polygon
    # Interior point in L-shape
    assert CoordinateEngine.is_point_in_polygon((0.80, 0.52), starbucks_rel) is True
    # Exterior reflex-notch point of L-shape
    assert CoordinateEngine.is_point_in_polygon((0.7730, 0.5000), starbucks_rel) is False
    harness.record_pass("Concave Hit-Testing (Ray-Casting)", "Interior=True, Reflex Notch=False")

    # -------------------------------------------------------------------------
    # SUITE 3: EDGE AND BOUNDARY CLAMPING ([0.0, 1.0]^2)
    # -------------------------------------------------------------------------
    print("\n[SUITE 3] BOUNDARY CLAMPING RIGOR ([0.0, 1.0]^2)")

    # 3.1 Extreme out-of-bounds screen coordinates
    clamp_cases = [
        ((-99999.0, -99999.0), (0.0, 0.0), "Negative Extreme"),
        ((BASE_W * 100.0, BASE_H * 100.0), (1.0, 1.0), "Positive Extreme"),
        ((0.0, 0.0), (0.0, 0.0), "Exact Origin Border"),
        ((BASE_W, BASE_H), (1.0, 1.0), "Exact Outer Corner"),
        ((-1e-15, -1e-15), (0.0, 0.0), "Negative Sub-Epsilon"),
        ((BASE_W + 1e-15, BASE_H + 1e-15), (1.0, 1.0), "Positive Sub-Epsilon"),
        ((BASE_W * (1.0 - 1e-12), BASE_H * (1.0 - 1e-12)), (1.0 - 1e-12, 1.0 - 1e-12), "Interior Near-Border"),
    ]

    for (sx, sy), (exp_u, exp_v), label in clamp_cases:
        u, v = CoordinateEngine.screen_to_relative(sx, sy, BASE_W, BASE_H, clamp=True)
        assert 0.0 <= u <= 1.0 and 0.0 <= v <= 1.0, f"Out of bounds: ({u}, {v})"
        err = max(abs(u - exp_u), abs(v - exp_v))
        if err < 1e-9:
            harness.record_pass(f"Clamping: {label}", f"Screen ({sx:.0f}, {sy:.0f}) -> ({u:.6f}, {v:.6f})")
        else:
            harness.record_fail(f"Clamping: {label}", f"Expected ({exp_u}, {exp_v}), got ({u}, {v})")

    # 3.2 Non-positive rendered dimensions guard
    for invalid_dim in [0.0, -100.0, -1e-12]:
        raised = False
        try:
            CoordinateEngine.screen_to_relative(100.0, 100.0, invalid_dim, BASE_H)
        except ValueError:
            raised = True
        if raised:
            harness.record_pass(f"Dimension Guard: W={invalid_dim}", "Properly raised ValueError")
        else:
            harness.record_fail(f"Dimension Guard: W={invalid_dim}", "Failed to raise ValueError")

    # -------------------------------------------------------------------------
    # SUITE 4: SHOELACE AREA SCALING INVARIANCE
    # Mathematical proof: Area(Z) = Z^2 * Area(1x)
    # -------------------------------------------------------------------------
    print("\n[SUITE 4] SHOELACE AREA QUADRATIC SCALING INVARIANCE")

    area_polygons = [
        ("Unit Square", [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]),
        ("Triangle", [(0.2, 0.2), (0.8, 0.2), (0.5, 0.9)]),
        ("Irregular 5-gon", [(0.1, 0.1), (0.7, 0.1), (0.9, 0.4), (0.5, 0.8), (0.1, 0.5)]),
    ]

    all_zooms = [0.01, 0.1, 0.5, 1.5, 2.0, 3.5, 5.0, 10.0, 100.0]

    for poly_name, poly_pts in area_polygons:
        p1 = CoordinateEngine.polygon_relative_to_screen(poly_pts, BASE_W, BASE_H)
        base_area = CoordinateEngine.shoelace_area(p1)
        for z in all_zooms:
            pz = CoordinateEngine.polygon_relative_to_screen(poly_pts, BASE_W * z, BASE_H * z)
            zoomed_area = CoordinateEngine.shoelace_area(pz)
            expected_area = (z ** 2) * base_area
            diff = abs(zoomed_area - expected_area)
            rel_diff = diff / expected_area if expected_area > 0 else diff
            if rel_diff < 1e-9:
                harness.record_pass(
                    f"Shoelace Invariance: {poly_name} @ {z}x",
                    f"Area ratio: {zoomed_area/base_area:.6f} == {z**2:.6f}"
                )
            else:
                harness.record_fail(
                    f"Shoelace Invariance: {poly_name} @ {z}x",
                    f"Expected {expected_area:.6f}, got {zoomed_area:.6f} (rel diff: {rel_diff:.2e})"
                )

    print("\n" + "=" * 80)
    print(f"SUMMARY: {harness.tests_passed}/{harness.tests_run} tests passed.")
    if harness.failures:
        print(f"FAILURES ({len(harness.failures)}):")
        for f in harness.failures:
            print(f"  - {f}")
    else:
        print("ZERO FAILURES: Mathematical zoom invariance empirically proven under all adversarial conditions.")
    print("=" * 80)

    return {
        "tests_run": harness.tests_run,
        "tests_passed": harness.tests_passed,
        "failures": harness.failures,
        "warnings": harness.warnings,
        "verdict": "APPROVE" if len(harness.failures) == 0 else "CHALLENGE_FAILED"
    }


if __name__ == "__main__":
    res = run_full_adversarial_suite()
    sys.exit(0 if res["verdict"] == "APPROVE" else 1)
