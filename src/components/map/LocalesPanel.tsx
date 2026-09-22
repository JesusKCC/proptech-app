'use client';

import React, { useState, useEffect } from 'react';
import { CentroComercial, LocalComercial } from '../../types';
import { fetchCommercialUnits } from '../../lib/api';
import {
  X,
  Building2,
  MapPin,
  Layers,
  Search,
  CheckCircle2,
  AlertCircle,
  Clock,
  RefreshCw,
} from '../common/Icons';

interface LocalesPanelProps {
  mall: CentroComercial | null;
  onClose: () => void;
}

const estadoBadge = (estado: string) => {
  switch (estado) {
    case 'arrendado':
      return 'bg-emerald-100 text-emerald-800 border-emerald-200';
    case 'disponible':
      return 'bg-blue-100 text-blue-800 border-blue-200';
    case 'reservado':
      return 'bg-amber-100 text-amber-800 border-amber-200';
    case 'mantenimiento':
      return 'bg-red-100 text-red-700 border-red-200';
    default:
      return 'bg-slate-100 text-slate-600 border-slate-200';
  }
};

const estadoIcon = (estado: string) => {
  switch (estado) {
    case 'arrendado':
      return <CheckCircle2 size={11} />;
    case 'disponible':
      return <Building2 size={11} />;
    case 'reservado':
      return <Clock size={11} />;
    default:
      return <AlertCircle size={11} />;
  }
};

