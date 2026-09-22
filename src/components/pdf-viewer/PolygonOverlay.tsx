'use client';

import React, { useState, useRef, useEffect, useCallback } from 'react';
import { createPortal } from 'react-dom';
import { PoligonoBlueprint, UserRole, LocalEstado } from '../../types';
import {
  RelativePoint,
  screenToRelative,
  polygonCentroid,
  relativeToSvgViewBox,
  shoelaceArea,
} from '../../lib/coordinateMath';

interface PolygonOverlayProps {
  polygons: PoligonoBlueprint[];
  userRole?: UserRole;
  drawingMode?: boolean;
  onPolygonDrawn?: (newPolygon: RelativePoint[]) => void;
  onSelectLocal?: (localId: string) => void;
  selectedLocalId?: string | null;
  onCancelDrawing?: () => void;
  onDrawingStateChange?: (isDrawing: boolean) => void;
  onEditPolygon?: (polygon: PoligonoBlueprint) => void;
}

const VIEWBOX_SIZE = 1000;

export const PolygonOverlay: React.FC<PolygonOverlayProps> = ({
  polygons,
  userRole = 'comercial',
  drawingMode = false,
  onPolygonDrawn,
  onSelectLocal,
  selectedLocalId,
  onCancelDrawing,
  onDrawingStateChange,
  onEditPolygon,
}) => {
  const [mounted, setMounted] = useState(false);
  useEffect(() => {
    setMounted(true);
  }, []);

  const svgRef = useRef<SVGSVGElement | null>(null);

  // In-progress drawing state
  const [draftVertices, setDraftVertices] = useState<RelativePoint[]>([]);
  const [cursorPos, setCursorPos] = useState<RelativePoint | null>(null);
  const [hoveredPolygonId, setHoveredPolygonId] = useState<string | null>(null);
  const [tooltipPos, setTooltipPos] = useState<{ x: number; y: number } | null>(null);
  const mouseDownPosRef = useRef<{ x: number; y: number } | null>(null);

  const isDrawing = draftVertices.length > 0;

  // Inform parent when drawing starts or stops
  useEffect(() => {
    if (onDrawingStateChange) {
      onDrawingStateChange(isDrawing);
    }
  }, [isDrawing, onDrawingStateChange]);

  // Cancel drawing on Escape key
  const cancelDrawing = useCallback(() => {
    setDraftVertices([]);
    setCursorPos(null);
    if (onCancelDrawing) {
      onCancelDrawing();
    }
  }, [onCancelDrawing]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isDrawing) {
        e.preventDefault();
        cancelDrawing();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isDrawing, cancelDrawing]);

  // Convert mouse event to normalized [0..1] coordinates
  const getNormalizedCoordinates = (e: React.MouseEvent<SVGSVGElement>): RelativePoint | null => {
    if (!svgRef.current) return null;
    const rect = svgRef.current.getBoundingClientRect();
    if (rect.width <= 0 || rect.height <= 0) return null;

    const screenX = e.clientX - rect.left;
    const screenY = e.clientY - rect.top;

    return screenToRelative(screenX, screenY, rect.width, rect.height);
  };

  // Handle clicking to add vertex or close polygon
  const handleSvgClick = (e: React.MouseEvent<SVGSVGElement>) => {
    if (!drawingMode || userRole !== 'proyectos') return;

    // Ignore if user was panning/dragging
    if (mouseDownPosRef.current) {
      const dist = Math.hypot(e.clientX - mouseDownPosRef.current.x, e.clientY - mouseDownPosRef.current.y);
      if (dist > 5) return;
    }

    const relPt = getNormalizedCoordinates(e);
    if (!relPt) return;

    // Check if clicking near start point to close polygon (tolerance: 2% of dimension)
    if (draftVertices.length >= 3) {
      const startPt = draftVertices[0];
      const dist = Math.hypot(relPt.x - startPt.x, relPt.y - startPt.y);
      if (dist < 0.02) {
        finalizePolygon();
        return;
      }
    }

    setDraftVertices((prev) => [...prev, relPt]);
  };

  // Double click closes polygon if at least 3 vertices
  const handleSvgDoubleClick = (e: React.MouseEvent<SVGSVGElement>) => {
    if (!drawingMode || userRole !== 'proyectos') return;
    e.stopPropagation();

    if (draftVertices.length >= 3) {
      finalizePolygon();
    }
  };

  // Finalize polygon and fire callback
  const finalizePolygon = () => {
    if (draftVertices.length < 3) return;

    const completed = [...draftVertices];
    setDraftVertices([]);
    setCursorPos(null);

    if (onPolygonDrawn) {
      onPolygonDrawn(completed);
    }
  };

  // Track mouse movement for rubber-band preview line
  const handleMouseMove = (e: React.MouseEvent<SVGSVGElement>) => {
    if (drawingMode && isDrawing) {
      const relPt = getNormalizedCoordinates(e);
      if (relPt) {
        setCursorPos(relPt);
      }
    }
  };

  // Polygon Status Color Helper
  const getPolygonStyle = (poly: PoligonoBlueprint) => {
    const estado: LocalEstado = poly.local?.estado || 'disponible';
    const isSelected = selectedLocalId && (poly.local_id === selectedLocalId || poly.id === selectedLocalId);
    const isHovered = hoveredPolygonId === poly.id;

    let baseColor = poly.color_relleno || '#3B82F6';
    let borderColor = poly.color_borde || '#1D4ED8';

    switch (estado) {
      case 'disponible':
        baseColor = '#10B981';
        borderColor = '#047857';
        break;
      case 'arrendado':
        baseColor = '#3B82F6';
        borderColor = '#1D4ED8';
        break;
      case 'reservado':
        baseColor = '#F59E0B';
        borderColor = '#B45309';
        break;
      case 'mantenimiento':
        baseColor = '#EF4444';
        borderColor = '#B91C1C';
        break;
    }

    return {
      fill: baseColor,
      stroke: isSelected ? '#FACC15' : borderColor,
      strokeWidth: isSelected ? 3.5 : isHovered ? 2.5 : 1.5,
      fillOpacity: isSelected ? 0.65 : isHovered ? 0.55 : poly.opacidad || 0.35,
    };
  };

  return (
    <>
      <svg
        ref={svgRef}
        viewBox={`0 0 ${VIEWBOX_SIZE} ${VIEWBOX_SIZE}`}
        preserveAspectRatio="none"
        onMouseDown={(e) => {
          mouseDownPosRef.current = { x: e.clientX, y: e.clientY };
        }}
        onClick={handleSvgClick}
        onDoubleClick={handleSvgDoubleClick}
        onMouseMove={handleMouseMove}
        className={`absolute inset-0 w-full h-full select-none ${
          drawingMode && userRole === 'proyectos'
            ? 'cursor-crosshair'
            : 'cursor-inherit pointer-events-auto'
        }`}
      >
        <defs>
          <filter id="polygon-glow" x="-20%" y="-20%" width="140%" height="140%">
            <feDropShadow dx="0" dy="2" stdDeviation="3" floodColor="#000000" floodOpacity="0.2" />
          </filter>
        </defs>

        {/* 1. Render Existing Saved Polygons */}
        {polygons.map((poly) => {
          if (!poly.coordenadas_relativas || poly.coordenadas_relativas.length < 3) return null;

          const pointsAttr = relativeToSvgViewBox(poly.coordenadas_relativas, VIEWBOX_SIZE, VIEWBOX_SIZE);
          const style = getPolygonStyle(poly);
          return (
            <g
              key={poly.id}
              className="transition-all duration-150 group"
              onClick={(e) => {
                if (!drawingMode) {
                  if (mouseDownPosRef.current) {
                    const dist = Math.hypot(e.clientX - mouseDownPosRef.current.x, e.clientY - mouseDownPosRef.current.y);
                    if (dist > 5) return; // Ignore drag/pan
                  }
                  e.stopPropagation();
                  if (userRole === 'proyectos' && onEditPolygon) {
                    onEditPolygon(poly);
                  } else if (onSelectLocal) {
                    onSelectLocal(poly.local_id || poly.id);
                  }
                }
              }}
              onMouseEnter={(e) => {
                if (!drawingMode) {
                  setHoveredPolygonId(poly.id);
                  setTooltipPos({ x: e.clientX, y: e.clientY });
                }
              }}
              onMouseMove={(e) => {
                if (!drawingMode && hoveredPolygonId === poly.id) {
                  setTooltipPos({ x: e.clientX, y: e.clientY });
                }
              }}
              onMouseLeave={() => {
                setHoveredPolygonId(null);
                setTooltipPos(null);
              }}
            >
              <polygon
                points={pointsAttr}
                vectorEffect="non-scaling-stroke"
                fill={style.fill}
                fillOpacity={style.fillOpacity}
                stroke={style.stroke}
                strokeWidth={style.strokeWidth}
                filter="url(#polygon-glow)"
                className={!drawingMode ? 'cursor-pointer hover:filter-none' : ''}
              />
            </g>
          );
        })}

        {/* 2. Render In-Progress Draft Polygon & Rubber-Band Line */}
        {drawingMode && draftVertices.length > 0 && (
          <g className="pointer-events-none">
            {/* Draft Closed Area Preview if >= 3 points */}
            {draftVertices.length >= 3 && cursorPos && (
              <polygon
                points={[...draftVertices, cursorPos]
                  .map((pt) => `${(pt.x * VIEWBOX_SIZE).toFixed(1)},${(pt.y * VIEWBOX_SIZE).toFixed(1)}`)
                  .join(' ')}
                vectorEffect="non-scaling-stroke"
                fill="#3B82F6"
                fillOpacity={0.2}
                stroke="#2563EB"
                strokeWidth={1}
                strokeDasharray="4 4"
              />
            )}

            {/* Connecting Lines between vertices */}
            <polyline
              points={draftVertices
                .map((pt) => `${(pt.x * VIEWBOX_SIZE).toFixed(1)},${(pt.y * VIEWBOX_SIZE).toFixed(1)}`)
                .join(' ')}
              vectorEffect="non-scaling-stroke"
              fill="none"
              stroke="#2563EB"
              strokeWidth={2}
            />

            {/* Live Rubber-Band Line to current mouse cursor */}
            {cursorPos && draftVertices.length > 0 && (
              <line
                x1={draftVertices[draftVertices.length - 1].x * VIEWBOX_SIZE}
                y1={draftVertices[draftVertices.length - 1].y * VIEWBOX_SIZE}
                x2={cursorPos.x * VIEWBOX_SIZE}
                y2={cursorPos.y * VIEWBOX_SIZE}
                vectorEffect="non-scaling-stroke"
                stroke="#F59E0B"
                strokeWidth={2}
                strokeDasharray="3 3"
              />
            )}

            {/* Vertex Anchor Circles */}
            {draftVertices.map((vertex, idx) => (
              <circle
                key={idx}
                cx={vertex.x * VIEWBOX_SIZE}
                cy={vertex.y * VIEWBOX_SIZE}
                r={idx === 0 ? 6 : 4}
                vectorEffect="non-scaling-stroke"
                fill={idx === 0 ? '#10B981' : '#2563EB'}
                stroke="#FFFFFF"
                strokeWidth={2}
              />
            ))}
          </g>
        )}
      </svg>

      {/* Hover Floating Tooltip via React Portal to document.body (guarantees cursor-relative positioning without transform drift) */}
      {mounted && hoveredPolygonId && tooltipPos && createPortal(
        <div
          style={{
            position: 'fixed',
            left: `${tooltipPos.x + 14}px`,
            top: `${tooltipPos.y + 14}px`,
            zIndex: 99999,
          }}
          className="pointer-events-none bg-slate-900/95 backdrop-blur text-white text-xs rounded-xl px-3.5 py-2.5 shadow-2xl border border-slate-700 max-w-xs transition-opacity duration-150 animate-in fade-in"
        >
          {(() => {
            const poly = polygons.find((p) => p.id === hoveredPolygonId);
            if (!poly) return null;
            const loc = poly.local;
            return (
              <div className="space-y-1">
                <div className="flex items-center justify-between gap-3 border-b border-slate-700/80 pb-1">
                  <span className="font-bold text-blue-300 font-mono text-sm">
                    {loc?.codigo_local || poly.etiqueta || 'Local'}
                  </span>
                  <span
                    className={`text-[10px] uppercase font-bold px-1.5 py-0.5 rounded ${
                      loc?.estado === 'disponible'
                        ? 'bg-emerald-500/20 text-emerald-300'
                        : loc?.estado === 'arrendado'
                        ? 'bg-blue-500/20 text-blue-300'
                        : loc?.estado === 'reservado'
                        ? 'bg-amber-500/20 text-amber-300'
                        : 'bg-rose-500/20 text-rose-300'
                    }`}
                  >
                    {loc?.estado || 'disponible'}
                  </span>
                </div>
                {loc?.nombre_comercial && (
                  <p className="font-semibold text-slate-100">{loc.nombre_comercial}</p>
                )}
                <div className="flex items-center justify-between text-[11px] text-slate-300 pt-0.5">
                  <span>{loc?.categoria || 'Comercial'}</span>
                  <span className="font-mono font-medium">{loc?.area_m2 || 0} m²</span>
                </div>
                <p className="text-[10px] text-slate-400 italic pt-1">
                  {userRole === 'proyectos' ? 'Haga clic para editar polígono' : 'Haga clic para ver Ficha del Local'}
                </p>
              </div>
            );
          })()}
        </div>,
        document.body
      )}
    </>
  );
};
