/**
 * Coordinate Math Engine for PropTech Architectural Blueprint Viewer
 * 
 * Provides zoom-invariant transformation between rendered screen pixels
 * and normalized [0..1] relative coordinates, Shoelace polygon area calculation,
 * SVG viewBox transformations, and mathematical invariance proofs.
 */

export interface Point2D {
  x: number;
  y: number;
}

export type RelativePoint = Point2D;
export type ScreenPoint = Point2D;

export interface BoundingBox {
  minX: number;
  minY: number;
  maxX: number;
  maxY: number;
}

export interface ZoomInvarianceResult {
  passed: boolean;
  maxCoordinateDrift: number;
  areaScaleRatio: number;
  edgeScaleRatios: number[];
  errors: string[];
}

/**
 * Clamps a number to the range [min, max].
 */
export function clamp(val: number, min = 0, max = 1): number {
  if (isNaN(val)) return min;
  return Math.min(Math.max(val, min), max);
}

/**
 * Converts screen/canvas coordinates to normalized relative coordinates [0..1].
 * 
 * Formula:
 *   u = clamp((X_screen - X_origin) / W_rendered, 0, 1)
 *   v = clamp((Y_screen - Y_origin) / H_rendered, 0, 1)
 * 
 * @param screenX Click/cursor X in viewport/client pixels
 * @param screenY Click/cursor Y in viewport/client pixels
 * @param renderedWidth Width of the rendered PDF canvas in pixels
 * @param renderedHeight Height of the rendered PDF canvas in pixels
 * @param originX Left edge X offset of the PDF canvas (default 0)
 * @param originY Top edge Y offset of the PDF canvas (default 0)
 */
export function screenToRelative(
  screenX: number,
  screenY: number,
  renderedWidth: number,
  renderedHeight: number,
  originX = 0,
  originY = 0
): RelativePoint {
  if (renderedWidth <= 0 || renderedHeight <= 0) {
    throw new Error(`Invalid rendered dimensions: ${renderedWidth}x${renderedHeight}. Must be > 0.`);
  }

  const u = (screenX - originX) / renderedWidth;
  const v = (screenY - originY) / renderedHeight;

  return {
    x: clamp(u, 0, 1),
    y: clamp(v, 0, 1),
  };
}

/**
 * Converts normalized relative coordinates [0..1] to screen/canvas pixels at current zoom.
 * 
 * Formula:
 *   X_screen = u * W_rendered
 *   Y_screen = v * H_rendered
 * 
 * @param u Normalized X coordinate in [0..1]
 * @param v Normalized Y coordinate in [0..1]
 * @param renderedWidth Current rendered canvas width in pixels
 * @param renderedHeight Current rendered canvas height in pixels
 */
export function relativeToScreen(
  u: number,
  v: number,
  renderedWidth: number,
  renderedHeight: number
): ScreenPoint {
  if (renderedWidth <= 0 || renderedHeight <= 0) {
    throw new Error(`Invalid rendered dimensions: ${renderedWidth}x${renderedHeight}. Must be > 0.`);
  }

  return {
    x: u * renderedWidth,
    y: v * renderedHeight,
  };
}

/**
 * Converts an array of screen points to normalized relative coordinates.
 */
export function polygonScreenToRelative(
  polygon: ScreenPoint[],
  renderedWidth: number,
  renderedHeight: number,
  originX = 0,
  originY = 0
): RelativePoint[] {
  return polygon.map((pt) =>
    screenToRelative(pt.x, pt.y, renderedWidth, renderedHeight, originX, originY)
  );
}

/**
 * Converts an array of relative points to screen coordinates at the given zoom/canvas size.
 */
export function polygonRelativeToScreen(
  polygon: RelativePoint[],
  renderedWidth: number,
  renderedHeight: number
): ScreenPoint[] {
  return polygon.map((pt) => relativeToScreen(pt.x, pt.y, renderedWidth, renderedHeight));
}

/**
 * Formats relative coordinates into an SVG points string scaled to the SVG viewBox.
 * For instance, if viewBox is "0 0 1000 1000", each point (u, v) is mapped to (u*1000, v*1000).
 * 
 * @param polygon Array of normalized relative points
 * @param viewBoxWidth Virtual width of the SVG viewBox (default: 1000)
 * @param viewBoxHeight Virtual height of the SVG viewBox (default: 1000)
 */
export function relativeToSvgViewBox(
  polygon: RelativePoint[],
  viewBoxWidth = 1000,
  viewBoxHeight = 1000
): string {
  return polygon
    .map((pt) => `${(pt.x * viewBoxWidth).toFixed(2)},${(pt.y * viewBoxHeight).toFixed(2)}`)
    .join(' ');
}

