'use client';

import React, { useState } from 'react';
import { Ticket, TicketPriority, TicketType, UserRole } from '../../types';
import { createTicket } from '../../lib/api';
import { useRole } from '../../context/RoleContext';
import { X, TicketIcon, CheckCircle2, AlertCircle } from '../common/Icons';

interface TicketModalProps {
  isOpen: boolean;
  onClose: () => void;
  onTicketCreated?: (ticket: Ticket) => void;
  initialMallId?: string;
  initialLocalId?: string;
  initialLocalCode?: string;
  mallName?: string;
}

export const TicketModal: React.FC<TicketModalProps> = ({
  isOpen,
  onClose,
  onTicketCreated,
  initialMallId = 'plaza-center-villa-el-salvador',
  initialLocalId,
  initialLocalCode,
  mallName = 'Plaza Center Villa El Salvador',
}) => {
  const { role } = useRole();

  const [titulo, setTitulo] = useState('');
  const [descripcion, setDescripcion] = useState('');
  const [tipo, setTipo] = useState<TicketType>('modificacion_plano');
  const [prioridad, setPrioridad] = useState<TicketPriority>('media');
  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!titulo.trim() || !descripcion.trim()) {
      setErrorMsg('Por favor complete el título y la descripción del requerimiento.');
      return;
    }

    setSubmitting(true);
    setErrorMsg(null);

    try {
      const created = await createTicket(
        {
          centro_comercial_id: initialMallId,
          local_id: initialLocalId,
          titulo: titulo.trim(),
          descripcion: descripcion.trim(),
          tipo,
          prioridad,
        },
        role
      );

      if (created) {
        setSuccessMsg(`Requerimiento #${created.codigo_ticket || 'creado'} registrado con éxito.`);
        setTimeout(() => {
          if (onTicketCreated) onTicketCreated(created);
          onClose();
          // Reset form
          setTitulo('');
          setDescripcion('');
          setSuccessMsg(null);
        }, 1200);
      } else {
        throw new Error('No se pudo registrar el ticket en el servidor');
      }
    } catch (err: any) {
      setErrorMsg(err.message || 'Error al conectar con la API de tickets');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-xs animate-in fade-in duration-200">
      <div className="relative w-full max-w-lg bg-white rounded-3xl shadow-2xl border border-slate-200 overflow-hidden">
        {/* Header */}
        <div className="px-6 py-5 bg-gradient-to-r from-blue-600 to-indigo-700 text-white flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-white/15 backdrop-blur-md flex items-center justify-center">
              <TicketIcon size={22} className="text-white" />
            </div>
            <div>
              <h3 className="text-base font-bold leading-tight">Nuevo Requerimiento Técnico</h3>
              <p className="text-xs text-blue-100">
                {initialLocalCode
                  ? `Vinculado al Local ${initialLocalCode} • ${mallName}`
                  : mallName}
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-white/80 hover:text-white p-1.5 rounded-xl hover:bg-white/10 transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        {/* Feedback Alerts */}
        {errorMsg && (
          <div className="mx-6 mt-4 p-3.5 bg-red-50 border border-red-200 rounded-2xl flex items-center gap-2.5 text-xs text-red-700 font-medium">
            <AlertCircle size={16} className="text-red-500 flex-shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        {successMsg && (
          <div className="mx-6 mt-4 p-3.5 bg-emerald-50 border border-emerald-200 rounded-2xl flex items-center gap-2.5 text-xs text-emerald-800 font-semibold">
            <CheckCircle2 size={16} className="text-emerald-600 flex-shrink-0" />
            <span>{successMsg}</span>
          </div>
        )}

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4 text-xs">
          {/* Linked Local Badge */}
          {initialLocalCode && (
            <div className="p-3 bg-blue-50/70 border border-blue-200/80 rounded-2xl flex items-center justify-between">
              <div>
                <span className="text-[10px] font-bold uppercase tracking-wider text-blue-600 block">
                  Activo Asociado
                </span>
                <span className="font-extrabold text-sm text-slate-900 font-mono">
                  {initialLocalCode}
                </span>
              </div>
              <span className="text-[11px] font-medium text-slate-600">
                Plano PACITA VES Nivel 1
              </span>
            </div>
          )}

          {/* Título */}
          <div>
            <label className="block font-bold text-slate-700 mb-1">
              Título del Requerimiento <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              required
              placeholder="Ej. Modificación de fachada, división de local o punto de agua..."
              value={titulo}
              onChange={(e) => setTitulo(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl font-medium text-slate-900 placeholder:text-slate-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all text-xs"
            />
          </div>

          {/* Tipo & Prioridad */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block font-bold text-slate-700 mb-1">Tipo de Requerimiento</label>
              <select
                value={tipo}
                onChange={(e) => setTipo(e.target.value as TicketType)}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl font-medium text-slate-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all text-xs"
              >
                <option value="modificacion_plano">Modificación de Plano</option>
                <option value="division_local">División de Local</option>
                <option value="mantenimiento">Mantenimiento</option>
                <option value="revision_comercial">Revisión Comercial</option>
                <option value="nuevo_requerimiento">Nuevo Requerimiento</option>
              </select>
            </div>

            <div>
              <label className="block font-bold text-slate-700 mb-1">Prioridad</label>
              <select
                value={prioridad}
                onChange={(e) => setPrioridad(e.target.value as TicketPriority)}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl font-medium text-slate-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all text-xs"
              >
                <option value="baja">Baja</option>
                <option value="media">Media</option>
                <option value="alta">Alta</option>
                <option value="urgente">Urgente</option>
              </select>
            </div>
          </div>

          {/* Descripción */}
          <div>
            <label className="block font-bold text-slate-700 mb-1">
              Descripción Detallada <span className="text-red-500">*</span>
            </label>
            <textarea
              required
              rows={3}
              placeholder="Describa el alcance técnico, justificación comercial y consideraciones para el área de proyectos..."
              value={descripcion}
              onChange={(e) => setDescripcion(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl font-medium text-slate-900 placeholder:text-slate-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all text-xs resize-none"
            />
          </div>

          {/* Solicitante Role indicator */}
          <div className="flex items-center justify-between pt-2 border-t border-slate-100 text-[11px] text-slate-500">
            <span>
              Emitido con perfil:{' '}
              <strong className="text-slate-800 uppercase font-bold">{role}</strong>
            </span>
            <span className="text-slate-400">Header: X-User-Role: {role}</span>
          </div>

          {/* Action buttons */}
          <div className="flex items-center justify-end gap-2.5 pt-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl font-bold text-slate-600 hover:bg-slate-100 transition-colors"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-5 py-2.5 rounded-xl font-bold text-white bg-blue-600 hover:bg-blue-700 shadow-md shadow-blue-500/20 transition-all disabled:opacity-50 flex items-center gap-2"
            >
              {submitting ? (
                <>
                  <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  <span>Registrando...</span>
                </>
              ) : (
                <span>Crear Requerimiento</span>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
