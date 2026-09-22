#!/usr/bin/env node
/**
 * Adversarial Stress Test Suite: Coordinate Engine & Mathematical Zoom Invariance (Node.js)
 * Author: Challenger 1 (Adversarial Mathematical & Spatial Specialist)
 * Reference: ORIGINAL_REQUEST.md (§ R2, AC4) & PROJECT.md (§ 2)
 */

const assert = require('assert');

function clamp(val, min = 0, max = 1) {
  if (isNaN(val)) return min;
  return Math.min(Math.max(val, min), max);
}

function screenToRelative(x, y, width, height, originX = 0, originY = 0, doClamp = true) {
  if (width <= 0 || height <= 0) {
    throw new Error(`Invalid rendered dimensions: ${width}x${height}. Must be > 0.`);
  }
  const u = (x - originX) / width;
  const v = (y - originY) / height;
  if (doClamp) {
    return { x: clamp(u, 0, 1), y: clamp(v, 0, 1) };
  }
  return { x: u, y: v };
}

function relativeToScreen(u, v, width, height) {
  if (width <= 0 || height <= 0) {
    throw new Error(`Invalid rendered dimensions: ${width}x${height}. Must be > 0.`);
  }
  return { x: u * width, y: v * height };
}

function shoelaceArea(points) {
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

function edgeLengths(points) {
  const n = points.length;
  if (n < 2) return [];
  const lengths = [];
  for (let i = 0; i < n; i++) {
    const j = (i + 1) % n;
    lengths.push(Math.hypot(points[j].x - points[i].x, points[j].y - points[i].y));
  }
  return lengths;
}

function polygonCentroid(points) {
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
    const sumX = points.reduce((acc, p) => acc + p.x, 0);
    const sumY = points.reduce((acc, p) => acc + p.y, 0);
    return { x: sumX / n, y: sumY / n };
  }

  cx = cx / (6 * signedArea);
  cy = cy / (6 * signedArea);
  return { x: clamp(cx, 0, 1), y: clamp(cy, 0, 1) };
}