/**
 * Parses an SVG points string back into normalized relative coordinates.
 */
export function svgPointsToRelative(
  pointsStr: string,
  viewBoxWidth = 1000,
  viewBoxHeight = 1000
): RelativePoint[] {
  if (!pointsStr || !pointsStr.trim()) return [];
  const parts = pointsStr.trim().split(/\s+/);
  return parts.map((pair) => {
    const [xStr, yStr] = pair.split(',');
    return {
      x: clamp(parseFloat(xStr) / viewBoxWidth, 0, 1),
      y: clamp(parseFloat(yStr) / viewBoxHeight, 0, 1),
    };
  });
}

/**
 * Calculates polygon area using the Shoelace formula (Gauss's area formula).
 * 
 * Area = 0.5 * | sum_{i=0}^{n-1} (x_i * y_{i+1} - x_{i+1} * y_i) |
 * 
 * @param points Array of 2D vertices
 */
export function shoelaceArea(points: Point2D[]): number {
  const n = points.length;
  if (n < 3) return 0;

  let sum = 0;
  for (let i = 0; i < n; i++) {
    const j = (i + 1) % n;
    sum += points[i].x * points[j].y;
    sum -= points[j].x * points[i].y;
  }

  return Math.abs(sum) / 2.0;
}

/**
 * Calculates polygon perimeter (sum of edge lengths).
 */
export function polygonPerimeter(points: Point2D[]): number {
  const n = points.length;
  if (n < 2) return 0;

  let perimeter = 0;
  for (let i = 0; i < n; i++) {
    const j = (i + 1) % n;
    const dx = points[j].x - points[i].x;
    const dy = points[j].y - points[i].y;
    perimeter += Math.hypot(dx, dy);
  }
  return perimeter;
}

/**
 * Calculates the centroid of a polygon.
 * Used for placing labels, badges, or pins at the center of commercial units on the blueprint.
 */
export function polygonCentroid(points: RelativePoint[]): RelativePoint {
  const n = points.length;
  if (n === 0) return { x: 0.5, y: 0.5 };
  if (n === 1) return { x: points[0].x, y: points[0].y };
  if (n === 2) return { x: (points[0].x + points[1].x) / 2, y: (points[0].y + points[1].y) / 2 };

  let signedArea = 0;
  let cx = 0;
  let cy = 0;

  for (let i = 0; i < n; i++) {
    const j = (i + 1) % n;
    const factor = points[i].x * points[j].y - points[j].x * points[i].y;
    signedArea += factor;
    cx += (points[i].x + points[j].x) * factor;
    cy += (points[i].y + points[j].y) * factor;
  }

  signedArea *= 0.5;

  if (Math.abs(signedArea) < 1e-12) {
    // Fallback to arithmetic mean if degenerate polygon
    const sumX = points.reduce((acc, p) => acc + p.x, 0);
    const sumY = points.reduce((acc, p) => acc + p.y, 0);
    return { x: sumX / n, y: sumY / n };
  }

  cx = cx / (6 * signedArea);
  cy = cy / (6 * signedArea);

  return { x: clamp(cx, 0, 1), y: clamp(cy, 0, 1) };
}

/**
 * Calculates the bounding box of a polygon in relative coordinates.
 */
export function polygonBoundingBox(points: Point2D[]): BoundingBox {
  if (points.length === 0) {
    return { minX: 0, minY: 0, maxX: 0, maxY: 0 };
  }

  let minX = Infinity;
  let minY = Infinity;
  let maxX = -Infinity;
  let maxY = -Infinity;

  for (const pt of points) {
    if (pt.x < minX) minX = pt.x;
    if (pt.y < minY) minY = pt.y;
    if (pt.x > maxX) maxX = pt.x;
    if (pt.y > maxY) maxY = pt.y;
  }

  return { minX, minY, maxX, maxY };
}

/**
 * Tests whether a relative point is inside a polygon using the Ray-Casting algorithm.
 */
export function isPointInPolygon(point: RelativePoint, polygon: RelativePoint[]): boolean {
  const n = polygon.length;
  if (n < 3) return false;

  let inside = false;
  const { x, y } = point;

  for (let i = 0, j = n - 1; i < n; j = i++) {
    const xi = polygon[i].x;
    const yi = polygon[i].y;
    const xj = polygon[j].x;
    const yj = polygon[j].y;

    const intersect = yi > y !== yj > y && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi;
    if (intersect) inside = !inside;
  }

  return inside;
}

