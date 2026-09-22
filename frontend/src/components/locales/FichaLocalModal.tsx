'use client';

import React, { useState, useEffect } from 'react';
import { LocalComercial, LocalEstado, Ticket } from '../../types';
import { updateLocal, fetchTickets } from '../../lib/api';
import { useRole } from '../../context/RoleContext';
import { TicketModal } from '../tickets/TicketModal';
import {
  X,
  Edit3,
  Check,
  AlertCircle,
  CheckCircle2,
  TicketIcon,
  Building2,
  Clock,
  Layers,
} from '../common/Icons';

interface FichaLocalModalProps {
  local: LocalComercial | null;
  isOpen: boolean;
  onClose: () => void;
  onLocalUpdated?: (updatedLocal: LocalComercial) => void;
  mallName?: string;
}

export const FichaLocalModal: React.FC<FichaLocalModalProps> = ({
  local,
  isOpen,
  onClose,
  onLocalUpdated,
  mallName = 'Plaza Center Villa El Salvador',
}) => {
  const { role } = useRole();

  // Active tab: 'detalle' | 'editar' | 'tickets'
  const [activeTab, setActiveTab] = useState<'detalle' | 'editar' | 'tickets'>('detalle');

  // Edit form state
  const [formData, setFormData] = useState({
    nombre_comercial: '',
    categoria: '',
    estado: 'disponible' as LocalEstado,
    area_m2: 0,
    precio_alquiler_mensual: 0,
    moneda: 'USD' as 'USD' | 'PEN',
    piso_nivel: 'Nivel 1',
    descripcion: '',
  });

  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [loadingTickets, setLoadingTickets] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [statusMessage, setStatusMessage] = useState('');

  // Ticket Modal open
  const [isTicketModalOpen, setIsTicketModalOpen] = useState(false);

  // Sync form data when local changes
  useEffect(() => {
    if (local) {
      setFormData({
        nombre_comercial: local.nombre_comercial || '',
        categoria: local.categoria || 'Comercio General',
        estado: local.estado || 'disponible',
        area_m2: local.area_m2 || 0,
        precio_alquiler_mensual: local.precio_alquiler_mensual || 0,
        moneda: local.moneda || 'USD',
        piso_nivel: local.piso_nivel || 'Nivel 1',
        descripcion: local.descripcion || '',
      });
      setActiveTab('detalle');
      setSaveStatus('idle');

      // Load associated tickets
      loadTickets(local.id, local.codigo_local);
    }
  }, [local]);

  const loadTickets = async (localId: string, codigoLocal?: string) => {
    setLoadingTickets(true);
    try {
      const allTickets = await fetchTickets(local?.centro_comercial_id);
      const matched = allTickets.filter(
        (t) =>
          t.local_id === localId ||
          (codigoLocal && t.codigo_local === codigoLocal) ||
          (t.descripcion && codigoLocal && t.descripcion.includes(codigoLocal)) ||
          (t.titulo && codigoLocal && t.titulo.includes(codigoLocal))
      );
      setTickets(matched);
    } catch (err) {
      console.warn('Could not load tickets for local:', err);
    } finally {
      setLoadingTickets(false);
    }
  };

  if (!isOpen || !local) return null;

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setSaveStatus('idle');

    try {
      const updated = await updateLocal(
        local.id,
        {
          nombre_comercial: formData.nombre_comercial,
          categoria: formData.categoria,
          estado: formData.estado,
          area_m2: Number(formData.area_m2),
          precio_alquiler_mensual: Number(formData.precio_alquiler_mensual),
          moneda: formData.moneda,
          piso_nivel: formData.piso_nivel,
          descripcion: formData.descripcion,
        },
        role
      );

      if (updated) {
        setSaveStatus('success');
        setStatusMessage('Términos comerciales actualizados en base de datos.');
        if (onLocalUpdated) onLocalUpdated(updated);
        setTimeout(() => {
          setActiveTab('detalle');
          setSaveStatus('idle');
        }, 1200);
      } else {
        throw new Error('Error al actualizar local');
      }
    } catch (err: any) {
      setSaveStatus('error');
      setStatusMessage(err.message || 'Error al persistir cambios');
    } finally {
      setSaving(false);
    }
  };

  const getStatusBadge = (estado: LocalEstado) => {
    switch (estado) {
      case 'disponible':
        return {
          label: 'Disponible',
          bg: 'bg-emerald-50 text-emerald-700 border-emerald-200',
          dot: 'bg-emerald-500',
        };
      case 'arrendado':
        return {
          label: 'Arrendado',
          bg: 'bg-blue-50 text-blue-700 border-blue-200',
          dot: 'bg-blue-600',
        };
      case 'reservado':
        return {
          label: 'Reservado',
          bg: 'bg-amber-50 text-amber-700 border-amber-200',
          dot: 'bg-amber-500',
        };
      case 'mantenimiento':
        return {
          label: 'Mantenimiento',
          bg: 'bg-red-50 text-red-700 border-red-200',
          dot: 'bg-red-500',
        };
      default:
        return {
          label: estado,
          bg: 'bg-slate-50 text-slate-700 border-slate-200',
          dot: 'bg-slate-400',
        };
    }
  };

  const statusInfo = getStatusBadge(local.estado);

  return (
    <>
      <div className="fixed inset-0 z-50 overflow-hidden bg-slate-950/60 backdrop-blur-xs flex justify-end animate-in fade-in duration-200">
        <div className="w-full max-w-md bg-white h-full shadow-2xl flex flex-col justify-between border-l border-slate-200 animate-in slide-in-from-right duration-250">
          {/* Header */}
          <div className="p-5 border-b border-slate-200 bg-slate-50/80">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-black uppercase tracking-widest text-blue-600 bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
                  Ficha del Activo
                </span>
                <span
                  className={`inline-flex items-center gap-1 text-[11px] font-bold px-2 py-0.5 rounded-full border ${statusInfo.bg}`}
                >
                  <span className={`w-1.5 h-1.5 rounded-full ${statusInfo.dot}`} />
                  {statusInfo.label}
                </span>
              </div>
              <button
                type="button"
                onClick={onClose}
                className="text-slate-400 hover:text-slate-700 p-1 rounded-xl hover:bg-slate-200 transition-colors"
              >
                <X size={20} />
              </button>
            </div>

            <div className="flex items-baseline justify-between">
              <div>
                <h2 className="text-2xl font-black text-slate-900 font-mono tracking-tight">
                  {local.codigo_local}
                </h2>
                <p className="text-xs text-slate-500 mt-0.5">
                  {local.nombre_comercial || 'Sin arrendatario asignado'} • {mallName}
                </p>
              </div>
            </div>

            {/* Navigation Tabs */}
            <div className="flex items-center gap-1.5 mt-4 bg-slate-200/70 p-1 rounded-xl">
              <button
                type="button"
                onClick={() => setActiveTab('detalle')}
                className={`flex-1 py-1.5 rounded-lg text-xs font-bold transition-all ${
                  activeTab === 'detalle'
                    ? 'bg-white text-slate-900 shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                Detalle Técnico
              </button>
              <button
                type="button"
                onClick={() => setActiveTab('editar')}
                className={`flex-1 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center justify-center gap-1 ${
                  activeTab === 'editar'
                    ? 'bg-white text-blue-700 shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                <Edit3 size={13} />
                <span>Editar Términos</span>
              </button>
              <button
                type="button"
                onClick={() => setActiveTab('tickets')}
                className={`flex-1 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center justify-center gap-1 ${
                  activeTab === 'tickets'
                    ? 'bg-white text-slate-900 shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                <TicketIcon size={13} />
                <span>Tickets ({tickets.length})</span>
              </button>
            </div>
          </div>

          {/* Body Content by Tab */}
          <div className="flex-1 overflow-y-auto p-5 space-y-5 text-xs">
            {/* Status alerts */}
            {saveStatus === 'success' && (
              <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl flex items-center gap-2 text-emerald-800 font-semibold animate-in fade-in">
                <CheckCircle2 size={16} className="text-emerald-600" />
                <span>{statusMessage}</span>
              </div>
            )}
            {saveStatus === 'error' && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-xl flex items-center gap-2 text-red-700 font-medium animate-in fade-in">
                <AlertCircle size={16} className="text-red-500" />
                <span>{statusMessage}</span>
              </div>
            )}

            {/* TAB 1: DETALLE */}
            {activeTab === 'detalle' && (
              <div className="space-y-4">
                {/* Commercial Key Metrics */}
                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-slate-50 p-3.5 rounded-2xl border border-slate-200">
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                      ÁREA COMERCIAL
                    </span>
                    <span className="text-xl font-black text-slate-900 font-mono mt-0.5 block">
                      {local.area_m2} <span className="text-xs font-normal text-slate-500">m²</span>
                    </span>
                  </div>

                  <div className="bg-slate-50 p-3.5 rounded-2xl border border-slate-200">
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                      RENTA MENSUAL
                    </span>
                    <span className="text-xl font-black text-blue-600 font-mono mt-0.5 block">
                      {local.precio_alquiler_mensual.toLocaleString()}{' '}
                      <span className="text-xs font-normal text-slate-500">{local.moneda}/mes</span>
                    </span>
                  </div>
                </div>

                {/* Technical Specifications */}
                <div className="bg-white rounded-2xl border border-slate-200 divide-y divide-slate-100 overflow-hidden">
                  <div className="p-3 flex justify-between items-center">
                    <span className="text-slate-500 font-medium">Marca / Operador</span>
                    <strong className="text-slate-900 font-bold">
                      {local.nombre_comercial || 'Vacante'}
                    </strong>
                  </div>

                  <div className="p-3 flex justify-between items-center">
                    <span className="text-slate-500 font-medium">Categoría / Rubro</span>
                    <span className="text-slate-800 font-semibold">{local.categoria}</span>
                  </div>

                  <div className="p-3 flex justify-between items-center">
                    <span className="text-slate-500 font-medium">Ubicación / Piso</span>
                    <span className="text-slate-800 font-semibold">{local.piso_nivel}</span>
                  </div>

                  <div className="p-3 flex justify-between items-center">
                    <span className="text-slate-500 font-medium">Centro Comercial</span>
                    <span className="text-slate-800 font-semibold">{mallName}</span>
                  </div>
                </div>

                {/* Description */}
                <div>
                  <h4 className="font-bold text-slate-700 mb-1.5">Descripción del Local</h4>
                  <p className="text-slate-600 leading-relaxed bg-slate-50 p-3 rounded-xl border border-slate-200/80">
                    {local.descripcion ||
                      'Local comercial ubicado sobre la galería principal de alto tránsito peatonal con excelente visibilidad para escaparates y marcas de conveniencia.'}
                  </p>
                </div>

                {/* Outbox integration note */}
                <div className="p-3 bg-blue-50/60 rounded-xl border border-blue-200 text-[11px] text-blue-800 flex items-start gap-2">
                  <Layers size={14} className="text-blue-600 flex-shrink-0 mt-0.5" />
                  <span>
                    Cualquier actualización de este local registra automáticamente un evento en el Outbox
                    (<code className="font-mono text-[10px]">local.actualizado</code>) para sincronización con CRM.
                  </span>
                </div>
              </div>
            )}

            {/* TAB 2: EDITAR */}
            {activeTab === 'editar' && (
              <form onSubmit={handleSave} className="space-y-3.5">
                <div>
                  <label className="block font-bold text-slate-700 mb-1">Nombre Comercial / Marca</label>
                  <input
                    type="text"
                    value={formData.nombre_comercial}
                    onChange={(e) => setFormData({ ...formData, nombre_comercial: e.target.value })}
                    placeholder="Ej. STARBUCKS, COOLBOX, etc."
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl font-medium text-slate-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block font-bold text-slate-700 mb-1">Estado</label>
                    <select
                      value={formData.estado}
                      onChange={(e) => setFormData({ ...formData, estado: e.target.value as LocalEstado })}
                      className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl font-medium text-slate-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                    >
                      <option value="disponible">Disponible</option>
                      <option value="arrendado">Arrendado</option>
                      <option value="reservado">Reservado</option>
                      <option value="mantenimiento">Mantenimiento</option>
                    </select>
                  </div>

                  <div>
                    <label className="block font-bold text-slate-700 mb-1">Categoría</label>
                    <input
                      type="text"
                      value={formData.categoria}
                      onChange={(e) => setFormData({ ...formData, categoria: e.target.value })}
                      placeholder="Tecnología, Moda, etc."
                      className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl font-medium text-slate-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block font-bold text-slate-700 mb-1">Área (m²)</label>
                    <input
                      type="number"
                      step="0.01"
                      value={formData.area_m2}
                      onChange={(e) => setFormData({ ...formData, area_m2: parseFloat(e.target.value) || 0 })}
                      className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl font-mono font-medium text-slate-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block font-bold text-slate-700 mb-1">Renta Mensual ({formData.moneda})</label>
                    <input
                      type="number"
                      step="0.1"
                      value={formData.precio_alquiler_mensual}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          precio_alquiler_mensual: parseFloat(e.target.value) || 0,
                        })
                      }
                      className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl font-mono font-medium text-slate-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                    />
                  </div>
                </div>

                <div>
                  <label className="block font-bold text-slate-700 mb-1">Piso / Nivel</label>
                  <input
                    type="text"
                    value={formData.piso_nivel}
                    onChange={(e) => setFormData({ ...formData, piso_nivel: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl font-medium text-slate-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                  />
                </div>

                <div>
                  <label className="block font-bold text-slate-700 mb-1">Descripción</label>
                  <textarea
                    rows={3}
                    value={formData.descripcion}
                    onChange={(e) => setFormData({ ...formData, descripcion: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl font-medium text-slate-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 resize-none"
                  />
                </div>

                <div className="pt-2">
                  <button
                    type="submit"
                    disabled={saving}
                    className="w-full py-2.5 px-4 rounded-xl font-bold text-white bg-blue-600 hover:bg-blue-700 transition-colors shadow-md shadow-blue-500/20 disabled:opacity-50 flex items-center justify-center gap-2"
                  >
                    {saving ? (
                      <>
                        <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                        <span>Guardando cambios...</span>
                      </>
                    ) : (
                      <>
                        <Check size={16} />
                        <span>Guardar Términos Comerciales</span>
                      </>
                    )}
                  </button>
                </div>
              </form>
            )}

            {/* TAB 3: TICKETS */}
            {activeTab === 'tickets' && (
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-slate-700">Requerimientos Registrados</span>
                  <button
                    type="button"
                    onClick={() => setIsTicketModalOpen(true)}
                    className="text-blue-600 hover:text-blue-700 font-bold text-xs flex items-center gap-1"
                  >
                    + Nuevo Ticket
                  </button>
                </div>

                {loadingTickets ? (
                  <div className="py-8 text-center text-slate-400">
                    <div className="w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
                    <span>Cargando tickets asociados...</span>
                  </div>
                ) : tickets.length === 0 ? (
                  <div className="p-6 text-center bg-slate-50 rounded-2xl border border-dashed border-slate-200">
                    <TicketIcon size={24} className="text-slate-300 mx-auto mb-1.5" />
                    <p className="font-semibold text-slate-600">Sin tickets activos</p>
                    <p className="text-[11px] text-slate-400 mt-0.5">
                      Este local no presenta requerimientos pendientes.
                    </p>
                  </div>
                ) : (
                  tickets.map((t) => (
                    <div
                      key={t.id}
                      className="p-3.5 bg-slate-50 rounded-2xl border border-slate-200 hover:border-slate-300 transition-colors space-y-1.5"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-mono font-bold text-slate-900">{t.codigo_ticket}</span>
                        <span
                          className={`text-[10px] font-extrabold uppercase px-2 py-0.5 rounded-full ${
                            t.estado === 'resuelto'
                              ? 'bg-emerald-100 text-emerald-800'
                              : t.estado === 'en_progreso'
                              ? 'bg-blue-100 text-blue-800'
                              : 'bg-amber-100 text-amber-800'
                          }`}
                        >
                          {t.estado}
                        </span>
                      </div>
                      <p className="font-bold text-slate-800 text-[12px]">{t.titulo}</p>
                      <p className="text-slate-500 text-[11px] line-clamp-2">{t.descripcion}</p>
                      {t.notas_resolucion && (
                        <div className="mt-2 p-2 bg-emerald-50/80 rounded-lg border border-emerald-200 text-[11px] text-emerald-900">
                          <strong>Resolución Proyectos:</strong> {t.notas_resolucion}
                        </div>
                      )}
                    </div>
                  ))
                )}
              </div>
            )}
          </div>

          {/* Footer Actions */}
          <div className="p-5 border-t border-slate-200 bg-slate-50/60 flex items-center gap-3">
            <button
              type="button"
              onClick={() => setIsTicketModalOpen(true)}
              className="flex-1 py-2.5 px-4 rounded-xl text-xs font-bold text-white bg-blue-600 hover:bg-blue-700 transition-all shadow-md shadow-blue-500/20 flex items-center justify-center gap-2"
            >
              <TicketIcon size={15} />
              <span>Crear Requerimiento</span>
            </button>
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2.5 rounded-xl text-xs font-bold text-slate-600 hover:bg-slate-200 transition-colors"
            >
              Cerrar
            </button>
          </div>
        </div>
      </div>

      {/* Ticket Creation Modal */}
      <TicketModal
        isOpen={isTicketModalOpen}
        onClose={() => setIsTicketModalOpen(false)}
        initialMallId={local.centro_comercial_id || 'plaza-center-villa-el-salvador'}
        initialLocalId={local.id}
        initialLocalCode={local.codigo_local}
        mallName={mallName}
        onTicketCreated={(newTicket) => {
          setTickets((prev) => [newTicket, ...prev]);
          setActiveTab('tickets');
        }}
      />
    </>
  );
};
