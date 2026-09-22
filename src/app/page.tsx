'use client';

import React, { useState, useEffect, useMemo } from 'react';
import Link from 'next/link';
import { AppNavbar } from '../components/navbar/AppNavbar';
import { PeruSatelliteMap } from '../components/map/PeruSatelliteMap';
import { MallSummaryTable } from '../components/map/MallSummaryTable';
import { CentroComercial, LocalComercial } from '../types';
import { fetchCentrosComerciales, FALLBACK_MALLS, FALLBACK_LOCALES } from '../lib/api';
import { useRole } from '../context/RoleContext';
import {
  Globe,
  Layers,
  TicketIcon,
  Building2,
  ChevronRight,
  ArrowRight,
} from '../components/common/Icons';

export default function HomePage() {
  const { role } = useRole();
  const [malls, setMalls] = useState<CentroComercial[]>(FALLBACK_MALLS);
  const [selectedMall, setSelectedMall] = useState<CentroComercial | null>(null);

  // Search query shared between table and satellite map
  const [searchTerm, setSearchTerm] = useState<string>('');

  // All commercial units across the portfolio
  const [allLocales, setAllLocales] = useState<LocalComercial[]>(FALLBACK_LOCALES);

  useEffect(() => {
    fetchCentrosComerciales()
      .then((data) => setMalls(data))
      .catch(() => setMalls(FALLBACK_MALLS));
  }, []);

  const handleSelectMall = (mall: CentroComercial) => {
    setSelectedMall((prev) => (prev?.id === mall.id ? null : mall));
  };

  // Handle new mall added by Proyectos
  const handleMallCreated = (mall: CentroComercial) => {
    setMalls((prev) => [...prev, mall]);
  };

  // Handle mall updated by Proyectos
  const handleMallUpdated = (updated: CentroComercial) => {
    setMalls((prev) => prev.map((m) => (m.id === updated.id ? updated : m)));
  };

  // Filter locales for satellite map highlights
  const searchedLocales = useMemo(() => {
    const term = searchTerm.toLowerCase().trim();
    if (!term) return [];
    return allLocales.filter(
      (l) =>
        l.codigo_local.toLowerCase().includes(term) ||
        (l.nombre_comercial && l.nombre_comercial.toLowerCase().includes(term)) ||
        l.categoria.toLowerCase().includes(term) ||
        (l.centro_comercial_nombre && l.centro_comercial_nombre.toLowerCase().includes(term))
    );
  }, [allLocales, searchTerm]);

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <AppNavbar />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Hero Section */}
        <section className="bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-900 rounded-3xl p-6 sm:p-10 text-white shadow-xl relative overflow-hidden border border-slate-800">
          <div className="absolute -right-16 -top-16 w-80 h-80 bg-blue-500/10 rounded-full blur-3xl pointer-events-none" />
          <div className="absolute -left-16 -bottom-16 w-80 h-80 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />
          <div className="relative z-10 max-w-3xl space-y-4">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/20 border border-blue-400/30 text-blue-300 text-xs font-semibold">
              <span className="w-2 h-2 rounded-full bg-blue-400 animate-ping" />
              <span>Plataforma PropTech Activa • Georreferenciación &amp; Planos Homotéticos</span>
            </div>
            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-black tracking-tight leading-tight">
              Gestión Comercial de Centros Comerciales en el Perú
            </h1>
            <p className="text-slate-300 text-sm sm:text-base leading-relaxed max-w-2xl">
              Visualización satelital de alta resolución (Esri World Imagery) combinada con planos
              arquitectónicos PDF interactivos. Coordenadas relativas normalizadas con 0.00 drift ante
              zoom e integración de requerimientos técnicos entre Comercial y Proyectos.
            </p>
            <div className="flex flex-wrap items-center gap-3 pt-2">
              <Link
                href="/planos"
                className="px-5 py-2.5 rounded-xl font-bold text-white bg-blue-600 hover:bg-blue-500 shadow-lg shadow-blue-600/30 transition-all text-xs flex items-center gap-2"
              >
                <Layers size={16} />
                <span>Explorar Visor de Planos</span>
                <ChevronRight size={14} />
              </Link>
              <Link
                href="/tickets"
                className="px-5 py-2.5 rounded-xl font-bold text-slate-200 bg-white/10 hover:bg-white/15 border border-white/20 transition-all text-xs flex items-center gap-2"
              >
                <TicketIcon size={16} />
                <span>Bandeja de Tickets</span>
              </Link>
            </div>
          </div>
        </section>

        {/* Section 1: Peru Satellite GIS Map — synchronized with searched locales */}
        <section className="space-y-3">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div>
              <h2 className="text-xl font-extrabold text-slate-900 tracking-tight flex items-center gap-2">
                <Globe size={20} className="text-blue-600" />
                <span>Mapa Satelital Esri — Portafolio Nacional</span>
              </h2>
              <p className="text-xs text-slate-500">
                {searchTerm
                  ? `Mostrando ubicación geográfica de ${searchedLocales.length} local(es) coincidente(s) con "${searchTerm}"`
                  : `${malls.length} centros comerciales georreferenciados • haz clic en un marcador para enfocar`}
              </p>
            </div>
          </div>

          <PeruSatelliteMap
            onSelectMall={handleSelectMall}
            selectedMallId={selectedMall?.id}
            hideCarousel
            searchedLocales={searchedLocales}
            searchQuery={searchTerm}
          />
        </section>

        {/* Section 2: Portfolio Table with all features */}
        <section className="space-y-4 pt-2">
          <div>
            <h2 className="text-xl font-extrabold text-slate-900 tracking-tight flex items-center gap-2">
              <Building2 size={20} className="text-blue-600" />
              <span>Resumen de Activos Comerciales</span>
            </h2>
            <p className="text-xs text-slate-500">
              Métricas reales consolidadas • haz clic en cualquier tarjeta para ver su desglose en tabla
            </p>
          </div>

          <MallSummaryTable
            malls={malls}
            onSelectMall={handleSelectMall}
            selectedMallId={selectedMall?.id}
            userRole={role as 'comercial' | 'proyectos'}
            onMallCreated={handleMallCreated}
            onMallUpdated={handleMallUpdated}
            searchTerm={searchTerm}
            onSearchChange={setSearchTerm}
            onLocalesLoaded={setAllLocales}
          />
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200 bg-white py-6 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-500">
          <div className="flex items-center gap-2">
            <span className="font-bold text-slate-800">PropTech Perú</span>
            <span>•</span>
            <span>Sistema Integral de Gestión de Activos Comerciales</span>
          </div>
          <div className="flex items-center gap-4">
            <Link href="/planos" className="hover:text-blue-600 font-medium">Visor de Planos</Link>
            <Link href="/tickets" className="hover:text-blue-600 font-medium">Bandeja de Requerimientos</Link>
            <span className="font-mono text-[11px] text-slate-400">Esri World Imagery &amp; GIS</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
