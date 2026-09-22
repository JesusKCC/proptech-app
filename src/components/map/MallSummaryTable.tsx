'use client';

import React, { useState, useMemo, useEffect } from 'react';
import Link from 'next/link';
import { CentroComercial, LocalComercial } from '../../types';
import { fetchCommercialUnits, FALLBACK_LOCALES } from '../../lib/api';
import { LocalesPanel } from './LocalesPanel';
import { CreateMallModal } from './CreateMallModal';
import { EditMallModal } from './EditMallModal';
import {
  Search,
  Filter,
  Building2,
  MapPin,
  Layers,
  ChevronRight,
  Plus,
  Edit3,
  CheckCircle2,
  AlertCircle,
  Clock,
  ExternalLink,
  X,
} from '../common/Icons';

type ActiveFilter = 'malls' | 'locales_todos' | 'locales_ocupados' | 'locales_vacios';

interface MallSummaryTableProps {
  malls: CentroComercial[];
  onSelectMall?: (mall: CentroComercial) => void;
  selectedMallId?: string;
  userRole?: 'comercial' | 'proyectos';
  onMallCreated?: (mall: CentroComercial) => void;
  onMallUpdated?: (mall: CentroComercial) => void;
  searchTerm?: string;
  onSearchChange?: (term: string) => void;
  onLocalesLoaded?: (locales: LocalComercial[]) => void;
}

interface MallStats {
  total: number;
  ocupados: number;
  vacios: number;
  loaded: boolean;
}

// Check if blueprint PDF is available for a mall
const hasBlueprint = (mallIdOrSlug?: string): boolean => {
  if (!mallIdOrSlug) return false;
  const s = mallIdOrSlug.toLowerCase();
  return (
    s === 'plaza-center-villa-el-salvador' ||
    s === '8341cdb0-19c2-4c01-8938-cf59fdfe7aa1' ||
    s.includes('villa-el-salvador')
  );
};

