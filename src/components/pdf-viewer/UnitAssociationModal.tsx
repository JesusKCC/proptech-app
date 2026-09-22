'use client';

import React, { useState } from 'react';
import { LocalComercial, LocalEstado } from '../../types';
import { RelativePoint, shoelaceArea } from '../../lib/coordinateMath';

interface UnitAssociationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (data: {
    codigo_local: string;
    nombre_comercial: string;
    categoria: string;
    estado: LocalEstado;
    area_m2: number;
    color_relleno: string;
    existing_local_id?: string;
  }) => void;
  draftPolygon: RelativePoint[];
  availableLocales?: LocalComercial[];
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
  { label: 'Azul (Comercial)', value: '#3B82F6' },
  { label: 'Verde (Disponible)', value: '#10B981' },
  { label: 'Ámbar (Reservado)', value: '#F59E0B' },
  { label: 'Rojo (Mantenimiento)', value: '#EF4444' },
  { label: 'Morado (Especial)', value: '#8B5CF6' },
];

export const UnitAssociationModal: React.FC<UnitAssociationModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  draftPolygon,
  availableLocales = [],
}) => {
  const [mode, setMode] = useState<'existing' | 'new'>('new');
  const [selectedLocalId, setSelectedLocalId] = useState<string>('');
  const [codigoLocal, setCodigoLocal] = useState<string>('');
  const [nombreComercial, setNombreComercial] = useState<string>('');
  const [categoria, setCategoria] = useState<string>(CATEGORIAS_COMERCIALES[0]);
  const [estado, setEstado] = useState<LocalEstado>('disponible');
  const [areaM2, setAreaM2] = useState<number>(35.0);
  const [colorRelleno, setColorRelleno] = useState<string>('#3B82F6');
  const [errorMsg, setErrorMsg] = useState<string>('');

  if (!isOpen) return null;

  // Approximate normalized polygon area fraction
  const relAreaFraction = shoelaceArea(draftPolygon);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg('');

    if (mode === 'existing') {
      if (!selectedLocalId) {
        setErrorMsg('Por favor seleccione un local existente de la lista.');
        return;
      }
      const found = availableLocales.find((l) => l.id === selectedLocalId);
      if (!found) {
        setErrorMsg('Local seleccionado no encontrado.');
        return;
      }
      onConfirm({
        codigo_local: found.codigo_local,
        nombre_comercial: found.nombre_comercial || '',
        categoria: found.categoria,
        estado: found.estado,
        area_m2: found.area_m2,
        color_relleno: colorRelleno,
        existing_local_id: found.id,
      });
    } else {
      if (!codigoLocal.trim()) {
        setErrorMsg('El código de local es obligatorio (ej. LCE-101).');
        return;
      }
      if (areaM2 <= 0) {
        setErrorMsg('El área en m² debe ser mayor a 0.');
        return;
      }
      onConfirm({
        codigo_local: codigoLocal.trim().toUpperCase(),
        nombre_comercial: nombreComercial.trim(),
        categoria,
        estado,
        area_m2: areaM2,
        color_relleno: colorRelleno,
      });
    }
  };

  const handleSelectExisting = (localId: string) => {
    setSelectedLocalId(localId);
    const found = availableLocales.find((l) => l.id === localId);
    if (found) {
      setCodigoLocal(found.codigo_local);
      setNombreComercial(found.nombre_comercial || '');
      setCategoria(found.categoria);
      setEstado(found.estado);
      setAreaM2(found.area_m2);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4 overflow-y-auto">
      <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 max-w-lg w-full overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-700 to-indigo-800 px-6 py-4 text-white">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-bold">Asociar Polígono a Local Comercial</h3>
              <p className="text-xs text-blue-100 mt-0.5">
                Vértices trazados: {draftPolygon.length} | Fracción relativa de plano: {(relAreaFraction * 100).toFixed(2)}%
              </p>
            </div>
            <button
              onClick={onClose}
              className="text-blue-200 hover:text-white rounded-lg p-1 transition-colors"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {errorMsg && (
            <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg text-rose-700 text-xs font-medium">
              {errorMsg}
            </div>
          )}

          {/* Mode Switcher */}
          {availableLocales.length > 0 && (
            <div className="flex border border-slate-200 rounded-lg p-1 bg-slate-50 text-xs font-semibold">
              <button
                type="button"
                onClick={() => setMode('new')}
                className={`flex-1 py-1.5 rounded-md transition-all ${
                  mode === 'new'
                    ? 'bg-white text-blue-700 shadow-sm border border-slate-200/60'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                Crear Nuevo Local
              </button>
              <button
                type="button"
                onClick={() => setMode('existing')}
                className={`flex-1 py-1.5 rounded-md transition-all ${
                  mode === 'existing'
                    ? 'bg-white text-blue-700 shadow-sm border border-slate-200/60'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                Vincular Existente ({availableLocales.length})
              </button>
            </div>
          )}

          {mode === 'existing' ? (
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Seleccionar Local Registrado
              </label>
              <select
                value={selectedLocalId}
                onChange={(e) => handleSelectExisting(e.target.value)}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
              >
                <option value="">-- Seleccionar local del plano --</option>
                {availableLocales.map((loc) => (
                  <option key={loc.id} value={loc.id}>
                    {loc.codigo_local} - {loc.nombre_comercial || 'Sin arrendatario'} ({loc.area_m2} m² - {loc.estado})
                  </option>
                ))}
              </select>
            </div>
          ) : (
            <>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Código de Local *
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="Ej. LCE-103"
                    value={codigoLocal}
                    onChange={(e) => setCodigoLocal(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm font-mono focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Arrendatario / Marca
                  </label>
                  <input
                    type="text"
                    placeholder="Ej. Coolbox, Bitel..."
                    value={nombreComercial}
                    onChange={(e) => setNombreComercial(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Categoría
                  </label>
                  <select
                    value={categoria}
                    onChange={(e) => setCategoria(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                  >
                    {CATEGORIAS_COMERCIALES.map((cat) => (
                      <option key={cat} value={cat}>
                        {cat}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Estado Comercial
                  </label>
                  <select
                    value={estado}
                    onChange={(e) => setEstado(e.target.value as LocalEstado)}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                  >
                    <option value="disponible">Disponible</option>
                    <option value="arrendado">Arrendado</option>
                    <option value="reservado">Reservado</option>
                    <option value="mantenimiento">Mantenimiento</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Área Comercial (m²) *
                </label>
                <input
                  type="number"
                  step="0.01"
                  min="0.1"
                  required
                  value={areaM2}
                  onChange={(e) => setAreaM2(parseFloat(e.target.value) || 0)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                />
              </div>
            </>
          )}

          {/* Color Selector */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1.5">
              Color de Identificación en Plano
            </label>
            <div className="flex items-center gap-2">
              {COLOR_PRESETS.map((cp) => (
                <button
                  key={cp.value}
                  type="button"
                  onClick={() => setColorRelleno(cp.value)}
                  className={`w-7 h-7 rounded-full border-2 transition-transform ${
                    colorRelleno === cp.value ? 'scale-110 border-slate-900 ring-2 ring-blue-400' : 'border-white'
                  }`}
                  style={{ backgroundColor: cp.value }}
                  title={cp.label}
                />
              ))}
              <input
                type="color"
                value={colorRelleno}
                onChange={(e) => setColorRelleno(e.target.value)}
                className="w-7 h-7 rounded cursor-pointer border border-slate-200 p-0 ml-1"
                title="Color personalizado"
              />
            </div>
          </div>

          {/* Modal Actions */}
          <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-200">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-xs font-semibold text-slate-600 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors"
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="px-5 py-2 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg shadow-sm transition-all"
            >
              Guardar y Asociar Polígono
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