/**
 * Mathematically verifies that transforming a polygon between zoom levels preserves
 * exact scaling, aspect ratio, edge lengths, and area with zero relative drift.
 * 
 * Verifies:
 *   1. X_2 = zoomFactor * X_1, Y_2 = zoomFactor * Y_1 (within tolerance)
 *   2. Edge lengths scale by zoomFactor
 *   3. Polygon area scales by (zoomFactor)^2
 *   4. Round-trip screen -> relative -> screen yields identical coordinates
 */
export function verifyZoomInvariance(
  polygon1x: ScreenPoint[],
  baseWidth: number,
  baseHeight: number,
  zoomFactor = 2.0,
  tolerance = 1e-9
): ZoomInvarianceResult {
  const errors: string[] = [];
  const edgeScaleRatios: number[] = [];

  // Step 1: Normalize to relative coordinates at 1x zoom
  const polygonRel = polygonScreenToRelative(polygon1x, baseWidth, baseHeight);

  // Step 2: Compute scaled dimensions
  const scaledWidth = baseWidth * zoomFactor;
  const scaledHeight = baseHeight * zoomFactor;

  // Step 3: Project back to screen at target zoom factor
  const polygonZoomed = polygonRelativeToScreen(polygonRel, scaledWidth, scaledHeight);

  // Step 4: Verify vertex positions and relative drift
  let maxCoordinateDrift = 0;
  for (let i = 0; i < polygon1x.length; i++) {
    const expectedX = polygon1x[i].x * zoomFactor;
    const expectedY = polygon1x[i].y * zoomFactor;
    const driftX = Math.abs(polygonZoomed[i].x - expectedX);
    const driftY = Math.abs(polygonZoomed[i].y - expectedY);
    const drift = Math.max(driftX, driftY);
    if (drift > maxCoordinateDrift) {
      maxCoordinateDrift = drift;
    }

    if (drift > tolerance) {
      errors.push(
        `Vertex ${i} drift (${drift.toExponential(4)}) exceeded tolerance (${tolerance}). ` +
          `Expected (${expectedX}, ${expectedY}), got (${polygonZoomed[i].x}, ${polygonZoomed[i].y})`
      );
    }
  }

  // Step 5: Verify edge length scaling (must be zoomFactor)
  for (let i = 0; i < polygon1x.length; i++) {
    const j = (i + 1) % polygon1x.length;
    const len1x = Math.hypot(polygon1x[j].x - polygon1x[i].x, polygon1x[j].y - polygon1x[i].y);
    const lenZoomed = Math.hypot(
      polygonZoomed[j].x - polygonZoomed[i].x,
      polygonZoomed[j].y - polygonZoomed[i].y
    );
    const ratio = lenZoomed / len1x;
    edgeScaleRatios.push(ratio);

    if (Math.abs(ratio - zoomFactor) > tolerance) {
      errors.push(`Edge ${i}->${j} scale ratio (${ratio}) did not match zoom factor (${zoomFactor})`);
    }
  }

  // Step 6: Verify Shoelace area scaling (must be zoomFactor^2)
  const area1x = shoelaceArea(polygon1x);
  const areaZoomed = shoelaceArea(polygonZoomed);
  const expectedAreaRatio = zoomFactor * zoomFactor;
  const actualAreaRatio = areaZoomed / area1x;

  if (Math.abs(actualAreaRatio - expectedAreaRatio) > tolerance) {
    errors.push(
      `Area ratio (${actualAreaRatio}) did not match expected (${expectedAreaRatio}). Area 1x: ${area1x}, Area 2x: ${areaZoomed}`
    );
  }

  // Step 7: Round-trip check (screen -> rel -> screen -> rel)
  for (let i = 0; i < polygonRel.length; i++) {
    const roundTripRel = screenToRelative(
      polygonZoomed[i].x,
      polygonZoomed[i].y,
      scaledWidth,
      scaledHeight
    );
    const diffX = Math.abs(roundTripRel.x - polygonRel[i].x);
    const diffY = Math.abs(roundTripRel.y - polygonRel[i].y);
    if (diffX > tolerance || diffY > tolerance) {
      errors.push(`Round-trip normalized drift at index ${i}: dx=${diffX}, dy=${diffY}`);
    }
  }

  return {
    passed: errors.length === 0,
    maxCoordinateDrift,
    areaScaleRatio: actualAreaRatio,
    edgeScaleRatios,
    errors,
  };
}