export const LocalesPanel: React.FC<LocalesPanelProps> = ({ mall, onClose }) => {
  const [locales, setLocales] = useState<LocalComercial[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterEstado, setFilterEstado] = useState<string>('todos');

  useEffect(() => {
    if (!mall) return;
    setLoading(true);
    setSearchTerm('');
    setFilterEstado('todos');
    fetchCommercialUnits(mall.id)
      .then((data) => setLocales(data))
      .catch(() => setLocales([]))
      .finally(() => setLoading(false));
  }, [mall?.id]);

  if (!mall) return null;

  const filteredLocales = locales.filter((l) => {
    const term = searchTerm.toLowerCase();
    const matchSearch =
      !term ||
      l.codigo_local.toLowerCase().includes(term) ||
      (l.nombre_comercial && l.nombre_comercial.toLowerCase().includes(term)) ||
      l.categoria.toLowerCase().includes(term);
    const matchEstado = filterEstado === 'todos' || l.estado === filterEstado;
    return matchSearch && matchEstado;
  });

  const ocupados = locales.filter((l) => l.estado === 'arrendado' || l.estado === 'reservado' || l.estado === 'mantenimiento').length;
  const vacios = locales.filter((l) => l.estado === 'disponible').length;

  return (
    <div className="bg-white rounded-3xl border border-slate-200 shadow-sm flex flex-col overflow-hidden" style={{ maxHeight: '680px' }}>
      {/* Header */}
      <div className="p-4 bg-gradient-to-r from-blue-600 to-indigo-600 text-white flex items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2 mb-0.5">
            <div className="w-7 h-7 rounded-lg bg-white/20 flex items-center justify-center font-black text-sm">
              {mall.nombre.charAt(0)}
            </div>
            <h3 className="font-black text-sm leading-tight">{mall.nombre}</h3>
          </div>
          <div className="flex items-center gap-1.5 text-xs text-blue-100 mt-0.5">
            <MapPin size={11} />
            <span>{mall.departamento}{mall.distrito ? ` • ${mall.distrito}` : ''}</span>
          </div>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="p-1.5 rounded-xl bg-white/20 hover:bg-white/30 transition-colors flex-shrink-0"
        >
          <X size={16} />
        </button>
      </div>

      {/* Stats strip */}
      <div className="grid grid-cols-3 divide-x divide-slate-100 border-b border-slate-100">
        <div className="py-2.5 text-center">
          <p className="text-lg font-black text-slate-900 font-mono">{loading ? '...' : locales.length}</p>
          <p className="text-[10px] text-slate-500 uppercase font-bold tracking-wide">Total</p>
        </div>
        <div className="py-2.5 text-center">
          <p className="text-lg font-black text-emerald-600 font-mono">{ocupados}</p>
          <p className="text-[10px] text-emerald-600 uppercase font-bold tracking-wide">Ocupados</p>
        </div>
        <div className="py-2.5 text-center">
          <p className="text-lg font-black text-blue-600 font-mono">{vacios}</p>
          <p className="text-[10px] text-blue-600 uppercase font-bold tracking-wide">Vacíos</p>
        </div>
      </div>

      {/* Search + filter */}
      <div className="px-3 pt-3 pb-2 space-y-2">
        <div className="relative">
          <Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Buscar código, marca, categoría..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-8 pr-3 py-1.5 bg-slate-50 border border-slate-200 rounded-xl text-xs font-medium placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
          />
        </div>
        <div className="flex gap-1 flex-wrap">
          {['todos', 'arrendado', 'disponible', 'reservado', 'mantenimiento'].map((e) => (
            <button
              key={e}
              type="button"
              onClick={() => setFilterEstado(e)}
              className={`px-2.5 py-1 rounded-lg text-[10px] font-bold capitalize transition-all ${
                filterEstado === e
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              {e === 'todos' ? 'Todos' : e}
            </button>
          ))}
        </div>
      </div>

      {/* List */}
      <div className="flex-1 overflow-y-auto px-3 pb-3 space-y-1.5">
        {loading ? (
          <div className="flex flex-col items-center justify-center py-10 gap-2">
            <div className="w-7 h-7 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
            <p className="text-xs text-slate-400">Cargando locales...</p>
          </div>
        ) : filteredLocales.length === 0 ? (
          <div className="text-center py-8 text-slate-400">
            <Building2 size={28} className="mx-auto mb-2 text-slate-300" />
            <p className="text-xs font-medium">No se encontraron locales</p>
            <p className="text-[11px] text-slate-300 mt-1">Intenta cambiar el filtro</p>
          </div>
        ) : (
          filteredLocales.map((local) => (
            <div
              key={local.id}
              className="p-3 rounded-xl bg-slate-50 border border-slate-150 hover:bg-blue-50/60 hover:border-blue-200 transition-all"
            >
              {/* Row 1: code + estado + area */}
              <div className="flex items-center justify-between gap-2 mb-1">
                <div className="flex items-center gap-1.5">
                  <span className="font-mono font-extrabold text-xs text-slate-900">
                    {local.codigo_local}
                  </span>
                  <span className={`inline-flex items-center gap-0.5 text-[9px] font-bold uppercase px-1.5 py-0.5 rounded-full border ${estadoBadge(local.estado)}`}>
                    {estadoIcon(local.estado)}
                    {local.estado}
                  </span>
                </div>
                <span className="font-mono text-xs font-bold text-slate-700">
                  {local.area_m2} m²
                </span>
              </div>
              {/* Row 2: name + category */}
              <div className="flex items-center justify-between gap-2">
                <span className="text-[11px] font-semibold text-slate-700 truncate">
                  {local.nombre_comercial || <span className="text-slate-400 italic">Sin asignar</span>}
                </span>
                <span className="text-[10px] text-slate-400 flex-shrink-0">
                  {local.categoria}
                </span>
              </div>
              {/* Row 3: level + price */}
              <div className="flex items-center justify-between gap-2 mt-1">
                <span className="text-[10px] text-slate-400">
                  {local.piso_nivel || 'Nivel 1'}
                </span>
                {local.precio_alquiler_mensual > 0 && (
                  <span className="text-[10px] font-mono text-slate-500">
                    ${local.precio_alquiler_mensual.toLocaleString()}/mes
                  </span>
                )}
              </div>
              {/* Description if exists */}
              {local.descripcion && (
                <p className="text-[10px] text-slate-400 mt-1 leading-relaxed line-clamp-2">
                  {local.descripcion}
                </p>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};