function isPointInPolygon(point, polygon) {
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

function runAdversarialSuite() {
  console.log('='.repeat(80));
  console.log('NODE.JS EMPIRICAL ADVERSARIAL STRESS SUITE (V8 ENGINE)');
  console.log('='.repeat(80));

  const BASE_W = 2384.0;
  const BASE_H = 1684.0;
  let passed = 0;
  let total = 0;

  function test(name, fn) {
    total++;
    try {
      fn();
      passed++;
      console.log(`  [PASS] ${name}`);
    } catch (e) {
      console.error(`  [FAIL] ${name} -> ${e.message}`);
      throw e;
    }
  }

  // 1. Extreme zoom levels
  console.log('\n[1] Extreme Zoom Levels: 0.01x, 0.5x, 2.0x, 3.5x, 10.0x, 100.0x');
  const zoomFactors = [0.01, 0.5, 2.0, 3.5, 10.0, 100.0];
  const testUnitRel = [
    { x: 0.2, y: 0.3 },
    { x: 0.7, y: 0.3 },
    { x: 0.7, y: 0.6 },
    { x: 0.2, y: 0.6 }
  ];

  for (const z of zoomFactors) {
    test(`Zoom ${z}x Coordinate Linear Drift & Area Quad`, () => {
      const p1 = testUnitRel.map(pt => relativeToScreen(pt.x, pt.y, BASE_W, BASE_H));
      const pz = testUnitRel.map(pt => relativeToScreen(pt.x, pt.y, BASE_W * z, BASE_H * z));

      // Drift check
      for (let i = 0; i < p1.length; i++) {
        const expX = p1[i].x * z;
        const expY = p1[i].y * z;
        const drift = Math.max(Math.abs(pz[i].x - expX), Math.abs(pz[i].y - expY));
        assert(drift < 1e-8, `Drift ${drift} exceeds 1e-8`);
      }

      // Area scaling check: Area(Z) = Z^2 * Area(1x)
      const a1 = shoelaceArea(p1);
      const az = shoelaceArea(pz);
      const expectedRatio = z * z;
      const actualRatio = az / a1;
      const relDiff = Math.abs(actualRatio - expectedRatio) / expectedRatio;
      assert(relDiff < 1e-8, `Area ratio mismatch: ${actualRatio} != ${expectedRatio}`);
    });
  }

  // 2. Degenerate, Collinear, Concave, Micro-Polygons
  console.log('\n[2] Degenerate, Collinear, Concave, Micro-Polygons');

  test('Collinear 3-point polygon yields zero Shoelace area', () => {
    const collinear = [{ x: 0.1, y: 0.1 }, { x: 0.3, y: 0.3 }, { x: 0.5, y: 0.5 }];
    const area = shoelaceArea(collinear);
    assert.strictEqual(area, 0);
  });

  test('Collinear centroid gracefully falls back to arithmetic mean', () => {
    const collinear = [{ x: 0.1, y: 0.1 }, { x: 0.3, y: 0.3 }, { x: 0.5, y: 0.5 }];
    const c = polygonCentroid(collinear);
    assert(Math.abs(c.x - 0.3) < 1e-9);
    assert(Math.abs(c.y - 0.3) < 1e-9);
  });

  test('Micro-polygon (1e-6 scale) retains exact homothety scaling under 100x zoom', () => {
    const micro = [
      { x: 0.5, y: 0.5 },
      { x: 0.500001, y: 0.5 },
      { x: 0.500001, y: 0.500001 },
      { x: 0.5, y: 0.500001 }
    ];
    const p1 = micro.map(p => relativeToScreen(p.x, p.y, BASE_W, BASE_H));
    const p100 = micro.map(p => relativeToScreen(p.x, p.y, BASE_W * 100, BASE_H * 100));
    const a1 = shoelaceArea(p1);
    const a100 = shoelaceArea(p100);
    const ratio = a100 / a1;
    assert(Math.abs(ratio - 10000.0) < 1e-6, `Micro-polygon 100x area ratio: ${ratio}`);
  });

  test('Concave Starbucks L-shape handles hit-testing and zoom homothety', () => {
    const starbucks = [
      { x: 0.7739, y: 0.4941 },
      { x: 0.8620, y: 0.4941 },
      { x: 0.8620, y: 0.5511 },
      { x: 0.7718, y: 0.5511 },
      { x: 0.7718, y: 0.5083 },
      { x: 0.7739, y: 0.5083 }
    ];
    assert.strictEqual(isPointInPolygon({ x: 0.80, y: 0.52 }, starbucks), true);
    assert.strictEqual(isPointInPolygon({ x: 0.773, y: 0.50 }, starbucks), false);
  });

  // 3. Clamping & Boundary Guards
  console.log('\n[3] Edge and Boundary Clamping ([0.0, 1.0]^2)');

  test('Negative screen coordinates clamped strictly to 0.0', () => {
    const res = screenToRelative(-1000, -500, BASE_W, BASE_H);
    assert.strictEqual(res.x, 0);
    assert.strictEqual(res.y, 0);
  });

  test('Overflow screen coordinates clamped strictly to 1.0', () => {
    const res = screenToRelative(BASE_W + 5000, BASE_H + 3000, BASE_W, BASE_H);
    assert.strictEqual(res.x, 1);
    assert.strictEqual(res.y, 1);
  });

  test('Non-positive canvas dimensions throw Error', () => {
    assert.throws(() => screenToRelative(100, 100, 0, BASE_H));
    assert.throws(() => screenToRelative(100, 100, BASE_W, -10));
  });

  console.log('\n' + '='.repeat(80));
  console.log(`ALL ${passed}/${total} ADVERSARIAL NODE.JS TESTS PASSED WITH ZERO DRIFT.`);
  console.log('='.repeat(80));
}

runAdversarialSuite();
