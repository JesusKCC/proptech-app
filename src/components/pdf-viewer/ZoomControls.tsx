'use client';

import React from 'react';
import { UserRole } from '../../types';

interface ZoomControlsProps {
  zoom: number;
  onZoomChange: (newZoom: number) => void;
  minZoom?: number;
  maxZoom?: number;
  onReset?: () => void;
  onFitToScreen?: () => void;
  drawingMode?: boolean;
  onToggleDrawingMode?: () => void;
  userRole?: UserRole;
  isDrawingInProgress?: boolean;
}

const ZOOM_PRESETS = [0.4, 0.6, 1.0, 1.5, 2.0];

export const ZoomControls: React.FC<ZoomControlsProps> = ({
  zoom,
  onZoomChange,
  minZoom = 0.2,
  maxZoom = 3.5,
  onReset,
  onFitToScreen,
  drawingMode = false,
  onToggleDrawingMode,
  userRole = 'comercial',
  isDrawingInProgress = false,
}) => {
  const visiblePresets = ZOOM_PRESETS.filter((p) => p >= minZoom - 0.08);

  const handleZoomIn = () => {
    const nextPreset = visiblePresets.find((z) => z > zoom + 0.05);
    if (nextPreset && nextPreset <= maxZoom) {
      onZoomChange(nextPreset);
    } else {
      onZoomChange(Math.min(maxZoom, +(zoom + 0.2).toFixed(2)));
    }
  };

  const handleZoomOut = () => {
    const prevPreset = [...visiblePresets].reverse().find((z) => z < zoom - 0.05);
    if (prevPreset && prevPreset >= minZoom) {
      onZoomChange(prevPreset);
    } else {
      onZoomChange(Math.max(minZoom, +(zoom - 0.2).toFixed(2)));
    }
  };

  const handlePresetClick = (preset: number) => {
    onZoomChange(Math.max(minZoom, preset));
  };

  const handleReset = () => {
    if (onReset) {
      onReset();
    } else {
      onZoomChange(Math.max(minZoom, 1.0));
    }
  };

  return (
    <div className="flex flex-wrap items-center justify-between gap-3 bg-white/95 backdrop-blur-sm border border-slate-200 rounded-xl px-4 py-2.5 shadow-md">
      {/* Zoom Step Controls */}
      <div className="flex items-center gap-1.5">
        <button
          type="button"
          onClick={handleZoomOut}
          disabled={zoom <= minZoom}
          className="p-1.5 text-slate-700 hover:text-slate-950 hover:bg-slate-100 disabled:opacity-40 disabled:hover:bg-transparent rounded-lg transition-colors"
          title="Alejar (-)"
          aria-label="Disminuir zoom"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
          </svg>
        </button>

        <span className="text-sm font-semibold text-slate-800 min-w-[58px] text-center font-mono">
          {Math.round(zoom * 100)}%
        </span>

        <button
          type="button"
          onClick={handleZoomIn}
          disabled={zoom >= maxZoom}
          className="p-1.5 text-slate-700 hover:text-slate-950 hover:bg-slate-100 disabled:opacity-40 disabled:hover:bg-transparent rounded-lg transition-colors"
          title="Acercar (+)"
          aria-label="Aumentar zoom"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
        </button>

        {onFitToScreen && (
          <button
            type="button"
            onClick={onFitToScreen}
            className="flex items-center gap-1 px-2.5 py-1.5 text-xs font-bold text-blue-700 hover:text-blue-900 bg-blue-50 hover:bg-blue-100 border border-blue-200 rounded-lg transition-colors ml-1"
            title="Encuadrar y centrar plano en la pantalla"
            aria-label="Encuadrar plano"
          >
            <svg className="w-3.5 h-3.5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
            </svg>
            <span className="hidden sm:inline">Encuadrar</span>
          </button>
        )}

        <button
          type="button"
          onClick={handleReset}
          className="p-1.5 text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition-colors ml-0.5"
          title="Restablecer a 1.0x (100%)"
          aria-label="Restablecer zoom"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
            />
          </svg>
        </button>
      </div>

      {/* Preset Pills */}
      <div className="hidden sm:flex items-center gap-1 border-l border-slate-200 pl-3">
        {visiblePresets.map((preset) => {
          const isActive = Math.abs(zoom - preset) < 0.05;
          return (
            <button
              key={preset}
              type="button"
              onClick={() => handlePresetClick(preset)}
              className={`px-2.5 py-1 text-xs font-medium rounded-md transition-all ${
                isActive
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
              }`}
            >
              {preset}x
            </button>
          );
        })}
      </div>

      {/* Role & Drawing Mode Action */}
      <div className="flex items-center gap-2 border-l border-slate-200 pl-3">
        {userRole === 'proyectos' ? (
          <button
            type="button"
            onClick={onToggleDrawingMode}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              drawingMode
                ? 'bg-amber-500 text-white shadow-sm ring-2 ring-amber-300 animate-pulse'
                : 'bg-slate-900 text-white hover:bg-slate-800'
            }`}
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"
              />
            </svg>
            <span>{drawingMode ? 'Modo Dibujo Activo' : 'Dibujar Polígono'}</span>
          </button>
        ) : (
          <div
            className="flex items-center gap-1.5 text-xs text-slate-500 bg-slate-100 px-3 py-1 rounded-md cursor-default"
            title="Área Comercial: Modo solo lectura activado"
          >
            <svg className="w-3.5 h-3.5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
              />
            </svg>
            <span>Solo Lectura (Comercial)</span>
          </div>
        )}

        {isDrawingInProgress && (
          <span className="text-[11px] text-amber-700 bg-amber-50 border border-amber-200 px-2 py-0.5 rounded font-medium animate-pulse">
            Trazando (Esc cancela, doble clic finaliza)
          </span>
        )}
      </div>
    </div>
  );
};
