'use client';

import React, { useState, useEffect } from 'react';
import { PoligonoBlueprint, LocalEstado } from '../../types';

interface EditPolygonModalProps {
  isOpen: boolean;
  polygon: PoligonoBlueprint | null;
  onClose: () => void;
  onSave: (updated: PoligonoBlueprint) => void;
  onDelete: (polygonId: string) => void;
  onViewFicha?: (localId: string) => void;
}

const CATEGORIAS_COMERCIALES = [
  'Tecnología y Electro',
  'Gastronomía y Cafetería',
  'Moda y Calzado',
  'Bancos y Servicios Financieros',
  'Salud y Belleza',
  'Entretenimiento',
  'Supermercados y Conveniencia',
  'Hogar y Decoración',
  'Otros',
];

const COLOR_PRESETS = [
  { label: 'Verde (Disponible)', value: '#10B981' },
  { label: 'Azul (Arrendado)', value: '#3B82F6' },
  { label: 'Ámbar (Reservado)', value: '#F59E0B' },
  { label: 'Rojo (Mantenimiento)', value: '#EF4444' },
  { label: 'Púrpura (Especial)', value: '#8B5CF6' },
  { label: 'Cyan (Retail)', value: '#06B6D4' },
];

export const EditPolygonModal: React.FC<EditPolygonModalProps> = ({
  isOpen,
  polygon,
  onClose,
  onSave,
  onDelete,
  onViewFicha,
}) => {
  const [codigoLocal, setCodigoLocal] = useState('');
  const [nombreComercial, setNombreComercial] = useState('');
  const [categoria, setCategoria] = useState(CATEGORIAS_COMERCIALES[0]);
  const [estado, setEstado] = useState<LocalEstado>('disponible');
  const [areaM2, setAreaM2] = useState<number>(35.0);
  const [colorRelleno, setColorRelleno] = useState('#3B82F6');
  const [opacidad, setOpacidad] = useState<number>(0.45);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  useEffect(() => {
    if (polygon) {
      setCodigoLocal(polygon.etiqueta || polygon.local?.codigo_local || '');
      setNombreComercial(polygon.local?.nombre_comercial || '');
      setCategoria(polygon.local?.categoria || CATEGORIAS_COMERCIALES[0]);
      setEstado(polygon.local?.estado || 'disponible');
      setAreaM2(polygon.local?.area_m2 || 35.0);
      setColorRelleno(polygon.color_relleno || '#3B82F6');
      setOpacidad(polygon.opacidad || 0.45);
      setShowDeleteConfirm(false);
    }
  }, [polygon]);

  if (!isOpen || !polygon) return null;

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    const updated: PoligonoBlueprint = {
      ...polygon,
      etiqueta: codigoLocal.trim().toUpperCase(),
      color_relleno: colorRelleno,
      opacidad,
      local: {
        ...(polygon.local || {
          id: polygon.local_id || `loc-${Date.now()}`,
          precio_alquiler_mensual: 1500,
          moneda: 'USD',
          piso_nivel: 'Nivel 1',
        }),
        codigo_local: codigoLocal.trim().toUpperCase(),
        nombre_comercial: nombreComercial.trim(),
        categoria,
        estado,
        area_m2: Number(areaM2) || 0,
      },
    };
    onSave(updated);
    onClose();
  };

  const handleDelete = () => {
    onDelete(polygon.id);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-in fade-in duration-150">
      <div className="relative w-full max-w-lg bg-white rounded-2xl shadow-2xl border border-slate-200 overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="flex items-center justify-between p-4 px-6 bg-slate-900 text-white">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center font-bold text-sm">
              ✏️
            </div>
            <div>
              <h2 className="text-sm font-bold">Modificar Polígono y Local</h2>
              <p className="text-[11px] text-slate-400">Modo Proyectos • Edición de propiedades</p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            ✕
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSave} className="p-6 overflow-y-auto space-y-4 flex-1">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">
                Código del Local *
              </label>
              <input
                type="text"
                required
                value={codigoLocal}
                onChange={(e) => setCodigoLocal(e.target.value.toUpperCase())}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-mono font-bold text-slate-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">
                Estado Comercial *
              </label>
              <select
                value={estado}
                onChange={(e) => setEstado(e.target.value as LocalEstado)}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-semibold text-slate-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
              >
                <option value="disponible">Disponible (Verde)</option>
                <option value="arrendado">Arrendado (Azul)</option>
                <option value="reservado">Reservado (Ámbar)</option>
                <option value="mantenimiento">Mantenimiento (Rojo)</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">
              Nombre Comercial / Marca
            </label>
            <input
              type="text"
              value={nombreComercial}
              onChange={(e) => setNombreComercial(e.target.value)}
              placeholder="Ej. STARBUCKS, BITEL, DISPONIBLE..."
              className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-semibold text-slate-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">
                Categoría *
              </label>
              <select
                value={categoria}
                onChange={(e) => setCategoria(e.target.value)}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-medium text-slate-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
              >
                {CATEGORIAS_COMERCIALES.map((cat) => (
                  <option key={cat} value={cat}>
                    {cat}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">
                Superficie Área (m²) *
              </label>
              <input
                type="number"
                step="0.01"
                min="1"
                required
                value={areaM2}
                onChange={(e) => setAreaM2(parseFloat(e.target.value) || 0)}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-mono font-bold text-slate-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
              />
            </div>
          </div>

          {/* Color Presets */}
          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1.5">
              Color de Relleno del Polígono
            </label>
            <div className="grid grid-cols-3 gap-2">
              {COLOR_PRESETS.map((preset) => (
                <button
                  key={preset.value}
                  type="button"
                  onClick={() => setColorRelleno(preset.value)}
                  className={`flex items-center gap-2 p-2 rounded-xl border text-left text-xs font-medium transition-all ${
                    colorRelleno === preset.value
                      ? 'border-blue-500 bg-blue-50/50 shadow-xs'
                      : 'border-slate-200 bg-slate-50 hover:bg-slate-100'
                  }`}
                >
                  <span
                    className="w-3.5 h-3.5 rounded-full flex-shrink-0 border border-black/20"
                    style={{ backgroundColor: preset.value }}
                  />
                  <span className="truncate text-[11px]">{preset.label.split(' ')[0]}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Opacity Slider */}
          <div>
            <div className="flex items-center justify-between text-xs font-bold text-slate-700 mb-1">
              <span>Opacidad del Polígono</span>
              <span className="font-mono text-slate-500">{Math.round(opacidad * 100)}%</span>
            </div>
            <input
              type="range"
              min="0.15"
              max="0.85"
              step="0.05"
              value={opacidad}
              onChange={(e) => setOpacidad(parseFloat(e.target.value))}
              className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
            />
          </div>

          {/* Action Footer Buttons */}
          <div className="pt-3 border-t border-slate-100 flex items-center justify-between gap-2">
            {!showDeleteConfirm ? (
              <button
                type="button"
                onClick={() => setShowDeleteConfirm(true)}
                className="px-3 py-2 text-xs font-bold text-rose-600 hover:text-rose-700 hover:bg-rose-50 rounded-xl transition-colors flex items-center gap-1.5"
              >
                🗑️ Eliminar Polígono
              </button>
            ) : (
              <div className="flex items-center gap-1.5 animate-in fade-in">
                <span className="text-[11px] text-rose-700 font-semibold">¿Seguro?</span>
                <button
                  type="button"
                  onClick={handleDelete}
                  className="px-2.5 py-1 text-xs font-bold bg-rose-600 text-white rounded-lg hover:bg-rose-700"
                >
                  Sí, eliminar
                </button>
                <button
                  type="button"
                  onClick={() => setShowDeleteConfirm(false)}
                  className="px-2 py-1 text-xs font-medium text-slate-600 hover:bg-slate-100 rounded-lg"
                >
                  Cancelar
                </button>
              </div>
            )}

            <div className="flex items-center gap-2 ml-auto">
              {onViewFicha && polygon.local_id && (
                <button
                  type="button"
                  onClick={() => {
                    onClose();
                    onViewFicha(polygon.local_id);
                  }}
                  className="px-3 py-2 text-xs font-bold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-xl transition-colors"
                >
                  Ficha Técnica
                </button>
              )}
              <button
                type="submit"
                className="px-4 py-2 text-xs font-bold text-white bg-blue-600 hover:bg-blue-500 rounded-xl shadow-md shadow-blue-500/20 transition-all"
              >
                Guardar Cambios
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};