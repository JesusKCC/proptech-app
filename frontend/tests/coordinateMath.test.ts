import {
  screenToRelative,
  relativeToScreen,
  polygonScreenToRelative,
  polygonRelativeToScreen,
  shoelaceArea,
  polygonPerimeter,
  polygonCentroid,
  relativeToSvgViewBox,
  svgPointsToRelative,
  verifyZoomInvariance,
  isPointInPolygon,
  clamp,
} from '../src/lib/coordinateMath';

describe('Coordinate Math Engine - Mathematical Proofs and Invariance', () => {
  const BASE_WIDTH = 2384.0;
  const BASE_HEIGHT = 1684.0;

  // Commercial Unit 1: Rectangular COOLBOX
  const COOLBOX_1X = [
    { x: 1750.0, y: 830.0 },
    { x: 1820.0, y: 830.0 },
    { x: 1820.0, y: 885.0 },
    { x: 1750.0, y: 885.0 },
  ];

  // Commercial Unit 2: Multi-vertex STARBUCKS LCE-101/102 (6 vertices)
  const STARBUCKS_1X = [
    { x: 1845.0, y: 832.0 },
    { x: 2055.0, y: 832.0 },
    { x: 2055.0, y: 928.0 },
    { x: 1840.0, y: 928.0 },
    { x: 1840.0, y: 856.0 },
    { x: 1845.0, y: 856.0 },
  ];

  test('screenToRelative normalizes coordinates strictly to [0..1] range', () => {
    const origin = screenToRelative(0, 0, BASE_WIDTH, BASE_HEIGHT);
    expect(origin.x).toBe(0);
    expect(origin.y).toBe(0);

    const center = screenToRelative(BASE_WIDTH / 2, BASE_HEIGHT / 2, BASE_WIDTH, BASE_HEIGHT);
    expect(center.x).toBeCloseTo(0.5, 9);
    expect(center.y).toBeCloseTo(0.5, 9);

    const corner = screenToRelative(BASE_WIDTH, BASE_HEIGHT, BASE_WIDTH, BASE_HEIGHT);
    expect(corner.x).toBe(1);
    expect(corner.y).toBe(1);

    // Out of bounds are clamped
    const negative = screenToRelative(-100, -50, BASE_WIDTH, BASE_HEIGHT);
    expect(negative.x).toBe(0);
    expect(negative.y).toBe(0);

    const overflow = screenToRelative(BASE_WIDTH + 500, BASE_HEIGHT + 300, BASE_WIDTH, BASE_HEIGHT);
    expect(overflow.x).toBe(1);
    expect(overflow.y).toBe(1);
  });

  test('relativeToScreen maps [0..1] back to exact screen pixels at any zoom factor', () => {
    const screen1x = relativeToScreen(0.5, 0.5, BASE_WIDTH, BASE_HEIGHT);
    expect(screen1x.x).toBe(BASE_WIDTH * 0.5);
    expect(screen1x.y).toBe(BASE_HEIGHT * 0.5);

    const zoomFactor = 2.0;
    const screen2x = relativeToScreen(0.5, 0.5, BASE_WIDTH * zoomFactor, BASE_HEIGHT * zoomFactor);
    expect(screen2x.x).toBe(BASE_WIDTH * 0.5 * 2.0);
    expect(screen2x.y).toBe(BASE_HEIGHT * 0.5 * 2.0);
    expect(screen2x.x).toBe(screen1x.x * 2.0);
  });

  test('Mathematical Invariance Proof under 2.0x Zoom: zero drift (< 1e-9), edges 2x, area 4x', () => {
    const units = [
      { name: 'COOLBOX (LCE-103)', poly: COOLBOX_1X },
      { name: 'STARBUCKS (LCE-101/102)', poly: STARBUCKS_1X },
    ];

    for (const unit of units) {
      const result = verifyZoomInvariance(unit.poly, BASE_WIDTH, BASE_HEIGHT, 2.0, 1e-9);
      expect(result.passed).toBe(true);
      expect(result.maxCoordinateDrift).toBeLessThan(1e-9);
      expect(result.areaScaleRatio).toBeCloseTo(4.0, 6);
      for (const edgeRatio of result.edgeScaleRatios) {
        expect(edgeRatio).toBeCloseTo(2.0, 6);
      }
    }
  });

  test('Mathematical Invariance Proof under 3.0x Zoom and 1.5x Zoom', () => {
    const result3x = verifyZoomInvariance(COOLBOX_1X, BASE_WIDTH, BASE_HEIGHT, 3.0, 1e-9);
    expect(result3x.passed).toBe(true);
    expect(result3x.areaScaleRatio).toBeCloseTo(9.0, 6);

    const result15x = verifyZoomInvariance(COOLBOX_1X, BASE_WIDTH, BASE_HEIGHT, 1.5, 1e-9);
    expect(result15x.passed).toBe(true);
    expect(result15x.areaScaleRatio).toBeCloseTo(2.25, 6);
  });

  test('Shoelace area formula accurately computes known polygon geometry', () => {
    // 100 x 50 rectangle: Area = 5000
    const rect = [
      { x: 10, y: 20 },
      { x: 110, y: 20 },
      { x: 110, y: 70 },
      { x: 10, y: 70 },
    ];
    expect(shoelaceArea(rect)).toBe(5000);

    // Right triangle with base 30, height 40: Area = 0.5 * 30 * 40 = 600
    const triangle = [
      { x: 0, y: 0 },
      { x: 30, y: 0 },
      { x: 0, y: 40 },
    ];
    expect(shoelaceArea(triangle)).toBe(600);
  });

  test('polygonCentroid accurately calculates interior center for label positioning', () => {
    const rect = [
      { x: 0.1, y: 0.2 },
      { x: 0.3, y: 0.2 },
      { x: 0.3, y: 0.4 },
      { x: 0.1, y: 0.4 },
    ];
    const centroid = polygonCentroid(rect);
    expect(centroid.x).toBeCloseTo(0.2, 5);
    expect(centroid.y).toBeCloseTo(0.3, 5);
  });

  test('SVG ViewBox 1000x1000 virtual grid encoding and decoding round-trip', () => {
    const relPoints = [
      { x: 0.123, y: 0.456 },
      { x: 0.789, y: 0.101 },
      { x: 0.555, y: 0.888 },
    ];
    const svgStr = relativeToSvgViewBox(relPoints, 1000, 1000);
    expect(svgStr).toBe('123.00,456.00 789.00,101.00 555.00,888.00');

    const decoded = svgPointsToRelative(svgStr, 1000, 1000);
    expect(decoded.length).toBe(3);
    expect(decoded[0].x).toBeCloseTo(0.123, 2);
    expect(decoded[0].y).toBeCloseTo(0.456, 2);
  });

  test('isPointInPolygon accurately performs spatial hit-testing', () => {
    const square = [
      { x: 0.2, y: 0.2 },
      { x: 0.8, y: 0.2 },
      { x: 0.8, y: 0.8 },
      { x: 0.2, y: 0.8 },
    ];

    expect(isPointInPolygon({ x: 0.5, y: 0.5 }, square)).toBe(true);
    expect(isPointInPolygon({ x: 0.3, y: 0.3 }, square)).toBe(true);
    expect(isPointInPolygon({ x: 0.1, y: 0.5 }, square)).toBe(false);
    expect(isPointInPolygon({ x: 0.9, y: 0.5 }, square)).toBe(false);
  });
});
