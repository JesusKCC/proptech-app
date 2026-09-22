'use client';

import React, { useState, useEffect, useMemo } from 'react';
import { Ticket, TicketStatus, TicketPriority } from '../../types';
import { fetchTickets, resolveTicket } from '../../lib/api';
import { useRole } from '../../context/RoleContext';
import { TicketModal } from './TicketModal';
import {
  TicketIcon,
  Search,
  Filter,
  CheckCircle2,
  AlertCircle,
  Clock,
  UserCheck,
  Shield,
  Plus,
  X,
  Building2,
  Check,
} from '../common/Icons';

export const TicketInbox: React.FC = () => {
  const { role, isProyectos, isComercial } = useRole();

  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<'todos' | 'abiertos' | 'resueltos'>('todos');
  const [priorityFilter, setPriorityFilter] = useState<string>('todos');

  // Creation modal state
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

  // Resolution modal state
  const [resolvingTicket, setResolvingTicket] = useState<Ticket | null>(null);
  const [resolutionNotes, setResolutionNotes] = useState('');
  const [resolvingLoading, setResolvingLoading] = useState(false);
  const [resolutionError, setResolutionError] = useState<string | null>(null);

  // Load tickets
  const loadTickets = async () => {
    setLoading(true);
    try {
      const data = await fetchTickets();
      setTickets(data);
    } catch (err) {
      console.warn('Could not load tickets:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTickets();
  }, []);

  // Filtered tickets
  const filteredTickets = useMemo(() => {
    return tickets.filter((t) => {
      // Status filter
      let matchesStatus = true;
      if (statusFilter === 'abiertos') {
        matchesStatus = t.estado === 'abierto' || t.estado === 'en_progreso';
      } else if (statusFilter === 'resueltos') {
        matchesStatus = t.estado === 'resuelto' || t.estado === 'cancelado';
      }

      // Priority filter
      const matchesPriority =
        priorityFilter === 'todos' || t.prioridad === priorityFilter;

      // Search term
      const term = searchTerm.toLowerCase();
      const matchesSearch =
        !term ||
        t.codigo_ticket.toLowerCase().includes(term) ||
        t.titulo.toLowerCase().includes(term) ||
        t.descripcion.toLowerCase().includes(term) ||
        (t.codigo_local && t.codigo_local.toLowerCase().includes(term)) ||
        (t.centro_comercial_nombre && t.centro_comercial_nombre.toLowerCase().includes(term));

      return matchesStatus && matchesPriority && matchesSearch;
    });
  }, [tickets, statusFilter, priorityFilter, searchTerm]);

  // Handle ticket resolution by Proyectos
  const handleConfirmResolution = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!resolvingTicket) return;
    if (!resolutionNotes.trim()) {
      setResolutionError('Por favor ingrese las notas técnicas de resolución.');
      return;
    }

    setResolvingLoading(true);
    setResolutionError(null);

    try {
      const resolved = await resolveTicket(
        resolvingTicket.id,
        { notas_resolucion: resolutionNotes.trim() },
        role
      );

      if (resolved) {
        setTickets((prev) =>
          prev.map((t) => (t.id === resolvingTicket.id ? { ...t, ...resolved } : t))
        );
        setResolvingTicket(null);
        setResolutionNotes('');
      } else {
        throw new Error('Error al resolver ticket');
      }
    } catch (err: any) {
      setResolutionError(err.message || 'Error al conectar con la API');
    } finally {
      setResolvingLoading(false);
    }
  };

  // Status counts
  const counts = useMemo(() => {
    const total = tickets.length;
    const abiertos = tickets.filter(
      (t) => t.estado === 'abierto' || t.estado === 'en_progreso'
    ).length;
    const resueltos = tickets.filter((t) => t.estado === 'resuelto').length;
    return { total, abiertos, resueltos };
  }, [tickets]);

  const getPriorityBadge = (p: TicketPriority) => {
    switch (p) {
      case 'urgente':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'alta':
        return 'bg-amber-100 text-amber-800 border-amber-200';
      case 'media':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'baja':
        return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  };

  const getStatusBadge = (s: TicketStatus) => {
    switch (s) {
      case 'resuelto':
        return 'bg-emerald-100 text-emerald-800 border-emerald-200';
      case 'en_progreso':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'abierto':
        return 'bg-amber-100 text-amber-800 border-amber-200';
      case 'cancelado':
        return 'bg-slate-100 text-slate-600 border-slate-200';
    }
  };

  return (
    <div className="space-y-6">
      {/* 1. Header & Quick Actions */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-black text-slate-900 tracking-tight flex items-center gap-2.5">
            <TicketIcon size={26} className="text-blue-600" />
            <span>Bandeja de Requerimientos Técnicos</span>
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Triage colaborativo entre Comercial (solicitud) y Proyectos (resolución técnica de planos)
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => setIsCreateModalOpen(true)}
            className="px-4 py-2.5 rounded-xl text-xs font-bold text-white bg-blue-600 hover:bg-blue-700 shadow-md shadow-blue-500/20 transition-all flex items-center gap-1.5"
          >
            <Plus size={16} />
            <span>Nuevo Requerimiento</span>
          </button>
        </div>
      </div>

      {/* 2. RBAC Policy Notice Banner */}
      <div
        className={`p-4 rounded-2xl border text-xs flex items-center justify-between gap-3 ${
          isProyectos
            ? 'bg-emerald-50 border-emerald-200 text-emerald-900'
            : 'bg-blue-50 border-blue-200 text-blue-900'
        }`}
      >
        <div className="flex items-center gap-2.5">
          <Shield size={18} className={isProyectos ? 'text-emerald-600' : 'text-blue-600'} />
          <div>
            <span className="font-bold">
              Rol Activo: {isProyectos ? 'Área de Proyectos' : 'Área Comercial'}
            </span>
            <p className="text-[11px] opacity-90 mt-0.5">
              {isProyectos
                ? 'Permisos habilitados para evaluación técnica, edición de planos y resolución de tickets.'
                : 'Permisos de lectura y creación de tickets activos. La resolución requiere perfil de Proyectos.'}
            </p>
          </div>
        </div>
        <span className="hidden md:inline font-mono font-bold text-[10px] uppercase bg-white/70 px-2 py-1 rounded-lg border border-current">
          Header: X-User-Role: {role}
        </span>
      </div>

      {/* 3. Filter and Triage Bar */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs flex flex-col md:flex-row items-center justify-between gap-4">
        {/* Status Pills */}
        <div className="flex items-center gap-1.5 w-full md:w-auto">
          <button
            type="button"
            onClick={() => setStatusFilter('todos')}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 ${
              statusFilter === 'todos'
                ? 'bg-slate-900 text-white shadow-xs'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            <span>Todos</span>
            <span className="font-mono text-[11px] opacity-80">({counts.total})</span>
          </button>

          <button
            type="button"
            onClick={() => setStatusFilter('abiertos')}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 ${
              statusFilter === 'abiertos'
                ? 'bg-amber-500 text-white shadow-xs'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            <span>Abiertos</span>
            <span className="font-mono text-[11px] opacity-80">({counts.abiertos})</span>
          </button>

          <button
            type="button"
            onClick={() => setStatusFilter('resueltos')}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 ${
              statusFilter === 'resueltos'
                ? 'bg-emerald-600 text-white shadow-xs'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            <span>Resueltos</span>
            <span className="font-mono text-[11px] opacity-80">({counts.resueltos})</span>
          </button>
        </div>

        {/* Search & Priority Select */}
        <div className="flex items-center gap-3 w-full md:w-auto">
          <div className="relative flex-1 md:w-64">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Buscar por código, local..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 bg-slate-50 border border-slate-200 rounded-xl text-xs font-medium text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
            />
          </div>

          <select
            value={priorityFilter}
            onChange={(e) => setPriorityFilter(e.target.value)}
            className="px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-xl text-xs font-medium text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
          >
            <option value="todos">Prioridad: Todas</option>
            <option value="urgente">Urgente</option>
            <option value="alta">Alta</option>
            <option value="media">Media</option>
            <option value="baja">Baja</option>
          </select>
        </div>
      </div>

      {/* 4. Ticket List */}
      <div className="space-y-3">
        {loading ? (
          <div className="bg-white p-12 rounded-3xl border border-slate-200 text-center text-slate-400">
            <div className="w-8 h-8 border-3 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
            <p className="text-xs font-semibold">Cargando bandeja de tickets...</p>
          </div>
        ) : filteredTickets.length === 0 ? (
          <div className="bg-white p-12 rounded-3xl border border-slate-200 text-center text-slate-400">
            <TicketIcon size={32} className="mx-auto text-slate-300 mb-2" />
            <p className="font-bold text-slate-700">No se encontraron tickets</p>
            <p className="text-xs text-slate-400 mt-0.5">
              Pruebe cambiando los filtros de búsqueda o registre un nuevo requerimiento.
            </p>
          </div>
        ) : (
          filteredTickets.map((ticket) => {
            const isResolved = ticket.estado === 'resuelto';

            return (
              <div
                key={ticket.id}
                className="bg-white p-5 rounded-3xl border border-slate-200 shadow-xs hover:border-slate-300 transition-all flex flex-col md:flex-row md:items-center justify-between gap-4"
              >
                {/* Left info */}
                <div className="space-y-2 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-mono font-black text-slate-900 text-sm bg-slate-100 px-2.5 py-0.5 rounded-lg border border-slate-200">
                      {ticket.codigo_ticket}
                    </span>

                    <span
                      className={`text-[10px] font-extrabold uppercase px-2.5 py-0.5 rounded-full border ${getStatusBadge(
                        ticket.estado
                      )}`}
                    >
                      {ticket.estado}
                    </span>

                    <span
                      className={`text-[10px] font-extrabold uppercase px-2.5 py-0.5 rounded-full border ${getPriorityBadge(
                        ticket.prioridad
                      )}`}
                    >
                      {ticket.prioridad}
                    </span>

                    {ticket.codigo_local && (
                      <span className="text-[11px] font-bold text-blue-700 bg-blue-50 px-2 py-0.5 rounded-md border border-blue-200 font-mono">
                        Local {ticket.codigo_local}
                      </span>
                    )}

                    <span className="text-[11px] text-slate-400 flex items-center gap-1">
                      <Clock size={12} />
                      {new Date(ticket.creado_en).toLocaleDateString('es-PE', {
                        day: '2-digit',
                        month: 'short',
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </span>
                  </div>

                  <div>
                    <h4 className="text-base font-extrabold text-slate-900 leading-snug">
                      {ticket.titulo}
                    </h4>
                    <p className="text-xs text-slate-600 mt-1 leading-relaxed">
                      {ticket.descripcion}
                    </p>
                  </div>

                  {/* Resolution Notes preview if resolved */}
                  {ticket.notas_resolucion && (
                    <div className="p-3 bg-emerald-50/80 rounded-2xl border border-emerald-200 text-xs text-emerald-900 mt-2">
                      <div className="flex items-center gap-1.5 font-bold mb-0.5">
                        <CheckCircle2 size={14} className="text-emerald-600" />
                        <span>Resolución Técnica (Área de Proyectos):</span>
                      </div>
                      <p className="text-[11px] text-emerald-800 leading-relaxed font-mono">
                        {ticket.notas_resolucion}
                      </p>
                      {ticket.resuelto_en && (
                        <span className="block text-[10px] text-emerald-600 mt-1">
                          Resuelto el: {new Date(ticket.resuelto_en).toLocaleString('es-PE')}
                        </span>
                      )}
                    </div>
                  )}

                  <div className="flex items-center gap-4 text-[11px] text-slate-400 pt-1">
                    <span>
                      Solicitado por:{' '}
                      <strong className="text-slate-700 uppercase font-semibold">
                        {ticket.creado_por}
                      </strong>
                    </span>
                    <span>•</span>
                    <span>
                      Centro Comercial:{' '}
                      <strong className="text-slate-700 font-semibold">
                        {ticket.centro_comercial_nombre || 'Plaza Center Villa El Salvador'}
                      </strong>
                    </span>
                  </div>
                </div>

                {/* Right Action */}
                <div className="flex items-center gap-2 self-end md:self-center">
                  {!isResolved ? (
                    isProyectos ? (
                      <button
                        type="button"
                        onClick={() => setResolvingTicket(ticket)}
                        className="px-4 py-2.5 rounded-xl text-xs font-bold text-white bg-emerald-600 hover:bg-emerald-700 shadow-md shadow-emerald-500/20 transition-all flex items-center gap-1.5"
                      >
                        <Check size={14} />
                        <span>Resolver Requerimiento</span>
                      </button>
                    ) : (
                      <div className="px-3 py-2 rounded-xl text-xs font-semibold text-slate-400 bg-slate-100 border border-slate-200 flex items-center gap-1.5 cursor-not-allowed">
                        <Shield size={14} className="text-slate-400" />
                        <span title="Solo el Área de Proyectos puede resolver tickets">
                          Resolución (Solo Proyectos)
                        </span>
                      </div>
                    )
                  ) : (
                    <div className="px-3 py-2 rounded-xl text-xs font-bold text-emerald-700 bg-emerald-50 border border-emerald-200 flex items-center gap-1.5">
                      <CheckCircle2 size={16} className="text-emerald-600" />
                      <span>Completado</span>
                    </div>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Ticket Create Modal */}
      <TicketModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onTicketCreated={(newTicket) => {
          setTickets((prev) => [newTicket, ...prev]);
        }}
      />

      {/* Resolution Modal for Proyectos */}
      {resolvingTicket && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-xs animate-in fade-in">
          <div className="relative w-full max-w-lg bg-white rounded-3xl shadow-2xl border border-slate-200 overflow-hidden">
            <div className="px-6 py-5 bg-gradient-to-r from-emerald-600 to-teal-700 text-white flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-2xl bg-white/15 backdrop-blur-md flex items-center justify-center">
                  <CheckCircle2 size={22} className="text-white" />
                </div>
                <div>
                  <h3 className="text-base font-bold leading-tight">Resolución Técnica de Ticket</h3>
                  <p className="text-xs text-emerald-100 font-mono">
                    #{resolvingTicket.codigo_ticket} — {resolvingTicket.titulo}
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setResolvingTicket(null)}
                className="text-white/80 hover:text-white p-1 rounded-xl hover:bg-white/10"
              >
                <X size={20} />
              </button>
            </div>

            {resolutionError && (
              <div className="mx-6 mt-4 p-3 bg-red-50 border border-red-200 rounded-xl text-xs text-red-700 flex items-center gap-2">
                <AlertCircle size={16} className="text-red-500" />
                <span>{resolutionError}</span>
              </div>
            )}

            <form onSubmit={handleConfirmResolution} className="p-6 space-y-4 text-xs">
              <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl">
                <span className="text-[10px] font-bold uppercase text-slate-400 block">
                  Descripción Original del Requerimiento
                </span>
                <p className="text-slate-700 mt-1 font-medium">{resolvingTicket.descripcion}</p>
              </div>

              <div>
                <label className="block font-bold text-slate-700 mb-1">
                  Notas Técnicas de Resolución <span className="text-red-500">*</span>
                </label>
                <textarea
                  required
                  rows={4}
                  placeholder="Detalle la inspección realizada, adecuación arquitectónica en plano o dictamen de aprobación técnica..."
                  value={resolutionNotes}
                  onChange={(e) => setResolutionNotes(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl font-medium text-slate-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 resize-none"
                />
              </div>

              <div className="flex items-center justify-between pt-2 border-t border-slate-100 text-[11px] text-slate-500">
                <span>Autorizador: Área de Proyectos</span>
                <span className="font-mono">PATCH /api/v1/tickets/{resolvingTicket.id}/resolve</span>
              </div>

              <div className="flex items-center justify-end gap-2.5 pt-3">
                <button
                  type="button"
                  onClick={() => setResolvingTicket(null)}
                  className="px-4 py-2 rounded-xl font-bold text-slate-600 hover:bg-slate-100"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={resolvingLoading}
                  className="px-5 py-2.5 rounded-xl font-bold text-white bg-emerald-600 hover:bg-emerald-700 shadow-md shadow-emerald-500/20 disabled:opacity-50 flex items-center gap-2"
                >
                  {resolvingLoading ? (
                    <>
                      <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      <span>Resolviendo...</span>
                    </>
                  ) : (
                    <>
                      <Check size={16} />
                      <span>Confirmar Resolución</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
