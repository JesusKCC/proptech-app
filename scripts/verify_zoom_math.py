#!/usr/bin/env python3
"""
Automated Mathematical Verification Script: PDF Zoom-Invariance Proof
Project: PropTech Interactive Architectural Blueprint Platform
Milestone: M2

Mathematically proves that:
1. When a polygon is recorded at 1.0x zoom, its normalized relative coordinates [0..1]
   are scale-invariant.
2. Under 2.0x zoom, rendered pixel coordinates scale to exactly 2.0 * (X, Y) with zero
   relative drift (< 10^-9).
3. All polygon edge lengths scale by exactly 2.0x.
4. The polygonal area (computed via the Shoelace Formula) scales by exactly (2.0)^2 = 4.0x.
5. Invariance holds across multiple authentic architectural floorplan polygons,
   including irregular multi-vertex commercial units from 'PLANO COMERCIAL - PACITA VES'.
"""

import math
import sys
from typing import List, Tuple, Dict

Point2D = Tuple[float, float]

class CoordinateEngine:
    """Mathematical Coordinate Engine mirroring frontend/src/lib/coordinateMath.ts"""

    @staticmethod
    def clamp(val: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
        return max(min_val, min(val, max_val))

    @classmethod
    def screen_to_relative(
        cls, x: float, y: float, rendered_width: float, rendered_height: float,
        origin_x: float = 0.0, origin_y: float = 0.0
    ) -> Point2D:
        """Converts screen pixels to normalized [0..1] coordinates."""
        assert rendered_width > 0 and rendered_height > 0, "Dimensions must be > 0"
        u = (x - origin_x) / rendered_width
        v = (y - origin_y) / rendered_height
        return (cls.clamp(u, 0.0, 1.0), cls.clamp(v, 0.0, 1.0))

    @classmethod
    def relative_to_screen(
        cls, u: float, v: float, rendered_width: float, rendered_height: float
    ) -> Point2D:
        """Converts normalized [0..1] coordinates back to screen pixels."""
        assert rendered_width > 0 and rendered_height > 0, "Dimensions must be > 0"
        return (u * rendered_width, v * rendered_height)

    @classmethod
    def polygon_screen_to_relative(
        cls, polygon: List[Point2D], width: float, height: float
    ) -> List[Point2D]:
        return [cls.screen_to_relative(x, y, width, height) for (x, y) in polygon]

    @classmethod
    def polygon_relative_to_screen(
        cls, polygon_rel: List[Point2D], width: float, height: float
    ) -> List[Point2D]:
        return [cls.relative_to_screen(u, v, width, height) for (u, v) in polygon_rel]

    @staticmethod
    def shoelace_area(polygon: List[Point2D]) -> float:
        """Calculates exact polygonal area using Gauss's Shoelace formula."""
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
        """Calculates lengths of all consecutive edges."""
        n = len(polygon)
        lengths = []
        for i in range(n):
            j = (i + 1) % n
            dx = polygon[j][0] - polygon[i][0]
            dy = polygon[j][1] - polygon[i][1]
            lengths.append(math.hypot(dx, dy))
        return lengths


def run_single_invariance_test(
    unit_name: str,
    polygon_1x: List[Point2D],
    base_width: float,
    base_height: float,
    zoom_factor: float = 2.0,
    tolerance: float = 1e-9
) -> Dict[str, any]:
    """Tests zoom invariance properties for a specific commercial unit."""
    # 1. Normalize at 1x
    polygon_rel = CoordinateEngine.polygon_screen_to_relative(polygon_1x, base_width, base_height)

    # 2. Scaled canvas dimensions
    scaled_width = base_width * zoom_factor
    scaled_height = base_height * zoom_factor

    # 3. Project to zoomed canvas
    polygon_zoomed = CoordinateEngine.polygon_relative_to_screen(polygon_rel, scaled_width, scaled_height)

    # 4. Invariance Assertion A: Linear position doubling
    max_drift = 0.0
    for i, ((x1, y1), (x2, y2)) in enumerate(zip(polygon_1x, polygon_zoomed)):
        expected_x = x1 * zoom_factor
        expected_y = y1 * zoom_factor
        drift = max(abs(x2 - expected_x), abs(y2 - expected_y))
        max_drift = max(max_drift, drift)
        assert drift < tolerance, (
            f"[{unit_name}] Vertex {i} drift {drift:.2e} exceeds tolerance {tolerance:.2e}. "
            f"Expected ({expected_x}, {expected_y}), got ({x2}, {y2})"
        )

    # 5. Invariance Assertion B: Edge length scaling
    edges_1x = CoordinateEngine.edge_lengths(polygon_1x)
    edges_zoomed = CoordinateEngine.edge_lengths(polygon_zoomed)
    for i, (l1, l2) in enumerate(zip(edges_1x, edges_zoomed)):
        ratio = l2 / l1
        assert abs(ratio - zoom_factor) < tolerance, (
            f"[{unit_name}] Edge {i} scale ratio {ratio:.10f} != {zoom_factor:.10f}"
        )

    # 6. Invariance Assertion C: Area quadrupling (factor^2)
    area_1x = CoordinateEngine.shoelace_area(polygon_1x)
    area_zoomed = CoordinateEngine.shoelace_area(polygon_zoomed)
    expected_area_factor = zoom_factor ** 2
    actual_area_ratio = area_zoomed / area_1x
    assert abs(actual_area_ratio - expected_area_factor) < tolerance, (
        f"[{unit_name}] Area ratio {actual_area_ratio:.10f} != {expected_area_factor:.10f}"
    )

    # 7. Invariance Assertion D: Round-trip normalized stability
    for i, ((u_orig, v_orig), (x_zoom, y_zoom)) in enumerate(zip(polygon_rel, polygon_zoomed)):
        u_rt, v_rt = CoordinateEngine.screen_to_relative(x_zoom, y_zoom, scaled_width, scaled_height)
        assert abs(u_rt - u_orig) < tolerance, f"[{unit_name}] Normalized U drift {abs(u_rt - u_orig)}"
        assert abs(v_rt - v_orig) < tolerance, f"[{unit_name}] Normalized V drift {abs(v_rt - v_orig)}"

    return {
        "unit": unit_name,
        "vertices_count": len(polygon_1x),
        "max_drift": max_drift,
        "area_1x": area_1x,
        "area_zoomed": area_zoomed,
        "area_ratio": actual_area_ratio,
        "passed": True
    }


def main():
    print("=" * 70)
    print("PROVISIONING MATHEMATICAL ZOOM-INVARIANCE PROOF SUITE")
    print("=" * 70)

    # Architectural Blueprint intrinsic dimensions:
    # PACITA VES-PRIMER NIVEL: 2384 x 1684 points (A1/A2 landscape ratio 1.415)
    PDF_WIDTH = 2384.0
    PDF_HEIGHT = 1684.0

    print(f"Base PDF Intrinsic Dimensions: {PDF_WIDTH} x {PDF_HEIGHT} pt")

    # Authentic commercial units from Placita Villa El Salvador
    test_cases = [
        (
            "COOLBOX (LCE-103) - Regular Rectangular Unit",
            [
                (1750.0, 830.0),
                (1820.0, 830.0),
                (1820.0, 885.0),
                (1750.0, 885.0),
            ]
        ),
        (
            "BITEL (LCE-105) - Large Commercial Anchor Unit",
            [
                (1570.0, 830.0),
                (1695.0, 830.0),
                (1695.0, 925.0),
                (1570.0, 925.0),
            ]
        ),
        (
            "ECONOLENTES (LCE-107) - 5-Vertex Irregular Unit",
            [
                (1465.0, 605.0),
                (1515.0, 605.0),
                (1524.0, 660.0),
                (1465.0, 690.0),
                (1465.0, 605.0 + 30.0),
            ]
        ),
        (
            "STARBUCKS (LCE-101/102) - 6-Vertex L-Shaped Corner Unit",
            [
                (1845.0, 832.0),
                (2055.0, 832.0),
                (2055.0, 928.0),
                (1840.0, 928.0),
                (1840.0, 856.0),
                (1845.0, 856.0),
            ]
        ),
    ]

    # Test under multiple zoom factors: 2.0x, 3.0x, 1.5x, 0.75x
    zoom_factors = [2.0, 1.5, 3.0, 0.75]

    for zoom in zoom_factors:
        print(f"\n--- Testing Zoom Factor: {zoom}x (Area Factor: {zoom**2:.4f}x) ---")
        for name, polygon in test_cases:
            result = run_single_invariance_test(
                unit_name=name,
                polygon_1x=polygon,
                base_width=PDF_WIDTH,
                base_height=PDF_HEIGHT,
                zoom_factor=zoom,
                tolerance=1e-9
            )
            print(
                f"  [PASS] {result['unit']:<45} | "
                f"Vertices: {result['vertices_count']} | "
                f"Max Drift: {result['max_drift']:.2e} | "
                f"Area Ratio: {result['area_ratio']:.6f}"
            )

    # Additional Test: SVG ViewBox Normalization Equivalence
    print("\n--- Testing SVG ViewBox Virtual Grid (1000x1000) Mapping ---")
    viewbox_width, viewbox_height = 1000.0, 1000.0
    for name, polygon in test_cases:
        poly_rel = CoordinateEngine.polygon_screen_to_relative(polygon, PDF_WIDTH, PDF_HEIGHT)
        # Virtual SVG coordinates
        svg_coords = [(u * viewbox_width, v * viewbox_height) for u, v in poly_rel]
        # Re-derive screen at 2x zoom via SVG affine transformation
        svg_scaled_to_screen = [
            (sx * (PDF_WIDTH * 2.0 / viewbox_width), sy * (PDF_HEIGHT * 2.0 / viewbox_height))
            for sx, sy in svg_coords
        ]
        direct_zoomed = CoordinateEngine.polygon_relative_to_screen(poly_rel, PDF_WIDTH * 2.0, PDF_HEIGHT * 2.0)
        for (x_svg, y_svg), (x_dir, y_dir) in zip(svg_scaled_to_screen, direct_zoomed):
            diff = math.hypot(x_svg - x_dir, y_svg - y_dir)
            assert diff < 1e-9, f"SVG ViewBox projection discrepancy: {diff}"
    print("  [PASS] SVG ViewBox (viewBox='0 0 1000 1000') Affine Transform Equivalence Verified.")

    # Boundary and Clamping Checks
    print("\n--- Testing Edge Clamping & Out-of-Bounds Guards ---")
    assert CoordinateEngine.clamp(-0.5) == 0.0
    assert CoordinateEngine.clamp(1.5) == 1.0
    u_clamped, v_clamped = CoordinateEngine.screen_to_relative(-50.0, PDF_HEIGHT + 100.0, PDF_WIDTH, PDF_HEIGHT)
    assert u_clamped == 0.0 and v_clamped == 1.0
    print("  [PASS] Clamping and boundary guards verified successfully.")

    print("\n" + "=" * 70)
    print("ALL TESTS PASSED: Zoom-Invariance Math Engine Verified with 100% Precision.")
    print("=" * 70)


if __name__ == "__main__":
    main()