export const MallSummaryTable: React.FC<MallSummaryTableProps> = ({
  malls,
  onSelectMall,
  selectedMallId,
  userRole = 'comercial',
  onMallCreated,
  onMallUpdated,
  searchTerm: externalSearchTerm,
  onSearchChange,
  onLocalesLoaded,
}) => {
  // Search term can be controlled or uncontrolled
  const [internalSearchTerm, setInternalSearchTerm] = useState('');
  const searchTerm = externalSearchTerm !== undefined ? externalSearchTerm : internalSearchTerm;

  const handleSearchInput = (val: string) => {
    setInternalSearchTerm(val);
    if (onSearchChange) onSearchChange(val);
  };

  const [selectedDept, setSelectedDept] = useState('Todos');
  const [activeFilter, setActiveFilter] = useState<ActiveFilter>('malls');

  // Panel: selected mall for drawer/sidebar display
  const [panelMall, setPanelMall] = useState<CentroComercial | null>(null);

  // Modals
  const [showCreate, setShowCreate] = useState(false);
  const [editMall, setEditMall] = useState<CentroComercial | null>(null);

  // All commercial units across the entire portfolio (initialized with verified fallbacks)
  const [allLocales, setAllLocales] = useState<LocalComercial[]>(FALLBACK_LOCALES);
  const [loadingLocales, setLoadingLocales] = useState<boolean>(false);

  // 1. Fetch all commercial units across portfolio on mount with continuous sync
  useEffect(() => {
    let isMounted = true;
    setLoadingLocales(true);

    const safetyTimer = setTimeout(() => {
      if (isMounted) setLoadingLocales(false);
    }, 1200);

    fetchCommercialUnits()
      .then((units) => {
        if (!isMounted) return;
        setAllLocales(units);
        if (onLocalesLoaded) onLocalesLoaded(units);
      })
      .catch((err) => {
        console.warn('Error fetching all commercial units:', err);
      })
      .finally(() => {
        if (isMounted) setLoadingLocales(false);
      });

    return () => {
      isMounted = false;
      clearTimeout(safetyTimer);
    };
  }, [onLocalesLoaded]);

  // Dynamic per-mall stats calculated reactively from allLocales
  const mallStats = useMemo(() => {
    const statsMap: Record<string, MallStats> = {};

    // Initialize stats for each mall
    malls.forEach((m) => {
      const initial: MallStats = { total: 0, ocupados: 0, vacios: 0, loaded: true };
      statsMap[m.id] = initial;
      if (m.slug && m.slug !== m.id) {
        statsMap[m.slug] = initial;
      }
    });

    // Populate counts dynamically from allLocales
    allLocales.forEach((u) => {
      const targetMall = malls.find(
        (m) =>
          m.id === u.centro_comercial_id ||
          m.slug === u.centro_comercial_id ||
          (u.centro_comercial_nombre && m.nombre.toLowerCase() === u.centro_comercial_nombre.toLowerCase())
      );

      const key = targetMall ? targetMall.id : (u.centro_comercial_id || '');
      if (!statsMap[key]) {
        statsMap[key] = { total: 0, ocupados: 0, vacios: 0, loaded: true };
      }

      statsMap[key].total++;
      if (u.estado === 'arrendado' || u.estado === 'reservado' || u.estado === 'mantenimiento') {
        statsMap[key].ocupados++;
      } else if (u.estado === 'disponible') {
        statsMap[key].vacios++;
      }

      if (targetMall && targetMall.slug && targetMall.slug !== key) {
        statsMap[targetMall.slug] = statsMap[key];
      }
    });

    return statsMap;
  }, [malls, allLocales]);

  // Fast Mall lookup map by ID and by slug
  const mallsMap = useMemo(() => {
    const map: Record<string, CentroComercial> = {};
    malls.forEach((m) => {
      map[m.id] = m;
      if (m.slug) map[m.slug] = m;
    });
    return map;
  }, [malls]);

  // Unique departments
  const departments = useMemo(() => {
    const set = new Set<string>();
    malls.forEach((m) => set.add(m.departamento));
    return ['Todos', ...Array.from(set).sort()];
  }, [malls]);

  // 2. Exact Real Portfolio KPI Metrics (Requirement 1)
  const portfolioStats = useMemo(() => {
    const totalMalls = malls.length;
    const totalLocales = allLocales.length;
    const totalOcupados = allLocales.filter(
      (l) => l.estado === 'arrendado' || l.estado === 'reservado' || l.estado === 'mantenimiento'
    ).length;
    const totalVacios = allLocales.filter((l) => l.estado === 'disponible').length;
    return { totalMalls, totalLocales, totalOcupados, totalVacios };
  }, [malls, allLocales]);

  // 3. Filtered Malls (by department + search)
  const filteredMalls = useMemo(() => {
    const term = searchTerm.toLowerCase().trim();
    return malls.filter((m) => {
      const matchesDept = selectedDept === 'Todos' || m.departamento === selectedDept;
      if (!matchesDept) return false;
      if (!term) return true;

      // Matches mall properties directly
      const directMatch =
        m.nombre.toLowerCase().includes(term) ||
        m.departamento.toLowerCase().includes(term) ||
        m.direccion.toLowerCase().includes(term) ||
        (m.distrito && m.distrito.toLowerCase().includes(term));

      if (directMatch) return true;

      // Or matches a local belonging to this mall
      const hasMatchingLocal = allLocales.some(
        (l) =>
          (l.centro_comercial_id === m.id || l.centro_comercial_id === m.slug) &&
          (l.codigo_local.toLowerCase().includes(term) ||
            (l.nombre_comercial && l.nombre_comercial.toLowerCase().includes(term)) ||
            l.categoria.toLowerCase().includes(term))
      );

      return hasMatchingLocal;
    });
  }, [malls, selectedDept, searchTerm, allLocales]);

  // 4. Filtered Locales (by search term and active KPI filter)
  const filteredLocales = useMemo(() => {
    const term = searchTerm.toLowerCase().trim();
    return allLocales.filter((l) => {
      // Filter by KPI activeFilter
      if (activeFilter === 'locales_ocupados') {
        if (l.estado !== 'arrendado' && l.estado !== 'reservado' && l.estado !== 'mantenimiento') return false;
      } else if (activeFilter === 'locales_vacios') {
        if (l.estado !== 'disponible') return false;
      }

      // Filter by search term
      if (!term) return true;

      const mall = mallsMap[l.centro_comercial_id || ''];
      const mallName = mall?.nombre || l.centro_comercial_nombre || '';
      const mallDept = mall?.departamento || '';

      return (
        l.codigo_local.toLowerCase().includes(term) ||
        (l.nombre_comercial && l.nombre_comercial.toLowerCase().includes(term)) ||
        l.categoria.toLowerCase().includes(term) ||
        mallName.toLowerCase().includes(term) ||
        mallDept.toLowerCase().includes(term) ||
        l.estado.toLowerCase().includes(term)
      );
    });
  }, [allLocales, activeFilter, searchTerm, mallsMap]);

  // Helper for status badge style
  const getEstadoBadge = (estado: string) => {
    switch (estado) {
      case 'arrendado':
        return 'bg-emerald-100 text-emerald-800 border-emerald-200';
      case 'disponible':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'reservado':
        return 'bg-amber-100 text-amber-800 border-amber-200';
      case 'mantenimiento':
        return 'bg-rose-100 text-rose-700 border-rose-200';
      default:
        return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  };

  const handleRowClick = (mall: CentroComercial) => {
    setPanelMall((prev) => (prev?.id === mall.id ? null : mall));
    if (onSelectMall) onSelectMall(mall);
  };

  const handleMallCreated = (mall: CentroComercial) => {
    if (onMallCreated) onMallCreated(mall);
    setShowCreate(false);
  };

  const handleMallUpdated = (mall: CentroComercial) => {
    if (onMallUpdated) onMallUpdated(mall);
    setEditMall(null);
  };

  const isProyectos = userRole === 'proyectos';

  return (
    <div className="space-y-6">
      {/* 1. Portfolio KPI Metric Cards — Interactive Clickable Filters (Requirement 1 & 2) */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1: Centros Comerciales */}
        <button
          type="button"
          onClick={() => setActiveFilter('malls')}
          className={`text-left p-5 rounded-2xl border transition-all duration-200 cursor-pointer ${
            activeFilter === 'malls'
              ? 'bg-blue-50/80 border-blue-500 shadow-md ring-2 ring-blue-500/30'
              : 'bg-white border-slate-200 hover:border-blue-300 hover:shadow-xs'
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-600">
              Centros Comerciales
            </span>
            <div
              className={`w-8 h-8 rounded-xl flex items-center justify-center transition-colors ${
                activeFilter === 'malls' ? 'bg-blue-600 text-white' : 'bg-blue-50 text-blue-600'
              }`}
            >
              <Building2 size={18} />
            </div>
          </div>
          <p className="text-3xl font-black text-slate-900 mt-2 font-mono">
            {portfolioStats.totalMalls}
          </p>
          <div className="flex items-center justify-between mt-1 text-xs">
            <span className="text-slate-500">Activos georreferenciados</span>
            <span
              className={`font-bold ${
                activeFilter === 'malls' ? 'text-blue-600' : 'text-slate-400'
              }`}
            >
              {activeFilter === 'malls' ? '• Mostrando' : 'Ver tabla →'}
            </span>
          </div>
        </button>

        {/* Card 2: Locales Totales */}
        <button
          type="button"
          onClick={() => setActiveFilter('locales_todos')}
          className={`text-left p-5 rounded-2xl border transition-all duration-200 cursor-pointer ${
            activeFilter === 'locales_todos'
              ? 'bg-indigo-50/80 border-indigo-500 shadow-md ring-2 ring-indigo-500/30'
              : 'bg-white border-slate-200 hover:border-indigo-300 hover:shadow-xs'
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-600">
              Locales Totales
            </span>
            <div
              className={`w-8 h-8 rounded-xl flex items-center justify-center transition-colors ${
                activeFilter === 'locales_todos'
                  ? 'bg-indigo-600 text-white'
                  : 'bg-indigo-50 text-indigo-600'
              }`}
            >
              <Layers size={18} />
            </div>
          </div>
          <p className="text-3xl font-black text-slate-900 mt-2 font-mono">
            {loadingLocales ? '...' : portfolioStats.totalLocales.toLocaleString()}
          </p>
          <div className="flex items-center justify-between mt-1 text-xs">
            <span className="text-slate-500">Unidades en sistema</span>
            <span
              className={`font-bold ${
                activeFilter === 'locales_todos' ? 'text-indigo-600' : 'text-slate-400'
              }`}
            >
              {activeFilter === 'locales_todos' ? '• Mostrando' : 'Ver locales →'}
            </span>
          </div>
        </button>

        {/* Card 3: Locales Ocupados */}
        <button
          type="button"
          onClick={() => setActiveFilter('locales_ocupados')}
          className={`text-left p-5 rounded-2xl border transition-all duration-200 cursor-pointer ${
            activeFilter === 'locales_ocupados'
              ? 'bg-emerald-50/80 border-emerald-500 shadow-md ring-2 ring-emerald-500/30'
              : 'bg-white border-slate-200 hover:border-emerald-300 hover:shadow-xs'
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-emerald-700">
              Locales Ocupados
            </span>
            <div
              className={`w-8 h-8 rounded-xl flex items-center justify-center transition-colors ${
                activeFilter === 'locales_ocupados'
                  ? 'bg-emerald-600 text-white'
                  : 'bg-emerald-50 text-emerald-600'
              }`}
            >
              <CheckCircle2 size={18} />
            </div>
          </div>
          <p className="text-3xl font-black text-emerald-700 mt-2 font-mono">
            {loadingLocales ? '...' : portfolioStats.totalOcupados.toLocaleString()}
          </p>
          <div className="flex items-center justify-between mt-1 text-xs">
            <span className="text-emerald-600">Arrendados / Reservados / Mant.</span>
            <span
              className={`font-bold ${
                activeFilter === 'locales_ocupados' ? 'text-emerald-700' : 'text-slate-400'
              }`}
            >
              {activeFilter === 'locales_ocupados' ? '• Mostrando' : 'Ver ocupados →'}
            </span>
          </div>
        </button>

        {/* Card 4: Locales Vacíos */}
        <button
          type="button"
          onClick={() => setActiveFilter('locales_vacios')}
          className={`text-left p-5 rounded-2xl border transition-all duration-200 cursor-pointer ${
            activeFilter === 'locales_vacios'
              ? 'bg-blue-50/80 border-blue-500 shadow-md ring-2 ring-blue-500/30'
              : 'bg-white border-slate-200 hover:border-blue-300 hover:shadow-xs'
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-blue-700">
              Locales Vacíos
            </span>
            <div
              className={`w-8 h-8 rounded-xl flex items-center justify-center transition-colors ${
                activeFilter === 'locales_vacios'
                  ? 'bg-blue-600 text-white'
                  : 'bg-blue-50 text-blue-600'
              }`}
            >
              <AlertCircle size={18} />
            </div>
          </div>
          <p className="text-3xl font-black text-blue-700 mt-2 font-mono">
            {loadingLocales ? '...' : portfolioStats.totalVacios.toLocaleString()}
          </p>
          <div className="flex items-center justify-between mt-1 text-xs">
            <span className="text-blue-600">Disponibles comercialmente</span>
            <span
              className={`font-bold ${
                activeFilter === 'locales_vacios' ? 'text-blue-700' : 'text-slate-400'
              }`}
            >
              {activeFilter === 'locales_vacios' ? '• Mostrando' : 'Ver vacíos →'}
            </span>
          </div>
        </button>
      </div>

      {/* 2. Combined Search Bar (Mall & Local Comercial) + Controls (Requirement 3) */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs flex flex-col md:flex-row items-center justify-between gap-4">
        {/* Search input for Mall & Local */}
        <div className="relative w-full md:w-96">
          <Search size={18} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Buscar por mall (nombre, distrito) o por local (código, marca, categoría)..."
            value={searchTerm}
            onChange={(e) => handleSearchInput(e.target.value)}
            className="w-full pl-10 pr-9 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-medium text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all"
          />
          {searchTerm && (
            <button
              type="button"
              onClick={() => handleSearchInput('')}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 p-0.5 rounded-full"
            >
              <X size={14} />
            </button>
          )}
        </div>

        {/* View Switcher Tabs & Filters */}
        <div className="flex items-center gap-2 w-full md:w-auto overflow-x-auto pb-1 md:pb-0">
          {/* Quick tab switch between Malls and Locales */}
          <div className="flex bg-slate-100 p-1 rounded-xl text-xs font-bold">
            <button
              type="button"
              onClick={() => setActiveFilter('malls')}
              className={`px-3 py-1.5 rounded-lg transition-all flex items-center gap-1.5 ${
                activeFilter === 'malls'
                  ? 'bg-white text-blue-700 shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Building2 size={13} />
              <span>Centros Comerciales ({filteredMalls.length})</span>
            </button>
            <button
              type="button"
              onClick={() => setActiveFilter('locales_todos')}
              className={`px-3 py-1.5 rounded-lg transition-all flex items-center gap-1.5 ${
                activeFilter !== 'malls'
                  ? 'bg-white text-blue-700 shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Layers size={13} />
              <span>Locales Comerciales ({filteredLocales.length})</span>
            </button>
          </div>

          {/* Department Filter (Visible when looking at malls) */}
          {activeFilter === 'malls' && (
            <div className="flex items-center gap-1.5 overflow-x-auto pl-2">
              <Filter size={14} className="text-slate-400 flex-shrink-0" />
              <select
                value={selectedDept}
                onChange={(e) => setSelectedDept(e.target.value)}
                className="px-3 py-1.5 bg-slate-100 text-slate-700 rounded-xl text-xs font-bold border-none focus:outline-none focus:ring-2 focus:ring-blue-500/20"
              >
                {departments.map((dept) => (
                  <option key={dept} value={dept}>
                    {dept === 'Todos' ? 'Todos los Deptos' : dept}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Proyectos: Create Button */}
          {isProyectos && (
            <button
              type="button"
              onClick={() => setShowCreate(true)}
              className="flex-shrink-0 flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold text-white bg-emerald-600 hover:bg-emerald-500 transition-all shadow-md shadow-emerald-500/25 ml-auto md:ml-2"
            >
              <Plus size={15} />
              <span>Agregar Centro Comercial</span>
            </button>
          )}
        </div>
      </div>

      {/* 3. Main Tables Area (Requirement 2 & 3) */}
      <div className="flex flex-col xl:flex-row gap-4">
        {/* Table Container */}
        <div className="bg-white rounded-3xl border border-slate-200 shadow-xs overflow-hidden flex-1 min-w-0 transition-all">
          {/* Table Header Strip */}
          <div className="px-6 py-4 border-b border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-bold text-slate-900">
                  {activeFilter === 'malls'
                    ? 'Portafolio de Centros Comerciales'
                    : activeFilter === 'locales_ocupados'
                    ? 'Locales Comerciales — Ocupados (Arrendados / Reservados)'
                    : activeFilter === 'locales_vacios'
                    ? 'Locales Comerciales — Vacíos (Disponibles)'
                    : 'Directorio de Locales Comerciales'}
                </h3>
                {activeFilter !== 'malls' && (
                  <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-blue-100 text-blue-800">
                    {filteredLocales.length} locales
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                {activeFilter === 'malls'
                  ? `Mostrando ${filteredMalls.length} de ${malls.length} centros comerciales en el Perú`
                  : `Listado detallado de unidades con vinculación directa al plano arquitectónico`}
                {searchTerm && (
                  <span className="ml-2 text-blue-600 font-semibold">
                    • Filtro de búsqueda: &quot;{searchTerm}&quot;
                  </span>
                )}
              </p>
            </div>

            {/* If in locales view, sub-filters for quick toggling */}
            {activeFilter !== 'malls' && (
              <div className="flex items-center gap-1.5 bg-slate-50 p-1 rounded-xl border border-slate-200 text-xs">
                <button
                  type="button"
                  onClick={() => setActiveFilter('locales_todos')}
                  className={`px-2.5 py-1 rounded-lg font-bold transition-all ${
                    activeFilter === 'locales_todos'
                      ? 'bg-white text-slate-900 shadow-xs'
                      : 'text-slate-500 hover:text-slate-800'
                  }`}
                >
                  Todos ({portfolioStats.totalLocales})
                </button>
                <button
                  type="button"
                  onClick={() => setActiveFilter('locales_ocupados')}
                  className={`px-2.5 py-1 rounded-lg font-bold transition-all ${
                    activeFilter === 'locales_ocupados'
                      ? 'bg-emerald-600 text-white shadow-xs'
                      : 'text-emerald-700 hover:bg-emerald-50'
                  }`}
                >
                  Ocupados ({portfolioStats.totalOcupados})
                </button>
                <button
                  type="button"
                  onClick={() => setActiveFilter('locales_vacios')}
                  className={`px-2.5 py-1 rounded-lg font-bold transition-all ${
                    activeFilter === 'locales_vacios'
                      ? 'bg-blue-600 text-white shadow-xs'
                      : 'text-blue-700 hover:bg-blue-50'
                  }`}
                >
                  Vacíos ({portfolioStats.totalVacios})
                </button>
              </div>
            )}
          </div>

          {/* VIEW A: Tabla de Centros Comerciales */}
          {activeFilter === 'malls' ? (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 text-slate-500 font-bold border-b border-slate-200 uppercase tracking-wider text-[11px]">
                  <tr>
                    <th className="px-6 py-3.5">Centro Comercial</th>
                    <th className="px-4 py-3.5">Departamento</th>
                    <th className="px-4 py-3.5 text-center">Locales Ocupados</th>
                    <th className="px-4 py-3.5 text-center">Locales Vacíos</th>
                    <th className="px-4 py-3.5 text-center">Locales Totales</th>
                    <th className="px-4 py-3.5 text-right">Acciones</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 font-medium">
                  {filteredMalls.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="px-6 py-12 text-center text-slate-400">
                        No se encontraron centros comerciales con el término &quot;{searchTerm}&quot;.
                      </td>
                    </tr>
                  ) : (
                    filteredMalls.map((mall) => {
                      const isSelected = selectedMallId === mall.id || panelMall?.id === mall.id;
                      const stats = mallStats[mall.id] || mallStats[mall.slug];

                      return (
                        <tr
                          key={mall.id}
                          onClick={() => handleRowClick(mall)}
                          className={`hover:bg-blue-50/50 transition-colors cursor-pointer ${
                            isSelected ? 'bg-blue-50 border-l-2 border-l-blue-500' : ''
                          }`}
                        >
                          {/* Name & Address */}
                          <td className="px-6 py-4">
                            <div className="flex items-center gap-3">
                              <div
                                className={`w-10 h-10 rounded-xl bg-gradient-to-br from-blue-600 to-indigo-700 text-white font-black flex items-center justify-center text-sm shadow-xs flex-shrink-0 ${
                                  isSelected ? 'ring-2 ring-blue-400' : ''
                                }`}
                              >
                                {mall.nombre.charAt(0)}
                              </div>
                              <div>
                                <span className="font-bold text-slate-900 block text-sm">
                                  {mall.nombre}
                                </span>
                                <span className="text-slate-500 text-[11px] block truncate max-w-xs">
                                  {mall.direccion}
                                </span>
                              </div>
                            </div>
                          </td>

                          {/* Department */}
                          <td className="px-4 py-4">
                            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold bg-slate-100 text-slate-700 border border-slate-200">
                              <MapPin size={11} className="text-blue-500" />
                              {mall.departamento}
                            </span>
                            {mall.distrito && (
                              <span className="block text-[11px] text-slate-400 mt-1">
                                {mall.distrito}
                              </span>
                            )}
                          </td>

                          {/* Locales Ocupados */}
                          <td className="px-4 py-4 text-center">
                            {stats?.loaded ? (
                              <span className="font-mono font-bold text-emerald-700 text-sm bg-emerald-50 px-2.5 py-1 rounded-lg border border-emerald-200">
                                {stats.ocupados}
                              </span>
                            ) : (
                              <span className="text-slate-300 text-sm">—</span>
                            )}
                          </td>

                          {/* Locales Vacíos */}
                          <td className="px-4 py-4 text-center">
                            {stats?.loaded ? (
                              <span className="font-mono font-bold text-blue-700 text-sm bg-blue-50 px-2.5 py-1 rounded-lg border border-blue-200">
                                {stats.vacios}
                              </span>
                            ) : (
                              <span className="text-slate-300 text-sm">—</span>
                            )}
                          </td>

                          {/* Locales Totales */}
                          <td className="px-4 py-4 text-center">
                            {stats?.loaded ? (
                              <span className="font-mono font-bold text-slate-900 text-sm bg-slate-100 px-2.5 py-1 rounded-lg">
                                {stats.total}
                              </span>
                            ) : (
                              <span className="text-slate-300 text-sm">—</span>
                            )}
                          </td>

                          {/* Actions */}
                          <td className="px-4 py-4 text-right" onClick={(e) => e.stopPropagation()}>
                            <div className="flex items-center justify-end gap-1.5">
                              <Link
                                href={`/planos?mall_id=${mall.id}`}
                                className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs font-bold text-white bg-blue-600 hover:bg-blue-700 transition-colors shadow-xs"
                              >
                                <Layers size={12} />
                                <span>Ver Planos</span>
                                <ChevronRight size={12} />
                              </Link>
                              {/* Proyectos-only: Edit button */}
                              {isProyectos && (
                                <button
                                  type="button"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    setEditMall(mall);
                                  }}
                                  className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs font-bold text-indigo-700 bg-indigo-50 hover:bg-indigo-100 border border-indigo-200 transition-colors"
                                  title="Editar centro comercial y cargar plano"
                                >
                                  <Edit3 size={12} />
                                  <span>Editar</span>
                                </button>
                              )}
                            </div>
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          ) : (
            /* VIEW B: Tabla de Locales Comerciales (Requirements 2 & 3)
               Columnas: "LOCAL COMERCIAL" | "CODIGO DE LOCAL" | "CENTRO COMERCIAL" | "AREA" | "ESTADO COMERCIAL" | "NIVEL" | "ACCION" */
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 text-slate-500 font-bold border-b border-slate-200 uppercase tracking-wider text-[11px]">
                  <tr>
                    <th className="px-6 py-3.5">LOCAL COMERCIAL</th>
                    <th className="px-4 py-3.5">CODIGO DE LOCAL</th>
                    <th className="px-4 py-3.5">CENTRO COMERCIAL</th>
                    <th className="px-4 py-3.5 text-right">AREA</th>
                    <th className="px-4 py-3.5 text-center">ESTADO COMERCIAL</th>
                    <th className="px-4 py-3.5">NIVEL</th>
                    <th className="px-6 py-3.5 text-right">ACCION</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 font-medium">
                  {filteredLocales.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="px-6 py-12 text-center text-slate-400">
                        {loadingLocales
                          ? 'Cargando directorio de locales comerciales...'
                          : `No se encontraron locales comerciales con los criterios seleccionados.`}
                      </td>
                    </tr>
                  ) : (
                    filteredLocales.map((local) => {
                      const mall = mallsMap[local.centro_comercial_id || ''];
                      const mallName =
                        mall?.nombre || local.centro_comercial_nombre || 'Centro Comercial';
                      const mallId = mall?.id || local.centro_comercial_id || '';
                      const mallSlug = mall?.slug || local.centro_comercial_id || '';
                      const planAvailable = hasBlueprint(mallSlug) || hasBlueprint(mallId);

                      return (
                        <tr
                          key={local.id}
                          className="hover:bg-blue-50/40 transition-colors"
                        >
                          {/* 1. LOCAL COMERCIAL */}
                          <td className="px-6 py-3.5">
                            <div className="flex items-center gap-2.5">
                              <div className="w-8 h-8 rounded-lg bg-slate-100 text-slate-700 font-extrabold flex items-center justify-center text-xs flex-shrink-0 border border-slate-200">
                                {(local.nombre_comercial || local.codigo_local).charAt(0)}
                              </div>
                              <div>
                                <span className="font-bold text-slate-900 block text-sm">
                                  {local.nombre_comercial || (
                                    <span className="text-slate-400 italic">Disponible</span>
                                  )}
                                </span>
                                <span className="text-slate-400 text-[11px] block">
                                  {local.categoria}
                                </span>
                              </div>
                            </div>
                          </td>

                          {/* 2. CODIGO DE LOCAL */}
                          <td className="px-4 py-3.5">
                            <span className="font-mono font-black text-slate-800 text-xs bg-slate-100 px-2 py-1 rounded-md border border-slate-200">
                              {local.codigo_local}
                            </span>
                          </td>

                          {/* 3. CENTRO COMERCIAL */}
                          <td className="px-4 py-3.5">
                            <span className="font-semibold text-slate-800 block text-xs">
                              {mallName}
                            </span>
                            {mall?.departamento && (
                              <span className="text-slate-400 text-[10px]">
                                {mall.departamento}
                              </span>
                            )}
                          </td>

                          {/* 4. AREA */}
                          <td className="px-4 py-3.5 text-right font-mono font-bold text-slate-800 text-xs">
                            {local.area_m2.toFixed(2)} <span className="text-slate-400 text-[10px]">m²</span>
                          </td>

                          {/* 5. ESTADO COMERCIAL */}
                          <td className="px-4 py-3.5 text-center">
                            <span
                              className={`inline-flex items-center gap-1 text-[10px] font-bold uppercase px-2 py-0.5 rounded-full border ${getEstadoBadge(
                                local.estado
                              )}`}
                            >
                              {local.estado}
                            </span>
                          </td>

                          {/* 6. NIVEL */}
                          <td className="px-4 py-3.5 text-xs text-slate-600 font-medium">
                            {local.piso_nivel || 'Nivel 1'}
                          </td>

                          {/* 7. ACCION */}
                          <td className="px-6 py-3.5 text-right">
                            {planAvailable ? (
                              <Link
                                href={`/planos?mall_id=${mallId}&local_id=${local.id}&local_code=${local.codigo_local}`}
                                className="inline-flex items-center gap-1 px-3 py-1.5 rounded-xl text-xs font-bold text-white bg-blue-600 hover:bg-blue-700 transition-all shadow-xs"
                                title="Ver ubicación exacta del módulo en el plano arquitectónico"
                              >
                                <Layers size={13} />
                                <span>Ver en Plano</span>
                                <ChevronRight size={13} />
                              </Link>
                            ) : (
                              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-xl text-[11px] font-bold text-amber-700 bg-amber-50 border border-amber-200">
                                <AlertCircle size={13} className="text-amber-500" />
                                <span>PENDIENTE CARGAR INFORMACIÓN</span>
                              </span>
                            )}
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Side Panel: Locales del mall seleccionado al hacer clic en la fila de Centros Comerciales */}
        {panelMall && activeFilter === 'malls' && (
          <div className="w-full xl:w-80 flex-shrink-0">
            <LocalesPanel mall={panelMall} onClose={() => setPanelMall(null)} />
          </div>
        )}
      </div>

      {/* Modals */}
      <CreateMallModal
        isOpen={showCreate}
        onClose={() => setShowCreate(false)}
        onCreated={handleMallCreated}
      />
      <EditMallModal
        isOpen={!!editMall}
        mall={editMall}
        onClose={() => setEditMall(null)}
        onUpdated={handleMallUpdated}
      />
    </div>
  );
};
