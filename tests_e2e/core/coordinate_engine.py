# Mathematical Coordinate Engine for PDF Zoom Invariance and Point-in-Polygon Hit-Testing.
# Authoritative sources: ORIGINAL_REQUEST.md ? R2 & Acceptance Criteria, PROJECT.md ? 2.
import math
from typing import List, Tuple, Dict, Any, Optional

def screen_to_relative(x: float, y: float, width: float, height: float, clamp: bool = False) -> Tuple[float, float]:
    if width <= 0 or height <= 0:
        raise ValueError(f"Viewport dimensions must be strictly positive, got ({width}, {height})")
    u = x / width
    v = y / height
    if clamp:
        u = max(0.0, min(1.0, u))
        v = max(0.0, min(1.0, v))
    return (u, v)

def relative_to_screen(u: float, v: float, width: float, height: float) -> Tuple[float, float]:
    if width <= 0 or height <= 0:
        raise ValueError(f"Viewport dimensions must be strictly positive, got ({width}, {height})")
    return (u * width, v * height)

def polygon_area(vertices: List[Tuple[float, float]]) -> float:
    n = len(vertices)
    if n < 3:
        return 0.0
    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        area += vertices[i][0] * vertices[j][1]
        area -= vertices[j][0] * vertices[i][1]
    return abs(area) / 2.0

def point_in_polygon(point: Tuple[float, float], polygon: List[Tuple[float, float]]) -> bool:
    x, y = point
    inside = False
    n = len(polygon)
    if n < 3:
        return False
    p1x, p1y = polygon[0]
    for i in range(n + 1):
        p2x, p2y = polygon[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside

def homothety_verification(p1: List[Tuple[float, float]], p2: List[Tuple[float, float]], ratio: float = 2.0, tolerance: float = 1e-9) -> Tuple[bool, Optional[str]]:
    if len(p1) != len(p2):
        return False, f"Polygon length mismatch: {len(p1)} vs {len(p2)}"
    for i, ((x1, y1), (x2, y2)) in enumerate(zip(p1, p2)):
        exp_x = x1 * ratio
        exp_y = y1 * ratio
        dx = abs(x2 - exp_x)
        dy = abs(y2 - exp_y)
        if dx > tolerance or dy > tolerance:
            return False, f"Vertex {i} drift ({dx}, {dy}) exceeds tolerance {tolerance}"
    area1 = polygon_area(p1)
    area2 = polygon_area(p2)
    expected_area_ratio = ratio * ratio
    if area1 > 0:
        actual_area_ratio = area2 / area1
        if abs(actual_area_ratio - expected_area_ratio) > tolerance:
            return False, f"Area ratio {actual_area_ratio} differs from expected {expected_area_ratio}"
    return True, None

def calculate_bounding_box(vertices: List[Tuple[float, float]]) -> Tuple[float, float, float, float]:
    if not vertices:
        return 0.0, 0.0, 0.0, 0.0
    min_x = min(v[0] for v in vertices)
    max_x = max(v[0] for v in vertices)
    min_y = min(v[1] for v in vertices)
    max_y = max(v[1] for v in vertices)
    return min_x, min_y, max_x, max_y

def filter_polygons_by_page(polygons: List[Dict[str, Any]], page_number: int) -> List[Dict[str, Any]]:
    return [p for p in polygons if p.get("page_number", 1) == page_number]


class CoordinateEngine:
    """Wrapper class providing static math operations for relative/screen coordinate transformations."""

    @staticmethod
    def screen_to_relative(x: float, y: float, width: float, height: float, clamp: bool = False) -> Dict[str, float]:
        u, v = screen_to_relative(x, y, width, height, clamp=clamp)
        return {"x": u, "y": v, "u": u, "v": v}

    @staticmethod
    def relative_to_screen(u: float, v: float, width: float, height: float) -> Dict[str, float]:
        x, y = relative_to_screen(u, v, width, height)
        return {"x": x, "y": y}

    @staticmethod
    def calculate_relative_area(points: Any) -> float:
        if not points:
            return 0.0
        if isinstance(points[0], dict):
            pts = [(p["x"], p["y"]) for p in points]
        else:
            pts = points
        return polygon_area(pts)

    @staticmethod
    def is_point_in_polygon(x: float, y: float, polygon: Any) -> bool:
        if not polygon:
            return False
        if isinstance(polygon[0], dict):
            poly = [(p["x"], p["y"]) for p in polygon]
        else:
            poly = polygon
        return point_in_polygon((x, y), poly)

    @staticmethod
    def verify_homothety(original_points: Any, viewport_w: float, viewport_h: float) -> float:
        max_drift = 0.0
        for pt in original_points:
            orig_x = pt["x"] if isinstance(pt, dict) else pt[0]
            orig_y = pt["y"] if isinstance(pt, dict) else pt[1]
            screen_x = orig_x * viewport_w
            screen_y = orig_y * viewport_h
            back_x = screen_x / viewport_w
            back_y = screen_y / viewport_h
            drift = max(abs(orig_x - back_x), abs(orig_y - back_y))
            if drift > max_drift:
                max_drift = drift
        return max_drift

    @staticmethod
    def calculate_bounding_box(points: Any):
        if not points:
            return 0.0, 0.0, 0.0, 0.0
        if isinstance(points[0], dict):
            pts = [(p["x"], p["y"]) for p in points]
        else:
            pts = points
        return calculate_bounding_box(pts)

    @staticmethod
    def filter_polygons_by_page(polygons: List[Dict[str, Any]], blueprint_id: Any) -> List[Dict[str, Any]]:
        res = []
        for p in polygons:
            if p.get("blueprint_id") == blueprint_id or p.get("page_number") == blueprint_id:
                res.append(p)
        return res

