#!/usr/bin/env node
/**
 * Automated Mathematical Verification Script (Node.js): PDF Zoom Invariance Proof
 * Project: PropTech Interactive Architectural Blueprint Platform
 * Milestone: M2
 */

const assert = require('assert');

function clamp(val, min = 0, max = 1) {
  return Math.min(Math.max(val, min), max);
}

function screenToRelative(x, y, renderedWidth, renderedHeight, originX = 0, originY = 0) {
  if (renderedWidth <= 0 || renderedHeight <= 0) {
    throw new Error('Invalid dimensions');
  }
  const u = (x - originX) / renderedWidth;
  const v = (y - originY) / renderedHeight;
  return { x: clamp(u, 0, 1), y: clamp(v, 0, 1) };
}

function relativeToScreen(u, v, renderedWidth, renderedHeight) {
  if (renderedWidth <= 0 || renderedHeight <= 0) {
    throw new Error('Invalid dimensions');
  }
  return { x: u * renderedWidth, y: v * renderedHeight };
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
  const lengths = [];
  for (let i = 0; i < n; i++) {
    const j = (i + 1) % n;
    lengths.push(Math.hypot(points[j].x - points[i].x, points[j].y - points[i].y));
  }
  return lengths;
}

function verifyUnit(name, polygon1x, baseW, baseH, zoom = 2.0, tolerance = 1e-9) {
  const polyRel = polygon1x.map(pt => screenToRelative(pt.x, pt.y, baseW, baseH));
  const scaledW = baseW * zoom;
  const scaledH = baseH * zoom;
  const polyZoomed = polyRel.map(pt => relativeToScreen(pt.x, pt.y, scaledW, scaledH));

  // Assertion 1: Coordinate linear scaling
  for (let i = 0; i < polygon1x.length; i++) {
    const expX = polygon1x[i].x * zoom;
    const expY = polygon1x[i].y * zoom;
    const driftX = Math.abs(polyZoomed[i].x - expX);
    const driftY = Math.abs(polyZoomed[i].y - expY);
    assert(driftX < tolerance, `[${name}] Vertex ${i} X drift ${driftX} >= ${tolerance}`);
    assert(driftY < tolerance, `[${name}] Vertex ${i} Y drift ${driftY} >= ${tolerance}`);
  }

  // Assertion 2: Edge lengths scale by zoom
  const edges1x = edgeLengths(polygon1x);
  const edgesZoomed = edgeLengths(polyZoomed);
  for (let i = 0; i < edges1x.length; i++) {
    const ratio = edgesZoomed[i] / edges1x[i];
    assert(Math.abs(ratio - zoom) < tolerance, `[${name}] Edge ${i} scale ratio ${ratio} != ${zoom}`);
  }

  // Assertion 3: Area scales by zoom^2
  const area1x = shoelaceArea(polygon1x);
  const areaZoomed = shoelaceArea(polyZoomed);
  const expectedAreaRatio = zoom * zoom;
  const actualAreaRatio = areaZoomed / area1x;
  assert(
    Math.abs(actualAreaRatio - expectedAreaRatio) < tolerance,
    `[${name}] Area ratio ${actualAreaRatio} != ${expectedAreaRatio}`
  );

  // Assertion 4: Normalized round-trip invariance
  for (let i = 0; i < polyRel.length; i++) {
    const rt = screenToRelative(polyZoomed[i].x, polyZoomed[i].y, scaledW, scaledH);
    assert(Math.abs(rt.x - polyRel[i].x) < tolerance, `[${name}] Rel X drift`);
    assert(Math.abs(rt.y - polyRel[i].y) < tolerance, `[${name}] Rel Y drift`);
  }

  return { name, vertices: polygon1x.length, areaRatio: actualAreaRatio };
}

function runSuite() {
  console.log('='.repeat(70));
  console.log('NODE.JS AUTOMATED MATHEMATICAL ZOOM-INVARIANCE TEST');
  console.log('='.repeat(70));

  const PDF_W = 2384.0;
  const PDF_H = 1684.0;

  const testUnits = [
    {
      name: 'COOLBOX (LCE-103)',
      polygon: [
        { x: 1750, y: 830 },
        { x: 1820, y: 830 },
        { x: 1820, y: 885 },
        { x: 1750, y: 885 }
      ]
    },
    {
      name: 'BITEL (LCE-105)',
      polygon: [
        { x: 1570, y: 830 },
        { x: 1695, y: 830 },
        { x: 1695, y: 925 },
        { x: 1570, y: 925 }
      ]
    },
    {
      name: 'ECONOLENTES (LCE-107)',
      polygon: [
        { x: 1465, y: 605 },
        { x: 1515, y: 605 },
        { x: 1524, y: 660 },
        { x: 1465, y: 690 },
        { x: 1465, y: 635 }
      ]
    },
    {
      name: 'STARBUCKS (LCE-101/102)',
      polygon: [
        { x: 1845, y: 832 },
        { x: 2055, y: 832 },
        { x: 2055, y: 928 },
        { x: 1840, y: 928 },
        { x: 1840, y: 856 },
        { x: 1845, y: 856 }
      ]
    }
  ];

  const zooms = [2.0, 1.5, 3.0, 0.75];
  for (const z of zooms) {
    console.log(`\nTesting Zoom: ${z}x`);
    for (const u of testUnits) {
      const res = verifyUnit(u.name, u.polygon, PDF_W, PDF_H, z);
      console.log(`  [PASS] ${res.name} (Vertices: ${res.vertices}) -> Area Ratio: ${res.areaRatio.toFixed(4)}`);
    }
  }

  console.log('\n' + '='.repeat(70));
  console.log('ALL TESTS PASSED: Mathematical Verification Confirmed in Node.js Runtime.');
  console.log('='.repeat(70));
}

runSuite();
